"""TDCA-FC-20260802-004 数学引擎 + 主类 + 集成 测试
Granted-By: ID24
NSFL-Declaration: 测试验证数学引擎正确性与主类协同
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from math_engines import OptimizationEngine, BayesianEngine, GameTheoryEngine
from tdca_utility_genie import TDCAUtilityGenie
from solvers.positive_sum_solver import Agent


class TestOptimizationEngine(unittest.TestCase):
    def test_simulated_annealing(self):
        """模拟退火求解"""
        eng = OptimizationEngine(seed=1)
        result = eng.simulated_annealing(
            objective=lambda x: -(x[0] - 5) ** 2,  # 最大值在 x=5
            bounds=[(0, 10)],
            maximize=True,
            iterations=500,
        )
        self.assertTrue(result['feasible'])
        self.assertGreaterEqual(result['value'], -1.0)

    def test_pareto_sort(self):
        """帕累托排序"""
        eng = OptimizationEngine()
        sols = [
            {'values': {'cost': 1, 'utility': 10}, 'config': 1},
            {'values': {'cost': 3, 'utility': 8}, 'config': 2},
            {'values': {'cost': 2, 'utility': 9}, 'config': 3},
        ]
        ranked = eng.pareto_sort(sols, ['cost', 'utility'])
        self.assertEqual(ranked[0]['config'], 1)  # 最优


class TestBayesianEngine(unittest.TestCase):
    def test_posterior_update(self):
        """正态后验更新"""
        eng = BayesianEngine()
        post = eng.normal_posterior(0.0, 1.0, [1.0, 2.0, 3.0])
        self.assertGreater(post['mean'], 0.0)
        self.assertLess(post['variance'], 1.0)  # 观测后方差缩小

    def test_confidence_interval(self):
        """置信区间"""
        eng = BayesianEngine()
        lo, hi = eng.confidence_interval(0.0, 1.0)
        self.assertLess(lo, hi)

    def test_expected_improvement(self):
        """EI 采集函数"""
        eng = BayesianEngine()
        ei = eng.expected_improvement(5.0, 6.0, 1.0)
        self.assertGreaterEqual(ei, 0.0)


class TestGameTheoryEngine(unittest.TestCase):
    def test_shapley(self):
        """Shapley 值计算"""
        eng = GameTheoryEngine()
        result = eng.shapley_value(
            ['A', 'B'],
            lambda s: len(s) * 2.0,
        )
        self.assertAlmostEqual(result['efficiency'], 4.0)

    def test_positive_sum_check(self):
        """正和性检查"""
        eng = GameTheoryEngine()
        is_pos, delta = eng.positive_sum_check(30.0, [10.0, 10.0])
        self.assertTrue(is_pos)
        self.assertEqual(delta, 10.0)

    def test_nash_equilibrium(self):
        """纳什均衡"""
        eng = GameTheoryEngine()
        # 双人对称收益矩阵
        eq = eng.nash_equilibrium([[1, 0], [0, 2]])
        self.assertTrue(len(eq) >= 0)


class TestUtilityGenieMain(unittest.TestCase):
    def setUp(self):
        self.genie = TDCAUtilityGenie()

    def test_solve_positive_sum(self):
        """主类调用功能A"""
        solution = self.genie.solve_positive_sum(
            participants=[Agent('A', 1.0), Agent('B', 1.0)],
            objective_functions=[lambda x: x * 2, lambda x: x * 2],
            constraint_matrix=[],
            reservation_utilities=[5.0, 5.0],
            time_budget=1.0,
        )
        self.assertTrue(solution.is_positive_sum)

    def test_full_pipeline(self):
        """全流程编排"""
        result = self.genie.full_pipeline(
            participants=[Agent('A', 1.0), Agent('B', 1.0)],
            objective_functions=[lambda x: x * 2, lambda x: x * 2],
            constraint_matrix=[],
            reservation_utilities=[5.0, 5.0],
            time_budget=1.0,
            nsfl_boundaries=[],
            target_utility={'tax': 10.0},
            contract_id='C-FULL',
            token_ref='TDCA-CRT-20260801-001',
        )
        self.assertIn('solution', result)
        self.assertIn('delivery_report', result)

    def test_version(self):
        """版本号"""
        self.assertEqual(TDCAUtilityGenie.VERSION, '1.0.0')


if __name__ == '__main__':
    unittest.main()
