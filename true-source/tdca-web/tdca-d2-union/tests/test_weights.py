# -*- coding: utf-8 -*-
"""risk_premium 权重表单元测试（schema §六：抗稀释 + 特例 + 熔断语义）。"""
from decimal import Decimal

from nsfl_union.schema import (FuseLevel, NS_Operator, NS_Rule, NS_Type,
                               Severity)
from nsfl_union.weights import RiskPremiumCalculator

calc = RiskPremiumCalculator()


def _c(ns, op, val=None, sev=None):
    kw = {}
    if val is not None:
        kw["parameter"] = Decimal(str(val))
        kw["unit"] = "CNY"
    r = NS_Rule(f"R-{ns.value}-{op.value}", ns, op, **kw)
    return r


def _conflict(rule_a, rule_b, severity):
    from nsfl_union.schema import Conflict, Resolution
    return Conflict(ns_type=rule_a.ns_type, rule_a=rule_a, rule_b=rule_b,
                    severity=severity, resolution=Resolution.FORBID, reason="t")


def test_legal_conflict_always_one():
    la = NS_Rule("LA", NS_Type.LEGAL, NS_Operator.FORBID)
    rb = _c(NS_Type.ETHICAL, NS_Operator.ALLOW)
    assert calc.compute([_conflict(la, rb, Severity.HIGH)]) == 1.0


def test_no_conflict_market_only():
    """无冲突特例: risk_premium = M（REV2 统一 N1）。"""
    assert calc.compute([]) == 0.2  # 缺省 OBSERVE
    assert calc.compute([], tier_a=FuseLevel.TEARDOWN) == 0.8
    assert calc.compute([], tier_a=FuseLevel.SUSPEND, tier_b=FuseLevel.TEARDOWN) == 0.8  # 取严


def test_highest_severity_protection():
    """S-10: S̄ 取最高严重度（非均值）——LOW 洪水不压低 MEDIUM。"""
    low_rules = [_c(NS_Type.ETHICAL, NS_Operator.ALLOW) for _ in range(20)]
    med_a = _c(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100)
    med_b = _c(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 50)
    conflicts = [_conflict(med_a, med_b, Severity.MEDIUM)]
    for i in range(0, 19):
        conflicts.append(_conflict(low_rules[i], low_rules[i + 1], Severity.LOW))
    p = calc.compute(conflicts)
    # MEDIUM 主导: w_s*0.6 = 0.30 起
    assert p >= 0.30
    assert p < 0.60


def test_pure_low_bounded():
    """纯 LOW 冲突上限 < 0.6（不触发 FAIL 语义，权重仅定价）。"""
    lows = [_c(NS_Type.ETHICAL, NS_Operator.ALLOW) for _ in range(20)]
    conflicts = [_conflict(lows[i], lows[i + 1], Severity.LOW) for i in range(19)]
    p = calc.compute(conflicts)
    assert p <= 0.15 + 0.3 + 0.2  # 0.65 上界（LOW 层权重 0.2 满 + M 0.2）
    assert p < 0.6


def test_layered_cap():
    """分层封顶: LOW 大量计数不线性放大 n_eff。"""
    lows = [_c(NS_Type.ETHICAL, NS_Operator.ALLOW) for _ in range(100)]
    conflicts = [_conflict(lows[i], lows[i + 1], Severity.LOW) for i in range(99)]
    p_many = calc.compute(conflicts)
    p_few = calc.compute([_conflict(lows[0], lows[1], Severity.LOW)])
    assert p_many < p_few + 0.3  # 封顶防止线性增长


def test_output_range():
    med_a = _c(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100)
    med_b = _c(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 50)
    p = calc.compute([_conflict(med_a, med_b, Severity.MEDIUM)])
    assert 0.0 <= p <= 1.0
