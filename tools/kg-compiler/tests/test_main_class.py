# SPDX-License-Identifier: Apache-2.0
"""TDCA-FC-20260803-005 主类冒烟测试
Granted-By: FC-005-SPEC
"""
import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tdca_kg_compiler import TDCAKnowledgeGraphCompiler


class TestMainClass(unittest.TestCase):
    def setUp(self):
        self.nca_generator = Mock(return_value={'NCA-ID': 'TDCA-NCA-MAIN-001'})
        self.compiler = TDCAKnowledgeGraphCompiler(nca_generator=self.nca_generator)

    def test_build_from_nca(self):
        """主类调用 FR-001"""
        result = self.compiler.build_from_nca({'scenario': ''})
        self.assertIn('nodes_created', result)

    def test_compile_prior(self):
        """主类调用 FR-005（空节点 → 回退均匀分布）"""
        result = self.compiler.compile_prior('G1', [], 'UNIFORM')
        self.assertEqual(result['status'], 'FAILED')  # 无节点回退
        self.assertEqual(result['prior_output']['distribution']['type'], 'UNIFORM')

    def test_necessity_check(self):
        """主类调用 ID90"""
        r = self.compiler.necessity_check(100.0, [20.0, 30.0])
        self.assertTrue(r['necessary'])

    def test_backtest(self):
        """主类调用 FR-006"""
        prior = self.compiler.compile_prior('G1', [], 'UNIFORM')
        report = self.compiler.backtest_prior(prior['prior_output'], [])
        self.assertEqual(report['report']['accuracy'], 0.0)

    def test_version(self):
        """版本号"""
        self.assertEqual(TDCAKnowledgeGraphCompiler.VERSION, '1.1.0')

    def test_create_domain_entry(self):
        """主类调用 FR-003"""
        entry = self.compiler.create_domain_entry('测试', {'d': 1}, '分类')
        self.assertEqual(entry['status'], 'DRAFT')


if __name__ == '__main__':
    unittest.main()
