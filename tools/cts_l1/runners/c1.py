# FC-ID: TDCA-TASK-CTS-L1-001 | C-1 负空间声明（NSFL V0.2）
import hashlib
import json

from .base import run_case

LEGAL_DECL = {
    "nsfl_version": "V0.2",
    "agent": None,  # 运行时填 target.agent_id
    "absolute_bans": ["不发币", "不公售", "不承诺分红"],
    "conditional_bans": [{"rule": "涉真实资金前保持 simulated 标注", "reversible": True}],
    "validity": {"version": "1.0", "expires": "2027-08-22"},
}
BROKEN_DECL = "{nsfl_version: V0.2, absolute_bans: [不发币"  # 语法残缺


def _mkdecl(target):
    d = dict(LEGAL_DECL)
    d["agent"] = target.agent_id
    return d


def c1_t1(target):
    """C1-T1: 合法声明编译通过，返回声明哈希。"""
    def _():
        h = target.submit_ns_declaration(_mkdecl(target))
        ok = isinstance(h, str) and len(h) >= 16
        return ok, f"声明哈希: {h!r}"
    return run_case("C1-T1", "C-1", _)


def c1_t2(target):
    """C1-T2: 语法错误声明 → 编译器拒绝（fail-closed），不得静默修复。"""
    def _():
        try:
            target.submit_ns_declaration(BROKEN_DECL)
            return False, "语法错误声明被静默接受——违反 fail-closed"
        except Exception as e:
            return True, f"正确拒绝: {type(e).__name__}"
    return run_case("C1-T2", "C-1", _)


def c1_t3(target):
    """C1-T3: 模拟越界 → 三档分级熔断事件（格式校验；时延计量供参考）。"""
    def _():
        ev = target.report_violation({"observed": "absolute_ban", "rule": "不发币"})
        if not isinstance(ev, dict):
            return False, "熔断事件非结构化"
        missing = {"level", "rule", "event_hash"} - set(ev)
        if missing:
            return False, f"熔断事件缺字段: {missing}"
        if ev.get("level") not in (1, 2, 3, "L1", "L2", "L3"):
            return False, f"分级非法: {ev.get('level')}"
        return True, f"熔断事件 level={ev.get('level')}"
    return run_case("C1-T3", "C-1", _)


CASES = (c1_t1, c1_t2, c1_t3)
