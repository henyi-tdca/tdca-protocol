# SPDX-License-Identifier: Apache-2.0
"""TDCA-FC-20260803-005 FR-005 单元测试 — PriorDistributionCompiler + NecessityChecker
Granted-By: FC-005-SPEC, ID90
NSFL-Declaration: 测试验证先验编译/回退策略/NecessityChecker
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prior_compilers.prior_compiler import (
    PriorDistributionCompiler, NecessityChecker,
)


def make_node(node_id, conf):
    return {
        'node_id': node_id,
        'content': {'objective_snapshot': f'知识{node_id}'},
        'confidence': {'final_score': conf},
    }


class TestNecessityChecker(unittest.TestCase):
    def setUp(self):
        self.checker = NecessityChecker()

    def test_necessary_pass(self):
        """三项全满足 → 必要（允许NCA化合）"""
        r = self.checker.check(
            compound_utility=100.0,
            component_utilities=[20.0, 30.0],  # 独立和=50 < 100
            irreducibility=True,
            nonlinearity=True,
        )
        self.assertTrue(r['necessary'])
        self.assertIn('允许NCA化合', r['recommendation'])

    def test_not_necessary_emergence_fail(self):
        """涌现价值不满足 → 建议物理叠加"""
        r = self.checker.check(
            compound_utility=40.0,
            component_utilities=[20.0, 30.0],  # 独立和=50 > 40
        )
        self.assertFalse(r['necessary'])
        self.assertIn('物理叠加', r['recommendation'])

    def test_not_necessary_irreducibility_fail(self):
        """不可拆分性不满足 → 建议物理叠加"""
        r = self.checker.check(
            compound_utility=100.0,
            component_utilities=[20.0, 30.0],
            irreducibility=False,  # 可拆分
        )
        self.assertFalse(r['necessary'])
        self.assertEqual(r['checks']['irreducibility'], False)

    def test_not_necessary_nonlinearity_fail(self):
        """非线性不满足 → 建议物理叠加"""
        r = self.checker.check(
            compound_utility=100.0,
            component_utilities=[20.0, 30.0],
            nonlinearity=False,
        )
        self.assertFalse(r['necessary'])
        self.assertEqual(r['checks']['nonlinearity'], False)


class TestPriorDistributionCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = PriorDistributionCompiler()
        self.nodes = [
            make_node('n1', 0.9),
            make_node('n2', 0.7),
            make_node('n3', 0.5),
        ]

    def test_compile_bayesian(self):
        """贝叶斯分布编译"""
        result = self.compiler.compile_prior(
            graph_ref='TDCA-KG-001',
            node_selection=['n1', 'n2'],
            distribution_type='BAYESIAN',
            nodes=self.nodes,
        )
        self.assertEqual(result['status'], 'SUCCESS')
        dist = result['prior_output']['distribution']
        self.assertEqual(dist['type'], 'BAYESIAN')
        self.assertIn('alpha', dist['parameters'])
        self.assertIn('beta', dist['parameters'])

    def test_compile_empirical(self):
        """经验分布编译"""
        result = self.compiler.compile_prior(
            graph_ref='G1', node_selection=[], distribution_type='EMPIRICAL',
            nodes=self.nodes,
        )
        self.assertEqual(result['prior_output']['distribution']['type'], 'EMPIRICAL')
        self.assertTrue(result['prior_output']['validation']['backtest_available'])

    def test_compile_uniform(self):
        """均匀分布"""
        result = self.compiler.compile_prior(
            graph_ref='G1', node_selection=[], distribution_type='UNIFORM',
            nodes=self.nodes,
        )
        self.assertEqual(result['prior_output']['distribution']['parameters']['lower'], 0.0)

    def test_compile_mixture(self):
        """混合分布"""
        result = self.compiler.compile_prior(
            graph_ref='G1', node_selection=[], distribution_type='MIXTURE',
            nodes=self.nodes,
        )
        self.assertEqual(result['prior_output']['distribution']['type'], 'MIXTURE')
        components = result['prior_output']['distribution']['parameters']['components']
        self.assertEqual(len(components), 3)

    def test_nsfl_trigger_empty_fallback(self):
        """无知识节点 → 回退均匀分布 + FAILED"""
        result = self.compiler.compile_prior(
            graph_ref='G1', node_selection=['n9'], distribution_type='BAYESIAN',
            nodes=self.nodes,
        )
        self.assertEqual(result['status'], 'FAILED')
        self.assertEqual(result['prior_output']['distribution']['type'], 'UNIFORM')
        self.assertTrue(any('回退' in w for w in result['warnings']))

    def test_min_confidence_filter(self):
        """最低置信度过滤"""
        result = self.compiler.compile_prior(
            graph_ref='G1', node_selection=[], distribution_type='EMPIRICAL',
            nodes=self.nodes, min_confidence=0.6,
        )
        trace = result['prior_output']['compilation_trace']
        self.assertEqual(len(trace['source_nodes']), 2)  # n1(0.9), n2(0.7)

    def test_conflict_human_review(self):
        """冲突检测 → 需人工审核"""
        conflict_nodes = [
            {'node_id': 'a', 'content': {'objective_snapshot': '相同内容'}, 'confidence': {'final_score': 0.8}},
            {'node_id': 'b', 'content': {'objective_snapshot': '相同内容'}, 'confidence': {'final_score': 0.5}},
        ]
        result = self.compiler.compile_prior(
            graph_ref='G1', node_selection=[], distribution_type='EMPIRICAL',
            nodes=conflict_nodes, conflict_resolution='HUMAN_REVIEW',
        )
        self.assertTrue(result['prior_output']['validation']['human_review_required'])
        self.assertTrue(any('冲突' in w for w in result['warnings']))

    def test_unknown_distribution(self):
        """未知分布类型 → FAILED + 警告"""
        result = self.compiler.compile_prior(
            graph_ref='G1', node_selection=[], distribution_type='UNKNOWN',
            nodes=self.nodes,
        )
        self.assertEqual(result['status'], 'FAILED')

    def test_validate_pass(self):
        """有效结果通过验证"""
        result = self.compiler.compile_prior(
            graph_ref='G1', node_selection=[], distribution_type='BAYESIAN',
            nodes=self.nodes,
        )
        self.compiler.validate(result)

    def test_validate_bad_status(self):
        """非法状态 → validate 抛异常"""
        with self.assertRaises(ValueError) as ctx:
            self.compiler.validate({'status': 'INVALID', 'prior_output': None})
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_mou_hard_constraint(self):
        """MOU 硬约束：编译的分布可作为 FC-004A 输入"""
        result = self.compiler.compile_prior(
            graph_ref='G1', node_selection=[], distribution_type='BAYESIAN',
            nodes=self.nodes,
        )
        # 验证输出结构符合 FC-004A 接口
        output = result['prior_output']
        self.assertIn('output_id', output)
        self.assertIn('distribution', output)
        self.assertIn('compilation_trace', output)
        self.assertIn('validation', output)


if __name__ == '__main__':
    unittest.main()
