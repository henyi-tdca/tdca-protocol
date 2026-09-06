# SPDX-License-Identifier: Apache-2.0
"""TDCA-DEV-TASK-004 LIM-001 单元测试 — 强制 NCA 生成
Granted-By: TDCA-DEV-TASK-004
NSFL-Declaration: 测试验证知识条目创建强制生成 NCA 存证
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.domain_manager import DomainKnowledgeManager


class TestLIM001NCAEnforcement(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_create_entry_generates_nca(self):
        """创建条目必须自动生成 NCA"""
        generator = Mock(return_value={'NCA-ID': 'TDCA-NCA-LIM001-001'})
        mgr = DomainKnowledgeManager(
            storage_dir=os.path.join(self.tmp, 'dk'),
            nca_generator=generator,
        )
        entry = mgr.create_entry('标题', {'d': 1}, '分类')
        # nca_generator.generate() 被调用一次
        generator.assert_called_once()
        # entry['nca_ref'] 非空
        self.assertEqual(entry['nca_ref'], 'TDCA-NCA-LIM001-001')

    def test_nsfl_trigger_no_generator(self):
        """未注入 nca_generator → NSFL-TRIGGER"""
        mgr = DomainKnowledgeManager(storage_dir=os.path.join(self.tmp, 'dk'))
        with self.assertRaises(ValueError) as ctx:
            mgr.create_entry('标题', {'d': 1}, '分类')
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))
        self.assertIn('nca_generator', str(ctx.exception))

    def test_explicit_nca_ref_no_generate(self):
        """显式提供 nca_ref → 不调用 generator"""
        generator = Mock()
        mgr = DomainKnowledgeManager(
            storage_dir=os.path.join(self.tmp, 'dk'),
            nca_generator=generator,
        )
        entry = mgr.create_entry('标题', {'d': 1}, '分类', nca_ref='TDCA-NCA-EXPLICIT')
        generator.assert_not_called()
        self.assertEqual(entry['nca_ref'], 'TDCA-NCA-EXPLICIT')


if __name__ == '__main__':
    unittest.main()
