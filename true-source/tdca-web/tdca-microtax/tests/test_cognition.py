# -*- coding: utf-8 -*-
"""TDCA-TASK-COGNITION-001 验收测试：多主体认知 × 效用精灵 × 税收 = 完整经济认知。"""
import pytest

from microtax import (EconomicCognitionEngine, MicroDelivery,
                      TaxEventType, TaxOfficerAgent)


def _states_high():
    """高认知主体组（全部 ≥ θ=0.70）。"""
    return {
        "agent-a": {"A": 0.85, "D": 0.90, "L": 0.80, "C": 0.88, "SC": 0.92},
        "agent-b": {"A": 0.80, "D": 0.85, "L": 0.78, "C": 0.82, "SC": 0.88},
    }


def _states_low():
    """低认知主体组（低于 θ）。"""
    return {
        "agent-a": {"A": 0.40, "D": 0.45, "L": 0.30, "C": 0.50, "SC": 0.55},
        "agent-b": {"A": 0.85, "D": 0.90, "L": 0.80, "C": 0.88, "SC": 0.92},
    }


def _delivery(participants=None, value=10000.0, tax_in=3000.0, tax_out=2000.0,
              event_type=TaxEventType.CONFIG_RIGHT_CALL, delivery_id="MD-COG"):
    return MicroDelivery(
        delivery_id=delivery_id, scene="cognition-scene", value=value,
        event_type=event_type, tax_in=tax_in, tax_out=tax_out,
        participants=(participants if participants is not None
                      else {"agent-a": 60.0, "agent-b": 40.0}),
    )


class TestC2UtilityGenieExtension:
    """C-2: PositiveSumSolver resource_pool 注入（税后净额资源池）。"""

    def test_resource_pool_injection(self):
        """注入 resource_pool → 分配 Σ = 注入值。"""
        from solvers.positive_sum_solver import Agent, PositiveSumSolver
        solver = PositiveSumSolver()
        sol = solver.solve(
            participants=[Agent("a"), Agent("b")],
            objective_functions=[lambda x: x, lambda x: x],
            constraint_matrix=[], reservation_utilities=[0.0, 0.0],
            resource_pool=972.50)
        assert round(sum(sol.allocations.values()), 2) == 972.50
        assert sol.is_positive_sum

    def test_default_backward_compat(self):
        """缺省 resource_pool → 硬编码行为不变（向后兼容）。"""
        from solvers.positive_sum_solver import Agent, PositiveSumSolver
        sol = PositiveSumSolver().solve(
            participants=[Agent("a"), Agent("b")],
            objective_functions=[lambda x: x, lambda x: x],
            constraint_matrix=[], reservation_utilities=[0.0, 0.0])
        assert round(sum(sol.allocations.values()), 2) == 20.00   # min(2*10, 100)


class TestC1Cognition:
    """C-1: 多主体认知接入（认知距离矩阵/不对称/协商触发）。"""

    def test_cognition_block_fields(self):
        """认知块含距离矩阵/不对称/协商触发。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(_delivery(), _states_high())
        cog = report.cognition
        assert cog["subject_count"] == 2
        assert len(cog["distance_matrix"]) == 2
        assert "asymmetry_ratio" in cog
        assert "min_cognitive_level" in cog
        assert "negotiation_required" in cog

    def test_low_cognition_triggers_negotiation(self):
        """低认知组 → 协商触发（距离 > 0.35）。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(_delivery(), _states_low())
        assert report.cognition["negotiation_required"] is True


class TestC3Taxation:
    """税收段（税务官 on_delivery 接入）。"""

    def test_taxation_block(self):
        """税收块含计税/预缴/净额/法规轨迹。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(_delivery(), _states_high())
        tax = report.taxation
        assert tax["tax_total"] == 200.0          # 10000 × 2%
        assert tax["net_value"] == 9800.0
        assert tax["prepay"]["status"] == "PREPAID"
        assert tax["regulatory"] == []

    def test_regulatory_fail_closed(self):
        """违规交付 → 完整认知 fail-closed（法规约束）。"""
        engine = EconomicCognitionEngine()
        d = _delivery(delivery_id="MD-COG-V")
        d.tax_violation = "tax_evasion"
        with pytest.raises(ValueError, match="L-CN-TX-001"):
            engine.cognize(d, _states_high())


class TestC4PositiveSumAndVerdict:
    """C-2 正和求解 + C-4 融合验证（TREATISE-026）。"""

    def test_positive_sum_uses_mou_pool(self):
        """效用精灵正和: Σ分配 = MOU（进项+出项=场景总效用），非税后净额（本体论纠偏）。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(_delivery(), _states_high())
        ps = report.positive_sum
        assert ps["pool_semantics"] == "mou"
        assert ps["resource_pool"] == 5000.0          # MOU = 3000 + 2000
        assert round(sum(ps["allocations"].values()), 2) == 5000.0
        assert ps["is_positive_sum"] is True
        # 正和判定依据是 MOU，非税后净额（taxation 块区分语义）
        assert report.taxation["mou_value"] == 5000.0
        assert report.taxation["net_value"] == 9800.0

    def test_full_cognition_high_states_with_spillover(self):
        """高认知 + ΔMOU>0 + 溢出达标 → U_正和=1（完整经济认知）。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(_delivery(), _states_high(), eco_spillover=2000.0)
        v = report.verdict
        assert v["mou_delta_ok"] is True
        assert v["min_cognitive_ok"] is True
        assert v["spillover_ok"] is True          # 2000/5000 = 0.4 > 0.30
        assert v["u_positive_sum"] == 1.0
        assert report.full_cognition is True

    def test_low_cognition_blocks_full_cognition(self):
        """min(S_协作) < θ → U_正和=0（认知不足阻断完整认知）。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(_delivery(), _states_low(), eco_spillover=2000.0)
        assert report.verdict["min_cognitive_ok"] is False
        assert report.verdict["u_positive_sum"] == 0.0
        assert report.full_cognition is False

    def test_no_spillover_blocks(self):
        """生态溢出不达标（按 MOU 比例）→ U_正和=0。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(_delivery(), _states_high(), eco_spillover=1000.0)
        # 1000/5000 = 0.20 < 0.30
        assert report.verdict["spillover_ok"] is False
        assert report.full_cognition is False

    def test_theta_registered_value(self):
        """θ=0.70 恒为 T-007 登记值（不得改值）。"""
        from microtax.economic_cognition import POSITIVE_SUM_THETA
        assert POSITIVE_SUM_THETA == 0.70

    def test_no_participants_rejected(self):
        """无参与方 → 拒绝（多主体输入要求）。"""
        engine = EconomicCognitionEngine()
        with pytest.raises(ValueError, match="无参与方贡献"):
            engine.cognize(_delivery(participants={}), _states_high())

    def test_report_to_dict(self):
        """完整报告 to_dict（认知+税收+正和+判定+主体生态全字段）。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(_delivery(), _states_high(), eco_spillover=2000.0)
        d = report.to_dict()
        assert set(d.keys()) == {"delivery_id", "cognition", "taxation",
                                 "positive_sum", "verdict", "subject_econ",
                                 "full_cognition", "simulated"}
        assert d["simulated"] is True
