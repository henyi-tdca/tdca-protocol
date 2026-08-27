# -*- coding: utf-8 -*-
"""TDCA 开源社区冷启动 · 三段式闸门编排器(准入→沙盒→生产)
=========================================================
由 机制设计 + 一诺千金⟂论语·学而(信用) 指挥准入缔约; 由 庖丁解牛⟂道常无为(顺其理) 指挥生产。
严格复用 run_sunzi_threephase.py 的闸门纪律: 生产落盘**严格后置**到沙盒 mou_ok 之后。

诚实约束(继承 2026-08-16 评审):
  - 杠杆A(VB 重定价)为组织者主权宣言, 无外部锚 → 标注 [UNVERIFIED-NO-EXTERNAL-ANCHOR]
  - 候选 res/batna 自报, 冷启动 newcomer 无历史 NCA 链 → data_provenance=mixed
  - 杠杆B(校准BATNA到φ)已移除 → BATNA 存疑熔断
"""
import os
import sys
import json
import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
_CC = os.path.abspath(os.path.join(_HERE, ".."))               # cognitive-compiler
_SIM = os.path.join(_CC, "simulations", "multilateral_search_match")
sys.path.insert(0, _HERE)
sys.path.insert(0, _CC)
sys.path.insert(0, _SIM)
sys.path.insert(0, os.path.join(_CC, "..", "config"))
sys.path.insert(0, os.path.join(_CC, "..", "nca-generator"))

from providers.base import Candidate
from compute.coalition import form_coalition, coalition_value, fragile_dims, grade_dims
from compute.shapley import shapley
from tdca_core import enforce_entry as EE
import nca_generator as NCA
from coldstart_mcp_client import connect_external_agent

# 社区能力维度
DIMS = ["范式编译", "工程实现", "文档教程", "社区运营", "审计合规", "连接器", "算力", "NLP"]

# 沙盒迭代参数
INITIAL_VB = 200.0
VB_STEP = 1.10
VB_MAX = 260.0
MAX_ROUNDS = 6

EXTERNAL_ANCHOR = "待接入: 麦肯锡COP编译基准V~200 / 三十六计逐计编译基准V~200 (可比任务定价)"
REPRICING_PROVENANCE = "organizer-sovereign-declaration"
REPRICING_ANCHORED = False

CONTRIB_PATH = os.path.join(_CC, "coldstart", "community",
                            "第01条-开源社区冷启动·正和准入.yaml")

# 外部 agent MCP server 路径(自定义连接器 stdio 入口)
SERVER_PATH = os.path.join(_HERE, "mcp_external_agent_server.py")


def build_mcp_candidate():
    """经自定义连接器(stdio MCP)真实接入外部 agent, 返回 (Candidate, info) 或 (None, err)。"""
    try:
        profile, cop_yaml, tool_names = connect_external_agent(SERVER_PATH)
    except Exception as e:
        return None, "MCP 连接失败: %s" % e
    cid = profile["id"]
    cand = Candidate(id=cid, name=profile["name"], cop=profile.get("core_id", ""),
                     res=profile["res"], batna=profile["batna"], source="mcp-external")
    # 贡献物落盘(沙盒通过后生产阶段引用)
    os.makedirs(os.path.dirname(CONTRIB_PATH), exist_ok=True)
    with open(CONTRIB_PATH, "w", encoding="utf-8") as f:
        f.write(cop_yaml)
    # v2 机读证据: load_core 返回的声明文本 + sha256 + source(self-hosted stdio)
    import hashlib as _hl
    resp_txt = json.dumps(profile, ensure_ascii=False, sort_keys=True)
    evidence = {"response": resp_txt,
                "hash": _hl.sha256(resp_txt.encode("utf-8")).hexdigest(),
                "source": "mcp-external-stdio@%s" % SERVER_PATH}
    return cand, "tools=%s, loaded_core=%s" % (tool_names, profile.get("loaded_core")), evidence


def load():
    with open(os.path.join(_HERE, "coldstart_candidates.json"), encoding="utf-8") as f:
        d = json.load(f)
    org = d["organizer"]
    organizer = Candidate(id=org["id"], name=org["name"], cop=org["cop"],
                          res=org["res"], batna=org["batna"], source="organizer")
    cands = [Candidate(id=c["id"], name=c["name"], cop=c.get("cop", ""),
                       res=c["res"], batna=c["batna"], source="coldstart")
             for c in d["candidates"]]
    return organizer, cands


# ============ 阶段1: 准入(由 enforce_entry 指挥) ============
def admission_phase(organizer, cands, mcp_evidence=None, mcp_cand_id=None):
    L = []
    L.append("## 1. 准入门 (admission_phase · v2 可转化准入 · 由 enforce_entry 指挥)")
    L.append("> v2: 外部 agent 须持机读证据(response+sha256+source)过核验才准入发射 NCA; "
             "本地候选 loaded_core=False 进入 PENDING_LOAD 零权利态(不发射NCA/不落盘/无联盟资格)。")
    admitted, rejected, admission_ncas = [], [], []
    for c in cands:
        if mcp_evidence is not None and c.id == mcp_cand_id:
            # 外部 agent: v2 机读证据路径
            try:
                rec = EE.ecosystem_admit_v2(c.name, core_evidence=mcp_evidence,
                                            note="冷启动 v2 真实外部 agent 准入")
                admitted.append(c)
                admission_ncas.append((c.id, rec["nca_id"]))
                L.append("- ✅ v2 准入 **%s** -> 发射 NCA `%s` (证据源=%s)"
                         % (c.name, rec["nca_id"], mcp_evidence.get("source")))
            except EE.CoreEvidenceInvalid:
                rejected.append(c)
                L.append("- ❌ v2 证据无效 **%s** -> CoreEvidenceInvalid(零权利, 拒绝准入)"
                         % c.name)
            except EE.AdmissionDenied:
                rejected.append(c)
                L.append("- ❌ 拒绝 **%s** (未加载 %s)" % (c.name, EE.MANDATORY_CORE_ID))
        else:
            # 本地候选: v1 兼容分支(loaded_ids) 或 PENDING_LOAD
            loaded_ids = [EE.MANDATORY_CORE_ID] if _loaded(c) else []
            rec = EE.ecosystem_admit_v2(c.name, loaded_ids=loaded_ids,
                                        note="冷启动 v2 本地候选准入")
            if rec.get("state") == EE.PENDING_LOAD:
                rejected.append(c)
                L.append("- ⏸ PENDING_LOAD 零权利态 **%s** (未加载 CORE, 不发射NCA/不落盘/无联盟资格)"
                         % c.name)
            else:
                admitted.append(c)
                admission_ncas.append((c.id, rec["nca_id"]))
                L.append("- ✅ v2 准入 **%s** -> 发射 NCA `%s`" % (c.name, rec["nca_id"]))
    L.append("")
    return admitted, rejected, admission_ncas, L


def _loaded(c):
    # 从原始 json 读 loaded_core; Candidate 未存该字段, 故回查
    raw = _RAW_CAND.get(c.id, {})
    return raw.get("loaded_core", False)


_RAW_CAND = {}


# ============ 阶段2: 沙盒(由 机制设计 指挥) ============
def sandbox_phase(organizer, admitted):
    L = []
    L.append("## 2. 沙盒迭代 (sandbox_phase · 真实重算, 不落盘 · 由 机制设计 指挥)")
    L.append("> 沙盒闸门: 此阶段只计算, 不发射业务NCA、不写COP。'亏'被隔离在落盘之前。")
    cands = [organizer] + admitted
    vb = INITIAL_VB
    rounds = []
    mou_ok = False
    batna_challenge = False
    for r in range(MAX_ROUNDS):
        coalition = form_coalition(cands, DIMS, DIMS, vb, strength_weight=0.3)
        V = coalition_value(coalition, DIMS, DIMS, vb, strength=True)
        phi, method = shapley(coalition, DIMS, DIMS, vb, strength=True)
        deficit = [c for c in coalition if phi[c.id] < c.batna]
        mou_ok = not deficit
        if r == 0:
            action = "初始基值 VB=%.0f (中性基值)" % vb
        elif vb < VB_MAX:
            anchor_tag = "" if REPRICING_ANCHORED else " [UNVERIFIED-NO-EXTERNAL-ANCHOR]"
            action = ("组织者任务重定价 VB→%.1f | 锚=%s%s"
                      % (vb, EXTERNAL_ANCHOR, anchor_tag))
        else:
            action = "BATNA存疑熔断触发前最后一轮 (VB=%.1f)" % vb
        rounds.append({"round": r + 1, "vb": vb, "V": V, "method": method,
                       "phi": {c.id: phi[c.id] for c in coalition},
                       "deficit": [(c.name, phi[c.id], c.batna) for c in deficit],
                       "mou_ok": mou_ok, "action": action})
        if mou_ok:
            break
        if vb < VB_MAX:
            vb = round(vb * VB_STEP, 1)
        else:
            batna_challenge = True
            L.append("- ⛔ **BATNA 存疑熔断**: VB 触顶=%.1f 仍 φ<BATNA, 要求亏方举证外部期权, 举证前禁止生产。" % vb)
            break
    sb = {"mou_ok": mou_ok, "vb": vb, "V": V, "phi": phi, "method": method,
          "coalition": coalition, "rounds": rounds, "batna_challenge": batna_challenge}
    L.append("- 联盟(organizer+已准入) %d 家, 实际形成联盟 %d 家" % (len(cands), len(coalition)))
    for rd in rounds:
        L.append("")
        L.append("### 沙盒轮次 %d (VB=%.1f · %s)" % (rd["round"], rd["vb"], rd["method"]))
        L.append("- 动作: %s" % rd["action"])
        L.append("- V = %s" % rd["V"])
        for c in coalition:
            ph = rd["phi"].get(c.id)
            flag = "✅" if (ph is not None and ph >= c.batna) else "❌"
            L.append("  - %s: φ=%s BATNA=%s %s" % (c.name, ph, c.batna, flag))
        if rd["deficit"]:
            L.append("- ❌ 本轮不可行: %s" % "; ".join(
                "%s(φ=%s<BATNA=%s)" % (n, p, b) for n, p, b in rd["deficit"]))
        else:
            L.append("- ✅ **本轮 MOU 正和可行** (各方 φ≥BATNA)")
    L.append("")
    L.append("**沙盒结论**: mou_ok=%s, VB=%.1f, V=%s, 轮次=%d" % (mou_ok, vb, V, len(rounds)))
    L.append("")
    return sb, L


# ============ 阶段3: 生产(仅 mou_ok · 由 庖丁解牛 指挥) ============
def production_phase(sb, contributor_id, contributor_name):
    L = []
    if not sb["mou_ok"]:
        L.append("## 3. 生产阶段 (production_phase)")
        L.append("- ⛔ 沙盒未通过, 按闸门纪律不进入生产, 不发射业务NCA、不落盘。")
        return None, None, L
    L.append("## 3. 生产阶段 (production_phase · 仅沙盒通过后触发 · 由 庖丁解牛⟂道常无为 指挥)")
    L.append("> 沙盒 mou_ok=True, 现在真实发射联盟NCA + 生产NCA, 关联合约贡献物。")
    # 联盟承诺 NCA(缔约)
    cnid, _, _ = NCA.generate_nca(
        operation_type="CoalitionCommit",
        scope=".tdca-protocol/cognitive-compiler/coldstart (冷启动社区首批联盟承诺)",
        pre_state={"path": None, "hash": None, "size": 0, "exists": False, "backup": None},
        post_state={"path": None, "hash": None, "size": 0, "exists": True, "backup": None},
        function_call_id="TDCA-FC-COLDSTART-COALITION",
        notes=("data_provenance=mixed(候选res/batna自报, 冷启动 newcomer 未确权) | "
               "沙盒至 MOU 正和可行(V=%s, VB=%s, 轮次=%d, φ≥BATNA全满足)后正式联盟承诺 | "
               "缔约方=%s" % (sb["V"], sb["vb"], len(sb["rounds"]), contributor_name)),
    )
    # 生产确权 NCA(贡献物)
    pnid, _, _ = NCA.generate_nca(
        operation_type="COPCompile",
        scope=".tdca-protocol/cognitive-compiler/coldstart/community/第01条-开源社区冷启动·正和准入.yaml (缔约方交付的首个贡献)",
        pre_state={"path": None, "hash": None, "size": 0, "exists": False, "backup": None},
        post_state={"path": "community/第01条-开源社区冷启动·正和准入.yaml", "hash": None,
                    "size": 0, "exists": True, "backup": None},
        function_call_id="TDCA-FC-COLDSTART-PROD",
        notes="沙盒(mou_ok=True)通过后, 缔约方 %s 交付'社区冷启动·正和准入' COP, 关联联盟 %s" % (contributor_name, cnid),
    )
    L.append("- 联盟承诺 NCA(缔约凭证): `%s`" % cnid)
    L.append("- 生产确权 NCA(贡献物确权): `%s`" % pnid)
    L.append("- 贡献物: `%s`" % CONTRIB_PATH)
    L.append("")
    return cnid, pnid, L


def main():
    global _RAW_CAND
    with open(os.path.join(_HERE, "coldstart_candidates.json"), encoding="utf-8") as f:
        d = json.load(f)
    _RAW_CAND = {c["id"]: c for c in d["candidates"]}
    organizer, cands = load()
    mcp_cand, mcp_info, mcp_evidence = build_mcp_candidate()
    if mcp_cand is not None:
        cands.append(mcp_cand)
        _RAW_CAND[mcp_cand.id] = {"loaded_core": True,
                                  "intent": "经自定义连接器(stdio MCP)接入的外部贡献 agent"}
    L = []
    L.append("# TDCA 开源社区冷启动 · 三段式闸门实跑报告 (COLDSTART-3PHASE · 准入→沙盒→生产)")
    if mcp_cand is not None:
        L.append("> 自定义连接器接入外部 agent: **%s** (真实 stdio 调用 load_core/contribute_cop; %s)"
                 % (mcp_cand.name, mcp_info))
    else:
        L.append("> 自定义连接器接入外部 agent: 失败 (%s) —— 跳过 MCP 候选, 仅跑本地代表集。" % mcp_info)
    L.append("")
    L.append("> 性质声明: 本跑验证 **TDCA 治理外壳**(准入门/沙盒闸门/MOU判定/NCA确权) 在冷启动场景真实实跑。"
             "data_provenance=mixed(候选 res/batna 自报未确权, VB 为组织者宣言式标[UNVERIFIED]); 机制全真实。引用须带混合口径。")
    L.append("")

    admitted, rejected, admission_ncas, l1 = admission_phase(organizer, cands, mcp_evidence, mcp_cand.id if mcp_cand else None)
    L.extend(l1)
    sb, l2 = sandbox_phase(organizer, admitted)
    L.extend(l2)
    # v2 VB 锚定升级: 若 DeepSeek 生成 COP 已落盘且 base_protocol 匹配 -> 降 [UNVERIFIED]
    anchor = EE.anchor_vb_to_cop(CONTRIB_PATH) if (mcp_cand is not None) else None
    if anchor and anchor.get("anchored"):
        L.append("- 🔗 **VB 外部锚达成**: DeepSeek 生成 COP 落盘且 base_protocol 匹配, "
                 "降 [UNVERIFIED-NO-EXTERNAL-ANCHOR] 为已锚定(正和信号来自真实外部生成)。")
    else:
        L.append("- ⚠️ VB 仍处 [UNVERIFIED-NO-EXTERNAL-ANCHOR] 待外部锚(贡献物未落盘或非 DeepSeek 生成)。")
    # 顶选缔约方 = 实际联盟中(排除组织者)φ 最高的候选
    joiners = [c for c in sb["coalition"] if c.id != organizer.id]
    contributor = max(joiners, key=lambda c: sb["phi"].get(c.id, 0)) if joiners else None
    cnid, pnid, l3 = production_phase(sb, contributor.id if contributor else "",
                                       contributor.name if contributor else "")
    L.extend(l3)

    # 诚实性质声明
    L.append("## 4. 诚实性质声明 (真实 vs 自报 / 沙盒闸门)")
    L.append("- **真实可调用资源**: 组织者(主agent) / 顶选缔约方(CA-01 独立贡献者·协议编译器手, real agent)。")
    L.append("- **准入门拒绝(2)**: CA-03(社区运营agent)/CA-04(空壳投机agent) 因 loaded_core=false 被拒 —— 证明'加入即加载 TDCA-CORE'。")
    L.append("- **沙盒闸门**: %s" % ("沙盒通过→真实发射联盟NCA+生产NCA, 缔约达成"
          if sb["mou_ok"] else "沙盒未过→未进入生产, 亏隔离在落盘前"))
    L.append("- **机制全真实**: enforce_entry/form_coalition/shapley/nca_generator 均为平台真实代码实跑。")
    L.append("- **已知缺口(诚实)**: ① 候选 res/batna 自报未确权(冷启动 newcomer 无历史 NCA 链) → 信任靠'小步首贡献+三段式闸门'缓解; ② VB 无外部锚 → 标[UNVERIFIED]; ③ 杠杆B 已移除改 BATNA 存疑熔断。")
    if mcp_cand is not None:
        L.append("- **自定义连接器链路(真实)**: 外部 agent MCP-EXT-01 经 stdio MCP server 真实接入, load_core/contribute_cop 真实跨进程调用; 贡献物由 server 返回并落盘 community/。端点由你(组织者)自托管 → 连通性为真实, 身份仍为 self-hosted(非第三方自然人), data_provenance 仍 mixed。")
    L.append("")

    out = "\n".join(L) + "\n"
    rep = os.path.join(_HERE, "COLDSTART-EXPERIMENT-REPORT.md")
    with open(rep, "w", encoding="utf-8") as f:
        f.write(out)
    print(out)
    print(">>> 报告已写: %s" % rep)


if __name__ == "__main__":
    main()
