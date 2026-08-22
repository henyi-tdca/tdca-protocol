# FC-ID: TDCA-TASK-CTS-L1-001 | 负例实现（故意违规，验证套件判别力 A-4）
"""故意违反轮廓 L1 的假智能体：静默修复声明 / 无 provenance / 自动生效重定价 / 静默改写 BATNA。
用途：套件负例验证——坏实现必须 FAIL，全过说明套件没有判别力。
"""
import hashlib

from .ref_agent import RefAgent


class BadAgent(RefAgent):
    agent_id = "bad-agent-000"

    def submit_ns_declaration(self, decl) -> str:
        return "sha256:" + hashlib.sha256(str(decl).encode()).hexdigest()  # 静默修复语法错误

    def meter(self, call_type, amount):
        return {"tax": float(amount) * 0.01}  # 错税率 + 无 provenance + 负数照算

    def adjudicate(self, request):
        if request.get("type") == "calibrate_batna":
            return {"status": "ok"}  # 校准攻击放行，无存证
        if request.get("type") == "reprice":
            return {"status": "applied", "applied": True}  # 无锚/超阈都自动生效
        if request.get("type") == "adjust":
            return {"status": "accepted", "batna_rewritten": True}  # 静默改写
        return {"status": "ok"}

    def interface_doc(self):
        return "本智能体支持任务委托和交付，正和效用按内部口径计算。"  # 无 T-编号


def make_agent() -> BadAgent:
    return BadAgent()
