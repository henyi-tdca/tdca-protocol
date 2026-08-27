# -*- coding: utf-8 -*-
"""算力层 · 候选遍历与剪枝 (并行 + 海量可扩展)
=========================================================
原 v1 引擎对候选库是串行 for 循环; 真实全网是海量主体,
必须用并行遍历 + 负空间剪枝把 2^n 爆炸压在可控范围。
"""
from concurrent.futures import ThreadPoolExecutor


def _coverage_score(cand, need):
    """主体对任务关键资源维度的平均覆盖度 (囚徒困境COP·pd_payoff_build: 先量化可标定的收益)"""
    return sum(cand.res.get(d, 0.0) for d in need) / len(need)


def traverse(candidates, need, workers=8):
    """并行遍历候选库, 计算每个主体的资源覆盖度 (思维协议驱动算力)"""
    cover = {}
    if not candidates:
        return cover
    if len(candidates) <= 1 or workers <= 1:
        for c in candidates:
            cover[c.id] = round(_coverage_score(c, need), 3)
        return cover
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for cand, sc in zip(candidates, ex.map(lambda c: _coverage_score(c, need), candidates)):
            cover[cand.id] = round(sc, 3)
    return cover


def prune(candidates, need, min_cover=0.12):
    """负空间剪枝: 丢掉对任务任何关键维度都无贡献的噪声主体,
    降低后续联盟形成的搜索空间 (防止 2^n 在海量候选下爆炸)。
    判据: 主体在所有 needed 维度强度均 < min_cover -> 不可能补缺口 -> 剪掉。"""
    kept = []
    for c in candidates:
        useful = any(c.res.get(d, 0.0) >= min_cover for d in need)
        if useful:
            kept.append(c)
    return kept


def ranked(cover):
    """按覆盖度降序的 (id, score) 列表"""
    return sorted(cover.items(), key=lambda kv: -kv[1])
