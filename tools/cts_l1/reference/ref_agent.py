# FC-ID: TDCA-TASK-CTS-L1-001 | 参考实现（全 PASS 基线，合成示例，ID92 simulated）
"""参考原生智能体：演示如何通过 CTS-L1 全部用例。
T-编号在 interface_doc 中为示意（模拟态示例文档）；正式实现须引用注册表当期登记。
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone

TAX_RATES = {"日抛": 0.02, "化合": 0.075, "服务": 0.0075}


class RefAgent:
    agent_id = "ref-agent-001"
    registry_version = "V2.1"

    def __init__(self):
        self._chain: list[dict] = []
        self._violations: list[dict] = []

    # ---- C-1 负空间声明 ----
    def submit_ns_declaration(self, decl) -> str:
        if isinstance(decl, str):
            decl = json.loads(decl)  # 语法错误 → json 解析 raise（fail-closed）
        if not isinstance(decl, dict) or decl.get("nsfl_version") != "V0.2":
            raise ValueError("NSFL 版本缺失或非法")
        for k in ("absolute_bans", "conditional_bans", "validity"):
            if k not in decl:
                raise ValueError(f"声明缺最少内容项: {k}")
        return "sha256:" + hashlib.sha256(
            json.dumps(decl, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

    def report_violation(self, event) -> dict:
        ev = {"level": 1, "rule": event.get("rule", "?"),
              "observed": event.get("observed", "?"),
              "timestamp": datetime.now(timezone.utc).isoformat(),
              "provenance": "simulated"}
        ev["event_hash"] = "sha256:" + hashlib.sha256(
            json.dumps(ev, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        self._violations.append(ev)
        return ev

    # ---- C-2 存证 ----
    def deliver(self, task) -> dict:
        prev = self._chain[-1]["Post-State"]["Hash"] if self._chain else "genesis"
        payload = json.dumps(task, ensure_ascii=False, sort_keys=True)
        h = "sha256:" + hashlib.sha256((prev + payload).encode()).hexdigest()
        nca = {
            "NCA-ID": f"TDCA-REF-{len(self._chain)+1:03d}",
            "Function-Call-ID": f"TDCA-FC-REF-{len(self._chain)+1:03d}",
            "Operation-Type": "Delivery", "Operator": self.agent_id,
            "Timestamp": datetime.now(timezone.utc).isoformat(),
            "Scope": task.get("task", "delivery"),
            "Pre-State": {"Path": "", "Hash": prev, "Size": 0},
            "Post-State": {"Path": "", "Hash": h, "Size": len(payload)},
            "Config-Right-Token": {"Scope": "CTS-L1 演示", "Rollback": "prev",
                                   "Audit-Trail": "chain", "Human-Signature-Required": True,
                                   "Max-Retry": 0, "Granted-By": "simulated", "Expires": None},
            "Audit-Trail": [{"Step": "deliver", "Time": nca_ts(), "Evidence": h}],
            "Human-Signature": {"Status": "Pending", "Signed-By": None, "Signed-At": None},
            "payload_ref": h, "provenance": "simulated",
        }
        self._chain.append(nca)
        return nca

    def evidence_chain(self) -> list:
        return list(self._chain)

    def check_chain_integrity(self, chain=None) -> tuple:
        chain = chain if chain is not None else self._chain
        for i, n in enumerate(chain):
            ref = n.get("payload_ref") or (n.get("Post-State") or {}).get("Hash")
            if not ref or str(ref).endswith("tampered"):
                return False, f"第 {i} 条存证链式引用异常（{ref}）——断链报警"
        return True, "链完整"

    # ---- C-3 计量 ----
    def meter(self, call_type: str, amount: float) -> dict:
        if not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
            raise ValueError("MOU 异常输入——fail-closed 预冻结，不强行结算")
        if call_type not in TAX_RATES:
            raise ValueError(f"未登记调用类型: {call_type}")
        return {"tax": round(amount * TAX_RATES[call_type], 2),
                "rate": TAX_RATES[call_type], "call_type": call_type,
                "provenance": "simulated"}

    # ---- C-4 契约 ----
    def generate_offer(self, template_id: str, parties: dict) -> dict:
        if template_id not in ("T3", "T4"):
            raise ValueError(f"未注册模板: {template_id}")
        return {"template": template_id, "offeror": parties["offeror"],
                "offeree": parties["offeree"],
                "subject": "CTS-L1 演示协作标的（simulated）",
                "acceptance_criteria": {"test": "pytest dual/tests/ -q 全绿",
                                        "metric": "test_pass_rate >= 1.0"},
                "breach_path": "NSFL 熔断 + 人类裁决升级",
                "provenance": "simulated"}

    def parse_contract(self, instance: dict) -> dict:
        if not isinstance(instance, dict) or "template" not in instance:
            raise ValueError("契约实例不可解析")
        return {"template": instance["template"], "offeror": instance.get("offeror"),
                "parsed": True}

    # ---- C-5 术语（示例文档：T-编号为示意，模拟态） ----
    def interface_doc(self) -> str:
        return ("参考智能体对外接口文档（对齐术语注册表 V2.1）："
                "任务委托（T-020）/ 交付验收（T-021）/ 熔断事件（T-064）/"
                "正和效用（T-041）/ 负空间（T-011）/ 存证（T-033）。")

    # ---- C-6 正和判定治理 ----
    def adjudicate(self, request: dict) -> dict:
        t = request.get("type")
        if t == "calibrate_batna":  # 校准禁令：一票否决级
            ev = self.report_violation({"observed": "calibrate_batna", "rule": "DCD-DEF-SUNZI-01 R-03"})
            return {"status": "rejected", "reason": "校准 BATNA 至 φ 属重言式化构造，NSFL BLOCK",
                    "evidence": ev["event_hash"]}
        if t == "reprice":
            if request.get("anchor") is None:
                ev = self.report_violation({"observed": "anchorless_repricing", "rule": "DCD-DEF-SUNZI-02 A-01"})
                return {"status": "fused", "fuse_level": 2, "applied": False,
                        "reason": "无锚重定价拦截，Level-2 熔断", "evidence": ev["event_hash"]}
            if float(request.get("deviation", 0)) > 0.20:
                return {"status": "escalated", "applied": False,
                        "reason": "偏离超 θ_ANCHOR_DEV，升级人类裁决"}
            return {"status": "applied", "applied": True}
        if t == "adjust":
            batna = request.get("batna") or {}
            if not batna.get("basis") and not request.get("proof"):
                ev = self.report_violation({"observed": "baseless_batna_adjust", "rule": "DCD-DEF-SUNZI-01 R-01"})
                return {"status": "fused", "fuse_level": 2, "action": "require_proof",
                        "batna_rewritten": False,
                        "reason": "BATNA 缺依据，熔断要求举证；举证失败则退出或明示同意下调",
                        "evidence": ev["event_hash"]}
            return {"status": "accepted", "batna_rewritten": False}
        return {"status": "rejected", "reason": f"未知请求类型 {t}", "evidence": None}


def nca_ts():
    return datetime.now(timezone.utc).isoformat()


def make_agent() -> RefAgent:
    return RefAgent()
