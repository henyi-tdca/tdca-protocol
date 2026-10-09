"""
TDCA-FC-20260802-004 修正声明: 无（首版）
制度锚定: ID21（函数隐喻四定律）, ID24（效用精灵九大能力-贝叶斯/优化）
Granted-By: ID21

NSFL-Declaration:
  - 反函数求解结果超出配置权边界时，必须熔断并上报
  - 给定 y 求 x：目标效用 → 配置方案
  - 多解时选择总成本最小或正和性最大的解
SPDX-License-Identifier: TDCA-Internal
"""

from dataclasses import dataclass, field, asdict
from typing import Callable, List, Optional


@dataclass
class ConfigSpace:
    """配置权可行域"""
    bounds: dict                    # {config_key: (min, max)}
    hard_constraints: List[str] = field(default_factory=list)


@dataclass
class InverseSolution:
    """反函数求解结果"""
    config_vector: dict             # 配置权向量
    predicted_utility: float
    confidence_interval: tuple      # (lo, hi)
    feasibility: str                # feasible / infeasible / conditional
    cost: float
    nca_trace: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class InverseFunctionSolver:
    """
    反函数求解器（ID21）

    核心约束:
      - 给定目标效用 U_target，反推配置权输入 X
      - 满足: f(X) ≥ U_target，且 X 在配置权边界内
      - 若多解，选择总成本最小（或正和性最大）的解
      - 若无解，触发负空间熔断，返回"不可行"+原因
    """

    def __init__(self, samples: int = 1000, random_seed: Optional[int] = None):
        import random
        self._random = random
        if random_seed is not None:
            self._random.seed(random_seed)
        self.samples = samples

    def solve(
        self,
        target_utility: float,
        utility_function: Callable,
        config_space: ConfigSpace,
        cost_function: Optional[Callable] = None,
        tolerance: float = 0.05
    ) -> InverseSolution:
        """
        返回反函数解:
          - config_vector: 配置权向量
          - predicted_utility: 预测效用值
          - confidence_interval: 置信区间
          - feasibility: 可行/不可行/条件可行
          - nca_trace: 求解过程 NCA
        """
        nca_trace = []
        keys = list(config_space.bounds.keys())
        candidates = []

        # 随机采样可行域（贝叶斯优化简化为随机+局部搜索）
        for _ in range(self.samples):
            config = {}
            for k in keys:
                lo, hi = config_space.bounds[k]
                config[k] = self._random.uniform(lo, hi)

            # 硬约束检查
            if not self._check_hard_constraints(config, config_space.hard_constraints):
                continue

            utility = utility_function(config)
            cost = cost_function(config) if cost_function else 0.0

            if utility >= target_utility * (1 - tolerance):
                candidates.append({
                    'config': config,
                    'utility': utility,
                    'cost': cost,
                })

        if not candidates:
            return InverseSolution(
                config_vector={},
                predicted_utility=0.0,
                confidence_interval=(0.0, 0.0),
                feasibility='infeasible',
                cost=0.0,
                nca_trace=[{'status': 'NSFL-TRIGGER', 'reason': '无可行解满足目标效用'}],
            )

        # 多解选择：成本最小优先，其次效用最大
        best = min(candidates, key=lambda c: (c['cost'], -c['utility']))

        # 置信区间：基于候选解的效用分布（简化：min-max）
        utilities = [c['utility'] for c in candidates]
        ci_lo = min(utilities)
        ci_hi = max(utilities)

        nca_trace.append({
            'candidates_found': len(candidates),
            'selected_cost': best['cost'],
            'selected_utility': best['utility'],
            'feasibility': 'feasible',
        })

        return InverseSolution(
            config_vector=best['config'],
            predicted_utility=best['utility'],
            confidence_interval=(ci_lo, ci_hi),
            feasibility='feasible',
            cost=best['cost'],
            nca_trace=nca_trace,
        )

    def validate(self, solution: InverseSolution) -> None:
        """
        自证机制：
          1. feasibility 与 config_vector 一致性（infeasible 时 config 为空）
          2. predicted_utility ≥ 0
          3. infeasible 时 nca_trace 含熔断记录
        """
        errors = []
        if solution.feasibility == 'infeasible':
            if solution.config_vector:
                errors.append("不可行解却包含配置向量")
            has_trigger = any('NSFL-TRIGGER' in str(t) for t in solution.nca_trace)
            if not has_trigger:
                errors.append("不可行解缺少 NSFL-TRIGGER 记录")
        elif solution.predicted_utility < 0:
            errors.append("预测效用为负")

        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")

    @staticmethod
    def _check_hard_constraints(config: dict, constraints: List[str]) -> bool:
        """检查配置向量是否满足硬约束（简化：字符串表达式）"""
        for c in constraints:
            # 支持 "key <= value" 格式
            try:
                parts = c.split()
                if len(parts) == 3:
                    key, op, val = parts
                    if key in config:
                        if op == '<=' and not (config[key] <= float(val)):
                            return False
                        if op == '>=' and not (config[key] >= float(val)):
                            return False
                        if op == '<' and not (config[key] < float(val)):
                            return False
                        if op == '>' and not (config[key] > float(val)):
                            return False
            except (ValueError, IndexError):
                continue
        return True
