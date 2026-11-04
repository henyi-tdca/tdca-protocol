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
              output: str, rejected: bool = False,
              space_id: str = "SBX", status: str = "SBX-ACTIVE",
              extra: dict | None = None,
              recognition: dict | None = None) -> dict:
        # TRISPACE-001 A4：每件必带 space_id 与状态位（⛔由件名/目录推断，由调用方显式传入）；
        # A8：跨段引用走 chain_ref；A5：SBX/PCM 面以 Post-State.Path 逻辑前缀分卷。
        # INTERFACE-001：extra 为 API 面扩展字段（ledger/authz_ref/Source/operation 等），
        # 缺省 None 行为与批2逐字节一致（纯追加参数，既有调用零影响）。
        # MCPDIAG-002 批2：recognition 为认定面扩展（agent_card_fingerprint 顶层字段
        # ＋Audit-Trail 认定步），缺省 None 时成件与批2逐字节一致（纯追加，零影响）。
        from .trispace import CHAIN_REF
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
            "space_id": space_id,
            "status": status,
            "chain_ref": CHAIN_REF,
            "Scope": f"MCP 工具调用: {tool}（输入摘要 sha256:{in_digest[:16]}…）",
            "Pre-State": {"Path": "", "Hash": prev, "Size": 0},
            "Post-State": {"Path": f"{space_id.lower()}:{tool}", "Hash": f"sha256:{out_hash}",
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
        if recognition:
            doc["agent_card_fingerprint"] = recognition["agent_card_fingerprint"]
            step2 = dict(recognition["step"])
            step2.setdefault("Time", now)
            doc["Audit-Trail"].append(step2)
        if extra:
            doc.update(extra)
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
                        "space_id": d.get("space_id"), "status": d.get("status"),
                        "Hash": (d.get("Post-State") or {}).get("Hash")})
        return out
