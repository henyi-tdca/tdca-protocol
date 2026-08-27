# -*- coding: utf-8 -*-
"""夏普利值公平分成
=========================================================
- 小规模联盟 (<= mc_threshold): 精确枚举所有子集 (2^n) -> 数学公平解
- 海量候选经剪枝/比配后最终联盟仍可能偏大 -> 用蒙特卡洛近似,
  以 O(samples * n) 替代 O(2^n), 让算力层在海量规模可控。

效率公理: 精确版 Shapley 值之和 = V(联盟); 蒙特卡洛版近似满足。
"""
import random
from itertools import combinations
from math import comb
from .coalition import coalition_value, overlap_ratio


def exact_shapley(coal, need, dims, value_base, strength=False):
    """精确夏普利值。
    按子集在随机排列中的出现频数加权: 权重 = 1 / (n · C(n-1, |S|)),
    保证效率公理 sum(phi_i) = V(联盟) - V(∅) = V(联盟)。
    (初版曾对所有子集等权平均 1/2^(n-1), 导致 sum(phi)≠V, 已修正)
    strength: 透传强度覆盖开关, 子集估值与最终 V 同语义。
    """
    ids = [c.id for c in coal]
    cmap = {c.id: c for c in coal}
    n = len(ids)
    phi = {i: 0.0 for i in ids}
    for i in ids:
        others = [x for x in ids if x != i]
        for r in range(len(others) + 1):
            w = 1.0 / (n * comb(len(others), r))     # 正确组合权重
            for S in combinations(others, r):
                Sset = [cmap[x] for x in S]
                before = coalition_value(Sset, need, dims, value_base, strength=strength)
                after = coalition_value(Sset + [cmap[i]], need, dims, value_base, strength=strength)
                phi[i] += w * (after - before)
        phi[i] = round(phi[i], 1)
    return phi


def montecarlo_shapley(coal, need, dims, value_base, samples=2000, seed=42, strength=False):
    rnd = random.Random(seed)
    ids = [c.id for c in coal]
    cmap = {c.id: c for c in coal}
    phi = {i: 0.0 for i in ids}
    cnt = {i: 0 for i in ids}
    for _ in range(samples):
        order = rnd.sample(ids, len(ids))
        prev = []
        for i in order:
            before = coalition_value(prev, need, dims, value_base, strength=strength)
            after = coalition_value(prev + [cmap[i]], need, dims, value_base, strength=strength)
            phi[i] += (after - before)
            cnt[i] += 1
            prev = prev + [cmap[i]]
    return {i: round(phi[i] / cnt[i], 1) for i in ids}


def shapley(coal, need, dims, value_base, mc_threshold=12, mc_samples=2000, strength=False):
    """自适应选择精确/蒙特卡洛: 最终联盟规模小走精确, 大走近似。"""
    if len(coal) <= mc_threshold:
        return exact_shapley(coal, need, dims, value_base, strength=strength), "exact"
    return montecarlo_shapley(coal, need, dims, value_base, samples=mc_samples,
                              strength=strength), "montecarlo"
