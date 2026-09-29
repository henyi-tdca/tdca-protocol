# -*- coding: utf-8 -*-
"""TDCA-TASK-BIAS-001 验收测试：买/卖权重细分 + 场景效用偏态 + 跨场景配置决策。"""
import pytest

from microtax import (EconomicCognitionEngine, MicroDelivery,
                      SubjectEcoWeightEngine, TaxEventType)


class TestB1BuySellWeights:
    """B-1: 买/卖权重细分（总量守恒）。"""

    def test_weights_decompose(self):
        """w_i = buy_weight + sell_weight（总量守恒）。"""
        engine = SubjectEcoWeightEngine()
        assessments = engine.assess({
            "agent-a": {"buy": 3000.0, "sell": 2000.0},   # MOU 5000
            "agent-b": {"buy": 1000.0, "sell": 1000.0},   # MOU 2000
        })
        a = {x.subject_id: x for x in assessments}
        assert a["agent-a"].weight == pytest.approx(5000.0 / 7000.0, abs=1e-6)
        assert a["agent-a"].buy_weight == pytest.approx(3000.0 / 7000.0, abs=1e-6)
        assert a["agent-a"].sell_weight == pytest.approx(2000.0 / 7000.0, abs=1e-6)
        # 守恒: w = buy_w + sell_w
        assert a["agent-a"].weight == pytest.approx(
            a["agent-a"].buy_weight + a["agent-a"].sell_weight, abs=1e-6)

    def test_weights_sum_conserved(self):
        """买/卖权重各自与总量守恒（Σbuy_w ≤ 1, Σsell_w ≤ 1, Σw=1）。"""
        engine = SubjectEcoWeightEngine()
        assessments = engine.assess({
            "agent-a": {"buy": 3000.0, "sell": 1000.0},
            "agent-b": {"buy": 1000.0, "sell": 2000.0},
        })
        assert round(sum(x.weight for x in assessments), 6) == 1.0
        assert round(sum(x.buy_weight for x in assessments), 6) <= 1.0
        assert round(sum(x.sell_weight for x in assessments), 6) <= 1.0


class TestB2Bias:
    """B-2: 场景效用偏态（偏买/偏卖/均衡）。"""

    def test_buy_biased(self):
        """买>卖 → 偏买（bias>0）。"""
        engine = SubjectEcoWeightEngine()
        a = engine.assess({"me": {"buy": 3000.0, "sell": 1000.0}})[0]
        assert a.bias > 0
        assert a.bias_label == "buy_biased"

    def test_sell_biased(self):
        """卖>买 → 偏卖（bias<0）。"""
        engine = SubjectEcoWeightEngine()
        a = engine.assess({"you": {"buy": 1000.0, "sell": 3000.0}})[0]
        assert a.bias < 0
        assert a.bias_label == "sell_biased"

    def test_balanced(self):
        """买卖均衡 → balanced。"""
        engine = SubjectEcoWeightEngine()
        a = engine.assess({"both": {"buy": 2000.0, "sell": 2000.0}})[0]
        assert a.bias_label == "balanced"

    def test_compute_bias_values(self):
        """偏态纯计算（归一化）。"""
        engine = SubjectEcoWeightEngine()
        bias = engine.compute_bias({
            "buyer": {"buy": 3000.0, "sell": 1000.0},     # (3000-1000)/4000 = 0.5
            "seller": {"buy": 1000.0, "sell": 3000.0},    # -0.5
        })
        assert bias["buyer"] == pytest.approx(0.5, abs=1e-6)
        assert bias["seller"] == pytest.approx(-0.5, abs=1e-6)


class TestB3CrossSceneMatch:
    """B-3: 跨场景配置决策（偏态互补匹配——用户例子）。"""

    def test_tourist_example(self):
        """用户例子: 我（文旅偏买）↔ 你（农产品偏卖进文旅）互补优先。"""
        engine = SubjectEcoWeightEngine()
        # 我: 文旅场景偏买（bias>0）; 你: 农产品场景偏卖（bias<0）——进入文旅
        my_bias = engine.compute_bias({"me": {"buy": 3000.0, "sell": 1000.0}})["me"]     # +0.5
        your_bias = engine.compute_bias({"you": {"buy": 1000.0, "sell": 3000.0}})["you"] # -0.5
        # 文旅场景主体: 我（偏买）+ 卖者 X（偏卖——会推销你不需要的）
        matches = engine.cross_scene_match(your_bias, {
            "me": my_bias,            # +0.5 偏买
            "seller-X": 0.5 * -1,     # -0.5 偏卖（同向）
        })
        # 互补优先: 我排前（互补），seller-X 同向排后
        assert matches[0]["subject_id"] == "me"
        assert matches[0]["complementary"] is True
        assert matches[0]["rank_hint"] == "preferred"
        assert matches[1]["subject_id"] == "seller-X"
        assert matches[1]["rank_hint"] == "same_side"

    def test_complementarity_sign(self):
        """互补度 = 进入者偏态 × 主体偏态（负=互补）。"""
        engine = SubjectEcoWeightEngine()
        matches = engine.cross_scene_match(-0.5, {"buyer-a": 0.5, "seller-b": -0.5})
        m = {x["subject_id"]: x for x in matches}
        assert m["buyer-a"]["complementarity"] == pytest.approx(-0.25, abs=1e-6)
        assert m["buyer-a"]["complementary"] is True
        assert m["seller-b"]["complementarity"] == pytest.approx(0.25, abs=1e-6)
        assert m["seller-b"]["complementary"] is False

    def test_match_sorting_by_satisfaction(self):
        """最终排序（用户深化 2026-08-12）: 互补候选内满意解值高者优先。"""
        engine = SubjectEcoWeightEngine()
        matches = engine.cross_scene_match(-0.5, {
            "buyer-low": 0.5,      # 互补
            "buyer-high": 0.9,     # 互补且满意解值高
            "same": -0.8,          # 同向
        }, satisfaction_values={"buyer-low": 60.0, "buyer-high": 95.0, "same": 99.0})
        ids = [m["subject_id"] for m in matches]
        # 互补候选内满意解值高者优先；同向排最后（即使满意解值高）
        assert ids == ["buyer-high", "buyer-low", "same"]
        assert matches[0]["satisfaction_value"] == 95.0
        assert matches[2]["satisfaction_value"] == 99.0   # 同向不因值高而前置

    def test_match_sorting_default_no_sat(self):
        """无满意解值输入 → 兼容降级（互补优先，原语义）。"""
        engine = SubjectEcoWeightEngine()
        matches = engine.cross_scene_match(-0.5, {
            "partial": 0.2, "strong": 0.9, "same": -0.8,
        })
        ids = [m["subject_id"] for m in matches]
        assert ids == ["strong", "partial", "same"]


class TestB4Integration:
    """B-4: 经济认知引擎集成（偏态块）。"""

    def _delivery(self):
        return MicroDelivery(
            delivery_id="MD-BIAS", scene="tourism-scene", value=10000.0,
            event_type=TaxEventType.CONFIG_RIGHT_CALL,
            tax_in=3000.0, tax_out=2000.0,
            participants={"me": 60.0, "seller-X": 40.0})

    def _states(self):
        return {
            "me": {"A": 0.85, "D": 0.90, "L": 0.80, "C": 0.88, "SC": 0.92},
            "seller-X": {"A": 0.80, "D": 0.85, "L": 0.78, "C": 0.82, "SC": 0.88},
        }

    def test_subject_econ_contains_bias(self):
        """报告 subject_econ assessments 含 bias/buy_weight/sell_weight。"""
        engine = EconomicCognitionEngine()
        report = engine.cognize(
            self._delivery(), self._states(), eco_spillover=2000.0,
            subject_eco={"me": {"buy": 3000.0, "sell": 1000.0},
                         "seller-X": {"buy": 500.0, "sell": 2500.0}})
        me = [a for a in report.subject_econ["assessments"]
              if a["subject_id"] == "me"][0]
        assert me["bias"] > 0
        assert me["bias_label"] == "buy_biased"
        assert "buy_weight" in me and "sell_weight" in me
