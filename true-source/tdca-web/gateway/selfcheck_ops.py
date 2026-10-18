# -*- coding: utf-8 -*-
"""
A-24 存证公开自查入口 M1″（L1SI154-031）：/api/v1/selfcheck/* —— 只读、匿名、白名单构造。

口径（031 令 · M1″ 第三版，取代已作废之 M1／M1′）：
  - 判据 1 存在性：查到 ⟹ 台账内；查不到 ⟹ 统一 404（同码同文）；
  - 判据 2 未被改写（单行级）：返回 rec_hash，第三方按公开口径重算本行 ⟹ 一致；
  - 判据 3 台账级一致：返回当日锚 anchor_digest 与 row_count，第三方对公开锚件复算 ⟹ 一致；
  - ⛔ 不返回：actor 原值（自然人标识一律不出）／handshake_id／chain_id／side／凭据／内部编号／负空间词面；
    第三方重算所需 actor 以脱敏值 actor_hash=sha256(actor) 前 8 位（小写十六进制）供给；
  - ⛔ 不做列表接口（防枚举）；限流 60 次/分/IP（内存滑窗，超限 429）；
  - 页面标注（031 令 §四 · 原文，不得省）见 _PAGE_DISCLAIMER；
  - 只读：⛔ 不含部署、⛔ 不含对外宣称（不得写「存证已可对外验证」）、⛔ 零凭据入件。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path, PurePosixPath

from fastapi import APIRouter, HTTPException, Request

from api_v1 import _nca_watermark, rec_hash_of  # noqa: E402  （公开口径，单一事实源）
from db import get_session  # noqa: E402
from db import models as M  # noqa: E402

router = APIRouter(prefix="/api/v1/selfcheck", tags=["selfcheck"])

# 031 令 §四 标注原文（⛔ 不得省）
_PAGE_DISCLAIMER = ("本查询可证：该条记录存在于台账，且其内容与写入时一致；"
                    "台账当日形态与公开锚一致。历史各日是否被改写，"
                    "取决于每日锚是否连续可核。")

_RECHASH_SPEC = ("rec_hash = sha256('nca_id|prev_nca|action|actor|artifact_path|"
                 "sha256_8|handshake_id|data_provenance|ts') → 十六进制大写前 16 位"
                 "（空值按空串计；actor 计入哈希但不出原值，以 actor_hash 脱敏供给）")
_ANCHOR_SPEC = ("anchor_digest = sha256('date|row_count|sorted(leaf_hashes).join(\",\")')"
                " → 十六进制大写前 16 位（口径写死在当日锚件 canonicalization 字段）")

_RATE_PER_MIN = 60
_RATE_WINDOW_S = 60
_buckets: dict[str, list[float]] = {}


def _rate_limit(request: Request) -> None:
    """内存滑窗限流（60/分/IP，超限 429）。单实例口径，⛔ 不冒充分布式限流。"""
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    win = _buckets.setdefault(ip, [])
    while win and now - win[0] > _RATE_WINDOW_S:
        win.pop(0)
    if len(win) >= _RATE_PER_MIN:
        raise HTTPException(429, "RATE_LIMITED: 自查入口限流 60 次/分/IP，请稍后再试")
    win.append(now)


def _actor_hash(actor: str | None) -> str:
    """actor 脱敏值：sha256(actor) 前 8 位（小写十六进制）——⛔ 不出原值。"""
    return hashlib.sha256((actor or "").encode("utf-8")).hexdigest()[:8]


def _artifact_filename(artifact_path: str | None) -> str:
    """只给文件名，⛔ 不给目录（031 令字段 4）。"""
    if not artifact_path:
        return ""
    p = artifact_path.replace("\\", "/")
    return PurePosixPath(p).name


def _anchor_dir() -> Path:
    """当日锚目录：env TDCA_ANCHOR_DIR 优先；缺省探测容器/仓内常位。"""
    env = os.environ.get("TDCA_ANCHOR_DIR", "").strip()
    cands = [Path(env)] if env else []
    cands += [Path("/data/anchors"),
              Path(__file__).resolve().parents[3] / "anchors",
              Path(__file__).resolve().parent / "anchors"]
    for c in cands:
        if c.is_dir():
            return c
    return cands[0]


def _latest_anchor() -> dict | None:
    """取当日（最新一份）锚件；无锚件 ⟹ None（fail-closed，不编造）。"""
    d = _anchor_dir()
    files = sorted(d.glob("anchor-*.json")) if d.is_dir() else []
    if not files:
        return None
    try:
        return json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


@router.get("/spec")
def selfcheck_spec():
    """口径公开：重算公式与字段白名单（第三方按此可独立验证，无需我方额外说明）。"""
    return _nca_watermark({
        "entry": {"record": "GET /api/v1/selfcheck/nca/{nca_id}",
                  "anchor": "GET /api/v1/selfcheck/anchor"},
        "rec_hash_spec": _RECHASH_SPEC,
        "anchor_digest_spec": _ANCHOR_SPEC,
        "fields_whitelist": ["nca_id", "action", "ts", "artifact_filename",
                             "sha256_8", "rec_hash", "prev_hash", "detached",
                             "detach_reason", "actor_hash"],
        "not_returned": ["actor（原值，自然人标识一律不出）", "handshake_id",
                         "chain_id", "side", "凭据", "内部编号", "负空间词面"],
        "rate_limit": f"{_RATE_PER_MIN}/min/IP（内存滑窗，单实例口径）",
        "sha256_8_note": "sha256_8 系 artifact_path 之哈希，非记录哈希（如实标注）",
        "page_disclaimer": _PAGE_DISCLAIMER,
    })


@router.get("/nca/{nca_id}")
def selfcheck_nca(nca_id: str, request: Request):
    """单行自查：白名单十字段；不存在 ⟹ 统一 404（同码同文，防探测差异）。"""
    _rate_limit(request)
    with get_session() as s:
        row = s.get(M.NcaChain, nca_id)
        if row is None:
            raise HTTPException(404, "NOT_FOUND: 该 nca_id 不存在于台账（统一 404）")
        payload = {  # ⛔ 白名单构造：不取全量再过滤
            "nca_id": row.nca_id,
            "action": row.action,
            "ts": row.ts,
            "artifact_filename": _artifact_filename(row.artifact_path),
            "sha256_8": row.sha256_8 or "",   # 如实标注：artifact_path 之哈希，非记录哈希
            "rec_hash": row.rec_hash or "",
            "prev_hash": row.prev_hash if row.prev_hash not in (None, "") else
                         ("MISSING" if row.detached == 1 else ""),
            "detached": int(row.detached or 0),
            "detach_reason": row.detach_reason or "",
            "actor_hash": _actor_hash(row.actor),
        }
    return _nca_watermark({
        "record": payload,
        "rec_hash_spec": _RECHASH_SPEC,
        "sha256_8_note": "sha256_8 系 artifact_path 之哈希，非记录哈希（如实标注）",
        "page_disclaimer": _PAGE_DISCLAIMER,
        "note": "只读自查；⛔ 响应不含 actor 原值/凭据/内部编号；"
                "⛔ 不构成对外证明（存证对外可验证性之宣称，另候明示）",
    })


@router.get("/anchor")
def selfcheck_anchor(request: Request):
    """当日锚摘要：anchor_digest 与 row_count；第三方对公开锚件复算 ⟹ 判据 3。
    无锚件 ⟹ 503 fail-closed（如实报，不编造、不冒充）。"""
    _rate_limit(request)
    anchor = _latest_anchor()
    if anchor is None:
        raise HTTPException(
            503, "ANCHOR_UNAVAILABLE: 当日锚件未生成或不可达——台账级一致暂不可核"
                 "（fail-closed，不编造；锚件落盘后自动可核）")
    return _nca_watermark({
        "anchor": {
            "date": anchor.get("date", ""),
            "row_count": anchor.get("row_count"),
            "anchor_digest": anchor.get("anchor_digest", ""),
            "leaf_count": anchor.get("leaf_count"),
            "detached_count": anchor.get("detached_count"),
            "detached_digest": anchor.get("detached_digest", ""),
            "schema_version": anchor.get("schema_version"),
        },
        "anchor_digest_spec": _ANCHOR_SPEC,
        "canonicalization": anchor.get(
            "canonicalization",
            "见锚件内 canonicalization 字段（口径写死，第三方可独立复算）"),
        "page_disclaimer": _PAGE_DISCLAIMER,
        "note": "判据 3：台账当日形态与公开锚一致 ⟸ 第三方复算 anchor_digest；"
                "历史各日须靠每日锚连续累积",
    })
