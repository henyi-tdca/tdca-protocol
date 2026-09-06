# SPDX-License-Identifier: Apache-2.0
"""TDCA-FC-20260803-005 FR-002 单元测试 — ExternalDataExtractor
Granted-By: FC-005-SPEC
NSFL-Declaration: 测试验证文件导入/负空间检查/可信度逻辑
"""
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors.external_extractor import ExternalDataExtractor


class TestExternalDataExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = ExternalDataExtractor()

    def _write_csv(self, tmp, rows):
        path = os.path.join(tmp, 'data.csv')
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_import_csv(self):
        """CSV 导入构建知识节点"""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_csv(tmp, [
                {'name': '供应商A', 'region': '苏州', 'rating': 'A'},
                {'name': '供应商B', 'region': '杭州', 'rating': 'B'},
            ])
            result = self.extractor.import_file(path, '供应商数据库', trust_level=0.8)
            self.assertEqual(result['nodes_created'], 2)
            self.assertTrue(result['nsfl_checked'])
            self.assertTrue(result['source_summary']['trust_level'] == 0.8)

    def test_import_json(self):
        """JSON 导入"""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([{'name': '行业基准', 'value': 100}], f)
            result = self.extractor.import_file(path, '行业数据库')
            self.assertEqual(result['nodes_created'], 1)

    def test_nsfl_trigger_sensitive(self):
        """负空间检查：敏感内容触发"""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_csv(tmp, [
                {'name': 'x', 'note': '含个人身份证信息'},
            ])
            with self.assertRaises(ValueError) as ctx:
                self.extractor.import_file(path, '测试源')
            self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_nsfl_trigger_file_not_found(self):
        """文件不存在 → NSFL-TRIGGER"""
        with self.assertRaises(FileNotFoundError) as ctx:
            self.extractor.import_file('/nonexistent/x.csv', 'x')
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_unsupported_format(self):
        """不支持的格式 → NSFL-TRIGGER"""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.xlsx')
            with open(path, 'w') as f:
                f.write('x')
            with self.assertRaises(ValueError) as ctx:
                self.extractor.import_file(path, 'x')
            self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_mapping(self):
        """字段映射"""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_csv(tmp, [{'col1': 'A', 'col2': 'B'}])
            result = self.extractor.import_file(
                path, '映射源', mapping={'objective': 'col1', 'region': 'col2'}
            )
            self.assertEqual(result['nodes'][0]['content']['objective_snapshot'], 'A')

    def test_trust_level_affects_confidence(self):
        """可信度影响最终置信度"""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_csv(tmp, [{'name': 'x', 'a': '1', 'b': '2', 'c': '3', 'd': '4'}])
            high = self.extractor.import_file(path, '高可信', trust_level=0.9)
            low = self.extractor.import_file(path, '低可信', trust_level=0.3)
            self.assertGreater(
                high['nodes'][0]['confidence']['final_score'],
                low['nodes'][0]['confidence']['final_score']
            )

    def test_api_not_implemented(self):
        """API 接入未实现 → NSFL-TRIGGER"""
        with self.assertRaises(NotImplementedError):
            self.extractor.import_api('http://x', 'x')

    def test_validate_pass(self):
        """有效结果通过验证"""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_csv(tmp, [{'name': 'x'}])
            result = self.extractor.import_file(path, '源')
            self.extractor.validate(result)

    def test_validate_nsfl_not_checked(self):
        """未负空间检查 → validate 抛异常"""
        bad = {'nodes_created': 1, 'node_refs': ['x'], 'nsfl_checked': False,
               'nodes': [{'node_id': 'x', 'metadata': {'source': 'external:y'}}]}
        with self.assertRaises(ValueError) as ctx:
            self.extractor.validate(bad)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_requires_approval_flag(self):
        """敏感领域审批标记"""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_csv(tmp, [{'name': 'x'}])
            result = self.extractor.import_file(path, '金融源', requires_approval=True)
            self.assertTrue(result['needs_approval'])


if __name__ == '__main__':
    unittest.main()
