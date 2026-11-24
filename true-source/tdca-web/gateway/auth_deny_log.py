# -*- coding: utf-8 -*-
"""CASENORM-K3-001 B部·K-3 留证补强：人类面鉴权拒绝专档（JSONL）。

落点：AUTH_DENY_LOG（默认 /data/auth_deny.log，与 tdca.db 同卷，持久）。
字段（B-1 四要素＋两辅助）：ts／path／method／http_code／subject／code／source。
隐私口径：subject 仅二选一——未登录记 anonymous；已登录记系统内注册主体 username。
⛔ 会话指纹／凭据值／自然人姓名字段；⛔ IP（不在四要素内，本批不增）。
best-effort：落档失败永不反转拒绝裁决（与 ops_auth_denials 同旨）。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

_DEFAULT_PATH = "/data/auth_deny.log"


def _path() -> str:
    return os.environ.get("AUTH_DENY_LOG", _DEFAULT_PATH)


def log_deny(*, path: str, method: str, http_code: int, subject: str,
             code: str, source: str, ts: str | None = None) -> None:
    """追加一行拒绝记录；任何异常吞掉（留证失败不反转裁决）。"""
    try:
        rec = {
            "ts": ts or datetime.now(timezone.utc).isoformat(),
            "path": path,
            "method": method,
            "http_code": int(http_code),
            "subject": subject if subject else "anonymous",
            "code": code or "",
            "source": source,  # middleware | http_exception
        }
        with open(_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
