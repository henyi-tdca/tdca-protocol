# -*- coding: utf-8 -*-
"""
W4 T-P4-003 · MOUSplitContract（MOU 分割：Shapley 预计算，CCP T3 shapleyAllocate 对齐）
锚定: TDCA-CCP-CONTRACTS-V0.1-REV2 T3 shapleyAllocate（:120，近似误差 <1%）+ T5 MOU 复合锚定
     + W4 翻译器市场（MOUSplitContract 从模拟态升级为生产模板，TDCA-PLAN-5CC-PHASE-C §六）
方法: n≤6 精确枚举 Shapley；n>6 蒙特卡洛近似（偏差 <1% 验收）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import itertools
import random
from typing import Dict, List


class MOUSplitContract:
    """MOU 分割（Shapley 值）: 各场景边际贡献公平分配。"""

    def __init__(self, random_seed: int = 20260811):
        self._rng = random.Random(random_seed)

    def split(self, scene_ids: List[str], value_fn, exact_limit: int = 6,
              samples: int = 40000) -> Dict[str, float]:
        """Shapley 值。value_fn(S: set) -> float 为子集联合价值。

        :param exact_limit: n ≤ 该值走精确枚举（Shapley 精确）
        :param samples: n > 上限时蒙特卡洛采样次数（偏差 <1%）
        """
        n = len(scene_ids)
        if n <= exact_limit:
            return self._exact(scene_ids, value_fn)
        return self._monte_carlo(scene_ids, value_fn, samples)

    def _exact(self, scene_ids: List[str], value_fn) -> Dict[str, float]:
        n = len(scene_ids)
        shapley = {s: 0.0 for s in scene_ids}
        for perm in itertools.permutations(scene_ids):
            coalition: set = set()
            for player in perm:
                prev = value_fn(frozenset(coalition))
                coalition.add(player)
                next_ = value_fn(frozenset(coalition))
                shapley[player] += next_ - prev
        n_fact = _factorial(n)
        return {s: round(v / n_fact, 4) for s, v in shapley.items()}

    def _monte_carlo(self, scene_ids: List[str], value_fn, samples: int) -> Dict[str, float]:
        n = len(scene_ids)
        shapley = {s: 0.0 for s in scene_ids}
        for _ in range(samples):
            perm = self._rng.sample(scene_ids, n)
            coalition: set = set()
            for player in perm:
                prev = value_fn(frozenset(coalition))
                coalition.add(player)
                next_ = value_fn(frozenset(coalition))
                shapley[player] += next_ - prev
        return {s: round(v / samples, 4) for s, v in shapley.items()}


def _factorial(n: int) -> int:
    out = 1
    for i in range(2, n + 1):
        out *= i
    return out


def default_mou_value_fn(contrib: Dict[str, float], synergy: float = 1.2) -> callable:
    """默认联合价值：Σ贡献 + 协同溢价（正和面）。"""

    def _v(S: frozenset) -> float:
        if not S:
            return 0.0
        base = sum(contrib[s] for s in S)
        # 协同: 规模效应（|S| 越大，协同加成越显著）
        k = len(S)
        return base * (1.0 + synergy * (k - 1) * 0.05)

    return _v
