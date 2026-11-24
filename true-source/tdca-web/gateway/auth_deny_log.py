# -*- coding: utf-8 -*-
"""CASENORM-K3-001 B部·K-3 留证补强：人类面鉴权拒绝专档（JSONL）＋轮转＋降级告警。

落点：AUTH_DENY_LOG（默认 /data/auth_deny.log，与 tdca.db 同卷，持久）。
字段（B-1 四要素＋三辅助）：ts／path／method／http_code／subject／code／source。
隐私口径：subject 仅二选一——未登录记 anonymous；已登录记系统内注册主体 username。
⛔ 会话指纹／凭据值／自然人姓名／IP（不在四要素内，本批不增）。

防护（MR613-API-001 §A-0）：
R-1 单档 ≤50MB，达限轮转；R-2 保留 7 份淘汰最旧；R-4 轮转件同格式 JSONL；
R-3/R-5 写失败／降级＋告警（不静默）：计数文件 AUTH_DENY_LOG_DROPPED
（默认 /data/auth_deny_log.dropped.json）＋stderr 一行 AUTH_DENY_LOG_DEGRADED。
全程 best-effort：落档/轮转/告警任何失败永不抛异常、永不反转拒绝裁决。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_PATH = "/data/auth_deny.log"
_DEFAULT_DROPPED = "/data/auth_deny_log.dropped.json"
_SIZE_LIMIT = 50 * 1024 * 1024  # R-1：50 MB
_KEEP = 7                      # R-2：保留 7 份


def _path() -> Path:
    return Path(os.environ.get("AUTH_DENY_LOG", _DEFAULT_PATH))


def _dropped_path() -> Path:
    return Path(os.environ.get("AUTH_DENY_LOG_DROPPED", _DEFAULT_DROPPED))


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _alert_degraded(reason: str) -> None:
    """R-3/R-5：降级告警（⛔静默）。计数文件＋stderr 各一行，均 best-effort。"""
    try:
        p = _dropped_path()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            data = {"dropped": 0}
        data["dropped"] = int(data.get("dropped", 0)) + 1
        data["last_reason"] = reason[:200]
        data["last_ts"] = _utcnow()
        p.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        pass
    try:
        sys.stderr.write(f"AUTH_DENY_LOG_DEGRADED dropped=+1 reason={reason[:120]!r}\n")
    except Exception:
        pass


def _rotate_if_needed(p: Path) -> None:
    """R-1/R-2/R-4：达限轮转 .1←现档, .2←.1 … 淘汰最旧；轮转件同 JSONL 格式不改。"""
    try:
        if not p.exists() or p.stat().st_size < _SIZE_LIMIT:
            return
        oldest = p.with_name(p.name + f".{_KEEP}")
        try:
            oldest.unlink()
        except FileNotFoundError:
            pass
        for i in range(_KEEP - 1, 0, -1):
            src = p.with_name(p.name + f".{i}")
            dst = p.with_name(p.name + f".{i + 1}")
            try:
                src.rename(dst)
            except FileNotFoundError:
                pass
        p.rename(p.with_name(p.name + ".1"))
    except Exception as e:  # 轮转失败不阻断写（写会再判大小，超限时继续尝试轮转）
        _alert_degraded(f"rotate:{type(e).__name__}")


def log_deny(*, path: str, method: str, http_code: int, subject: str,
             code: str, source: str, ts: str | None = None) -> None:
    """追加一行拒绝记录；任何异常吞掉并告警（降级＋计数，R-3/R-5）。"""
    try:
        p = _path()
        _rotate_if_needed(p)
        rec = {
            "ts": ts or _utcnow(),
            "path": path,
            "method": method,
            "http_code": int(http_code),
            "subject": subject if subject else "anonymous",
            "code": code or "",
            "source": source,  # middleware | http_exception
        }
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        _alert_degraded(f"write:{type(e).__name__}")
