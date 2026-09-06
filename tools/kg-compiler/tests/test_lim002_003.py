# SPDX-License-Identifier: Apache-2.0
"""TDCA-DEV-TASK-004 LIM-002/003 单元测试 — 主类集成
Granted-By: TDCA-DEV-TASK-004
NSFL-Declaration: 测试验证主类集成 FC-004B 负空间检查 + FC-001 NCA 生成器
"""
import csv
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tdca_kg_compiler import TDCAKnowledgeGraphCompiler


class TestLIM002003Integration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # 模拟 FC-004B 约束解释器
        self.constraint_interpreter = Mock()
        self.constraint_interpreter.check_negative_space.return_value = (True, "")
        # 模拟 FC-001 NCA 生成器
        self.nca_generator = Mock(return_value={'NCA-ID': 'TDCA-NCA-INTEG-001'})
        self.compiler = TDCAKnowledgeGraphCompiler(
            nca_generator=self.nca_generator,
            constraint_interpreter=self.constraint_interpreter,
        )

    def _write_csv(self, rows):
        path = os.path.join(self.tmp, 'data.csv')
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_import_external_with_nsfl_check(self):
        """外部数据导入必须调用 FC-004B 负空间检查"""
        path = self._write_csv([{'name': '供应商A', 'region': '苏州'}])
        result = self.compiler.import_external_file(path, '供应商库', trust_level=0.8)
        # check_negative_space 被调用一次
        self.constraint_interpreter.check_negative_space.assert_called_once()
        # result['nsfl_checked'] 为 True
        self.assertTrue(result['nsfl_checked'])

    def test_create_domain_entry_generates_nca(self):
        """创建领域条目自动生成 NCA"""
        entry = self.compiler.create_domain_entry('集成测试', {'d': 1}, '分类')
        # nca_generator 被调用一次
        self.nca_generator.assert_called_once()
        # nca_ref 非空
        self.assertEqual(entry['nca_ref'], 'TDCA-NCA-INTEG-001')

    def test_no_integration_fallback(self):
        """未注入集成 → 负空间检查用默认，NCA生成触发NSFL"""
        bare = TDCAKnowledgeGraphCompiler()
        path = self._write_csv([{'name': 'x'}])
        # 无 FC-004B → 用默认负空间检查（仍工作）
        result = bare.import_external_file(path, '源')
        self.assertTrue(result['nsfl_checked'])
        # 无 FC-001 → create_domain_entry 抛 NSFL-TRIGGER
        with self.assertRaises(ValueError) as ctx:
            bare.create_domain_entry('标题', {}, '分类')
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
