# -*- coding: utf-8 -*-
"""TDCA-TASK-ECOWEIGHT-001 验收测试：主体配置权场景价值权重 + 零和负和熔断。"""
import pytest

from microtax import (EconomicCognitionEngine, MicroDelivery,
                      SubjectEcoWeightEngine, TaxEventType)


class TestE1BuySellTotal:
    """E-1: 主体买卖总量（非单边指标）。"""

    def test_mou_total_is_buy_plus_sell(self):
        """MOU_i = buy + sell（买卖总量，非单买/单卖）。"""
        engine = SubjectEcoWeightEngine()
        assessments = engine.assess({
            "agent-a": {"buy": 3000.0, "sell": 2000.0},
            "agent-b": {"buy": 1000.0, "sell": 4000.0},
        })
        a = {x.subject_id: x for x in assessments}
        assert a["agent-a"].mou_total == 5000.0
        assert a["agent-b"].mou_total == 5000.0

    def test_single_side_not_equal_total(self):
        """单买≠总量：只买不卖的主体 MOU = buy（总量语义明确）。"""
        engine = SubjectEcoWeightEngine()
        assessments = engine.assess({
            "buyer-only": {"buy": 3000.0, "sell": 0.0},
            "both": {"buy": 1000.0, "sell": 2000.0},
        })
        a = {x.subject_id: x for x in assessments}
        assert a["buyer-only"].mou_total == 3000.0
        assert a["buyer-only"].buy == 3000.0
        assert a["buyer-only"].sell == 0.0


class TestE2Weights:
    """E-2: 经济生态权重（Σw=1）。"""

    def test_weights_sum_to_one(self):
        """Σw_i = 1（买卖总量相对权重）。"""
        engine = SubjectEcoWeightEngine()
        assessments = engine.assess({
            "agent-a": {"buy": 3000.0, "sell": 2000.0},   # MOU 5000
            "agent-b": {"buy": 1000.0, "sell": 4000.0},   # MOU 5000
        })
        assert round(sum(x.weight for x in assessments), 6) == 1.0
        assert all(x.weight == pytest.approx(0.5, abs=1e-6) for x in assessments)

    def test_unequal_totals_weighted(self):
        """买卖总量不同 → 权重按总量比例。"""
        engine = SubjectEcoWeightEngine()
        weights = engine.compute_weights({"a": 3000.0, "b": 1000.0})
        assert weights["a"] == pytest.approx(0.75, abs=1e-6)
        assert weights["b"] == pytest.approx(0.25, abs=1e-6)

    def test_all_zero_weights_even(self):
        """场景整体零和 → 权重均分。"""
        engine = SubjectEcoWeightEngine()
        weights = engine.compute_weights({"a": 0.0, "b": 0.0})
        assert weights["a"] == pytest.approx(0.5, abs=1e-6)
        assert weights["b"] == pytest.approx(0.5, abs=1e-6)


class TestE3ZeroNegativeFuse:
    """E-3: 零和/负和 → 经济熔断 → 沙盒重塑/休眠 → 禁入该场景 → 配置价值低。"""

    def test_zero_sum_fused(self):
        """零和主体 → 经济熔断 + 禁入该场景 + 配置价值低。"""
        engine = SubjectEcoWeightEngine()
        assessments = engine.assess({
            "agent-a": {"buy": 1000.0, "sell": 2000.0},    # MOU 3000 > 0
            "agent-b": {"buy": 0.0, "sell": 0.0},          # MOU 0 → 零和
        })
        a = {x.subject_id: x for x in assessments}
        assert a["agent-b"].zero_negative is True
        assert a["agent-b"].economic_fused is True
        assert a["agent-b"].disposition == "sandbox_reshape"
        assert a["agent-b"].scene_config_blocked is True
        assert a["agent-b"].config_value == "low"
        # 有益主体不受影响
        assert a["agent-a"].economic_fused is False
        assert a["agent-a"].scene_config_blocked is False
        assert a["agent-a"].config_value == "high"

    def test_negative_sum_fused(self):
        """负和主体（卖>买且负贡献）→ 熔断。"""
        engine = SubjectEcoWeightEngine()
        assessments = engine.assess({
            "agent-a": {"buy": 1000.0, "sell": 2000.0},
            "agent-b": {"buy": -500.0, "sell": -200.0},    # MOU -700 → 负和
        })
        a = {x.subject_id: x for x in assessments}
        assert a["agent-b"].zero_negative is True
        assert a["agent-b"].economic_fused is True

    def test_dormant_disposition(self):
        """可指定休眠处置（区别于 SBX-BANNED 法律永久休眠——经济级可恢复）。"""
        engine = SubjectEcoWeightEngine(disposition="dormant")
        assessments = engine.assess({
            "agent-a": {"buy": 1000.0, "sell": 2000.0},
            "agent-b": {"buy": 0.0, "sell": 0.0},
        })
        a = {x.subject_id: x for x in assessments}
        assert a["agent-b"].disposition == "dormant"

    def test_no_fuse_for_positive(self):
        """正和主体不熔断。"""
        engine = SubjectEcoWeightEngine()
        assessments = engine.assess({
            "agent-a": {"buy": 1000.0, "sell": 2000.0},
        })
        assert assessments[0].economic_fused is False
        assert assessments[0].disposition == "none"
        assert assessments[0].scene_config_blocked is False


class TestE4CognitionIntegration:
    """E-4: 经济认知引擎集成（主体级块）。"""

    def _delivery(self):
        return MicroDelivery(
            delivery_id="MD-ECO", scene="eco-scene", value=10000.0,
            event_type=TaxEventType.CONFIG_RIGHT_CALL,
            tax_in=3000.0, tax_out=2000.0,
            participants={"agent-a": 60.0, "agent-b": 40.0})

    def _states(self):
        return {
            "agent-a": {"A": 0.85, "D": 0.90, "L": 0.80, "C": 0.88, "SC": 0.92},
            "agent-b": {"A": 0.80, "D": 0.85, "L": 0.78, "C": 0.82, "SC": 0.88},
        }

    def test_subject_econ_block(self):
        """报告含主体生态块（assessments/weights/fused/blocked）。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(
            self._delivery(), self._states(), eco_spillover=2000.0,
            subject_eco={"agent-a": {"buy": 3000.0, "sell": 2000.0},
                         "agent-b": {"buy": 500.0, "sell": 500.0}})
        se = report.subject_econ
        assert len(se["assessments"]) == 2
        assert round(sum(se["weights"].values()), 6) == 1.0
        assert se["fused_subjects"] == []          # 均正和
        assert se["scene_config_blocked"] == []

    def test_subject_fuse_in_report(self):
        """零和主体 → 报告 subject_econ 标记熔断 + 禁入。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(
            self._delivery(), self._states(), eco_spillover=2000.0,
            subject_eco={"agent-a": {"buy": 3000.0, "sell": 2000.0},
                         "agent-b": {"buy": 0.0, "sell": 0.0}})   # 零和
        se = report.subject_econ
        assert "agent-b" in se["fused_subjects"]
        assert "agent-b" in se["scene_config_blocked"]
        b = [a for a in se["assessments"] if a["subject_id"] == "agent-b"][0]
        assert b["config_value"] == "low"

    def test_to_dict_contains_subject_econ(self):
        """报告 to_dict 含 subject_econ 字段。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(self._delivery(), self._states())
        assert "subject_econ" in report.to_dict()
