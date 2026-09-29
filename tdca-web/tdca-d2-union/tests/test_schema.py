# -*- coding: utf-8 -*-
"""schema 单元测试：枚举三元归属 + NS_Rule VALIDATE_RULES 校验（schema V0.1-REV2-FINAL §三/§四）。"""
from decimal import Decimal

import pytest

from nsfl_union.schema import (FuseLevel, NSLayer, NS_Operator, NS_Rule,
                               NS_Type, NSFuseType, Severity)


# ---- NS_Type 三元归属（§三）----

def test_ns_type_triple_anchoring():
    assert NS_Type.LEGAL.fuse_type == NSFuseType.LEGAL
    assert NS_Type.LEGAL.layer == NSLayer.L0
    assert NS_Type.LEGAL.severity_max == Severity.HIGH
    # L2 场景化
    for t in (NS_Type.DATA_CROSS_BORDER, NS_Type.TRANSACTION_LIMIT,
              NS_Type.SENSITIVE_CONTENT, NS_Type.TECH_CONSTRAINT):
        assert t.layer == NSLayer.L2
        assert t.severity_max == Severity.MEDIUM
    # L1 主体
    for t in (NS_Type.ETHICAL, NS_Type.EMOTIONAL, NS_Type.BELIEF):
        assert t.layer == NSLayer.L1
        assert t.severity_max == Severity.LOW


def test_legal_derived_concept_removed():
    """S-02: fuse_type==LEGAL 仅 LEGAL 一个值（无 LEGAL 派生概念）。"""
    assert NS_Type.DATA_CROSS_BORDER.fuse_type == NSFuseType.ETHICAL
    assert NS_Type.SENSITIVE_CONTENT.fuse_type == NSFuseType.ETHICAL
    legal_fts = [t for t in NS_Type if t.fuse_type == NSFuseType.LEGAL]
    assert legal_fts == [NS_Type.LEGAL]


# ---- NS_Rule 校验（§四 VALIDATE_RULES）----

def test_rule_valid_defaults():
    r = NS_Rule("R1", NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX,
                Decimal("1000000"), unit="CNY")
    assert r.severity == Severity.MEDIUM   # 默认=severity_max
    assert r.layer == NSLayer.L2


def test_legal_rule_operator_forbidden_only():
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.LEGAL, NS_Operator.ALLOW)
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.LEGAL, NS_Operator.LIMIT_MAX, Decimal("1"), unit="CNY")
    NS_Rule("R", NS_Type.LEGAL, NS_Operator.FORBID)  # 合法


def test_legal_severity_immutable():
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.LEGAL, NS_Operator.FORBID, severity=Severity.MEDIUM)


def test_legal_alt_path_forced_none():
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.LEGAL, NS_Operator.FORBID, alt_path="bypass")


def test_legal_enabled_immutable():
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.LEGAL, NS_Operator.FORBID, enabled=False)


def test_layer_mismatch_rejected():
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.ETHICAL, NS_Operator.ALLOW, layer=NSLayer.L2)


def test_severity_escalation_rejected():
    """S-06: L1≤LOW / L2≤MEDIUM 越级拒绝。"""
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.ETHICAL, NS_Operator.ALLOW, severity=Severity.MEDIUM)
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX,
                Decimal("1"), unit="CNY", severity=Severity.HIGH)


def test_limit_requires_parameter_and_unit():
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX)
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, Decimal("1"))


def test_parameter_nan_inf_negative_rejected():
    for bad in ("NaN", "Infinity", "-5"):
        with pytest.raises(ValueError):
            NS_Rule("R", NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX,
                    bad, unit="CNY")


def test_restrict_tier_enum():
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.TECH_CONSTRAINT, NS_Operator.RESTRICT_TIER, "HIGH")
    r = NS_Rule("R", NS_Type.TECH_CONSTRAINT, NS_Operator.RESTRICT_TIER,
                FuseLevel.SUSPEND)
    assert r.parameter == FuseLevel.SUSPEND


def test_permanent_ban_forces_no_alt_path():
    with pytest.raises(ValueError):
        NS_Rule("R", NS_Type.TECH_CONSTRAINT, NS_Operator.RESTRICT_TIER,
                FuseLevel.PERMANENT_BAN, alt_path="detour")


def test_allow_rule_ok():
    r = NS_Rule("R", NS_Type.ETHICAL, NS_Operator.ALLOW)
    assert r.severity == Severity.LOW
