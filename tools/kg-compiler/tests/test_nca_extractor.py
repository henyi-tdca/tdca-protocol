# SPDX-License-Identifier: Apache-2.0
"""TDCA-FC-20260803-005 FR-001 单元测试 — NCAExtractor
Granted-By: FC-005-SPEC
NSFL-Declaration: 测试用模拟NCA数据，验证抽取/置信度/时效衰减逻辑
"""
import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors.nca_extractor import NCAExtractor, KnowledgeNode


def make_nca(nca_id, scope, mou, operator='agent-1', timestamp='2026-08-01T10:00:00Z'):
    return {
        'NCA-ID': nca_id,
        'Scope': scope,
        'Operator': operator,
        'Timestamp': timestamp,
        'MOU': mou,
        'Config-Right-Token': {'Scope': 'test', 'Max-Retry': 0},
        'Audit-Trail': [{'Step': 'op'}],
    }


class TestNCAExtractor(unittest.TestCase):
    def setUp(self):
        self.records = [
            make_nca('TDCA-NCA-001', '政府采购-投标', 100.0),
            make_nca('TDCA-NCA-002', '政府采购-投标', 200.0),
            make_nca('TDCA-NCA-003', '企业采购-招标', 50.0),
        ]
        self.extractor = NCAExtractor(nca_loader=lambda q: self.records)

    def test_build_from_nca(self):
        """按场景构建知识节点"""
        result = self.extractor.build_from_nca({'scenario': '政府采购'})
        self.assertEqual(result['nodes_created'], 2)
        self.assertEqual(len(result['node_refs']), 2)
        # 置信度非零（MOU > 0）
        for node in result['nodes']:
            self.assertGreater(node['confidence']['final_score'], 0)

    def test_min_mou_filter(self):
        """最低 MOU 阈值过滤"""
        result = self.extractor.build_from_nca(
            {'scenario': '政府采购'},
            {'min_mou_threshold': 150.0}
        )
        self.assertEqual(result['nodes_created'], 1)  # 只有 NCA-002(200)

    def test_nsfl_trigger_no_source_ref(self):
        """缺来源NCA引用 → validate 抛异常"""
        bad = {
            'nodes_created': 1,
            'node_refs': ['TDCA-KN-001'],
            'nodes': [{
                'node_id': 'TDCA-KN-001',
                'metadata': {'source': 'manual'},  # 无 nca_ref
            }],
        }
        with self.assertRaises(ValueError) as ctx:
            self.extractor.validate(bad)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_validate_pass(self):
        """有效结果通过验证"""
        result = self.extractor.build_from_nca({'scenario': '政府采购'})
        self.extractor.validate(result)

    def test_recency_decay(self):
        """时效性衰减：旧NCA置信度低"""
        # 400天前（halflife=180）→ 衰减到 2^(-400/180) ≈ 0.21
        decay = self.extractor._recency_decay('2025-06-30T00:00:00Z', 180)
        self.assertLess(decay, 0.3)
        self.assertGreater(decay, 0.1)
        # 新NCA → 衰减接近1（用当前时间构造，避免固定日期随时间自然衰减导致断言脆弱）
        decay_new = self.extractor._recency_decay(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 180)
        self.assertAlmostEqual(decay_new, 1.0, delta=0.05)

    def test_node_refs_consistency(self):
        """node_refs 与 nodes_created 一致"""
        result = self.extractor.build_from_nca({'scenario': '企业采购'})
        self.assertEqual(result['nodes_created'], len(result['node_refs']))

    def test_stats_computed(self):
        """统计分布计算"""
        result = self.extractor.build_from_nca({'scenario': '政府采购'})
        self.assertEqual(result['stats']['node_count'], 2)
        self.assertGreater(result['stats']['avg_confidence'], 0)


if __name__ == '__main__':
    unittest.main()
