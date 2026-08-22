"""cog_align · NCA 存证（A-4）

每次评测自动落 NCA 存证（provenance 标注，ID92）。
存证目录可注入（测试用临时目录；生产默认 .tdca-nca/services/cog_align/）。
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional

# 默认存证目录（工作区根 .tdca-nca/services/cog_align/）
_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", ".tdca-nca", "services", "cog_align",
)


class CogAlignNotary:
    """认知对齐评测 NCA 存证器。"""

    def __init__(self, target_dir: Optional[str] = None, operator: str = "Reasonix"):
        self._dir = os.path.abspath(target_dir or _DEFAULT_DIR)
        os.makedirs(self._dir, exist_ok=True)
        self._operator = operator

    def record(self, report: dict, operation_type: str = "CogAlignMeasure") -> dict:
        """落一条 NCA 存证记录，返回记录 dict（含文件路径与哈希）。"""
        ts = datetime.now(timezone.utc)
        payload = json.dumps(report, ensure_ascii=False, sort_keys=True)
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        nca_id = f"NCA-COGALIGN-{ts.strftime('%Y%m%d')}-{self._next_seq(ts.strftime('%Y%m%d'))}"
        record = {
            "NCA-ID": nca_id,
            "Function-Call-ID": f"TDCA-FC-{ts.strftime('%Y%m%d')}-COGALIGN",
            "Operation-Type": operation_type,
            "Operator": self._operator,
            "Timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Scope": "cog_align 评测存证",
            "Report-Hash": f"sha256:{payload_hash}",
            "Report-Payload": report,
            "Provenance": report.get("provenance", "SIMULATED"),
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

    # ---- 工具 ----

    def _next_seq(self, date_str: str) -> int:
        prefix = f"NCA-COGALIGN-{date_str}-"
        existing = [f for f in os.listdir(self._dir) if f.startswith(prefix)]
        return len(existing) + 1

    @staticmethod
    def _write_yaml(path: str, record: dict) -> None:
        """YAML 落盘（无 pyyaml 依赖时回退 JSON——存证内容等价）。"""
        try:
            import yaml
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(record, f, allow_unicode=True, sort_keys=False)
        except ImportError:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
