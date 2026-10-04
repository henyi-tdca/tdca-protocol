"""GIM-OnCycle 增量环检测 + 环销（R-CLS-3 FROZEN 算法）

规格要点（M3 红队修订后）:
- DFS 强制简单路径（visited 集合禁止重复节点）→ 无重复边
- 环销 δ = min 边权；每轮至少删一边（离散权）→ 终止性
- 环销不改变净头寸（G-1: T_net 不变量）
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class CycleResult:
    """一次环销结果"""
    cycle_edges: List[Tuple[str, str]]       # 环边（有序）
    delta: float                             # 环销额（min 边权）
    nominal_net: float                       # 名义环销 = delta × len(cycle)


class GIMOnCycle:
    """GIM 增量环检测引擎（R-CLS-3）"""

    def __init__(self):
        self.debt: Dict[Tuple[str, str], float] = {}
        self.cycles: List[CycleResult] = []

    def add_edge(self, u: str, v: str, w: float) -> List[CycleResult]:
        """新债务边到达 → 增量环检测 + 环销（发现闭环即清算）"""
        assert w > 0
        self.debt[(u, v)] = self.debt.get((u, v), 0.0) + w
        new_cycles = []
        while (u, v) in self.debt and self.debt[(u, v)] > 1e-9:
            path = self._dfs_simple(v, u)     # 简单路径（visited 强制）
            if path is None:
                break
            # 环 = (u→v) ∪ path(v→...→u)
            cycle_edges = [(u, v)]
            for k in range(len(path) - 1):
                a, b = path[k], path[k + 1]
                if (a, b) not in self.debt:
                    return new_cycles
                cycle_edges.append((a, b))
            delta = min(self.debt[e] for e in cycle_edges)
            res = CycleResult(cycle_edges=cycle_edges, delta=delta, nominal_net=delta * len(cycle_edges))
            self.cycles.append(res)
            new_cycles.append(res)
            # 环销（每边扣 δ；min 边归零删除）
            for (a, b) in cycle_edges:
                self.debt[(a, b)] -= delta
                if abs(self.debt[(a, b)]) < 1e-9:
                    del self.debt[(a, b)]
        return new_cycles

    def _dfs_simple(self, start: str, target: str) -> List[str] | None:
        """反向 DFS：从 start 沿债务方向找 target，强制简单路径（visited）"""
        stack = [(start, [start])]
        visited = {start}
        while stack:
            node, path = stack.pop()
            if node == target:
                return path
            for (a, b) in self.debt.keys():
                if a == node and b not in visited:
                    visited.add(b)
                    stack.append((b, path + [b]))
        return None

    def residual_debt(self) -> Dict[Tuple[str, str], float]:
        return dict(self.debt)

    def residual_nominal(self) -> float:
        """环销后残余名义债务总额（G-4: ≥ T_net）"""
        return sum(self.debt.values())
