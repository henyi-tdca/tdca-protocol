# SPDX-License-Identifier: Apache-2.0
"""TDCA-FC-20260803-005 FR-006 单元测试 — BacktestValidator
Granted-By: FC-005-SPEC, ID38
NSFL-Declaration: 测试验证回测指标/破例信号
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validators.backtest_validator import BacktestValidator


def good_dataset():
    """高质量数据集：预测接近实际"""
    return [
        {'actual': 0.9, 'predicted': 0.92, 'interval_lower': 0.8, 'interval_upper': 1.0},
        {'actual': 0.7, 'predicted': 0.71, 'interval_lower': 0.6, 'interval_upper': 0.8},
        {'actual': 0.5, 'predicted': 0.51, 'interval_lower': 0.4, 'interval_upper': 0.6},
    ]


def bad_dataset():
    """低质量数据集：预测严重偏离"""
    return [
        {'actual': 0.9, 'predicted': 0.1, 'interval_lower': 0.0, 'interval_upper': 0.2},
        {'actual': 0.7, 'predicted': 0.1, 'interval_lower': 0.0, 'interval_upper': 0.2},
        {'actual': 0.5, 'predicted': 0.1, 'interval_lower': 0.0, 'interval_upper': 0.2},
    ]


def overestimate_dataset():
    """系统性高估数据集"""
    return [
        {'actual': 0.1, 'predicted': 0.9, 'interval_lower': 0.8, 'interval_upper': 1.0},
        {'actual': 0.2, 'predicted': 0.95, 'interval_lower': 0.8, 'interval_upper': 1.0},
        {'actual': 0.1, 'predicted': 0.85, 'interval_lower': 0.8, 'interval_upper': 1.0},
    ]


class TestBacktestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = BacktestValidator()
        self.prior = {'output_id': 'TDCA-PD-001'}

    def test_good_backtest(self):
        """高质量数据 → 高准确率 + 建议可用"""
        result = self.validator.backtest(self.prior, good_dataset())
        self.assertGreaterEqual(result['report']['accuracy'], 0.9)
        self.assertGreaterEqual(result['report']['coverage'], 0.9)
        self.assertIn('良好', result['report']['recommendation'])

    def test_nsfl_trigger_bad_accuracy(self):
        """低准确率 → 破例信号（ID38）+ validate 抛异常"""
        result = self.validator.backtest(self.prior, bad_dataset())
        self.assertLess(result['report']['accuracy'], 0.5)
        self.assertIn('破例', result['report']['recommendation'])
        # validate 会通过（含破例标记）
        self.validator.validate(result)

    def test_validate_missing_break_signal(self):
        """低准确率但无破例标记 → validate 抛异常"""
        bad_result = {
            'report': {'accuracy': 0.1, 'coverage': 0.1, 'recommendation': '该模型无法使用'},
        }
        with self.assertRaises(ValueError) as ctx:
            self.validator.validate(bad_result)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_bias_detection(self):
        """系统性高估检测"""
        result = self.validator.backtest(self.prior, overestimate_dataset())
        self.assertEqual(result['report']['bias_analysis']['direction'], '系统性高估')
        self.assertIn('高估', result['report']['recommendation'])

    def test_empty_dataset(self):
        """空数据集 → 无数据报告"""
        result = self.validator.backtest(self.prior, [])
        self.assertEqual(result['report']['accuracy'], 0.0)
        self.assertIn('无历史数据', result['report']['recommendation'])

    def test_backtest_id_format(self):
        """回测ID格式"""
        result = self.validator.backtest(self.prior, good_dataset())
        self.assertTrue(result['backtest_id'].startswith('TDCA-BT-'))
        self.assertEqual(result['prior_output_id'], 'TDCA-PD-001')

    def test_metrics_selection(self):
        """指标选择"""
        result = self.validator.backtest(self.prior, good_dataset(), metrics=['accuracy'])
        self.assertIn('accuracy', result['report'])
        self.assertNotIn('coverage', result['report'])

    def test_coverage_interval(self):
        """覆盖率计算"""
        dataset = [
            {'actual': 0.5, 'interval_lower': 0.4, 'interval_upper': 0.6},
            {'actual': 0.9, 'interval_lower': 0.4, 'interval_upper': 0.6},  # 未覆盖
        ]
        result = self.validator.backtest(self.prior, dataset, metrics=['coverage'])
        self.assertEqual(result['report']['coverage'], 0.5)


if __name__ == '__main__':
    unittest.main()
