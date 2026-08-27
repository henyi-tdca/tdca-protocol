# -*- coding: utf-8 -*-
"""TDCA 开源社区冷启动 · 招募比配智能体(真实计算)
=========================================================
由思维协议 孙子兵法·谋攻篇("知己知彼")指挥: 先知己(社区能力缺口), 再知彼(候选互补度),
用真实的 form_coalition / coalition_value / shapley / fragile_dims / grade_dims 计算层做比配。
仅调用计算层, 不发射 NCA、不落盘(招募阶段在准入之前, 闸门纪律: 未准入不缔约)。
"""
import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
_CC = os.path.abspath(os.path.join(_HERE, ".."))               # cognitive-compiler
_SIM = os.path.join(_CC, "simulations", "multilateral_search_match")
sys.path.insert(0, _HERE)
sys.path.insert(0, _CC)
sys.path.insert(0, _SIM)
sys.path.insert(0, os.path.join(_CC, "..", "config"))
sys.path.insert(0, os.path.join(_CC, "..", "nca-generator"))

from providers.base import Candidate
from compute.coalition import (form_coalition, coalition_value, fragile_dims,
                               grade_dims, cov_strength)
from compute.shapley import shapley

INITIAL_VB = 200.0


def load():
    with open(os.path.join(_HERE, "coldstart_candidates.json"), encoding="utf-8") as f:
        d = json.load(f)
    DIMS = d["meta"]["dims"]
    org = d["organizer"]
    organizer = Candidate(id=org["id"], name=org["name"], cop=org["cop"],
                          res=org["res"], batna=org["batna"], source="organizer")
    cands = [Candidate(id=c["id"], name=c["name"], cop=c.get("cop", ""),
                       res=c["res"], batna=c["batna"], source="coldstart")
             for c in d["candidates"]]
    raw = {c["id"]: c for c in d["candidates"]}
    return DIMS, organizer, cands, raw


def rank(DIMS, organizer, cands, raw):
    gaps = [d for d in DIMS if organizer.res.get(d, 0.0) < 0.5]
    scored = []
    for c in cands:
        gain = sum(cov_strength(c.res.get(d, 0.0)) for d in gaps)
        overlap = sum(1 for d in DIMS
                      if c.res.get(d, 0.0) >= 0.5 and organizer.res.get(d, 0.0) >= 0.5)
        scored.append((c, round(gain, 3), overlap, raw[c.id].get("loaded_core", False)))
    scored.sort(key=lambda x: (-x[1], x[2]))
    return gaps, scored


def main():
    DIMS, organizer, cands, raw = load()
    gaps, scored = rank(DIMS, organizer, cands, raw)
    admitted = [c for c in cands if raw[c.id].get("loaded_core", False)]

    L = []
    L.append("# 冷启动·招募比配报告 (由 孙子兵法·谋攻篇 指挥 · 真实计算层)")
    L.append("")
    L.append("> 思维协议指挥: `孙子兵法·谋攻篇`(知己知彼) → dispatch 搜索比配引擎(compute 层)。"
             "本阶段**只计算不缔约**, 候选 res/batna 为自报(冷启动 newcomer 未确权), 见诚实口径。")
    L.append("")
    L.append("## 1. 知己: TDCA 社区现状与缺口")
    L.append("- 组织者已覆盖: " + ", ".join("%s=%.2f" % (d, organizer.res[d])
                                            for d in DIMS if organizer.res[d] >= 0.5))
    L.append("- **能力缺口(最强<0.5)**: `%s`" % "`, `".join(gaps))
    L.append("")
    L.append("## 2. 知彼: 候选互补度排名(按缺口覆盖增益)")
    L.append("| 排名 | 候选 | 缺口覆盖增益 | 与组织者重叠维数 | loaded_core | 准入预判 |")
    L.append("|---|---|---|---|---|---|")
    for i, (c, gain, ov, lc) in enumerate(scored, 1):
        pred = "✅可准入" if lc else "❌准入门拒"
        L.append("| %d | %s | %.3f | %d | %s | %s |" % (i, c.name, gain, ov, "✅" if lc else "❌", pred))
    L.append("")
    L.append("## 3. 已准入候选 MOU 可行性预演(organizer + 已准入候选)")
    vb = INITIAL_VB
    coalition = form_coalition([organizer] + admitted, DIMS, DIMS, vb, strength_weight=0.3)
    V = coalition_value(coalition, DIMS, DIMS, vb, strength=True)
    phi, method = shapley(coalition, DIMS, DIMS, vb, strength=True)
    L.append("- 联盟(organizer+已准入 %d 家) V=%s, 方法=%s" % (len(admitted), V, method))
    L.append("- 逐方 φ vs BATNA:")
    for c in coalition:
        flag = "✅" if phi[c.id] >= c.batna else "❌"
        L.append("  - %s: φ=%s BATNA=%s %s" % (c.name, phi[c.id], c.batna, flag))
    L.append("- 脆弱维度(贴边达标, NSFL 披露): %s" % (fragile_dims(coalition, DIMS) or "无"))
    L.append("- 逐维置信分级: " + "; ".join("%s=%s(%s)" % (d, s, g)
            for (d, s, g, lo, hi) in grade_dims(coalition, DIMS)))
    L.append("")
    L.append("## 4. 招募建议(输出给准入缔约智能体)")
    top_adm = next((c for c, *_ in scored if raw[c.id].get("loaded_core", False)), None)
    L.append("- **优先邀约(顶选可准入候选)**: %s(缺口覆盖最高且 loaded_core=true)" % (top_adm.name if top_adm else "无"))
    L.append("- **准入门将拒绝**: " + ", ".join(c.name for c, *_ in scored if not raw[c.id].get("loaded_core", False))
             + " —— 证明'加入即加载 TDCA-CORE'")
    L.append("- 下一步: 准入缔约智能体对顶选跑 三段式闸门(准入→沙盒→生产)")
    L.append("")
    out = "\n".join(L) + "\n"
    rep = os.path.join(_HERE, "coldstart_candidates_ranked.md")
    with open(rep, "w", encoding="utf-8") as f:
        f.write(out)
    print(out)
    print(">>> 招募排名已写: %s" % rep)


if __name__ == "__main__":
    main()
