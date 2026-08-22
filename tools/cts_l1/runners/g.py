# FC-ID: TDCA-TASK-CTS-L1-001 | 通用要求 G-1 fail-closed / G-2 数据性质标注
from .base import run_case


def g1_fail_closed(target):
    """G-1: 综合抽查——拒绝路径必须带存证，不得静默降级。"""
    def _():
        r = target.adjudicate({"type": "calibrate_batna", "to_phi": True})
        if not (isinstance(r, dict) and r.get("status") == "rejected" and r.get("evidence")):
            return False, "拒绝路径缺存证"
        try:
            target.submit_ns_declaration("{broken")
            return False, "编译错误被静默放行"
        except Exception:
            pass
        return True, "拒绝与存证成对出现，无静默降级"
    return run_case("G-1", "G-1", _)


def g2_provenance(target):
    """G-2: 对外数值输出必须带 data provenance 标注。"""
    def _():
        r = target.meter("日抛", 100.0)
        p = r.get("provenance") if isinstance(r, dict) else None
        if p not in ("simulated", "real", "mixed"):
            return False, f"计量输出缺 provenance 或取值非法: {p!r}"
        ev = target.report_violation({"observed": "test", "rule": "x"})
        if isinstance(ev, dict) and "provenance" in ev and ev["provenance"] not in ("simulated", "real", "mixed"):
            return False, f"熔断事件 provenance 非法: {ev['provenance']!r}"
        return True, f"输出标注在位（provenance={p}）"
    return run_case("G-2", "G-2", _)


CASES = (g1_fail_closed, g2_provenance)
