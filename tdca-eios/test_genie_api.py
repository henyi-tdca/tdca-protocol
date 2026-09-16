# -*- coding: utf-8 -*-
"""E-INT-2.2 genie_api 单元测试（能力映射/契约）"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from genie_api import GenieAPI


class TestGenieAPI(unittest.TestCase):
    """九大能力 API 契约"""

    def setUp(self):
        self.api = GenieAPI()

    def test_01_ten_capabilities(self):
        """十端点完整（九大能力 + capabilities 派生）"""
        self.assertEqual(len(self.api.CAPABILITIES), 10)
        for ep in ['positive-sum', 'inverse', 'shape', 'validate-delivery', 'shapley',
                   'optimize', 'measure', 'bayesian', 'game-equilibrium', 'cross-domain']:
            self.assertIn(ep, self.api.CAPABILITIES)

    def test_02_routes_contract(self):
        """路由契约：/api/v1/genie/{endpoint} + POST"""
        routes = self.api.routes
        self.assertEqual(len(routes), 10)
        for r in routes:
            self.assertTrue(r['path'].startswith('/api/v1/genie/'))
            self.assertEqual(r['method'], 'POST')

    def test_03_positive_sum(self):
        """正和满意解"""
        from solvers.positive_sum_solver import Agent
        r = self.api.positive_sum(
            participants=[Agent('A', 1.0), Agent('B', 1.0)],
            objectives=[lambda x: x * 2, lambda x: x * 2],
            constraints=[], reservation_utilities=[5.0, 5.0], time_budget=1.0)
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(r['capability'], 'positive-sum')

    def test_04_optimize_engine(self):
        """约束优化（optimization_engine 封装）"""
        r = self.api.optimize(objective=lambda x: (x[0] - 3) ** 2, bounds=[(0, 10)])
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(r['capability'], 'optimize')

    def test_05_bayesian_engine(self):
        """贝叶斯更新（bayesian_engine.normal_posterior 封装）"""
        r = self.api.bayesian(prior_mean=0.0, prior_variance=1.0, observations=[1.0, 2.0])
        self.assertEqual(r['status'], 'ok')

    def test_06_measure_cross_implemented(self):
        """计量/跨域已实现（E-INT-2.3）：OLS 回归 + 坐标变换映射"""
        r1 = self.api.measure({'x': [1, 2, 3, 4], 'y': [2, 4, 6, 8]})
        self.assertEqual(r1['status'], 'ok')
        self.assertAlmostEqual(r1['beta'], 2.0, places=6)  # y=2x
        r2 = self.api.cross_domain(
            {'domain': 'medical', 'vector': [0, 5, 10]},
            {'domain': 'industrial'})
        self.assertEqual(r2['status'], 'ok')
        self.assertAlmostEqual(r2['mapped'], 0.5, places=6)  # 归一化均值

    def test_06b_measure_insufficient_nsfl(self):
        """计量数据不足触发 NSFL"""
        with self.assertRaises(ValueError) as ctx:
            self.api.measure({'x': [1], 'y': [2]})
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_07_dispatch(self):
        """dispatch 分发 + 未知端点 NSFL"""
        r = self.api.dispatch('bayesian', {'prior_mean': 0.0, 'prior_variance': 1.0, 'observations': [1.0]})
        self.assertEqual(r['capability'], 'bayesian')
        with self.assertRaises(ValueError) as ctx:
            self.api.dispatch('unknown-cap', {})
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
