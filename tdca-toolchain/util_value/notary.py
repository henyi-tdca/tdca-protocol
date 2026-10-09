"""util_value · NCA 存证（每次评估自动落链，provenance 标注 ID92）。"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", ".tdca-nca", "services", "util_value",
)


class UtilValueNotary:
    """效用价值评估 NCA 存证器。"""

    def __init__(self, target_dir: Optional[str] = None, operator: str = "Reasonix"):
        self._dir = os.path.abspath(target_dir or _DEFAULT_DIR)
        os.makedirs(self._dir, exist_ok=True)
        self._operator = operator

    def record(self, report: dict, operation_type: str = "UtilValueAssess") -> dict:
        ts = datetime.now(timezone.utc)
        payload = json.dumps(report, ensure_ascii=False, sort_keys=True)
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        nca_id = f"NCA-UTILVALUE-{ts.strftime('%Y%m%d')}-{self._next_seq(ts.strftime('%Y%m%d'))}"
        record = {
            "NCA-ID": nca_id,
            "Function-Call-ID": f"TDCA-FC-{ts.strftime('%Y%m%d')}-UTILVALUE",
            "Operation-Type": operation_type,
            "Operator": self._operator,
            "Timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Scope": "util_value 评估存证",
            "Report-Hash": f"sha256:{payload_hash}",
            "Report-Payload": report,
            "Provenance": report.get("provenance", "SIMULATED"),
            "MOU-Anchor": {
                "Status": "Simulated",
                "Floor-Semantics": "地板非天花板——只输出可观测下限（MEMO-006-Audit）",
            },
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
        prefix = f"NCA-UTILVALUE-{date_str}-"
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
