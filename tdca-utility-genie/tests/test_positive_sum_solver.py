"""TDCA-FC-20260802-004 子模块A 测试 — PositiveSumSolver
Granted-By: ID84
NSFL-Declaration: 测试验证满意解/正和性/熔断逻辑
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solvers.positive_sum_solver import PositiveSumSolver, Agent


class TestPositiveSumSolver(unittest.TestCase):
    def setUp(self):
        self.solver = PositiveSumSolver(random_seed=42)
        self.agents = [Agent('A', 1.0), Agent('B', 1.0)]

    def test_satisfying_solution_positive(self):
        """正和解：个体理性 + 正和性"""
        solution = self.solver.solve(
            participants=self.agents,
            objective_functions=[lambda x: x * 2, lambda x: x * 2],
            constraint_matrix=[],
            reservation_utilities=[5.0, 5.0],
            time_budget=1.0,
        )
        self.assertTrue(solution.is_positive_sum)
        self.assertTrue(solution.is_individual_rational)
        self.assertFalse(solution.touched_nsfl)
        self.assertGreater(solution.delta, 0)

    def test_nsfl_trigger(self):
        """触及负空间 → 熔断"""
        solution = self.solver.solve(
            participants=self.agents,
            objective_functions=[lambda x: x, lambda x: x],
            constraint_matrix=[],
            reservation_utilities=[1.0, 1.0],
            time_budget=1.0,
            nsfl_boundaries=['value_land_decisions_irreversible'],
        )
        self.assertTrue(solution.touched_nsfl)
        self.assertIsNotNone(solution.nsfl_reason)

    def test_nsfl_trigger_validate_raises(self):
        """非满意解 + 未熔断 → validate 抛异常"""
        # 构造一个不可能满足的解（保留效用极高）
        solution = self.solver.solve(
            participants=self.agents,
            objective_functions=[lambda x: x * 0.01, lambda x: x * 0.01],
            constraint_matrix=[],
            reservation_utilities=[999.0, 999.0],
            time_budget=0.1,
        )
        with self.assertRaises(ValueError) as ctx:
            self.solver.validate(solution)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_validate_pass(self):
        """有效解通过验证"""
        solution = self.solver.solve(
            participants=self.agents,
            objective_functions=[lambda x: x * 2, lambda x: x * 2],
            constraint_matrix=[],
            reservation_utilities=[5.0, 5.0],
            time_budget=1.0,
        )
        self.solver.validate(solution)  # 不应抛异常

    def test_nca_trace_generated(self):
        """求解过程生成 NCA 轨迹"""
        solution = self.solver.solve(
            participants=self.agents,
            objective_functions=[lambda x: x, lambda x: x],
            constraint_matrix=[],
            reservation_utilities=[1.0, 1.0],
            time_budget=1.0,
        )
        self.assertTrue(len(solution.nca_trace) > 0)
        self.assertIn('iteration', solution.nca_trace[0])


if __name__ == '__main__':
    unittest.main()
