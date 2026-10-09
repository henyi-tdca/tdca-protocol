"""
TDCA-FC-20260802-004 修正声明: 无（首版）
制度锚定: ID24（效用精灵九大数学能力-博弈论）, ID84（协作停机定理）
Granted-By: ID24

NSFL-Declaration:
  - 博弈求解须保证正和性（总效用 > 独立效用之和）
  - 满意解非最优解，人类保有最终决策权
SPDX-License-Identifier: TDCA-Internal
"""

from typing import List, Optional, Callable


class GameTheoryEngine:
    """
    博弈论引擎（九大能力-博弈论）

    支持:
      - Shapley 值计算（贡献分配）
      - 纳什均衡（简化：收益矩阵求解）
      - 帕累托改进检测
    """

    def __init__(self):
        pass

    def shapley_value(
        self,
        participants: List[str],
        coalition_value: Callable[[set], float]
    ) -> dict:
        """
        Shapley 值计算。

        participants: 参与方ID列表
        coalition_value: 联盟价值函数 v(S) -> float

        返回: {'values': {pid: shapley_value}, 'efficiency': float}
        """
        n = len(participants)
        import math
        import itertools
        values = {p: 0.0 for p in participants}

        for p in participants:
            others = [q for q in participants if q != p]
            for r in range(n):
                # 所有含 p 且 |S| = r+1 的联盟
                for subset in itertools.combinations(others, r):
                    coalition = set(subset)
                    with_p = coalition | {p}
                    v_with = coalition_value(with_p)
                    v_without = coalition_value(coalition)
                    weight = math.factorial(r) * math.factorial(n - r - 1) / math.factorial(n)
                    values[p] += weight * (v_with - v_without)

        total = sum(values.values())
        return {'values': values, 'efficiency': total}

    def nash_equilibrium(self, payoff_matrix: List[List[float]]) -> List[tuple]:
        """
        简化纳什均衡：纯策略均衡（2人有限博弈）。

        payoff_matrix[i][j] = (玩家A选择i, 玩家B选择j) 的A收益
        返回: [(i, j), ...] 纯策略纳什均衡列表
        """
        rows = len(payoff_matrix)
        cols = len(payoff_matrix[0])
        equilibria = []

        for i in range(rows):
            for j in range(cols):
                # 检查 i 是否是对 j 的最优回应
                best_response_a = all(payoff_matrix[i][j] >= payoff_matrix[k][j] for k in range(rows))
                # 检查 j 是否是对 i 的最优回应（需要B的收益矩阵，简化用对称）
                best_response_b = True
                for j2 in range(cols):
                    if payoff_matrix[i][j2] > payoff_matrix[i][j]:
                        best_response_b = False
                        break
                if best_response_a and best_response_b:
                    equilibria.append((i, j))

        return equilibria

    def pareto_improvement(
        self,
        current_utilities: List[float],
        candidate_utilities: List[float]
    ) -> bool:
        """
        帕累托改进检测。
        candidate 相对 current 是否帕累托改进：
          所有主体效用 ≥ 当前 且 至少一个严格大于
        """
        if len(current_utilities) != len(candidate_utilities):
            return False
        all_at_least = all(c >= d for c, d in zip(candidate_utilities, current_utilities))
        any_strict = any(c > d for c, d in zip(candidate_utilities, current_utilities))
        return all_at_least and any_strict

    def positive_sum_check(
        self,
        coalition_utility: float,
        independent_utilities: List[float]
    ) -> tuple:
        """
        正和性检查（ID84）:
          总效用 > 各主体独立效用之和 → 正和
        返回: (is_positive: bool, delta: float)
        """
        independent_sum = sum(independent_utilities)
        delta = coalition_utility - independent_sum
        return (delta > 0, delta)
