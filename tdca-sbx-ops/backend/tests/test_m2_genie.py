# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F6 正和验证适配层测试——正和判定/效用精灵真实对接/不可 mock
# 约束矩阵:     KB-ECON-001 §3（S_synergy>0）+ 开发纪律（正和不可 mock）
# 先验分布:     任务书 §二 F6 + utility_genie_adapter.py
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F6 正和验证适配层测试。"""

from __future__ import annotations

import pytest

from app import utility_genie_adapter as genie


class TestPositiveSumCheck:
    def test_positive_sum(self):
        """S_synergy = U_actual − ΣU_individual > 0 → 正和。"""
        r = genie.positive_sum_check(coalition_utility=300.0, independent_utilities=[80.0, 90.0, 50.0])
        assert r["is_positive_sum"] is True
        assert r["delta"] == 80.0
        assert r["fuse"] is False

    def test_non_positive_sum_fuse(self):
        """非正和 → FUSE 熔断标记（SV-3 方向）。"""
        r = genie.positive_sum_check(coalition_utility=200.0, independent_utilities=[80.0, 90.0, 50.0])
        assert r["is_positive_sum"] is False
        assert r["delta"] == -20.0
        assert r["fuse"] is True

    def test_invalid_inputs_rejected(self):
        with pytest.raises(ValueError):
            genie.positive_sum_check(100.0, [])
        with pytest.raises(ValueError):
            genie.positive_sum_check(100.0, [-1.0])


class TestUtilityGenieIntegration:
    """效用精灵真实对接（只读引用 tdca-utility-genie，不可 mock）。"""

    def test_solve_positive_sum_real(self):
        """真实 PositiveSumSolver：正和解 + 正和判定。"""
        participants = [
            {"agent_id": "innovator", "capability": 1.0},
            {"agent_id": "investor", "capability": 1.2},
            {"agent_id": "government", "capability": 0.8},
        ]

        # 效用精灵 PositiveSumSolver 目标函数签名: fn(分配量) -> 效用
        def obj(allocated: float):
            return allocated

        r = genie.solve_positive_sum(
            participants=participants,
            objective_functions=[obj],
            reservation_utilities=[5.0, 8.0, 2.0],
            nsfl_boundaries=["⊗ illegal.operation"],
        )
        assert "solution" in r
        assert r["is_positive_sum"] is True
        assert r["fuse"] is False
        assert r["delta"] > 0

    def test_delivery_confirm_real(self):
        """真实 ContractDeliveryValidator：MOU 税收锚定交付确认。"""
        r = genie.delivery_confirm(
            contract_id="CT-001",
            target_utility={"tax": 1000.0},
            actual_mou={"Actual-Total": 1200.0},
            token_ref="TDCA-CRT-sbx-1",  # 效用精灵硬校验前缀
        )
        assert r["tax_anchor_verification"] is True  # MOU 税收锚定验证通过
        assert r["utility_achievement"] == 120.0

    def test_genie_unavailable_raises(self, monkeypatch):
        """效用精灵不可用 → RuntimeError（F6 不可 mock 降级）。"""
        import pathlib

        monkeypatch.setattr(genie, "GENIE_DIR", pathlib.Path("/nonexistent/genie"))
        with pytest.raises(RuntimeError):
            genie.solve_positive_sum(
                participants=[{"agent_id": "a"}],
                objective_functions=[],
                reservation_utilities=[1.0],
            )
