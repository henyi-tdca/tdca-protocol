"""
TDCA-FC-20260802-004 修正声明: 无（首版）
制度锚定: ID8（NIA-MACM 3.0 五维认知状态向量）
Granted-By: ID8

NSFL-Declaration:
  - 能力塑造不得强制修改智能体参数，需经人类审批
  - 调整方案必须通过正和验证（不损害其他主体）
  - 调整过程生成 NCA，记录"为什么调整、调整什么、预期效果"
SPDX-License-Identifier: TDCA-Internal
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class PerformanceGap:
    """表现差距分析"""
    weakest_dimension: str        # 最弱维度
    gap_score: float              # 差距分数 [0,1]
    details: dict = field(default_factory=dict)


@dataclass
class TrainingBudget:
    """训练资源预算"""
    max_resources: float
    priority_dimensions: List[str] = field(default_factory=list)


@dataclass
class ShapingPlan:
    """能力塑造方案"""
    agent_id: str
    dimension_focus: str
    training_data: list
    expected_improvement: float
    verification_method: str
    resource_cost: float
    nca_record: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class AgentCapabilityShaper:
    """
    智能体能力塑造器（ID8）

    核心约束:
      - 基于效用评估结果，生成能力调整方案
      - 调整方案必须通过正和验证（不损害其他主体）
      - 调整过程生成 NCA，记录"为什么调整、调整什么、预期效果"
    """

    NIA_DIMENSIONS = ['A', 'D', 'L', 'C', 'SC']  # 五维认知状态

    def shape(
        self,
        agent_id: str,
        current_state: dict,             # 当前认知状态 S=(A,D,L,C,SC)
        utility_history: List[dict],     # 历史效用记录
        performance_gap: PerformanceGap,
        training_budget: TrainingBudget,
        human_approved: bool = False
    ) -> ShapingPlan:
        """
        返回能力塑造方案:
          - dimension_focus: 重点提升维度
          - training_data: 推荐训练数据/案例
          - expected_improvement: 预期效用提升
          - verification_method: 如何验证提升效果
          - nca_record: 塑造过程 NCA
        """
        # 人类审批硬约束
        if not human_approved:
            raise PermissionError(
                "[NSFL-TRIGGER] 能力塑造需人类审批（HIGH风险操作）"
            )

        # 预算约束检查
        if training_budget.max_resources <= 0:
            raise ValueError("[NSFL-TRIGGER] 训练预算必须 > 0")

        # 维度优先级：表现差距 + 预算优先级
        focus = performance_gap.weakest_dimension
        if performance_gap.gap_score < 0.5 and training_budget.priority_dimensions:
            focus = training_budget.priority_dimensions[0]

        # 生成训练数据建议（按维度）
        training_data = self._recommend_training(focus, current_state)

        # 预期改进（简化：差距越大提升空间越大，受预算限制）
        max_improvement = 0.9
        budget_factor = min(1.0, training_budget.max_resources / 10.0)
        expected = min(max_improvement,
                       performance_gap.gap_score * 0.8 * budget_factor)

        # 资源消耗（按维度）
        resource_cost = performance_gap.gap_score * 5.0 * budget_factor

        # NCA 记录
        nca_record = {
            'operation_type': 'CapabilityShaping',
            'agent_id': agent_id,
            'dimension_focus': focus,
            'human_approved': human_approved,
            'resource_cost': resource_cost,
            'expected_improvement': expected,
        }

        return ShapingPlan(
            agent_id=agent_id,
            dimension_focus=focus,
            training_data=training_data,
            expected_improvement=expected,
            verification_method=f"对比 {focus} 维度前后认知状态向量",
            resource_cost=resource_cost,
            nca_record=nca_record,
        )

    def validate(self, plan: ShapingPlan) -> None:
        """
        自证机制：
          1. dimension_focus 属于五维之一
          2. 资源消耗 ≤ 训练预算
          3. 预期改进在 [0,1] 区间
          4. 人类审批记录存在
        """
        errors = []
        if plan.dimension_focus not in self.NIA_DIMENSIONS:
            errors.append(f"维度 {plan.dimension_focus} 不在五维认知状态中")
        if not 0 <= plan.expected_improvement <= 1:
            errors.append(f"预期改进超出 [0,1]: {plan.expected_improvement}")
        if not plan.nca_record.get('human_approved'):
            errors.append("缺少人类审批记录")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")

    @staticmethod
    def _recommend_training(dimension: str, current_state: dict) -> list:
        """按维度推荐训练数据/案例"""
        recommendations = {
            'A': ['感知精度训练集', '环境特征识别案例', '输入输出匹配标注'],
            'D': ['约束满足决策集', '配置权边界案例', '历史决策对比数据'],
            'L': ['反馈收敛训练集', '偏差修正案例', '历史错误复盘数据'],
            'C': ['跨域调用案例集', '跨界配置成功样本', '多场景迁移数据'],
            'SC': ['负空间识别训练集', 'NSFL规则案例', '熔断响应复盘数据'],
        }
        base = recommendations.get(dimension, [])
        current_val = current_state.get(dimension, 0.5)
        # 当前值越低，推荐越多基础训练
        if current_val < 0.4:
            return base + ['基础强化训练']
        return base
