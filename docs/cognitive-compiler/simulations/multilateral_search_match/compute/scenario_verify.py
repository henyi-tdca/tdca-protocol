# -*- coding: utf-8 -*-
"""场景并行验证 (智能体根据用户约束展开场景, 并行压力测试 Plan A/B/C)
=================================================================================
输入: 三套候选联盟 (Plan A/B/C) + 用户约束档案展开的验证场景。
并行: 用 ProcessPoolExecutor 把 (计划 × 场景) 全组合分发到多进程并行跑存活率。
输出: 验证矩阵 + 跨场景通过计数 + 按用户目标权重排序的推荐。

判据 (复用红队): 失效维 d 在联盟内存活 <=> 除最强供给方外仍有 >=1 家备援 (供给方数>=2)。
"""
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List

from .coalition import coalition_value
from .planner import _providers_for, _best, red_team


def _survive(coal, need, failed_dims):
    n = len(need)
    retained = 0
    for d in need:
        if d in failed_dims:
            surv = len(_providers_for(coal, d)) >= 2
        else:
            surv = _best(coal, d) >= 0.5
        retained += 1 if surv else 0
    return round(retained / n, 3)


def _verify_task(task):
    """进程池工作单元 (模块级, 可 pickle)。task=(plan_key, coal, scen, failed, need)"""
    plan_key, coal, scen, failed, need = task
    return (plan_key, scen, _survive(coal, need, failed))


def parallel_verify(plans: Dict[str, list], need: List[str],
                    scenarios: Dict[str, List[str]], profile,
                    strength: bool = False, value_base: float = 200.0,
                    max_workers: int = None) -> Dict:
    """基于用户约束档案的验证场景, 并行跑 Plan A/B/C 存活矩阵。

    返回 {
      matrix:     {plan_key: {scenario: survival}},
      pass_count: {plan_key: 达标的场景数 (survival>=profile.min_survival_rate)},
      threshold:  profile.min_survival_rate,
      avg:        {plan_key: 平均存活率},
    }
    """
    tasks = []
    for key, coal in plans.items():
        for sname, failed in scenarios.items():
            tasks.append((key, coal, sname, failed, need))

    matrix = {k: {} for k in plans}
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            for key, sname, s in ex.map(_verify_task, tasks):
                matrix[key][sname] = s
    except Exception:
        # 环境不支持多进程时优雅回退顺序执行 (结果一致)
        for (key, coal, sname, failed, _) in tasks:
            matrix[key][sname] = _survive(coal, need, failed)

    thr = profile.min_survival_rate
    pass_count = {k: sum(1 for s in matrix[k].values() if s >= thr) for k in plans}
    avg = {k: round(sum(matrix[k].values()) / len(matrix[k]), 3) for k in plans}
    return {"matrix": matrix, "pass_count": pass_count, "threshold": thr, "avg": avg}


def recommend_by_profile(plans: Dict[str, list], need, dims, profile,
                         verify: Dict, strength: bool = False,
                         value_base: float = 200.0):
    """按用户目标权重 + 存活门槛推荐计划 (偏好来自 profile, 非硬编码)。

    优先: 平均存活率 >= 门槛 的计划中, 目标加权得分最高者。
    兜底: 若皆不达标, 取 V 最高者并标注警告 (仍由用户条件判定, 不静默替用户决策)。
    """
    rows = {}
    for key, coal in plans.items():
        V = coalition_value(coal, need, dims, value_base, strength=strength)
        batna_sum = sum(c.batna for c in coal)
        rows[key] = {
            "coal": coal, "V": V, "batna_sum": batna_sum,
            "avg_survival": verify["avg"][key],
            "pass": verify["avg"][key] >= verify["threshold"],
        }
    vmax = max((r["V"] for r in rows.values()), default=1) or 1
    costmax = max((r["batna_sum"] for r in rows.values()), default=1) or 1
    w = profile.objective_weights

    def _score(r):
        vn = r["V"] / vmax
        rn = r["avg_survival"]
        cn = 1 - r["batna_sum"] / costmax
        return w["v"] * vn + w["robustness"] * rn + w["cost"] * cn

    for r in rows.values():
        r["score"] = round(_score(r), 4)
    passing = [k for k in rows if rows[k]["pass"]]
    if passing:
        best = max(passing, key=lambda k: rows[k]["score"])
        note = f"达标计划中加权得分最高 (按用户条件 {profile.name})"
    else:
        best = max(rows, key=lambda k: rows[k]["V"])
        note = f"警告: 无计划达存活门槛 {verify['threshold']}, 取 V 最高 (仍由用户条件判定)"
    return {"key": best, "rows": rows, "note": note}
