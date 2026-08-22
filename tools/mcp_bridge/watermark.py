# FC-ID: DCD-MCP-BRIDGE-001 | 模块 1 NCA 存证水印（调用方/工具/输入摘要/输出哈希 + provenance）
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml


class Watermark:
    """每次工具调用自动落一条 NCA（YAML 存证目录，链式 payload_ref）。"""

    def __init__(self, evidence_dir: Path):
        self.dir = Path(evidence_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _chain(self) -> list:
        return sorted(self.dir.glob("NCA-MCP-*.yaml"))

    def _prev_hash(self) -> str:
        files = self._chain()
        if not files:
            return "genesis"
        doc = yaml.safe_load(files[-1].read_text(encoding="utf-8"))
        return str((doc.get("Post-State") or {}).get("Hash", "genesis"))

    def stamp(self, caller: str, tool: str, arguments: dict,
              output: str, rejected: bool = False) -> dict:
        prev = self._prev_hash()
        in_digest = hashlib.sha256(
            json.dumps(arguments, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        out_hash = hashlib.sha256(output.encode()).hexdigest()
        seq = len(self._chain()) + 1
        now = datetime.now(timezone.utc).isoformat()
        nca_id = f"NCA-MCP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{seq:03d}"
        doc = {
            "NCA-ID": nca_id,
            "Function-Call-ID": f"TDCA-FC-MCP-{seq:03d}",
            "Operation-Type": "FuseReject" if rejected else "ToolCall",
            "Operator": caller,
            "Timestamp": now,
            "Scope": f"MCP 工具调用: {tool}（输入摘要 sha256:{in_digest[:16]}…）",
            "Pre-State": {"Path": "", "Hash": prev, "Size": 0},
            "Post-State": {"Path": f"mcp-bridge:{tool}", "Hash": f"sha256:{out_hash}",
                           "Size": len(output)},
            "Config-Right-Token": {"Scope": "MCP 桥接存证（只读存证，不代执行业务）",
                                   "Rollback": "链式回退", "Audit-Trail": "NCA 链",
                                   "Human-Signature-Required": False,
                                   "Max-Retry": 0, "Granted-By": "mcp-bridge M1", "Expires": None},
            "Audit-Trail": [{"Step": f"{'熔断拒绝' if rejected else '调用执行'}: {tool}",
                             "Time": now, "Evidence": f"sha256:{out_hash}"}],
            "Human-Signature": {"Status": "Not-Required", "Signed-By": None, "Signed-At": None},
            "payload_ref": f"sha256:{out_hash}",
            "data_provenance": "simulated",
        }
        (self.dir / f"{nca_id}.yaml").write_text(
            yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return doc

    def get(self, nca_id: str) -> dict | None:
        p = self.dir / f"{nca_id}.yaml"
        return yaml.safe_load(p.read_text(encoding="utf-8")) if p.is_file() else None

    def chain(self, limit: int = 20) -> list:
        out = []
        for p in self._chain()[-limit:]:
            d = yaml.safe_load(p.read_text(encoding="utf-8"))
            out.append({"NCA-ID": d.get("NCA-ID"), "Operation-Type": d.get("Operation-Type"),
                        "Timestamp": d.get("Timestamp"),
                        "Hash": (d.get("Post-State") or {}).get("Hash")})
        return out
