"""TDCA-FC-20260802-004 子模块B 测试 — InverseFunctionSolver
Granted-By: ID21
NSFL-Declaration: 测试验证反函数求解/可行域/熔断逻辑
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solvers.inverse_function_solver import (
    InverseFunctionSolver, ConfigSpace, InverseSolution,
)


class TestInverseFunctionSolver(unittest.TestCase):
    def setUp(self):
        self.solver = InverseFunctionSolver(samples=2000, random_seed=42)

    def test_solve_feasible(self):
        """可行反函数解"""
        config_space = ConfigSpace(
            bounds={'x': (0.0, 10.0)},
            hard_constraints=['x <= 10'],
        )
        solution = self.solver.solve(
            target_utility=5.0,
            utility_function=lambda c: c['x'],
            config_space=config_space,
            tolerance=0.1,
        )
        self.assertEqual(solution.feasibility, 'feasible')
        self.assertGreaterEqual(solution.predicted_utility, 4.5)  # 5*(1-0.1)
        self.assertIn('x', solution.config_vector)

    def test_solve_infeasible_nsfl(self):
        """无可行解 → infeasible + NSFL-TRIGGER"""
        config_space = ConfigSpace(
            bounds={'x': (0.0, 1.0)},
            hard_constraints=['x <= 1'],
        )
        solution = self.solver.solve(
            target_utility=999.0,
            utility_function=lambda c: c['x'],
            config_space=config_space,
            tolerance=0.01,
        )
        self.assertEqual(solution.feasibility, 'infeasible')
        self.assertEqual(solution.config_vector, {})

    def test_nsfl_trigger_validate_infeasible(self):
        """不可行解缺 NSFL-TRIGGER 记录 → validate 抛异常"""
        bad = InverseSolution(
            config_vector={'x': 1.0},
            predicted_utility=0.0,
            confidence_interval=(0, 0),
            feasibility='infeasible',
            cost=0.0,
            nca_trace=[{'status': 'OK'}],
        )
        with self.assertRaises(ValueError) as ctx:
            self.solver.validate(bad)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_validate_pass(self):
        """可行解通过验证"""
        config_space = ConfigSpace(bounds={'x': (0.0, 10.0)})
        solution = self.solver.solve(
            target_utility=5.0,
            utility_function=lambda c: c['x'],
            config_space=config_space,
            tolerance=0.1,
        )
        self.solver.validate(solution)

    def test_cost_minimization(self):
        """多解时选择成本最小"""
        config_space = ConfigSpace(bounds={'x': (0.0, 10.0)})
        solution = self.solver.solve(
            target_utility=5.0,
            utility_function=lambda c: c['x'],
            config_space=config_space,
            cost_function=lambda c: c['x'],  # x 越大成本越高
            tolerance=0.1,
        )
        # 应该选择接近 5 的最小可行解
        self.assertLessEqual(solution.config_vector['x'], 5.5)

    def test_confidence_interval(self):
        """置信区间生成"""
        config_space = ConfigSpace(bounds={'x': (0.0, 10.0)})
        solution = self.solver.solve(
            target_utility=5.0,
            utility_function=lambda c: c['x'],
            config_space=config_space,
            tolerance=0.2,
        )
        lo, hi = solution.confidence_interval
        self.assertLessEqual(lo, hi)


if __name__ == '__main__':
    unittest.main()
