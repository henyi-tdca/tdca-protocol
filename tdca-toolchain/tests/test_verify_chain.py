"""TDCA-FC-20260801-003 任务C 单元测试 — tdca_verify_chain
Granted-By: TDCA-MEMO-008
NSFL-Declaration: 测试只读，不修改任何记录
"""
import os
import sys
import tempfile
import unittest
import yaml
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tdca_verify_chain import TDCACVerifyChain


class TestVerifyChain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.token_dir = os.path.join(self.tmp, 'tokens')
        self.nca_dir = os.path.join(self.tmp, 'nca')
        self.mou_dir = os.path.join(self.tmp, 'mou')
        os.makedirs(self.token_dir)
        os.makedirs(self.nca_dir)
        os.makedirs(self.mou_dir)

    def _write_token(self):
        token = {
            'Token-ID': 'TDCA-CRT-20260801-001',
            'Scope': 'test',
            'task_type': 'CodeGen',
            'Human-Signature-Required': True,
        }
        with open(os.path.join(self.token_dir, 'TDCA-CRT-20260801-001.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(token, f)

    def _write_nca(self):
        nca = {
            'NCA-ID': 'TDCA-NCA-20260801-001',
            'Timestamp': '2026-08-01T10:00:00Z',
        }
        with open(os.path.join(self.nca_dir, 'TDCA-NCA-20260801-001.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(nca, f)

    def _write_mou(self, token_ref='TDCA-CRT-20260801-001', tax_in=500.0, tax_out=300.0, actual=800.0):
        mou = {
            'MOU-ID': 'TDCA-MOU-20260801-001',
            'Token-Ref': token_ref,
            'Tax-In': tax_in,
            'Tax-Out': tax_out,
            'Actual-Total': actual,
            'Recorded-At': '2026-08-01T11:00:00Z',
        }
        with open(os.path.join(self.mou_dir, 'TDCA-MOU-20260801-001.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(mou, f)

    def test_verify_pass(self):
        """完整链路 PASS"""
        self._write_token()
        self._write_nca()
        self._write_mou()
        v = TDCACVerifyChain('TDCA-FC-001', self.token_dir, self.nca_dir, self.mou_dir)
        report = v.verify()
        self.assertEqual(report['Status'], 'PASS')
        self.assertTrue(report['Chain-Integrity']['Linked'])

    def test_nsfl_trigger_no_token_dir(self):
        """NSFL-TRIGGER：Token 目录缺失 → FAIL"""
        v = TDCACVerifyChain('TDCA-FC-001', os.path.join(self.tmp, 'missing'), self.nca_dir, self.mou_dir)
        report = v.verify()
        self.assertEqual(report['Status'], 'FAIL')

    def test_mou_token_ref_mismatch(self):
        """MOU Token-Ref 不匹配 → FAIL"""
        self._write_token()
        self._write_nca()
        self._write_mou(token_ref='TDCA-CRT-WRONG-001')
        v = TDCACVerifyChain('TDCA-FC-001', self.token_dir, self.nca_dir, self.mou_dir)
        report = v.verify()
        self.assertEqual(report['Status'], 'FAIL')

    def test_mou_tax_consistency_warn(self):
        """MOU 税收不一致 → WARN"""
        self._write_token()
        self._write_nca()
        self._write_mou(tax_in=500.0, tax_out=300.0, actual=850.0)
        v = TDCACVerifyChain('TDCA-FC-001', self.token_dir, self.nca_dir, self.mou_dir)
        report = v.verify()
        self.assertEqual(report['Status'], 'WARN')

    def test_nsfl_event_detected(self):
        """负空间任务缺少 NSFL-Declaration → 事件高亮"""
        token = {
            'Token-ID': 'TDCA-CRT-20260801-002',
            'Scope': 'test',
            'task_type': 'FileDelete',
            'Human-Signature-Required': True,
            # 缺少 NSFL-Declaration
        }
        with open(os.path.join(self.token_dir, 'TDCA-CRT-20260801-002.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(token, f)
        self._write_nca()
        self._write_mou()
        v = TDCACVerifyChain('TDCA-FC-001', self.token_dir, self.nca_dir, self.mou_dir)
        report = v.verify()
        self.assertTrue(len(report['NSFL-Events']) > 0)
        self.assertEqual(report['NSFL-Events'][0]['Severity'], 'P0')

    def test_report_has_id_and_timestamp(self):
        """报告包含 Verification-ID 与 Timestamp"""
        v = TDCACVerifyChain('TDCA-FC-001', self.token_dir, self.nca_dir, self.mou_dir)
        report = v.verify()
        self.assertIn('Verification-ID', report)
        self.assertIn('Timestamp', report)
        self.assertIn('FC-ID', report)


if __name__ == '__main__':
    unittest.main()
