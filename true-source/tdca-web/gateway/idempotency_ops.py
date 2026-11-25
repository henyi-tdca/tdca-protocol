# -*- coding: utf-8 -*-
"""
WIDEMPOT-BUILD-001（照准 GSEQ-9091/9093）幂等闸：押付／发授权两写端点
重复提交防护——甲路（Idempotency-Key 头）＋丙路（无键指纹 60s 窗）。

制度口径（照令）：
  - 甲路：同键串行重放 ⟹ 同码同体＋`Idempotent-Replayed: true`；同键异体 ⟹
    422「同键已用于不同请求体」（⛔ 静默返首次）；同键并发 ⟹ 一成一拒
    （409「同键处理中」，pending 行占位）；
  - 丙路：无键同体窗内（≤60s）视为重试即拒（409，设计件 §六 取舍）；隔窗
    upsert 重置旧行 ⟹ 均 201、账面 2 行；不同键同体 ⟹ 均 201（合法重复不误挡）；
  - 业务失败键置 failed，同键重试放行（⛔ 被锁死）；
  - ⭐ 重复请求⛔再落 NCA 链节——键表只存 nca_seq 锚；
  - 开关 `IDEMPOTENCY_ENFORCE=0/1`（默认 1；置 0 回旧行为）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError

from db import get_session  # noqa: E402
from db import models as M  # noqa: E402

_ENFORCE_ENV = "IDEMPOTENCY_ENFORCE"
_WINDOW_SEC = 60
_LOCK_RETRY = 3            # sqlite 并发锁短重试（重试间读行态：pending 即拒）
_LOCK_BACKOFF_S = 0.15


def enforce_on() -> bool:
    """开关（每次请求现读环境变量；缺省 1=enforce；非法值 fail-closed 视为 1）。"""
    return os.environ.get(_ENFORCE_ENV, "1").strip() != "0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _within_window(created_at: str) -> bool:
    try:
        ts = datetime.fromisoformat(created_at)
    except ValueError:
        return False
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    return 0 <= age <= _WINDOW_SEC


def fingerprint(subject: str, endpoint: str, reg_no: str, canonical_body: str) -> str:
    """丙路指纹：sha256(subject|endpoint|reg_no|canonical_json)（照令公式）。"""
    raw = f"{subject}|{endpoint}|{reg_no}|{canonical_body}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def body_digest(canonical_body: str) -> str:
    return hashlib.sha256(canonical_body.encode("utf-8")).hexdigest()


def canonical(body: dict) -> str:
    """请求体规范化：键排序＋紧凑分隔（指纹/摘要唯一口径）。"""
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass
class Guard:
    """闸结果：replayed 时端点早返回（同码同体＋回执头）；否则 used_key 供落账锚定。
    fp＝丙路指纹（甲路首投时带出，guard_done 同步落指纹行——K5FIX-001 D3x：
    防甲路带键首投成后丢键同体重放绕闸实产生第二笔）。"""
    active: bool = False
    replayed: bool = False
    replay_status: int = 0
    replay_body: dict | None = None
    used_key: str = ""
    fp: str = ""


def _get_row(s, subject: str, endpoint: str, key: str):
    return s.get(M.IdempotencyKey, {"subject": subject, "endpoint": endpoint,
                                    "key": key})


def _insert_pending(subject: str, endpoint: str, key: str, digest: str) -> None:
    """pending 行占位（独立小事务；冲突/锁即抛 409「同键处理中」）。"""
    for attempt in range(_LOCK_RETRY):
        try:
            with get_session() as s:
                s.add(M.IdempotencyKey(
                    subject=subject, endpoint=endpoint, key=key,
                    status="pending", http_code=None, resp_digest=digest,
                    resp_body_ref=None, nca_seq=None, created_at=_now()))
                s.commit()
            return
        except (IntegrityError, OperationalError):
            with get_session() as s:
                row = _get_row(s, subject, endpoint, key)
                if row is not None:
                    # 并发达成：他请求已占位（pending/done 皆拒；failed 走重试放行）
                    if row.status == "failed":
                        _reset_row(row, digest)
                        s.commit()
                        return
                    raise HTTPException(
                        409, "同键处理中" if row.status == "pending"
                             else "同键已受理——重复提交不受理（同键重放请走原键查询）")
            if attempt < _LOCK_RETRY - 1:
                time.sleep(_LOCK_BACKOFF_S)
    raise HTTPException(409, "同键处理中")


def _reset_row(row, digest: str) -> None:
    """重置旧行（failed 重试／丙路隔窗）：status→pending、窗起点重计。"""
    row.status = "pending"
    row.http_code = None
    row.resp_digest = digest
    row.resp_body_ref = None
    row.nca_seq = None
    row.created_at = _now()


def guard_begin(*, subject: str, endpoint: str, reg_no: str,
                idem_key: str | None, body: dict) -> Guard:
    """业务鉴权后、落账前调用。冲突即抛（409/422）；重放置 Guard.replayed。"""
    if not enforce_on():
        return Guard(active=False)
    canon = canonical(body)
    digest = body_digest(canon)
    fp = fingerprint(subject, endpoint, reg_no, canon)
    if idem_key:                                   # ── 甲路：键 ──
        with get_session() as s:
            row = _get_row(s, subject, endpoint, idem_key)
            if row is not None:
                if row.status == "pending":
                    raise HTTPException(409, "同键处理中")
                if row.status == "done":
                    if row.resp_digest == digest:
                        g = Guard(active=True, replayed=True,
                                  replay_status=int(row.http_code or 200),
                                  replay_body=json.loads(row.resp_body_ref or "{}"))
                        g.used_key = idem_key
                        return g
                    raise HTTPException(
                        422, "同键已用于不同请求体（⛔ 静默返首次：请另换幂等键）")
                # failed → 下方重试放行（重置）
                _reset_row(row, digest)
                s.commit()
                g = Guard(active=True, used_key=idem_key, fp=fp)
                return g
        _insert_pending(subject, endpoint, idem_key, digest)
        return Guard(active=True, used_key=idem_key, fp=fp)
    # ── 丙路：无键指纹窗 ──
    with get_session() as s:
        row = _get_row(s, subject, endpoint, fp)
        if row is not None and row.status == "done" and _within_window(row.created_at):
            raise HTTPException(
                409, "同请求体短时重复（60s 窗内视为重试即拒；设计件 §六 取舍）")
        if row is None:
            s.add(M.IdempotencyKey(
                subject=subject, endpoint=endpoint, key=fp,
                status="pending", http_code=None, resp_digest=digest,
                resp_body_ref=None, nca_seq=None, created_at=_now()))
            s.commit()
        else:
            _reset_row(row, digest)
            s.commit()
    return Guard(active=True, used_key=fp)


def guard_done(*, subject: str, endpoint: str, key: str, fp: str = "",
               http_code: int, body: dict, nca_seq: str) -> None:
    """首成落锚：status→done＋响应摘要＋nca_seq（⛔ 重复请求再落链节）。

    resp_digest 保持 pending 期所存之**请求体摘要**（重放判同体之据），
    此处⛔覆写——响应体摘要走 resp_body_ref 全文自证。
    K5FIX-001（甲案）：甲路首投成 ⟹ 同步落丙路指纹行（同 subject/endpoint/fp），
    封堵丢键同体重放绕闸；行已存在（丙路在役/pending 并发）不动，保其窗起点。
    """
    if not key or not enforce_on():
        return
    with get_session() as s:
        row = _get_row(s, subject, endpoint, key)
        if row is None:
            return
        row.status = "done"
        row.http_code = http_code
        row.resp_body_ref = json.dumps(body, ensure_ascii=False)
        row.nca_seq = nca_seq
        s.commit()
    if fp and fp != key:
        with get_session() as s:
            fp_row = _get_row(s, subject, endpoint, fp)
            if fp_row is None:
                try:
                    with get_session() as s2:
                        s2.add(M.IdempotencyKey(
                            subject=subject, endpoint=endpoint, key=fp,
                            status="done", http_code=http_code,
                            resp_digest=body_digest(canonical(body)),
                            resp_body_ref=json.dumps(body, ensure_ascii=False),
                            nca_seq=nca_seq, created_at=_now()))
                        s2.commit()
                except IntegrityError:
                    pass  # 并发已占位/在役：不打扰（其自身 guard_done 会落锚）


def guard_failed(*, subject: str, endpoint: str, key: str) -> None:
    """业务失败：键置 failed（同键重试放行，⛔ 锁死）。"""
    if not key or not enforce_on():
        return
    with get_session() as s:
        row = _get_row(s, subject, endpoint, key)
        if row is None:
            return
        row.status = "failed"
        row.http_code = None
        row.resp_body_ref = None
        row.nca_seq = None
        s.commit()
