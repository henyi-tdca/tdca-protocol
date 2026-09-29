# -*- coding: utf-8 -*-
"""_fallback_split 兜底路径测试（无基座环境的 Shapley 数学可靠性）。"""
import pytest

from microtax._fallback_split import MOUSplitContract, default_mou_value_fn


class TestFallbackValueFn:
    def test_single_element_equals_contribution(self):
        fn = default_mou_value_fn({"a": 60.0, "b": 40.0})
        assert fn(frozenset({"a"})) == 60.0
        assert fn(frozenset({"b"})) == 40.0

    def test_multi_element_synergy(self):
        fn = default_mou_value_fn({"a": 60.0, "b": 40.0}, synergy=1.2)
        assert fn(frozenset({"a", "b"})) == round((60.0 + 40.0) * 1.2, 6)

    def test_empty_set_zero(self):
        fn = default_mou_value_fn({"a": 60.0})
        assert fn(frozenset()) == 0.0


class TestFallbackSplit:
    def test_exact_two_player_symmetric(self):
        """对称贡献 → 对称 Shapley 分配（各半）。"""
        fn = default_mou_value_fn({"a": 50.0, "b": 50.0}, synergy=1.0)
        out = MOUSplitContract().split(["a", "b"], fn)
        assert out["a"] == pytest.approx(out["b"], abs=1e-6)
        assert out["a"] == pytest.approx(50.0, abs=1e-6)

    def test_exact_three_player_sum_of_ratios(self):
        """三参与方: Shapley 值总和 = 全体联合值（效率性）。"""
        contrib = {"a": 60.0, "b": 30.0, "c": 10.0}
        fn = default_mou_value_fn(contrib, synergy=1.2)
        out = MOUSplitContract().split(["a", "b", "c"], fn)
        total = sum(out.values())
        assert total == pytest.approx(fn(frozenset({"a", "b", "c"})), rel=1e-4)

    def test_monte_carlo_large_n(self):
        """>6 参与方走蒙特卡洛近似（不抛错且 Σ 守恒）。"""
        contrib = {f"agent-{i}": float(i + 1) for i in range(8)}
        fn = default_mou_value_fn(contrib, synergy=1.0)
        out = MOUSplitContract(random_seed=42).split(list(contrib), fn, samples=2000)
        assert abs(sum(out.values()) - fn(frozenset(contrib))) < 0.5
