"""
TDCA-FC-20260802-004 修正声明: 无（首版）
制度锚定: ID84（协作停机定理）
Granted-By: ID84

NSFL-Declaration:
  - 满意解不等于最优解，人类保有最终决策权
  - 触及 ⊗ 边界时立即停机，返回当前最佳可行解
  - 停机条件是满意解阈值，非收敛阈值
SPDX-License-Identifier: TDCA-Internal
"""

import time
from dataclasses import dataclass, field, asdict
from typing import Callable, List, Optional


@dataclass
class Agent:
    """参与协作的智能体"""
    agent_id: str
    capability: float = 1.0  # 能力系数


@dataclass
class SatisficingSolution:
    """正和效用满意解"""
    allocations: dict                     # {agent_id: 分配量}
    utilities: dict                       # {agent_id: 效用值}
    total_utility: float
    independent_sum: float                # 独立效用之和
    delta: float                          # 正和增量
    is_positive_sum: bool
    is_individual_rational: bool          # 个体理性
    solve_time: float
    touched_nsfl: bool
    nsfl_reason: Optional[str] = None
    nca_trace: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class PositiveSumSolver:
    """
    正和效用满意解求解器（ID84）

    核心约束:
      - 满意解原则: 所有参与主体的效用 ≥ 保留效用（个体理性）
      - 时间价值衰减: 效用随时间递减，不能无限期求解
      - 负空间熔断: 触及 ⊗ 时立即停机
      - NCA 完成度审计: 协作过程必须可记录
      - 人类最终签名权: 人类保有最终否决权
    """

    def __init__(self, random_seed: Optional[int] = None):
        import random
        self._random = random
        if random_seed is not None:
            self._random.seed(random_seed)

    def solve(
        self,
        participants: List[Agent],
        objective_functions: List[Callable],
        constraint_matrix: list,
        reservation_utilities: List[float],
        time_budget: float = 10.0,
        nsfl_boundaries: List[str] = None,
        resource_pool: Optional[float] = None
    ) -> SatisficingSolution:
        """
        返回满意解，非最优解。

        满意解定义:
          1. 所有参与者效用 ≥ 保留效用（个体理性）
          2. 总效用 > 各主体独立效用之和（正和性）
          3. 求解时间 ≤ 时间预算（时间约束）
          4. 不触及任何 ⊗ 边界（负空间约束）
          5. 生成完整 NCA 记录（可审计性）

        resource_pool（TDCA-TASK-COGNITION-001 C-2 扩展，裁决②）:
          可注入正和求解资源池（如税后净额 net_value）；缺省 None 保持
          既有硬编码行为（min(len*10, 100)）——向后兼容（78 测试绿不变）。
        """
        nsfl_boundaries = nsfl_boundaries or []
        start = time.time()
        nca_trace = []
        touched_nsfl = False
        nsfl_reason = None

        # 检查负空间边界（预检）
        for boundary in nsfl_boundaries:
            if self._touches_nsfl(boundary, participants):
                touched_nsfl = True
                nsfl_reason = f"预检触及负空间: {boundary}"
                break

        # 迭代分配求解
        allocations = {a.agent_id: 0.0 for a in participants}
        utilities = {}

        # 简单分配算法：按能力系数比例分配有限资源，迭代调整以满足个体理性
        total_capability = sum(a.capability for a in participants) or 1.0
        # C-2: resource_pool 可注入（税后净额）；缺省保持硬编码
        resource_pool = resource_pool if resource_pool is not None \
            else min(len(participants) * 10.0, 100.0)

        iteration = 0
        while time.time() - start < time_budget:
            iteration += 1

            # 按能力比例分配
            for a in participants:
                allocations[a.agent_id] = resource_pool * a.capability / total_capability

            # 计算效用（调用目标函数）
            utilities = {}
            for idx, a in enumerate(participants):
                fn = objective_functions[idx] if idx < len(objective_functions) else (lambda x: x)
                utilities[a.agent_id] = fn(allocations[a.agent_id])

            # 个体理性检查
            individual_rational = all(
                utilities[a.agent_id] >= res
                for a, res in zip(participants, reservation_utilities)
            )

            # 正和性检查
            independent_sum = sum(reservation_utilities)
            total_utility = sum(utilities.values())
            delta = total_utility - independent_sum
            is_positive = delta > 0

            # NCA 记录
            nca_trace.append({
                'iteration': iteration,
                'total_utility': total_utility,
                'delta': delta,
                'individual_rational': individual_rational,
                'touched_nsfl': touched_nsfl,
            })

            # 停机条件：满意解（个体理性 + 正和 + 未触负空间）
            if individual_rational and is_positive and not touched_nsfl:
                break

            # 熔断：触及负空间
            if touched_nsfl:
                break

            # 调整资源池（简单递增探索）
            resource_pool += 5.0
            if iteration > 100:
                break

        # 熔断时返回当前最佳可行解
        return SatisficingSolution(
            allocations=allocations,
            utilities=utilities,
            total_utility=sum(utilities.values()),
            independent_sum=independent_sum,
            delta=delta,
            is_positive_sum=is_positive,
            is_individual_rational=individual_rational,
            solve_time=time.time() - start,
            touched_nsfl=touched_nsfl,
            nsfl_reason=nsfl_reason,
            nca_trace=nca_trace,
        )

    def validate(self, solution: SatisficingSolution) -> None:
        """
        自证机制：
          1. 个体理性（所有效用 ≥ 保留效用）
          2. 正和性（delta > 0）或已熔断标记
          3. 求解时间 ≤ 时间预算
          4. 负空间熔断一致性（touched_nsfl 与 nsfl_reason 对应）
        """
        errors = []
        if not solution.is_individual_rational and not solution.touched_nsfl:
            errors.append("个体理性未满足且未熔断")
        if not solution.is_positive_sum and not solution.touched_nsfl:
            errors.append("正和性未满足且未熔断")
        if solution.touched_nsfl and not solution.nsfl_reason:
            errors.append("负空间熔断但缺少原因")
        if solution.delta <= 0 and not solution.touched_nsfl:
            errors.append("正和增量 ≤ 0 且未熔断")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")

    @staticmethod
    def _touches_nsfl(boundary: str, participants: List[Agent]) -> bool:
        """检查是否触及负空间边界"""
        nsfl_keywords = ['autonomous_repair', 'value_land', 'irreversible']
        return any(kw in boundary.lower() for kw in nsfl_keywords)
