# SPDX-License-Identifier: Apache-2.0
"""TDCA-FC-012 C-3 辅助模块测试
Granted-By: TDCA-FC-012-DESIGN-002
NSFL: 测试验证熔断档位/MOU闭环/NCA报告
"""
import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fuse_adapter import FuseAdapter
from src.mou_closer import MOUCloser
from src.nca_reporter import NCAReporter


class TestFuseAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = FuseAdapter()

    def test_trigger_level1(self):
        """Level-1 软熔断可重试"""
        r = self.adapter.trigger('LEVEL_1', '条件不满足', 'P2')
        self.assertTrue(r['retryable'])
        self.assertIn('软熔断', r['desc'])

    def test_trigger_level2(self):
        """Level-2 硬熔断不可重试"""
        r = self.adapter.trigger('LEVEL_2', '触及负空间', 'P3')
        self.assertFalse(r['retryable'])

    def test_trigger_level3(self):
        """Level-3 紧急熔断永久冻结"""
        r = self.adapter.trigger('LEVEL_3', '数据完整性', 'P8')
        self.assertFalse(r['retryable'])
        self.assertIn('永久冻结', r['desc'])

    def test_nsfl_trigger_invalid_level(self):
        """非法级别 → NSFL-TRIGGER"""
        with self.assertRaises(ValueError) as ctx:
            self.adapter.trigger('LEVEL_9', 'x', 'P0')
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_on_fuse_callback(self):
        """熔断回调通知前端"""
        callback = Mock()
        adapter = FuseAdapter(on_fuse=callback)
        adapter.trigger('LEVEL_2', '负空间', 'P1')
        callback.assert_called_once()

    def test_retry_count(self):
        """重试计数"""
        history = [
            {'level': 'LEVEL_1', 'reason': 'a'},
            {'level': 'LEVEL_2', 'reason': 'b'},
            {'level': 'LEVEL_1', 'reason': 'c'},
        ]
        self.assertEqual(self.adapter.retry_count(history), 2)

    # OPT-C3-002: 相变检测测试
    def test_phase_transition_activate(self):
        """Δw 超上限 → 激活提升"""
        self.assertEqual(self.adapter.phase_transition_detect(0.5), 'ACTIVATE')

    def test_phase_transition_suppress(self):
        """Δw 超下限 → 抑制归档"""
        self.assertEqual(self.adapter.phase_transition_detect(-0.5), 'SUPPRESS')

    def test_phase_transition_stable(self):
        """Δw 在阈值内 → 稳定"""
        self.assertEqual(self.adapter.phase_transition_detect(0.1), 'STABLE')


class TestMOUCloser(unittest.TestCase):
    def test_close_success(self):
        """MOU 闭环成功"""
        closer = MOUCloser()
        r = closer.close('FLOW-1', 100, 50)
        self.assertTrue(r['closed'])
        self.assertEqual(r['mou_total'], 150)

    def test_nsfl_trigger_not_closed(self):
        """MOU 未闭环 → NSFL-TRIGGER"""
        closer = MOUCloser()
        with self.assertRaises(ValueError) as ctx:
            closer.close('FLOW-1', 0, 0)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_mou_recorder_called(self):
        """MOU 记录器被调用"""
        recorder = Mock()
        closer = MOUCloser(mou_recorder=recorder)
        closer.close('FLOW-1', 10, 20)
        recorder.assert_called_once_with('FLOW-1', 10, 20)


class TestNCAReporter(unittest.TestCase):
    def test_report_mock(self):
        """无 FC-001 → mock NCA"""
        reporter = NCAReporter()
        nca = reporter.report('FLOW-1', 'P3')
        self.assertTrue(nca['mock'])
        self.assertEqual(nca['phase'], 'P3')

    def test_report_with_generator(self):
        """有 FC-001 → 真实 NCA"""
        generator = Mock(return_value={'nca_id': 'NCA-REAL-001'})
        reporter = NCAReporter(nca_generator=generator)
        nca = reporter.report('FLOW-1', 'P5')
        generator.assert_called_once_with('FLOW-1', 'P5')
        self.assertEqual(nca['nca_id'], 'NCA-REAL-001')


if __name__ == '__main__':
    unittest.main()
