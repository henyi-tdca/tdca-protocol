# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F5 五阶资产化合测试——CHEM-001~004 + ENG-003 检查器
# 约束矩阵:     FC-SBX-OPS-001 SV-5（最小化合）+ KB-ECON-001 §8
# 先验分布:     任务书 §二 F5 + chem_engine.py
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F5 五阶资产化合引擎测试（ENG-003 最小化合检查 + CHEM-001~004）。"""

from __future__ import annotations

import pytest

from app.chem_engine import (
    BASE_ACTIVATION_ENERGY,
    CATALYST_FACTOR,
    catalyst_field,
    chem_combine,
    chem_separate,
    eng003_min_compound_check,
    inhibitor_check,
)

_ASSETS = ["IP", "knowledge", "scene_weight"]
_COND_TRUE = {"indivisible": True, "emergent": True, "nonlinear": False}
_COND_FALSE = {"indivisible": False, "emergent": False, "nonlinear": False}


class TestEng003:
    def test_all_false_physical_overlay(self):
        """ENG-003: 三条件全 False → 物理叠加优先（不化合，SV-5）。"""
        r = eng003_min_compound_check(_ASSETS, _COND_FALSE, "资产可物理叠加复制")
        assert r["required"] is False
        assert r["physically_composable"] is True
        assert "物理叠加" in r["decision"]

    def test_any_true_requires_compound(self):
        r = eng003_min_compound_check(_ASSETS, _COND_TRUE, "组合产生涌现价值")
        assert r["required"] is True
        assert r["physically_composable"] is False

    def test_missing_conditions_rejected(self):
        with pytest.raises(ValueError):
            eng003_min_compound_check(_ASSETS, {"indivisible": True}, "x")

    def test_missing_justification_rejected(self):
        with pytest.raises(ValueError):
            eng003_min_compound_check(_ASSETS, _COND_TRUE, "")

    def test_invalid_asset_rejected(self):
        with pytest.raises(ValueError):
            eng003_min_compound_check(["ILLEGAL_ASSET"], _COND_TRUE, "x")


class TestChemCombine:
    def test_positive_combine(self):
        """CHEM-001: ENG-003 必要 + surplus>0 → combined。"""
        eng003 = eng003_min_compound_check(_ASSETS, _COND_TRUE, "涌现价值")
        rx = chem_combine("sbx-1", _ASSETS, "cfg-right:sbx-1", eng003, utility_surplus=120.0)
        assert rx["chem_type"] == "CHEM-001"
        assert rx["status"] == "combined"
        assert rx["utility_surplus"] == 120.0
        assert rx["activation_energy"] == BASE_ACTIVATION_ENERGY

    def test_catalyst_reduces_energy(self):
        """CHEM-003: 催化剂场降低活化能。"""
        eng003 = eng003_min_compound_check(_ASSETS, _COND_TRUE, "涌现价值")
        rx = chem_combine("sbx-1", _ASSETS, "cfg", eng003, utility_surplus=50.0, catalyst=True)
        assert rx["activation_energy"] == round(BASE_ACTIVATION_ENERGY * CATALYST_FACTOR, 2)

    def test_overlay_sufficient_rejected(self):
        """SV-5: ENG-003 判定物理叠加优先 → 化合拒绝。"""
        eng003 = eng003_min_compound_check(_ASSETS, _COND_FALSE, "可叠加")
        with pytest.raises(ValueError) as exc:
            chem_combine("sbx-1", _ASSETS, "cfg", eng003, utility_surplus=100.0)
        assert "SV-5" in str(exc.value)

    def test_non_positive_surplus_rejected(self):
        """CHEM-004: surplus≤0（非正和）→ 抑制剂阻断。"""
        eng003 = eng003_min_compound_check(_ASSETS, _COND_TRUE, "涌现价值")
        with pytest.raises(ValueError) as exc:
            chem_combine("sbx-1", _ASSETS, "cfg", eng003, utility_surplus=0.0)
        assert "CHEM-004" in str(exc.value)


class TestChemSeparate:
    def test_separate_requires_governance(self):
        """CHEM-002: 反向分离需治理介入。"""
        rx = chem_separate("sbx-1", "NCA-20260810-001", "gov-ref:ARB-001", 500.0)
        assert rx["chem_type"] == "CHEM-002"
        assert rx["status"] == "pending_governance"

    def test_separate_missing_governance_rejected(self):
        with pytest.raises(ValueError):
            chem_separate("sbx-1", "NCA-1", "", 100.0)


class TestCatalystAndInhibitor:
    def test_catalyst_field(self):
        r = catalyst_field(100.0)
        assert r["reduced_energy"] == 60.0

    def test_inhibitor_blocked(self):
        r = inhibitor_check(nsfl_hit=True, reason="触及法律负空间")
        assert r["blocked"] is True
        assert r["status"] == "BLOCKED"

    def test_inhibitor_allow(self):
        r = inhibitor_check(nsfl_hit=False)
        assert r["blocked"] is False
        assert r["status"] == "ALLOW"
