# SPDX-License-Identifier: Apache-2.0
"""TDCA-FC-20260803-005 FR-001 覆盖率补强
Granted-By: FC-005-SPEC
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors.nca_extractor import NCAExtractor


class TestNCAExtractorCoverage(unittest.TestCase):
    def test_load_from_dir_json(self):
        """从目录加载 JSON NCA"""
        with tempfile.TemporaryDirectory() as tmp:
            nca = {'NCA-ID': 'TDCA-NCA-X', 'Scope': '测试场景', 'MOU': 10.0}
            with open(os.path.join(tmp, 'nca1.json'), 'w', encoding='utf-8') as f:
                json.dump(nca, f)
            ext = NCAExtractor(nca_dir=tmp)
            result = ext.build_from_nca({'scenario': '测试场景'})
            self.assertEqual(result['nodes_created'], 1)

    def test_empty_dir(self):
        """空目录 → 0 节点"""
        with tempfile.TemporaryDirectory() as tmp:
            ext = NCAExtractor(nca_dir=tmp)
            result = ext.build_from_nca({'scenario': 'x'})
            self.assertEqual(result['nodes_created'], 0)

    def test_subject_did_filter(self):
        """主体 DID 过滤"""
        records = [
            {'NCA-ID': 'A', 'Scope': '场景', 'Operator': 'agent-1', 'MOU': 5.0},
            {'NCA-ID': 'B', 'Scope': '场景', 'Operator': 'agent-2', 'MOU': 5.0},
        ]
        ext = NCAExtractor(nca_loader=lambda q: records)
        result = ext.build_from_nca({'scenario': '场景', 'subject_dids': ['agent-1']})
        self.assertEqual(result['nodes_created'], 1)

    def test_invalid_timestamp_no_crash(self):
        """无效时间戳不崩溃，衰减=1.0"""
        ext = NCAExtractor()
        self.assertEqual(ext._recency_decay('not-a-date', 180), 1.0)
        self.assertEqual(ext._recency_decay(None, 180), 1.0)

    def test_halflife_zero(self):
        """半衰期<=0 → 衰减=1.0"""
        ext = NCAExtractor()
        self.assertEqual(ext._recency_decay('2020-01-01T00:00:00Z', 0), 1.0)

    def test_mou_as_dict(self):
        """MOU 为 dict 格式"""
        records = [{'NCA-ID': 'A', 'Scope': '场景', 'MOU': {'total': 50.0}}]
        ext = NCAExtractor(nca_loader=lambda q: records)
        result = ext.build_from_nca({'scenario': '场景'})
        self.assertEqual(result['nodes'][0]['confidence']['mou_anchor'], 50.0)

    def test_mou_invalid(self):
        """MOU 无效值 → 0"""
        records = [{'NCA-ID': 'A', 'Scope': '场景', 'MOU': 'invalid'}]
        ext = NCAExtractor(nca_loader=lambda q: records)
        result = ext.build_from_nca({'scenario': '场景'})
        self.assertEqual(result['nodes'][0]['confidence']['mou_anchor'], 0.0)

    def test_no_scope_record(self):
        """记录无 Scope 字段"""
        records = [{'NCA-ID': 'A', 'MOU': 5.0}]
        ext = NCAExtractor(nca_loader=lambda q: records)
        result = ext.build_from_nca({'scenario': ''})  # 空场景匹配全部
        self.assertEqual(result['nodes_created'], 1)


if __name__ == '__main__':
    unittest.main()
