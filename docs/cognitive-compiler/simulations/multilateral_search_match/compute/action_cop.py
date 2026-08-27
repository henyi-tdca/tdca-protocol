# -*- coding: utf-8 -*-
"""脆弱覆盖 -> 行动清单 (Action COP · 搜索比配引擎 v2 升级)
=========================================================
战术 2: 把 NSFL 负空间的"脆弱覆盖"告警从被动信息编译为可执行任务链,
直接推送给人类用户 (并经 MCP 连接器触发下一步搜索)。

触发条件 (对主选联盟):
  - 脆弱覆盖 (fragile): 某维联盟内最强 ∈ [0.5, 0.6) 贴边达标
  - 单点依赖 (single_point): 某维联盟内仅 1 家供给 (红队判定单点失效即丢失)
对每个触发维度生成两阶段任务:
  Phase 1: 联系全网最强替代者评估入盟 (补强该维)
  Phase 2 (条件): 若替代者无法入盟, 发起针对该维的 MCP 全网搜索寻找备用节点
"""
from typing import List, Dict
from .coalition import fragile_dims


def _providers_for(coalition, d):
    return [c for c in coalition if c.res.get(d, 0.0) >= 0.5]


def _best(candidates, d):
    return max((c.res.get(d, 0.0) for c in candidates), default=0.0)


def build_action_plan(primary_coalition, candidates, need):
    """返回行动清单 (list of dict): {dim, kind, phase, action, owner, trigger}"""
    frag = fragile_dims(primary_coalition, need)
    single_point = [d for d in need if len(_providers_for(primary_coalition, d)) < 2]

    triggered: Dict[str, str] = {}
    for d, _ in frag:
        triggered.setdefault(d, "fragile(贴边达标)")
    for d in single_point:
        triggered.setdefault(d, "single_point(单点依赖)")

    actions: List[dict] = []
    for d in need:
        if d not in triggered:
            continue
        kind = triggered[d]
        # 联盟外最强替代者
        alt = max((c for c in candidates if c not in primary_coalition),
                  key=lambda c: c.res.get(d, 0.0), default=None)
        in_best = _best(primary_coalition, d)
        if alt is None:
            actions.append({
                "dim": d, "kind": kind, "phase": 1, "owner": "人类用户",
                "action": f"维度[{d}]无联盟外替代者(联盟内最强仅 {in_best:.2f}); "
                          f"建议挂牌招募或放宽搜索条件",
                "trigger": kind,
            })
            continue
        actions.append({
            "dim": d, "kind": kind, "phase": 1, "owner": "人类用户",
            "action": f"联系 {alt.name} 评估入盟, 补强[{d}]维度 "
                      f"(联盟内最强 {in_best:.2f}, 全网最强替代 {alt.name} {alt.res.get(d,0.0):.2f})",
            "trigger": kind,
        })
        actions.append({
            "dim": d, "kind": kind, "phase": 2, "owner": "系统(MCP)", "conditional": True,
            "action": f"若 {alt.name} 无法入盟, 发起针对[{d}]维度的 MCP 全网搜索 "
                      f"(tdca-wan-registry), 寻找备用节点",
            "trigger": kind,
        })
    return actions


def render_action_chain(actions):
    """渲染为可读任务链文本 (Markdown 列表)"""
    if not actions:
        return "- (无) 主选联盟无脆弱覆盖/单点依赖, 无需行动清单"
    out = []
    for a in actions:
        tag = "[条件]" if a.get("conditional") else ""
        out.append(f"- **Phase {a['phase']}{tag}** `[{a['dim']}·{a['kind']}]** "
                   f"({a['owner']}): {a['action']}")
    return "\n".join(out)
