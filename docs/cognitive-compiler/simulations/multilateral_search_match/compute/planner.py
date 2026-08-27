# -*- coding: utf-8 -*-
"""多联盟备选 + 红队对抗 (搜索比配引擎 v2 升级)
=========================================================
战术 1: 不再只输出"单一联盟", 而在 match 阶段生成 3 个候选联盟组合:
  - Plan A: 最强互补 / 最大联合效用 V  (原贪心最优)
  - Plan B: 抗风险 / 冗余化  (每关键维 >=2 家供给, 单点失效可兜底)
  - Plan C: 低成本 / 最小 BATNA 和  (覆盖全维前提下总成本最低)
然后启动"红队测试 COP": 主动注入维度失效场景 (渠道断裂/算力故障/数据泄露/各单维失效),
计算各联盟存活率, 回答"哪个联盟在最坏压力下仍存活"。

红队核心判据: 某维在联盟内供给方数 >=2 即视为有备援 -> 该维在单点失效下存活;
仅 1 家供给 -> 单点失效即丢失该维。冗余度决定存活率。
"""
from typing import List, Dict
from .coalition import form_coalition, fragile_dims


def _best(candidates, d):
    return max((c.res.get(d, 0.0) for c in candidates), default=0.0)


def _providers_for(coalition, d):
    return [c for c in coalition if c.res.get(d, 0.0) >= 0.5]


# ---------- Plan A: 最强互补 (复用原贪心, 强度加权) ----------
def plan_A(candidates, need, dims, value_base, strength=False):
    sw = 8.0 if strength else 0.0
    return form_coalition(candidates, need, dims, value_base, strength_weight=sw)


# ---------- Plan B: 抗风险 / 冗余化 (每维 >=2 家供给) ----------
def plan_B(candidates, need, dims, value_base=200, strength=False):
    base = form_coalition(candidates, need, dims, value_base, strength_weight=0.0)
    coalition = list(base)
    pool = [c for c in candidates if c not in coalition]
    improved = True
    while improved:
        improved = False
        for d in need:
            if len(_providers_for(coalition, d)) < 2:
                # 找联盟外最强备选供给方补位
                alt = max((c for c in pool if c.res.get(d, 0.0) >= 0.5),
                          key=lambda c: c.res.get(d, 0.0), default=None)
                if alt is not None:
                    coalition.append(alt)
                    pool.remove(alt)
                    improved = True
    return coalition


# ---------- Plan C: 低成本 / 最小 BATNA 和 ----------
def plan_C(candidates, need, dims, value_base=200, strength=False):
    coalition: List = []
    pool = list(candidates)
    while True:
        uncovered = [d for d in need if _best(coalition, d) < 0.5]
        if not uncovered:
            break
        # 选 cheapest (BATNA 最小) 且能补至少 1 个未覆盖维的主体
        best = None
        best_batna = float("inf")
        for c in pool:
            if not any(c.res.get(d, 0.0) >= 0.5 for d in uncovered):
                continue
            if c.batna < best_batna:
                best_batna = c.batna
                best = c
        if best is None:
            break
        coalition.append(best)
        pool.remove(best)
    return coalition


def generate_plans(candidates, need, dims, value_base, strength=False):
    """返回 {'A': [...], 'B': [...], 'C': [...]} 三个候选联盟 (Candidate 列表)"""
    return {
        "A": plan_A(candidates, need, dims, value_base, strength=strength),
        "B": plan_B(candidates, need, dims, value_base, strength=strength),
        "C": plan_C(candidates, need, dims, value_base, strength=strength),
    }


# ---------- 红队测试 COP: 维度失效压力测试 ----------
def red_team(coalition, need, dims=None, scenarios=None):
    """对联盟注入维度失效场景, 返回各场景存活率与平均/最差。

    判据: 失效维 d 在联盟内存活 <=> 除最强供给方外仍有 >=1 家备援 (供给方数>=2)。
    非失效维: 只要联盟最佳强度>=0.5 即存活。
    """
    if scenarios is None:
        scenarios = {
            "渠道断裂": ["渠道"],
            "算力故障": ["算力"],
            "数据泄露": ["数据"],
        }
        for d in need:
            scenarios[f"单维失效:{d}"] = [d]
    out: Dict[str, float] = {}
    n = len(need)
    for name, failed in scenarios.items():
        retained = 0
        for d in need:
            if d in failed:
                # 该维供给方若仅 1 家 -> 单点失效即丢失; >=2 家 -> 有备援, 存活
                surv = len(_providers_for(coalition, d)) >= 2
            else:
                surv = _best(coalition, d) >= 0.5
            retained += 1 if surv else 0
        out[name] = round(retained / n, 3)
    avg = round(sum(out.values()) / len(out), 3)
    worst = min(out, key=out.get)
    return {
        "scenarios": out,
        "avg_survival": avg,
        "worst_scenario": worst,
        "worst_survival": out[worst],
        "redundancy": {d: len(_providers_for(coalition, d)) for d in need},
    }
