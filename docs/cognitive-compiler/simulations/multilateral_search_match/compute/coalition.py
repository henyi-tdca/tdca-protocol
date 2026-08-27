# -*- coding: utf-8 -*-
"""联盟形成与稳定校验 (思维协议驱动比配)
=========================================================
比配不是"覆盖越高越优先"的朴素排序, 而是:
  1. 优先补'关键资源缺口' (博弈论 COP·repetition_transform: 反复互动需先补齐互补维度)
  2. 其次选与已选联盟互补度高 (overlap 低) 的主体
  3. 负空间: 主体在所有 needed 维度强度<0.5 则无法补该缺口
"""
from typing import List

# ---- 强度覆盖与置信分级 (思维协议 A: 让 0.50 与 0.97 在效用层不等价) ----
STRENGTH_REF = 0.8       # 强度参考线: cov_s = min(1, max_strength / 0.8)
FRAGILE_MARGIN = 0.10    # 贴边判定余量: 最强值∈[0.5, 0.5+margin) 即脆弱
HOLD_REF = 12.0          # 满余量维度(强度1.0)在持续负荷下维持≥0.5 的月数


def cov_strength(max_str):
    """A: 强度加权覆盖度。0.50->0.625, 0.80->1.0, 0.97->1.0(封顶)。
    取代二值阈值, 使效用层对能力强度敏感 —— 0.50 与 0.97 不再等价。"""
    return min(1.0, max(0.0, max_str) / STRENGTH_REF)


def grade_dim(max_str, ci_half=0.10):
    """置信区间内分级: 基于强度点估计与评估噪声 CI(±ci_half)。
    返回 (grade, ci_low, ci_high): A=稳健(≥0.8) / B=普通 / C=脆弱(置信内或跌破0.5)。"""
    lo = max(0.0, max_str - ci_half)
    hi = min(1.0, max_str + ci_half)
    if max_str >= STRENGTH_REF:
        g = "A"
    elif lo < 0.5:
        g = "C"                       # 评估噪声下可能跌破可行线 -> 脆弱
    else:
        g = "B"
    return g, round(lo, 2), round(hi, 2)


def overlap_ratio(coal, dims):
    """联盟内资源重叠度 (多主体同维高强度 -> 重叠高 -> 互补低)"""
    if not coal:
        return 0.0
    total = 0.0
    n = len(coal)
    for d in dims:
        vals = [c.res.get(d, 0.0) for c in coal]
        mx = max(vals)
        shared = sum(v for v in vals if v >= 0.5) - (1 if mx >= 0.5 else 0)
        total += shared / n
    return total / len(dims)


def coalition_value(coal, need, dims, value_base, strength=False):
    """联盟联合效用函数 V (思维协议定义的正和潜力)。

    strength: A 强度加权覆盖开关。
      False = 原二值覆盖 (>=0.5 即 1), 维持历史可比性;
      True  = 每维覆盖度 = cov_strength(max_strength) = min(1, max/0.8),
              0.50 与 0.97 在效用层不等价, 脆弱联盟 V 自然偏低。
    """
    if not coal:
        return 0.0
    if len(coal) == 1:
        # 单家价值取决于其**实际覆盖**, 而非一律低
        # (修复: 原 flat floor vb*0.08 把真实巨头一律当弱方, 与'单家撮合可行'现实矛盾)
        c = coal[0]
        if strength:
            cov = sum(cov_strength(c.res.get(d, 0.0)) for d in need) / len(need)
        else:
            covered = sum(1 for d in need if c.res.get(d, 0.0) >= 0.5)
            cov = covered / len(need)
        synergy = 1.0                      # 单家无内部重叠, 协同系数=1
        return round(value_base * cov * synergy, 1)
    comp = 1 - overlap_ratio(coal, dims)          # 互补系数
    synergy = 0.5 + 0.5 * comp                    # 协同系数
    if strength:
        cov = sum(cov_strength(max(c.res.get(d, 0.0) for c in coal))
                  for d in need) / len(need)
    else:
        covered = sum(1 for d in need if any(c.res.get(d, 0.0) >= 0.5 for c in coal))
        cov = covered / len(need)
    return round(value_base * cov * synergy, 1)


def form_coalition(candidates, need, dims, value_base, strength_weight=0.0):
    """覆盖驱动贪心 + 互补评分, 撮合稳定联盟 (博弈论 COP 比配原则)

    strength_weight: 强度加权系数 (默认 0 = 原朴素行为, 只数覆盖个数)。
      朴素贪心的结构性缺陷: 0.50 与 0.97 在二值阈值下同权, 会撮合出"处处贴边"
      的脆弱联盟 (见 fragile_dims)。>0 时把新覆盖维度的**实际强度**计入增益,
      使比配偏好强能力主体 —— 供 A/B 对照, 不静默替换默认语义。
    """
    coalition: List = []
    pool = list(candidates)
    uncovered = set(need)
    while uncovered and pool:
        best = None
        best_gain = 0.0
        for c in pool:
            newly = [d for d in uncovered if c.res.get(d, 0.0) >= 0.5]
            new_cov = len(newly)
            comp = 1 - overlap_ratio(coalition + [c], dims)
            gain = new_cov * 10.0 + comp * 5.0     # 补缺口优先
            if strength_weight:
                # A: 新覆盖维度的强度计入增益 (用 cov_strength, 0.8 封顶)
                gain += strength_weight * sum(cov_strength(c.res.get(d, 0.0)) - 0.5
                                              for d in newly)
            if gain > best_gain:
                best_gain = gain
                best = c
        if best is None:
            break
        coalition.append(best)
        pool.remove(best)
        uncovered = set(d for d in need
                        if not any(x.res.get(d, 0.0) >= 0.5 for x in coalition))
    return coalition


def uncovered_dims(coalition, need):
    """联盟未覆盖的关键资源维度 (稳定校验)"""
    return [d for d in need if not any(c.res.get(d, 0.0) >= 0.5 for c in coalition)]


def fragile_dims(coalition, need, margin=0.10):
    """NSFL 负空间告警: '贴边达标'维度 (最强主体仅略高于阈值 0.5)。

    二值阈值 (>=0.5 即算覆盖) 会把 0.50 与 0.97 视为等同, 使联盟名义全覆盖
    但实质能力脆弱 —— 这是搜索比配的结构性盲区, 须显式披露而非隐藏。
    返回 [(dim, best_strength), ...], best < 0.5+margin 即判脆弱。
    """
    out = []
    for d in need:
        best = max((c.res.get(d, 0.0) for c in coalition), default=0.0)
        if 0.5 <= best < 0.5 + margin:
            out.append((d, round(best, 2)))
    return out


def grade_dims(coalition, need, ci_half=0.10):
    """逐维置信分级表 (A/B/C) —— 供 NSFL 负空间披露与有限时窗稳健评估。
    返回 [(dim, best_strength, grade, ci_low, ci_high), ...]。"""
    out = []
    for d in need:
        best = max((c.res.get(d, 0.0) for c in coalition), default=0.0)
        g, lo, hi = grade_dim(best, ci_half)
        out.append((d, round(best, 2), g, lo, hi))
    return out


def fragile_time_discount(coalition, need, horizon, penalty,
                          hold_ref=HOLD_REF, margin=FRAGILE_MARGIN):
    """B: 保留 V 定义, 对脆弱维度按时窗加折扣惩罚。

    脆弱维度余量 m = max_str - 0.5 越小, 在持续负荷下维持≥0.5 的月数 hold 越短;
    时窗 H > hold 后该维度效用暴露侵蚀, 折扣 = penalty × exposure(H)。
    即**脆弱维度的价值与时间效用正相关** —— 时窗越长, 脆弱联盟的效用折扣越大。
    无时间约束(H→∞)时折扣趋近上限, 正和满意解不保证稳健。
    """
    if penalty <= 0 or horizon <= 0:
        return 0.0
    disc = 0.0
    for d in need:
        ms = max((c.res.get(d, 0.0) for c in coalition), default=0.0)
        if 0.5 <= ms < 0.5 + margin:
            m = ms - 0.5                      # 脆弱余量 0..margin
            hold = (m / 0.5) * hold_ref       # 该维度维持≥0.5 的月数
            exposure = 0.0 if horizon <= hold else min(1.0, (horizon - hold) / hold_ref)
            disc += penalty * exposure
    return min(0.9, round(disc, 3))
