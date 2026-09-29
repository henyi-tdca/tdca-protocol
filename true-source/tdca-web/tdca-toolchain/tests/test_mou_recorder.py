"""TDCA-FC-20260801-003 任务A 单元测试 — TDCAMOURecorder
Granted-By: TDCA-PRINCIPLE-MOU-001
NSFL-Declaration: 测试不伪造税收数据，测试用 null 显式标注模拟阶段
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tdca_mou_recorder import TDCAMOURecorder


class TestTDCAMOURecorder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.mou_dir = os.path.join(self.tmp, 'mou')
        self.rec = TDCAMOURecorder(
            token_ref='TDCA-CRT-20260801-001',
            pre_est=1000.0,
            mou_dir=self.mou_dir
        )

    def test_record_simulated(self):
        """模拟阶段：Tax-In/Out 为 null，Pre-Est 标记 [SIMULATED]"""
        r = self.rec.record()
        self.assertIsNone(r['Tax-In'])
        self.assertIsNone(r['Tax-Out'])
        self.assertIsNone(r['Actual-Total'])
        self.assertEqual(r['Pre-Est'], 1000.0)
        self.assertEqual(r['Pre-Est-Status'], '[SIMULATED]')
        self.assertIsNone(r['Activation-Coefficient'])
        self.assertRegex(r['MOU-ID'], r'^TDCA-MOU-\d{8}-\d{3}$')

    def test_record_actual(self):
        """实际数据阶段：Tax-In/Out 提供真实值"""
        r = self.rec.record(tax_in=500.0, tax_out=300.0)
        self.assertEqual(r['Tax-In'], 500.0)
        self.assertEqual(r['Tax-Out'], 300.0)
        self.assertEqual(r['Actual-Total'], 800.0)

    def test_nsfl_trigger_invalid_token_ref(self):
        """NSFL-TRIGGER：无效 Token-Ref 格式"""
        with self.assertRaises(ValueError) as ctx:
            TDCAMOURecorder(token_ref='INVALID-TOKEN')
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_validate_missing_pre_est(self):
        """NSFL-TRIGGER：Tax-In/Out 为 null 但 Pre-Est 缺失"""
        rec = TDCAMOURecorder(token_ref='TDCA-CRT-20260801-001', mou_dir=self.mou_dir)
        bad = {
            'MOU-ID': 'TDCA-MOU-20260801-999',
            'Token-Ref': 'TDCA-CRT-20260801-001',
            'Tax-In': None, 'Tax-Out': None, 'Actual-Total': None,
            'Pre-Est': None, 'Pre-Est-Status': None,
            'Activation-Coefficient': None,
            'Recorded-At': '2026-08-01T10:00:00Z',
        }
        with self.assertRaises(ValueError) as ctx:
            rec.validate(bad)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_validate_activation_without_actual(self):
        """NSFL-TRIGGER：Actual-Total 为 null 但 Activation-Coefficient 非空"""
        rec = TDCAMOURecorder(token_ref='TDCA-CRT-20260801-001', mou_dir=self.mou_dir)
        bad = {
            'MOU-ID': 'TDCA-MOU-20260801-999',
            'Token-Ref': 'TDCA-CRT-20260801-001',
            'Tax-In': None, 'Tax-Out': None, 'Actual-Total': None,
            'Pre-Est': 1000.0, 'Pre-Est-Status': '[SIMULATED]',
            'Activation-Coefficient': 2.5,
            'Recorded-At': '2026-08-01T10:00:00Z',
        }
        with self.assertRaises(ValueError) as ctx:
            rec.validate(bad)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_compute_activation_coefficient(self):
        """激活系数公式验证"""
        c = self.rec.compute_activation_coefficient(800.0, 400.0, 200.0)
        self.assertEqual(c, 2.5)  # (800+200)/400

    def test_nsfl_trigger_gov_pcr_zero(self):
        """NSFL-TRIGGER：gov_pcr <= 0"""
        with self.assertRaises(ValueError) as ctx:
            self.rec.compute_activation_coefficient(100.0, 0)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_save_load_roundtrip(self):
        """保存/加载往返验证"""
        r = self.rec.record()
        path = self.rec.save(r)
        self.assertTrue(os.path.exists(path))
        loaded = TDCAMOURecorder.load(path)
        self.assertEqual(loaded['Token-Ref'], 'TDCA-CRT-20260801-001')
        self.assertEqual(loaded['Pre-Est'], 1000.0)

    def test_to_yaml_parses(self):
        """YAML 输出可被 yaml.safe_load 解析"""
        import yaml
        r = self.rec.record()
        y = self.rec.to_yaml(r)
        parsed = yaml.safe_load(y)
        self.assertEqual(parsed['Token-Ref'], 'TDCA-CRT-20260801-001')


if __name__ == '__main__':
    unittest.main()
