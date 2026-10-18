"""
TDCA-FC-20260802-004 修正声明: 无（首版）
制度锚定: ID24（效用精灵九大数学能力-优化）
Granted-By: ID24

NSFL-Declaration:
  - 优化是约束下的优化，禁止无约束最大化
  - 触及 ⊗ 边界时返回当前最佳可行解
SPDX-License-Identifier: TDCA-Internal
"""

import math
from typing import Callable, List, Optional


class OptimizationEngine:
    """
    优化引擎（九大能力-优化）

    支持:
      - 单目标约束优化（模拟退火，纯Python无scipy依赖）
      - 多目标 NSGA-II 简化版（帕累托排序）
    """

    def __init__(self, seed: Optional[int] = None):
        import random
        self._random = random
        if seed is not None:
            self._random.seed(seed)

    def simulated_annealing(
        self,
        objective: Callable[[List[float]], float],
        bounds: List[tuple],
        maximize: bool = True,
        iterations: int = 1000,
        initial_temp: float = 100.0,
        cooling_rate: float = 0.99
    ) -> dict:
        """
        模拟退火求解单目标约束优化。
        返回: {'solution': [...], 'value': float, 'feasible': bool}
        """
        dim = len(bounds)
        current = [self._random.uniform(b[0], b[1]) for b in bounds]
        current_val = objective(current)
        best = current[:]
        best_val = current_val
        temp = initial_temp

        for i in range(iterations):
            # 邻域扰动
            neighbor = []
            for j in range(dim):
                lo, hi = bounds[j]
                delta = (hi - lo) * 0.1 * (self._random.random() - 0.5) * 2
                neighbor.append(min(hi, max(lo, current[j] + delta)))
            neighbor_val = objective(neighbor)

            # 接受准则
            diff = neighbor_val - current_val
            if maximize:
                accept = diff > 0 or self._random.random() < math.exp(diff / temp)
            else:
                accept = diff < 0 or self._random.random() < math.exp(-diff / temp)

            if accept:
                current = neighbor
                current_val = neighbor_val

            if (maximize and current_val > best_val) or (not maximize and current_val < best_val):
                best = current[:]
                best_val = current_val

            temp *= cooling_rate
            if temp < 1e-8:
                break

        return {'solution': best, 'value': best_val, 'feasible': True}

    def pareto_sort(self, solutions: List[dict], objectives: List[str]) -> List[dict]:
        """
        简化 NSGA-II 帕累托排序（非支配排序）
        solutions: [{'values': {...}, 'config': ...}, ...]
        objectives: 目标键列表（默认全部最小化）
        """
        n = len(solutions)
        dominated_by = [set() for _ in range(n)]
        dominates = [set() for _ in range(n)]
        dom_count = [0] * n

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                si = solutions[i]['values']
                sj = solutions[j]['values']
                # i 支配 j 当且仅当 i 所有目标 ≤ j 且至少一个 <
                i_better = all(si[o] <= sj[o] for o in objectives)
                i_strict = any(si[o] < sj[o] for o in objectives)
                if i_better and i_strict:
                    dominates[i].add(j)
                    dominated_by[j].add(i)
                elif all(sj[o] <= si[o] for o in objectives) and any(sj[o] < si[o] for o in objectives):
                    dominates[j].add(i)
                    dominated_by[i].add(j)

        for i in range(n):
            dom_count[i] = len(dominated_by[i])

        fronts = [[]]
        for i in range(n):
            if dom_count[i] == 0:
                fronts[0].append(i)

        k = 0
        while fronts[k]:
            next_front = []
            for i in fronts[k]:
                for j in dominates[i]:
                    dom_count[j] -= 1
                    if dom_count[j] == 0:
                        next_front.append(j)
            k += 1
            fronts.append(next_front)

        fronts = [f for f in fronts if f]
        result = []
        for front in fronts:
            for idx in front:
                result.append(solutions[idx])
        return result
