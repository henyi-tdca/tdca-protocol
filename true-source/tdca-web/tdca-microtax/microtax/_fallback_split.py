# -*- coding: utf-8 -*-
"""Shapley 分割兜底实现（仅无基座环境用；常规路径复用 translator_market.mou_split）。

精确 Shapley（n ≤ 6 全枚举，> 6 蒙特卡洛近似），接口与 translator_market.mou_split 同构。
"""
from __future__ import annotations

import itertools
import random
from typing import Callable, Dict, List


def _factorial(n: int) -> int:
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def default_mou_value_fn(contrib: Dict[str, float], synergy: float = 1.2) -> Callable:
    """协同正和价值函数：V(S) = Σ贡献 × synergy（|S|>1 时），单元素 = 贡献。"""
    def _v(S: frozenset) -> float:
        total = sum(contrib[a] for a in S)
        if len(S) > 1:
            total *= synergy
        return total
    return _v


class MOUSplitContract:
    """Shapley 分割（精确 n≤6 / 蒙特卡洛近似）。"""

    def __init__(self, random_seed: int = 20260811):
        self._random = random.Random(random_seed)

    def split(self, scene_ids: List[str], value_fn: Callable,
              exact_limit: int = 6, samples: int = 2000) -> Dict[str, float]:
        if len(scene_ids) <= exact_limit:
            return self._exact(scene_ids, value_fn)
        return self._monte_carlo(scene_ids, value_fn, samples)

    def _exact(self, scene_ids: List[str], value_fn: Callable) -> Dict[str, float]:
        n = len(scene_ids)
        n_fact = _factorial(n)
        shapley = {a: 0.0 for a in scene_ids}
        for perm in itertools.permutations(scene_ids):
            S = frozenset()
            for player in perm:
                shapley[player] += (value_fn(S | {player}) - value_fn(S)) / n_fact
                S = S | {player}
        return {a: round(v, 6) for a, v in shapley.items()}

    def _monte_carlo(self, scene_ids: List[str], value_fn: Callable,
                     samples: int) -> Dict[str, float]:
        n = len(scene_ids)
        shapley = {a: 0.0 for a in scene_ids}
        for _ in range(samples):
            perm = scene_ids[:]
            self._random.shuffle(perm)
            S = frozenset()
            for player in perm:
                shapley[player] += value_fn(S | {player}) - value_fn(S)
                S = S | {player}
        return {a: round(v / samples, 6) for a, v in shapley.items()}
