# -*- coding: utf-8 -*-
"""E-INT-2.1 StorageAdapter 单元测试"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage_adapter import MemoryStore, StorageRegistry, Neo4jAdapter, TimescaleAdapter


class TestMemoryStore(unittest.TestCase):
    """仿真存储（替代 SQLite）"""

    def test_01_write_read(self):
        m = MemoryStore()
        m.write('flow_states', 'FLOW-1', {'phase': 'P0'})
        self.assertEqual(m.read('flow_states', 'FLOW-1')['phase'], 'P0')

    def test_02_query_filter(self):
        m = MemoryStore()
        m.write('utility_metrics', 'F1', {'mou': 10.0})
        m.write('utility_metrics', 'F2', {'mou': 20.0})
        hits = m.query('utility_metrics', mou=20.0)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]['_key'], 'F2')

    def test_03_delete(self):
        m = MemoryStore()
        m.write('nca_records', 'NCA-1', {})
        self.assertTrue(m.delete('nca_records', 'NCA-1'))
        self.assertFalse(m.delete('nca_records', 'NCA-1'))


class TestStorageRegistry(unittest.TestCase):
    """存储注册表（按层路由 + 生产替换）"""

    def test_04_default_routing(self):
        reg = StorageRegistry(MemoryStore())
        self.assertIsInstance(reg.adapter_for('config_memory'), MemoryStore)

    def test_05_production_replace(self):
        """仿真→生产仅注册一步（EIOS 业务代码零修改）"""
        reg = StorageRegistry(MemoryStore())
        reg.register('config_memory', Neo4jAdapter())
        reg.register('utility_metrics', TimescaleAdapter())
        self.assertIsInstance(reg.adapter_for('config_memory'), Neo4jAdapter)
        self.assertIsInstance(reg.adapter_for('utility_metrics'), TimescaleAdapter)
        self.assertIsInstance(reg.adapter_for('flow_states'), MemoryStore)  # 未替换保持仿真

    def test_06_store_binding_nsfl(self):
        """适配器存储绑定校验（错误 store 触发 NSFL）"""
        with self.assertRaises(ValueError) as ctx:
            Neo4jAdapter().write('utility_metrics', 'k', {})
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_07_eios_zero_modification(self):
        """EIOS 业务代码零修改验证：注册表接口稳定（write/read/query）"""
        reg = StorageRegistry(MemoryStore())
        for store in ['config_memory', 'utility_metrics', 'flow_states', 'nca_records']:
            reg.write(store, 'K-%s' % store, {'data': 1})
            self.assertIsNotNone(reg.read(store, 'K-%s' % store))


if __name__ == '__main__':
    unittest.main()
