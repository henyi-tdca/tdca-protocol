# -*- coding: utf-8 -*-
"""TDCA-TASK-ECOCOG-001 S-15 整合编排层验收测试（H-1 全链路一键认知+配置）。"""
import pytest

from microtax import (EconomicConfigurator, MicroDelivery, TaxEventType)


def _delivery(value=10000.0, tax_in=3000.0, tax_out=2000.0,
              delivery_id="MD-CFG", participants=None):
    return MicroDelivery(
        delivery_id=delivery_id, scene="tourism-scene", value=value,
        event_type=TaxEventType.CONFIG_RIGHT_CALL,
        tax_in=tax_in, tax_out=tax_out,
        participants=participants or {"me": 60.0, "buyer-b": 40.0})


def _states():
    return {
        "me": {"A": 0.85, "D": 0.90, "L": 0.80, "C": 0.88, "SC": 0.92},
        "buyer-b": {"A": 0.80, "D": 0.85, "L": 0.78, "C": 0.82, "SC": 0.88},
    }


def _subject_eco():
    return {
        "me": {"buy": 3000.0, "sell": 1000.0},        # 偏买
        "buyer-b": {"buy": 1000.0, "sell": 2500.0},   # 偏卖
    }


class TestS15Configure:
    """H-1: 全链路一键认知 + 配置。"""

    def test_full_pipeline(self):
        """经济事实 → 计税/法规 → 认知 → 配置（一键闭环）。"""
        cfg = EconomicConfigurator()
        # 进入者偏卖（农产品偏卖者进入文旅）→ 目标场景: me 偏买 + seller-X 偏卖
        result = cfg.configure(
            _delivery(), _states(), _subject_eco(),
            enterer_bias=-0.5,
            target_scene_bias={"me": 0.5, "seller-X": -0.6},
            eco_spillover=2000.0)
        assert result.full_cognition is True
        assert result.cognition.taxation["tax_total"] == 200.0
        assert result.cognition.taxation["mou_value"] == 5000.0
        # 配置匹配: me（互补）前置
        assert result.top_candidate["subject_id"] == "me"
        assert result.top_candidate["complementary"] is True
        assert result.config_matches[0]["rank_hint"] == "preferred"

    def test_satisfaction_values_linked_from_cognition(self):
        """满意解值衔接: 来自 cognize positive_sum.allocations。"""
        cfg = EconomicConfigurator()
        result = cfg.configure(
            _delivery(), _states(), _subject_eco(),
            enterer_bias=-0.5,
            target_scene_bias={"me": 0.5, "buyer-b": -0.6},
            eco_spillover=2000.0)
        # 目标场景主体满意解值 = 认知 positive_sum allocations 对应值
        allocs = result.cognition.positive_sum["allocations"]
        for m in result.config_matches:
            assert m["satisfaction_value"] == pytest.approx(
                allocs.get(m["subject_id"], 0.0), abs=1e-6)

    def test_same_side_blocked_even_high_satisfaction(self):
        """同向偏态即使满意解值高也不前置（互补性优先）。"""
        cfg = EconomicConfigurator()
        result = cfg.configure(
            _delivery(), _states(), _subject_eco(),
            enterer_bias=-0.5,
            target_scene_bias={"me": 0.5, "seller-X": -0.6},
            eco_spillover=2000.0)
        ids = [m["subject_id"] for m in result.config_matches]
        assert ids == ["me", "seller-X"]

    def test_regulatory_fail_closed(self):
        """违规交付 → 全链路 fail-closed（法规约束）。"""
        cfg = EconomicConfigurator()
        d = _delivery(delivery_id="MD-CFG-V")
        d.tax_violation = "tax_evasion"
        with pytest.raises(ValueError, match="L-CN-TX-001"):
            cfg.configure(d, _states(), _subject_eco(),
                          enterer_bias=-0.5, target_scene_bias={"me": 0.5})

    def test_report_to_dict_complete(self):
        """配置决策报告 to_dict 完整（认知+匹配+top）。"""
        cfg = EconomicConfigurator()
        result = cfg.configure(
            _delivery(), _states(), _subject_eco(),
            enterer_bias=-0.5, target_scene_bias={"me": 0.5},
            eco_spillover=2000.0)
        d = result.to_dict()
        assert set(d.keys()) == {"delivery_id", "cognition", "config_matches",
                                 "top_candidate", "full_cognition", "simulated"}
        assert d["simulated"] is True
