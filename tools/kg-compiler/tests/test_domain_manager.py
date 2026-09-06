# SPDX-License-Identifier: Apache-2.0
"""TDCA-FC-20260803-005 FR-003 单元测试 — DomainKnowledgeManager
Granted-By: FC-005-SPEC
NSFL-Declaration: 测试验证CRUD/版本控制/审批流/敏感标记
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.domain_manager import DomainKnowledgeManager


class TestDomainKnowledgeManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # LIM-001: 注入 mock nca_generator 使现有测试通过
        self.generator = Mock(return_value={'NCA-ID': 'TDCA-NCA-TEST-001'})
        self.mgr = DomainKnowledgeManager(
            storage_dir=os.path.join(self.tmp, 'dk'),
            nca_generator=self.generator,
        )

    def test_create_entry(self):
        """创建条目（草稿状态）"""
        entry = self.mgr.create_entry('测试知识', {'data': 1}, '测试分类')
        self.assertEqual(entry['status'], 'DRAFT')
        self.assertEqual(entry['version'], 1)
        self.assertEqual(len(entry['versions']), 1)

    def test_get_entry(self):
        """读取条目"""
        entry = self.mgr.create_entry('标题', {'d': 1}, '分类')
        fetched = self.mgr.get_entry(entry['entry_id'])
        self.assertEqual(fetched['title'], '标题')

    def test_get_nonexistent(self):
        """读取不存在条目 → None"""
        self.assertIsNone(self.mgr.get_entry('TDCA-DK-nonexistent'))

    def test_update_increments_version(self):
        """更新递增版本 + 重置为草稿"""
        entry = self.mgr.create_entry('标题', {'d': 1}, '分类')
        updated = self.mgr.update_entry(entry['entry_id'], content={'d': 2})
        self.assertEqual(updated['version'], 2)
        self.assertEqual(updated['status'], 'DRAFT')
        self.assertEqual(len(updated['versions']), 2)

    def test_update_nonexistent_raises(self):
        """更新不存在条目 → NSFL-TRIGGER"""
        with self.assertRaises(KeyError) as ctx:
            self.mgr.update_entry('TDCA-DK-x', content={})
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_delete_entry(self):
        """删除条目"""
        entry = self.mgr.create_entry('标题', {}, '分类')
        self.assertTrue(self.mgr.delete_entry(entry['entry_id']))
        self.assertFalse(self.mgr.delete_entry('TDCA-DK-gone'))

    def test_rollback(self):
        """版本回滚"""
        entry = self.mgr.create_entry('V1标题', {'data': 'v1'}, '分类')
        self.mgr.update_entry(entry['entry_id'], content={'data': 'v2'})
        rolled = self.mgr.rollback(entry['entry_id'], 1)
        self.assertEqual(rolled['content']['data'], 'v1')

    def test_rollback_invalid_version(self):
        """回滚无效版本 → NSFL-TRIGGER"""
        entry = self.mgr.create_entry('标题', {}, '分类')
        with self.assertRaises(ValueError) as ctx:
            self.mgr.rollback(entry['entry_id'], 99)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_approval_flow(self):
        """完整审批流：草稿→待审→通过"""
        entry = self.mgr.create_entry('标题', {}, '分类')
        pending = self.mgr.submit_for_approval(entry['entry_id'])
        self.assertEqual(pending['status'], 'PENDING_APPROVAL')
        approved = self.mgr.approve(entry['entry_id'], 'human-1')
        self.assertEqual(approved['status'], 'APPROVED')
        self.assertEqual(approved['approved_by'], 'human-1')

    def test_submit_non_draft_raises(self):
        """非草稿提交审批 → NSFL-TRIGGER"""
        entry = self.mgr.create_entry('标题', {}, '分类')
        self.mgr.submit_for_approval(entry['entry_id'])
        with self.assertRaises(ValueError) as ctx:
            self.mgr.submit_for_approval(entry['entry_id'])
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_reject(self):
        """审批拒绝"""
        entry = self.mgr.create_entry('标题', {}, '分类')
        self.mgr.submit_for_approval(entry['entry_id'])
        rejected = self.mgr.reject(entry['entry_id'], 'human-1', '内容不完整')
        self.assertEqual(rejected['status'], 'REJECTED')
        self.assertEqual(rejected['reject_reason'], '内容不完整')

    def test_approve_non_pending_raises(self):
        """非待审状态审批 → NSFL-TRIGGER"""
        entry = self.mgr.create_entry('标题', {}, '分类')
        with self.assertRaises(ValueError) as ctx:
            self.mgr.approve(entry['entry_id'], 'human-1')
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_list_entries_filter(self):
        """按分类/状态过滤"""
        self.mgr.create_entry('A', {}, '分类1')
        self.mgr.create_entry('B', {}, '分类2')
        results = self.mgr.list_entries(category='分类1')
        self.assertEqual(len(results), 1)

    def test_sensitive_requires_approval(self):
        """敏感条目需审批（validate 检查）"""
        entry = self.mgr.create_entry('敏感', {}, '政务', sensitive=True)
        with self.assertRaises(ValueError) as ctx:
            self.mgr.validate(entry)  # DRAFT 状态未审批
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))
        # 审批后通过
        self.mgr.submit_for_approval(entry['entry_id'])
        self.mgr.approve(entry['entry_id'], 'human-1')
        approved = self.mgr.get_entry(entry['entry_id'])
        self.mgr.validate(approved)

    def test_version_history(self):
        """版本历史"""
        entry = self.mgr.create_entry('标题', {}, '分类')
        self.mgr.update_entry(entry['entry_id'], content={'x': 2})
        history = self.mgr.get_version_history(entry['entry_id'])
        self.assertEqual(len(history), 2)

    def test_validate_missing_field(self):
        """缺字段 → validate 抛异常"""
        with self.assertRaises(ValueError) as ctx:
            self.mgr.validate({'title': 'x'})
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
