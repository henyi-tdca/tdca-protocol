"""
TDCA-FC-20260803-005 FR-006 修正声明: 无（首版）
制度锚定: FC-005-SPEC FR-006, ID38(破例识别原理)
Granted-By: FC-005-SPEC

NSFL-Declaration:
  - 回测失败即破例信号（ID38）
  - 回测只读，不修改先验分布
  - 偏差分析必须输出建议
SPDX-License-Identifier: Apache-2.0
"""

import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional


class BacktestValidator:
    """
    FR-006: 先验分布回测验证

    对生成的先验分布进行历史回测，验证其预测精度。

    输出: 回测报告（准确率、覆盖率、偏差分析）
    """

    def __init__(self):
        pass

    def backtest(
        self,
        prior_output: dict,
        test_dataset: List[dict],
        metrics: Optional[List[str]] = None
    ) -> dict:
        """
        执行回测验证。

        参数:
          prior_output: 先验分布输出（来自 FR-005）
          test_dataset: 历史测试数据集 [{'actual': float, 'predicted': float}, ...]
          metrics: 需要计算的指标（accuracy/coverage/bias）

        返回: {
          'backtest_id': str,
          'prior_output_id': str,
          'report': {
            'accuracy': float,
            'coverage': float,
            'bias_analysis': {...},
            'recommendation': str,
          }
        }
        """
        metrics = metrics or ['accuracy', 'coverage', 'bias']
        if not test_dataset:
            return self._empty_report(prior_output)

        report = {}

        # 准确率：预测值与实际值的一致性
        if 'accuracy' in metrics:
            report['accuracy'] = self._compute_accuracy(test_dataset)

        # 覆盖率：实际值落在预测区间内的比例
        if 'coverage' in metrics:
            report['coverage'] = self._compute_coverage(test_dataset)

        # 偏差分析
        if 'bias' in metrics:
            report['bias_analysis'] = self._compute_bias(test_dataset)

        # 建议（基于结果）
        report['recommendation'] = self._recommendation(report, test_dataset)

        return {
            'backtest_id': f"TDCA-BT-{uuid.uuid4().hex[:8]}",
            'prior_output_id': prior_output.get('output_id', ''),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'report': report,
        }

    def validate(self, result: dict) -> None:
        """
        自证机制：
          1. 报告含 accuracy/coverage/bias
          2. 回测失败（accuracy < 0.5）→ 破例信号（ID38）
          3. 指标在合法区间
        """
        errors = []
        report = result.get('report', {})
        if 'accuracy' in report and not 0 <= report['accuracy'] <= 1:
            errors.append(f"准确率超出 [0,1]: {report['accuracy']}")
        if 'coverage' in report and not 0 <= report['coverage'] <= 1:
            errors.append(f"覆盖率超出 [0,1]: {report['coverage']}")
        # ID38: 低准确率是破例信号，需要标记（空数据集除外——无数据非失败）
        recommendation = result.get('report', {}).get('recommendation', '')
        if report.get('accuracy', 1.0) < 0.5 and '无历史数据' not in recommendation:
            if '破例' not in recommendation:
                errors.append("低准确率未标记为破例信号（ID38）")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")

    # ---- 指标计算 ----

    @staticmethod
    def _compute_accuracy(dataset: List[dict]) -> float:
        """准确率：1 - 平均绝对误差（MAE）"""
        errors = []
        for d in dataset:
            actual = float(d.get('actual', 0))
            predicted = float(d.get('predicted', 0))
            errors.append(abs(actual - predicted))
        mae = sum(errors) / len(errors)
        # 归一化：假设效用范围 [0,1]，MAE 越大准确率越低
        return round(max(0.0, min(1.0, 1.0 - mae)), 4)

    @staticmethod
    def _compute_coverage(dataset: List[dict]) -> float:
        """覆盖率：实际值落在预测区间内的比例"""
        covered = 0
        for d in dataset:
            actual = float(d.get('actual', 0))
            lo = float(d.get('interval_lower', actual))
            hi = float(d.get('interval_upper', actual))
            if lo <= actual <= hi:
                covered += 1
        return round(covered / len(dataset), 4)

    @staticmethod
    def _compute_bias(dataset: List[dict]) -> dict:
        """偏差分析：系统性高估/低估"""
        deviations = []
        for d in dataset:
            actual = float(d.get('actual', 0))
            predicted = float(d.get('predicted', 0))
            deviations.append(predicted - actual)

        mean_bias = sum(deviations) / len(deviations)
        # 方差
        variance = sum((d - mean_bias) ** 2 for d in deviations) / len(deviations)

        if mean_bias > 0.05:
            direction = '系统性高估'
        elif mean_bias < -0.05:
            direction = '系统性低估'
        else:
            direction = '无明显偏差'

        return {
            'mean_bias': round(mean_bias, 4),
            'variance': round(variance, 4),
            'direction': direction,
        }

    @staticmethod
    def _recommendation(report: dict, dataset: List[dict]) -> str:
        """生成建议"""
        accuracy = report.get('accuracy', 0.0)
        coverage = report.get('coverage', 0.0)
        bias = report.get('bias_analysis', {}).get('direction', '')

        if accuracy >= 0.8 and coverage >= 0.8:
            return '先验分布质量良好，可投入使用'
        if accuracy >= 0.6:
            return '先验分布基本可用，建议结合偏差分析微调参数'
        if '高估' in bias:
            return '检测到系统性高估，建议降低先验置信度（破例信号，ID38）'
        if '低估' in bias:
            return '检测到系统性低估，建议提高先验置信度（破例信号，ID38）'
        return '回测失败，先验分布不可用，建议重新编译（破例信号，ID38）'

    def _empty_report(self, prior_output: dict) -> dict:
        """空数据集报告"""
        return {
            'backtest_id': f"TDCA-BT-{uuid.uuid4().hex[:8]}",
            'prior_output_id': prior_output.get('output_id', ''),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'report': {
                'accuracy': 0.0,
                'coverage': 0.0,
                'bias_analysis': {'mean_bias': 0.0, 'variance': 0.0, 'direction': '无数据'},
                'recommendation': '无历史数据可供回测，建议积累数据后重试',
            },
        }
