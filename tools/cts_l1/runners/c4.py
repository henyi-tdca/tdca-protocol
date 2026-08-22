# FC-ID: TDCA-TASK-CTS-L1-001 | C-4 契约模板（CCP REV2.1 T3/T4 基线）
from .base import run_case

REQUIRED_OFFER_FIELDS = {"template", "offeror", "offeree", "subject", "acceptance_criteria", "breach_path"}


def c4_t1(target):
    """C4-T1: T3 模板生成邀约 → 字段完整、可被另一原生智能体解析。"""
    def _():
        offer = target.generate_offer("T3", {"offeror": target.agent_id, "offeree": "peer-agent"})
        if not isinstance(offer, dict):
            return False, "邀约非结构化"
        missing = REQUIRED_OFFER_FIELDS - set(offer)
        if missing:
            return False, f"邀约缺关键字段: {missing}"
        parsed = target.parse_contract(offer)  # 自解析模拟「另一原生智能体」
        if not isinstance(parsed, dict) or parsed.get("template") != "T3":
            return False, "邀约不可被解析回读"
        return True, "T3 邀约字段完整且可解析"
    return run_case("C4-T1", "C-4", _)


def c4_t2(target):
    """C4-T2: 验收条款须可机械映射为验收测试（不允许「已完成」式模糊条款）。"""
    def _():
        offer = target.generate_offer("T3", {"offeror": target.agent_id, "offeree": "peer-agent"})
        ac = offer.get("acceptance_criteria")
        if isinstance(ac, dict) and ac.get("test"):  # 结构化可执行验收
            return True, f"验收条款可机械映射: {str(ac.get('test'))[:40]}"
        if isinstance(ac, str) and len(ac) > 4 and not any(k in ac for k in ("test", "校验", "断言", "≥", "<=", ">=")):
            return False, f"验收条款模糊不可机械映射: {ac!r}"
        if isinstance(ac, str):
            return True, f"验收条款含可机检判据: {ac[:40]}"
        return False, "验收条款缺失或非结构化"
    return run_case("C4-T2", "C-4", _)


CASES = (c4_t1, c4_t2)
