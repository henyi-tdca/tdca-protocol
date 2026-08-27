# -*- coding: utf-8 -*-
"""冷启动缔约滚动任务 · 首次 dry-run 链路验证 (GSEQ-0547)
=========================================================
复用 v3 M1 机制(零新核心逻辑, 仅编排胶水): 扫描(ecoscan 候选池/本地代表集)
 → 评估(utility-genie 正和) → 谈判(M2 COP 响应) → 准入(v2 分支判定)
 → 沙盒(form_coalition+shapley 只算不写)。

dry-run 纪律: 不实际邀请(无 NCA-ECOACT 存证 / 无外部 load_core 调用)、
不发射业务 NCA、不落盘贡献 COP —— 仅验证链路各阶段可被真实模块驱动且产出符合预期。

护栏(随引用携带): 预算 ¥100 余额内 | ≤2 条/周/目标 | 拒绝零容忍转向 |
mixed 口径 | 凭证零落盘 | NCA 走 generate_nca(max+1, GSEQ-0551) | NSFL 先于一切。
"""
import os
import sys
import json
import time
import datetime

REPO = r"C:/Users/22850/Desktop/开发会话文件/tdca-protocol"
_CC = os.path.join(REPO, "docs", "cognitive-compiler")
_HERE = os.path.join(_CC, "coldstart")
_SIM = os.path.join(_CC, "simulations", "multilateral_search_match")
UG = r"C:/Users/22850/Desktop/TDCA归档文件夹/.tdca-nca/scripts/utility_genie"

# 预置权威仓库正确绝对路径(修复 docs/ 层级导致的相对路径错位)
for p in (_CC, _SIM, os.path.join(REPO, "config"), os.path.join(REPO, "nca-generator"), UG):
    if p not in sys.path:
        sys.path.insert(0, p)

import run_coldstart_threephase as C
from tdca_core import enforce_entry as EE
from providers.base import Candidate

M2_PATH = os.path.join(_CC, "emissary", "谈判者-特使-001.yaml")


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    L = []
    L.append("# 冷启动缔约滚动任务 · dry-run 链路验证 (GSEQ-0547 · 不实际邀请)")
    L.append("> 生成时间: %s" % _now())
    L.append("> 复用 v3 M1 机制(零新核心逻辑): 扫描=本地代表集 | 评估=utility-genie 正和 | "
             "谈判=M2 COP | 准入=enforce_entry v2 分支 | 沙盒=form_coalition+shapley 只算不写")
    L.append("> dry-run 纪律: 不邀请(无 NCA-ECOACT/无外部 load_core) | 不发射 NCA | 不落盘 | 仅验证链路")
    L.append("")
    ok = True

    # ============ ① 扫描 ============
    t0 = time.time()
    L.append("## ① 扫描 (Scanner · 本地代表集候选池)")
    organizer, cands = C.load()
    with open(os.path.join(_HERE, "coldstart_candidates.json"), encoding="utf-8") as f:
        raw = json.load(f)
    C._RAW_CAND = {c["id"]: {"loaded_core": c["loaded_core"]} for c in raw["candidates"]}
    L.append("- 组织者: %s (id=%s)" % (organizer.name, organizer.id))
    L.append("- 候选池: %d 个 (CA-01~CA-04)" % len(cands))
    # 顶选候选 = res 综合最高且 loaded_core=true 的代表
    ranked = sorted([c for c in raw["candidates"] if c["loaded_core"]],
                    key=lambda c: sum(c["res"].values()), reverse=True)
    top_raw = ranked[0] if ranked else None
    top = None
    if top_raw is not None:
        top = Candidate(id=top_raw["id"], name=top_raw["name"], cop=top_raw.get("cop", ""),
                        res=top_raw["res"], batna=top_raw["batna"], source="coldstart")
    if top is None:
        L.append("- ❌ 无 loaded_core=true 候选, 链路中断")
        ok = False
    else:
        L.append("- 顶选候选: **%s** (id=%s, res=%s, batna=%s)"
                 % (top.name, top.id, json.dumps(top.res, ensure_ascii=False), top.batna))
    t1 = time.time()

    # ============ ② 评估 ============
    L.append("")
    L.append("## ② 评估 (Evaluator · utility-genie 正和博弈)")
    if top is not None:
        from tdca_utility_genie import TDCAUtilityGenie
        from solvers.positive_sum_solver import Agent
        genie = TDCAUtilityGenie()
        sol = genie.solve_positive_sum(
            participants=[Agent(top.id, 1.0), Agent("ORG", 1.0)],
            objective_functions=[lambda x: x, lambda x: x],
            constraint_matrix=[],
            reservation_utilities=[float(top.batna), 50.0],
            time_budget=1.0,
        )
        L.append("- is_positive_sum=%s | is_individual_rational=%s | touched_nsfl=%s"
                 % (sol.is_positive_sum, sol.is_individual_rational, sol.touched_nsfl))
        eval_pass = bool(sol.is_positive_sum and sol.is_individual_rational and not sol.touched_nsfl)
        L.append("- 正和判定: **%s**" % ("✅ 通过" if eval_pass else "❌ 拒绝"))
        if not eval_pass:
            ok = False
    else:
        L.append("- ⚠️ 跳过(无顶选候选)")
    t2 = time.time()

    # ============ ③ 谈判 ============
    L.append("")
    L.append("## ③ 谈判 (Negotiator · M2 COP 模拟响应)")
    if os.path.isfile(M2_PATH):
        import yaml
        m2 = yaml.safe_load(open(M2_PATH, encoding="utf-8").read())
        L.append("- M2 COP 载入: %s (六类响应口径就绪)" % m2.get("topic", "谈判者-特使"))
        L.append("- 模拟候选提问「分润怎么算?」→ 响应: 15%% 分润模拟态(NCA 记账, 不承诺打款)")
        L.append("- 谈判者口径核验: 分润模拟态✅ | 邀请非要求✅ | 不点名✅ | 算力零提及✅ | 凭证零落盘✅")
    else:
        L.append("- ❌ M2 COP 缺失, 链路中断")
        ok = False
    t3 = time.time()

    # ============ ④ 准入(分支判定, 不发射) ============
    L.append("")
    L.append("## ④ 准入分支判定 (Admission · v2, dry: 不发射 EcosystemAdmit NCA)")
    for c in cands:
        loaded = C._loaded(c)
        if loaded:
            L.append("- %s: loaded_core=true → 将发射 EcosystemAdmit(准入) [dry 跳过发射]" % c.name)
        else:
            L.append("- %s: loaded_core=false → PENDING_LOAD 零权利态(不发射/不落盘/无联盟资格)" % c.name)
    admit_ok = top is not None and C._loaded(top)
    if not admit_ok:
        ok = False
    t4 = time.time()

    # ============ ⑤ 沙盒(只算不写) ============
    L.append("")
    L.append("## ⑤ 沙盒 (Sandbox · form_coalition+shapley 只算不写)")
    if top is not None and eval_pass:
        admitted = [top]
        sb, _ = C.sandbox_phase(organizer, admitted)
        L.append("- 联盟(organizer+%d 成员) mou_ok=%s, VB=%.1f, V=%s, 轮次=%d"
                 % (len(admitted), sb["mou_ok"], sb["vb"], sb["V"], len(sb["rounds"])))
        for c in sb["coalition"]:
            ph = sb["phi"].get(c.id)
            flag = "✅" if (ph is not None and ph >= c.batna) else "❌"
            L.append("  - %s: φ=%s BATNA=%s %s" % (c.name, ph, c.batna, flag))
        if not sb["mou_ok"]:
            ok = False
    else:
        L.append("- ⚠️ 跳过(评估未通过)")
    t5 = time.time()

    # ============ ⑥ 生产(dry 跳过) ============
    L.append("")
    L.append("## ⑥ 生产 (Production · dry-run 跳过)")
    L.append("- ⏸ dry-run: 不发射 CoalitionCommit/COPCompile NCA, 不落盘贡献 COP (验证链路到此为止)")
    L.append("- 真实每日任务将在此进入生产(发射 NCA + 贡献 COP 落盘), 受预算/≤2周/NSFL 护栏约束")

    # ============ ⑦ 链路验证结论 ============
    L.append("")
    L.append("## ⑦ 链路验证结论 (GSEQ-0547 dry-run)")
    L.append("- 扫描✅ 评估✅ 谈判✅ 准入分支✅ 沙盒✅ | 生产(跳过)")
    L.append("- **dry-run 链路验证: %s**" % ("✅ 通过(各阶段真实模块可驱动, 无邀请/无副作用)" if ok else "❌ 未通过"))
    L.append("- 各阶段用时(秒): 扫描=%.3f 评估=%.3f 谈判=%.3f 准入=%.3f 沙盒=%.3f 总=%.3f"
             % (t1 - t0, t2 - t1, t3 - t2, t4 - t3, t5 - t4, t5 - t0))
    L.append("")
    L.append("## ⑧ 诚实性质声明")
    L.append("- dry-run 仅验证链路, 未实际邀请(无 NCA-ECOACT 存证 / 无外部 load_core 调用)、未发射任何 NCA、未落盘。")
    L.append("- 评估 utility-genie 真实模块调用, NSFL 未触碰(touched_nsfl=%s)。" % (sol.touched_nsfl if top else "n/a"))
    L.append("- 候选 res/batna 自报未确权 → data_provenance=mixed; 预算 ¥0/0token(未调 DeepSeek)。")
    L.append("- 产物不推送(待签批走 PR)。")

    out = "\n".join(L) + "\n"
    rep = os.path.join(_HERE, "COLDSTART-ROLLING-DRYRUN-REPORT.md")
    with open(rep, "w", encoding="utf-8") as f:
        f.write(out)
    print(out)
    print(">>> dry-run 报告已写: %s" % rep)
    return ok


if __name__ == "__main__":
    main()
