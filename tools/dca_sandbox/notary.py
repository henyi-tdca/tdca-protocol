"""dca_sandbox · 沙盒运行 NCA 存证（DCA-重塑版模拟运行落证，provenance SIMULATED ID92）。"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", ".tdca-nca", "services", "dca_sandbox",
)


class DcaSandboxNotary:
    """DCA-重塑版沙盒运行存证器。"""

    def __init__(self, target_dir: Optional[str] = None, operator: str = "TDCA"):
        self._dir = os.path.abspath(target_dir or _DEFAULT_DIR)
        os.makedirs(self._dir, exist_ok=True)
        self._operator = operator

    def record(self, payload: dict,
               operation_type: str = "DcaSandboxRun",
               scope_note: str = "DCA-重塑版沙盒模拟运行存证") -> dict:
        ts = datetime.now(timezone.utc)
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        date_key = ts.strftime("%Y%m%d")
        nca_id = f"NCA-DCASANDBOX-{date_key}-{self._next_seq(date_key)}"
        record = {
            "NCA-ID": nca_id,
            "Function-Call-ID": f"TDCA-FC-{ts.strftime('%Y%m%d')}-DCASANDBOX",
            "Operation-Type": operation_type,
            "Operator": self._operator,
            "Timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Scope": scope_note,
            "Report-Hash": f"sha256:{body_hash}",
            "Report-Payload": payload,
            "Provenance": payload.get("provenance", "SIMULATED"),
            "Sandbox-Discipline": {
                "Status": "Simulated",
                "Zero-Real-Funds": True,
                "Zero-Real-Config-Calls": True,
                "NSFL-Version": "V0.2",
            },
            "Boundary": "纯模拟参数运行；无真实配置权调用/无真实资金流；e-CNY 前全模拟态",
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
        prefix = f"NCA-DCASANDBOX-{date_str}-"
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
