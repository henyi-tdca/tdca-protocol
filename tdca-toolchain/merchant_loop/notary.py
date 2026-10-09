"""merchant_loop · NCA 存证（权益发布/核销落证，provenance 标注 ID92）。"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", ".tdca-nca", "services", "merchant_loop",
)


class MerchantLoopNotary:
    """merchant_loop NCA 存证器（发布存证 + 核销存证）。"""

    def __init__(self, target_dir: Optional[str] = None, operator: str = "TDCA"):
        self._dir = os.path.abspath(target_dir or _DEFAULT_DIR)
        os.makedirs(self._dir, exist_ok=True)
        self._operator = operator

    def record(self, payload: dict,
               operation_type: str = "MerchantLoopPublish",
               scope_note: str = "merchant_loop 存证") -> dict:
        ts = datetime.now(timezone.utc)
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        date_key = ts.strftime("%Y%m%d")
        nca_id = f"NCA-MERCHANTLOOP-{date_key}-{self._next_seq(date_key)}"
        record = {
            "NCA-ID": nca_id,
            "Function-Call-ID": f"TDCA-FC-{ts.strftime('%Y%m%d')}-MERCHANTLOOP",
            "Operation-Type": operation_type,
            "Operator": self._operator,
            "Timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Scope": scope_note,
            "Report-Hash": f"sha256:{body_hash}",
            "Report-Payload": payload,
            "Provenance": payload.get("provenance", "SIMULATED"),
            "MOU-Anchor": {
                "Status": "Simulated",
                "Note": "双边消费交易（不进 CLS，T-027）；无池/无杠杆/无升值承诺——让利逐笔即时",
            },
            "Boundary": "双边消费交易（不进 CLS 核心）；真实资金流 e-CNY 接入前全模拟态",
            "Negative-Space-Check": {
                "NSFL-Version": "V0.2",
                "Triggered": False,
                "Trigger-Reason": None,
            },
        }
        path = os.path.join(self._dir, f"{nca_id}.yaml")
        self._write_yaml(path, record)
        record["_path"] = path
        return record

    def _next_seq(self, date_str: str) -> int:
        prefix = f"NCA-MERCHANTLOOP-{date_str}-"
        existing = [f for f in os.listdir(self._dir) if f.startswith(prefix)]
        return len(existing) + 1

    @staticmethod
    def _write_yaml(path: str, record: dict) -> None:
        try:
            import yaml
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(record, f, allow_unicode=True, sort_keys=False)
        except ImportError:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
