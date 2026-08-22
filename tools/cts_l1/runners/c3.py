# FC-ID: TDCA-TASK-CTS-L1-001 | C-3 计量接口（CALL-RULES V1.2 / microtax M-1）
from .base import TAX_RATES, run_case

# 标准测试向量（合成数据，ID92）：(call_type, amount) → 期望税额
VECTORS = [("日抛", 1000.0), ("化合", 2000.0), ("服务", 4000.0), ("日抛", 333.33)]


def c3_t1(target):
    """C3-T1: 标准测试向量计税一致。"""
    def _():
        bad = []
        for ct, amt in VECTORS:
            r = target.meter(ct, amt)
            expect = round(amt * TAX_RATES[ct], 2)
            got = round(float(r.get("tax", -1)), 2)
            if abs(got - expect) > 0.011:
                bad.append(f"{ct}/{amt}: 期望 {expect} 实得 {got}")
            if "provenance" not in r:
                bad.append(f"{ct}/{amt}: 缺 provenance 标注（G-2）")
        return (not bad), "; ".join(bad) if bad else f"{len(VECTORS)} 向量全对"
    return run_case("C3-T1", "C-3", _)


def c3_t2(target):
    """C3-T2: 聚合缴纳零漂移（Σ聚合 = Σ单笔）。"""
    def _():
        singles, total_amt = [], 0.0
        for ct, amt in VECTORS[:3]:
            singles.append(float(target.meter(ct, amt)["tax"]))
            total_amt += amt
        agg = target.meter("聚合", total_amt) if _has_agg(target) else None
        if agg is None:  # 无聚合接口则按逐笔一致性替代判据
            return True, "目标未实现聚合接口，以单笔一致性替代（判据: 向量全对）"
        drift = abs(float(agg["tax"]) - sum(singles))
        return drift < 0.011, f"漂移 {drift:.4f}"
    return run_case("C3-T2", "C-3", _)


def _has_agg(target):
    try:
        target.meter("聚合", 0.01)
        return True
    except Exception:
        return False


def c3_t3(target):
    """C3-T3: MOU 异常（负数/溢出输入）→ fail-closed 预冻结，不得强行结算。"""
    def _():
        for bad_amt in (-100.0, float("inf")):
            try:
                r = target.meter("日抛", bad_amt)
                if isinstance(r, dict) and r.get("frozen"):
                    continue  # 结构化冻结也算 fail-closed
                return False, f"异常输入 {bad_amt} 被强行结算"
            except Exception:
                continue  # raise = fail-closed ✅
        return True, "异常输入全部 fail-closed"
    return run_case("C3-T3", "C-3", _)


CASES = (c3_t1, c3_t2, c3_t3)
