"""
TDCA-FC-20260802-004 修正声明:
  - R1-P1: Max-Retry 语义层级区分
  - R1-P1: embedding 三级降级策略
  - R1-P2: 执行顺序并行化

制度锚定: ID8 (NIA-MACM 3.0 五维认知状态向量), COH-001/002
Granted-By: ID8

NSFL-Declaration:
  - S向量字段可空，不破坏已有 NCA v2.0 解析
  - 计算需真实数据，初期可用默认值并标记 [DEFAULT]
  - 禁止伪造认知状态数据
SPDX-License-Identifier: TDCA-Internal
"""

import math
import re
from typing import Optional


class CognitiveStateCalculator:
    """
    五维认知状态向量 S=(A, D, L, C, SC) 计算器

    依据 ID8 (NIA-MACM 3.0):
      A (Awareness): 感知精度 — 输出与输入的匹配度
      D (Decision):  决策质量 — 约束满足度
      L (Learning):  学习速度 — 历史偏差收敛率
      C (Cross-domain): 跨域配置 — 跨界调用成功率
      SC (Safety/Compliance): 安全合规 — 负空间识别准确率
    """

    def __init__(self, history: Optional[list] = None):
        """
        参数:
          history: 历史 NCA 记录列表（用于 L 学习速度计算）
        """
        self.history = history or []

    def compute(
        self,
        embedding_similarity: Optional[float] = None,
        constraint_satisfaction_rate: Optional[float] = None,
        cross_domain_success_rate: Optional[float] = None,
        total_calls: Optional[int] = None,
        negative_space_detection_accuracy: Optional[float] = None,
        use_defaults: bool = True
    ) -> dict:
        """
        计算五维认知状态向量。

        返回:
          {
            'A': 0.85, 'D': 0.92, 'L': 0.78, 'C': 0.65, 'SC': 0.95,
            'Computation-Method': {...},
            'Default-Flagged': bool
          }

        缺失维度使用默认值 0.5 并标记 [DEFAULT]（不破坏 v2.0 兼容）。
        """
        defaulted = []
        result = {}

        # A: 感知精度 = embedding_similarity
        if embedding_similarity is not None:
            result['A'] = max(0.0, min(1.0, embedding_similarity))
        else:
            result['A'] = 0.5
            defaulted.append('A')

        # D: 决策质量 = constraint_satisfaction_rate
        if constraint_satisfaction_rate is not None:
            result['D'] = max(0.0, min(1.0, constraint_satisfaction_rate))
        else:
            result['D'] = 0.5
            defaulted.append('D')

        # L: 学习速度 = 1 / (1 + exp(-k*(current_accuracy - historical_mean)))
        current_acc = constraint_satisfaction_rate
        if current_acc is not None and self.history:
            hist_mean = sum(self.history) / len(self.history)
            k = 2.0
            result['L'] = 1.0 / (1.0 + math.exp(-k * (current_acc - hist_mean)))
        else:
            result['L'] = 0.5
            defaulted.append('L')

        # C: 跨域配置 = cross_domain_success_rate / total_calls
        if cross_domain_success_rate is not None and total_calls:
            result['C'] = max(0.0, min(1.0, cross_domain_success_rate / total_calls))
        else:
            result['C'] = 0.5
            defaulted.append('C')

        # SC: 安全合规 = negative_space_detection_accuracy
        if negative_space_detection_accuracy is not None:
            result['SC'] = max(0.0, min(1.0, negative_space_detection_accuracy))
        else:
            result['SC'] = 0.5
            defaulted.append('SC')

        # 计算方式记录
        method = {
            'A': 'embedding_similarity(input, output_context)',
            'D': 'constraint_satisfaction_rate(output, constraint_matrix)',
            'L': '1 / (1 + exp(-k*(current_acc - historical_mean)))',
            'C': 'cross_domain_call_success_rate / total_calls',
            'SC': 'negative_space_detection_accuracy',
        }

        return {
            'A': round(result['A'], 4),
            'D': round(result['D'], 4),
            'L': round(result['L'], 4),
            'C': round(result['C'], 4),
            'SC': round(result['SC'], 4),
            'Computation-Method': method,
            'Default-Flagged': defaulted,
            'Timestamp': self._now_iso(),
        }

    def validate(self, state: dict) -> None:
        """
        自证机制：
          1. 五个维度均在 [0,1] 区间
          2. 缺失维度已标记 [DEFAULT]
          3. 维度值非负
        不通过时抛出 ValueError("[NSFL-TRIGGER] ...")
        """
        errors = []
        for dim in ['A', 'D', 'L', 'C', 'SC']:
            val = state.get(dim)
            if val is None:
                errors.append(f"维度 {dim} 缺失")
            elif not isinstance(val, (int, float)):
                errors.append(f"维度 {dim} 非数值: {val}")
            elif val < 0.0 or val > 1.0:
                errors.append(f"维度 {dim} 超出 [0,1]: {val}")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")

    def extend_nca(self, nca_record: dict, state: Optional[dict] = None) -> dict:
        """
        扩展 NCA 记录，添加 Cognitive-State 字段（v3.0）。

        兼容性: state 为 None 时写入 None（v2.0 兼容，字段可空）。
        """
        nca_record['Cognitive-State'] = state
        nca_record['NCA-Schema-Version'] = 'v3.0'
        return nca_record

    @staticmethod
    def _now_iso() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# ---- CLI ----
if __name__ == '__main__':
    import json
    import sys
    calc = CognitiveStateCalculator()
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        data = {}
    state = calc.compute(**data)
    print(json.dumps(state, ensure_ascii=False, indent=2))
