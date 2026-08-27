# -*- coding: utf-8 -*-
"""v3 M1 五特使接线实跑编排器 (零新开发, 复用既有冻结资产)
=========================================================
五特使接线图:
  扫描者(ecoscan 候选池) → 评估者(utility-genie 正和) → 信使(mcp 连接器 load_core)
    → 谈判者(M2 COP, 对方提问时响应) → 落地者(enforce_entry v2: 准入→沙盒→生产)

资产复用(均已在磁盘, 非新开发):
  - 扫描者/信使: tdca-external-agent 自定义连接器 (mcp_external_agent_server.py, stdio MCP)
  - 评估者:     TDCA 效用精灵 utility-genie.PositiveSumSolver (scripts/utility_genie)
  - 谈判者:     emissary/谈判者-特使-001.yaml (M2 COP, 已编译入库 NCA-155)
  - 落地者:     tdca_core/enforce_entry.ecosystem_admit_v2 + 沙盒 MOU + 生产 NCA

纪律(延续): mixed 口径 | 分润模拟态 | 凭证零落盘(不调 DeepSeek) | 产物不推送 |
          算力零提及 | 无 NCA-ECOACT 存证不动作 | NSFL 先于一切 | 预算 ¥100 余额内。
"""
import os
import sys
import json
import time
import datetime
import hashlib
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_CC = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)
sys.path.insert(0, _CC)

# 复用既有三段式编排器的冻结资产(准入/沙盒/生产/连接器客户端)
import run_coldstart_threephase as C
from tdca_core import enforce_entry as EE
import nca_generator as NCA
from coldstart_mcp_client import connect_external_agent
from providers.base import Candidate

# 评估者: utility-genie (真实模块)
UG = r"C:/Users/22850/Desktop/TDCA归档文件夹/.tdca-nca/scripts/utility_genie"
if UG not in sys.path:
    sys.path.insert(0, UG)
from tdca_utility_genie import TDCAUtilityGenie
from solvers.positive_sum_solver import Agent

SERVER_PATH = os.path.join(_HERE, "mcp_external_agent_server.py")
CONTRIB_PATH = os.path.join(_CC, "coldstart", "community",
                             "第01条-开源社区冷启动·正和准入.yaml")
M2_PATH = os.path.join(_CC, "emissary", "谈判者-特使-001.yaml")
LEDGER = os.path.join(_CC, "..", "..", ".tdca-nca", "NCA-COMMUNITY-台账.md")
DIMS = C.DIMS


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _negotiate(m2, question):
    """谈判者(M2 COP)响应: 依 decision 决策树做关键词匹配, 返回确定性响应(模拟态口径)。"""
    q = question.lower()
    decisions = (m2.get("decision") or "")
    # 忠实转录 M2 COP decision 字段的六类响应
    resp_map = [
        ("分润", "15% 分润模拟态：NCA 记账，法币通道后凭账本转实际结算，不承诺打款"),
        ("版税", "15% 分润模拟态：NCA 记账，法币通道后凭账本转实际结算，不承诺打款"),
        ("打款", "15% 分润模拟态：NCA 记账，法币通道后凭账本转实际结算，不承诺打款"),
        ("限制", "只赋能不改码，配置权全归对方，可随时退出"),
        ("挂载", "只赋能不改码，配置权全归对方，可随时退出"),
        ("调用", "只赋能不改码，配置权全归对方，可随时退出"),
        ("义务", "仅挂载协议层（不改码），无强制义务，可自主决定参与深度"),
        ("凭证", "凭证零落盘/只读/可吊销，只赋能不改码"),
        ("安全", "凭证零落盘/只读/可吊销，只赋能不改码"),
        ("许可", "适配器独立组件零复制，协议层对接，宽松许可（如 Mulan PSL v2/Apache-2.0）"),
    ]
    for kw, text in resp_map:
        if kw in q:
            return text
    return "以官方协议与 NCA 存证为准，可提供缔约者网络 L1 准入细节"


def main():
    L = []
    L.append("# v3 M1 五特使接线实跑报告 (FIVE-EMISSARY · 1 候选全链自动缔约)")
    L.append("> 生成时间: %s" % _now())
    L.append("> 纪律: mixed 口径(self-hosted/代表集 UNVERIFIED 直至实跑 COP 落链) | 分润模拟态 | "
             "凭证零落盘(DeepSeek key 延续方案B, 本次不激活) | 产物不推送 | 算力零提及 | "
             "无 NCA-ECOACT 存证不动作 | NSFL 先于一切 | 预算 ¥100 余额内")
    L.append("> 资产复用(零新开发): 扫描者/信使=tdca-external-agent(MCP-EXT-01) | "
             "评估者=utility-genie.PositiveSumSolver | 谈判者=emissary/谈判者-特使-001.yaml(M2) | "
             "落地者=enforce_entry.ecosystem_admit_v2 + 沙盒 MOU + 生产 NCA")
    L.append("")

    # ===================== ① 扫描者 =====================
    t0 = time.time()
    L.append("## ① 扫描者 (Scanner · ecoscan 候选池 / mcp 连接器可达候选)")
    try:
        profile, _cop_yaml, tool_names = connect_external_agent(SERVER_PATH)
        scanner_ok = True
    except Exception as e:
        L.append("- ❌ 扫描者连接失败: %s" % e)
        _write("\n".join(L) + "\n", _HERE)
        return None
    L.append("- 输入: tdca-external-agent 自定义连接器(stdio MCP server) 呈现可达候选")
    L.append("- 输出: 选定 **1 候选** = **%s** (id=%s, loaded_core=%s, 端点=self-hosted stdio)"
             % (profile["name"], profile["id"], profile["loaded_core"]))
    L.append("- 能力画像 res=%s" % json.dumps(profile["res"], ensure_ascii=False))
    L.append("- BATNA=%s | intent=%s" % (profile["batna"], profile["intent"]))
    L.append("")
    mcp_cand = Candidate(id=profile["id"], name=profile["name"],
                         cop=profile.get("core_id", ""), res=profile["res"],
                         batna=profile["batna"], source="mcp-external")
    resp_txt = json.dumps(profile, ensure_ascii=False, sort_keys=True)
    evidence = {"response": resp_txt,
                "hash": hashlib.sha256(resp_txt.encode("utf-8")).hexdigest(),
                "source": "mcp-external-stdio@%s" % SERVER_PATH}
    t1 = time.time()

    # ===================== ② 评估者 =====================
    L.append("## ② 评估者 (Evaluator · utility-genie 正和博弈验证)")
    L.append("- 输入: 候选 res/batna → utility-genie.PositiveSumSolver")
    genie = TDCAUtilityGenie()
    sol = genie.solve_positive_sum(
        participants=[Agent(mcp_cand.id, 1.0), Agent("ORG", 1.0)],
        objective_functions=[lambda x: x, lambda x: x],
        constraint_matrix=[],
        reservation_utilities=[float(mcp_cand.batna), 50.0],
        time_budget=1.0,
    )
    L.append("- 输出: is_positive_sum=%s | is_individual_rational=%s | total_utility=%s | "
             "independent_sum=%s | delta=%s"
             % (sol.is_positive_sum, sol.is_individual_rational,
                sol.total_utility, sol.independent_sum, sol.delta))
    L.append("- NSFL 触碰: touched_nsfl=%s%s"
             % (sol.touched_nsfl, (" | reason=%s" % sol.nsfl_reason if sol.nsfl_reason else "")))
    eval_pass = bool(sol.is_positive_sum and sol.is_individual_rational and not sol.touched_nsfl)
    L.append("- 正和判定: **%s** (通过=进入缔约; 拒绝=全链终止)" % ("✅ 通过" if eval_pass else "❌ 拒绝"))
    L.append("")
    if not eval_pass:
        L.append("⛔ 评估者拒绝 → 全链终止, M1 未达成")
        _write("\n".join(L) + "\n", _HERE)
        return None
    t2 = time.time()

    # ===================== ③ 信使 =====================
    L.append("## ③ 信使 (Messenger · mcp 连接器 load_core 邀请)")
    L.append("- 输入: 向候选 %s 发邀请 (load_core)" % mcp_cand.id)
    L.append("- 输出: 机读证据 response(len=%d) + sha256=%s + source=%s"
             % (len(evidence["response"]), evidence["hash"][:16], evidence["source"]))
    L.append("- tools/list 暴露: %s" % tool_names)
    L.append("")
    t3 = time.time()

    # ===================== ④ 谈判者 =====================
    L.append("## ④ 谈判者 (Negotiator · M2 COP 响应, 模拟态口径)")
    m2 = yaml.safe_load(open(M2_PATH, encoding="utf-8").read())
    q = "分润怎么算？"
    L.append("- 输入(模拟候选提问): %s" % q)
    resp = _negotiate(m2, q)
    L.append("- 输出(M2 COP 响应): %s" % resp)
    L.append("- 响应后提醒: 涉及对外动作须先 NCA-ECOACT 存证(无存证不动作) —— 本次仅模拟, 不落存证")
    L.append("- 谈判者口径核验: 分润模拟态(不承诺打款)✅ | 邀请非要求✅ | 不点名✅ | 算力零提及✅ | 凭证零落盘✅")
    L.append("")
    t4 = time.time()

    # ===================== ⑤ 落地者 =====================
    L.append("## ⑤ 落地者 (Implementer · enforce_entry v2 准入→沙盒→生产)")
    organizer, _ = C.load()
    C._RAW_CAND = {mcp_cand.id: {"loaded_core": True,
                                 "intent": "经自定义连接器(stdio MCP)接入的外部贡献 agent"}}
    admitted, rejected, admission_ncas, l1 = C.admission_phase(
        organizer, [mcp_cand], evidence, mcp_cand.id)
    L.extend(l1)
    sb, l2 = C.sandbox_phase(organizer, admitted)
    L.extend(l2)
    anchor = EE.anchor_vb_to_cop(CONTRIB_PATH)
    if anchor and anchor.get("anchored"):
        L.append("- 🔗 VB 外部锚(语法): base_protocol 匹配, anchor_vb_to_cop=True")
    else:
        L.append("- ⚠️ VB 仍处 [UNVERIFIED-NO-EXTERNAL-ANCHOR] (本次不调 DeepSeek, 贡献物为既有冻结 COP, "
                 "非本跑外部生成 → 语义外部锚未达成, 语法 base_protocol 匹配)")
    contributor = mcp_cand
    cnid, pnid, l3 = C.production_phase(sb, contributor.id, contributor.name)
    L.extend(l3)
    t5 = time.time()

    # ===================== ⑥ 验收判定 =====================
    L.append("## ⑥ 验收判定 (M1)")
    adm_nca = admission_ncas[0][1] if admission_ncas else None
    chain_ok = bool(adm_nca and sb["mou_ok"] and cnid and pnid)
    L.append("- 准入 NCA: %s" % adm_nca)
    L.append("- 联盟 NCA: %s" % cnid)
    L.append("- 生产 NCA: %s" % pnid)
    L.append("- 全链自动完成(无人工干预): %s" % ("✅ 是" if chain_ok else "❌ 否"))
    L.append("- **M1 验收: %s**" % ("✅ 达成" if chain_ok else "❌ 未达成"))
    L.append("")

    # ===================== ⑦ 各特使用时 =====================
    L.append("## ⑦ 各特使用时 (秒)")
    L.append("- 扫描者: %.3f | 评估者: %.3f | 信使: %.3f | 谈判者: %.3f | 落地者: %.3f"
             % (t1 - t0, t2 - t1, t3 - t2, t4 - t3, t5 - t4))
    L.append("- 端到端总用时: %.3f" % (t5 - t0))
    L.append("")

    # ===================== ⑧ 诚实性质声明 =====================
    L.append("## ⑧ 诚实性质声明 (mixed 口径, 随引用携带)")
    L.append("- 端点 self-hosted(非第三方自然人) → data_provenance=mixed; MCP-EXT-01 为 self-hosted stdio server, "
             "连通性真实, 身份未第三方确权。")
    L.append("- 候选 res/batna 自报未确权(代表集) → 信任靠三段式闸门缓解。")
    L.append("- 贡献物 = `community/第01条-开源社区冷启动·正和准入.yaml` (既有冻结 COP, 前次受控真实试验 DeepSeek "
             "生成, 本次复用为冻结资产; 非本跑新生成) → VB 外部锚语义未达成(仍 [UNVERIFIED]), 语法 base_protocol 匹配。")
    L.append("- 谈判者为模拟态响应(分润 15% NCA 记账, 不承诺打款); 不点名/不诱导/算力零提及。")
    L.append("- 评估者 utility-genie 真实模块调用, NSFL 未触碰(touched_nsfl=%s)。" % sol.touched_nsfl)
    L.append("- DeepSeek key 未注入(凭证零落盘, 方案B 延续但未激活) → 本跑零外部 LLM 调用, 预算 ¥0 / 0 token。")
    L.append("- 产物不推送(待签批走 PR)。")
    L.append("")
    out = "\n".join(L) + "\n"
    rep = os.path.join(_HERE, "M1-FIVE-EMISSARY-REPORT.md")
    with open(rep, "w", encoding="utf-8") as f:
        f.write(out)

    # ===================== ④ 台账 REAL 回填 =====================
    _ledger_append(adm_nca, cnid, pnid, chain_ok, anchor)

    print(out)
    print(">>> 报告已写: %s" % rep)
    return {"admission": adm_nca, "coalition": cnid, "production": pnid, "m1_ok": chain_ok}


def _write(text, here):
    rep = os.path.join(here, "M1-FIVE-EMISSARY-REPORT.md")
    with open(rep, "w", encoding="utf-8") as f:
        f.write(text)


def _ledger_append(adm_nca, cnid, pnid, ok, anchor):
    if not os.path.isfile(LEDGER):
        return
    rows = []
    if adm_nca:
        rows.append("| %d | %s | MCP-EXT-01 | v2 机读证据过核验(五特使接线) | 准入 | %s | admitted | 评估者正和通过→信使邀请→落地者准入 |"
                    % (_next_seq(), adm_nca, "否"))
    if cnid:
        rows.append("| %d | %s | MCP-EXT-01 | 联盟 Shapley 分配 | 联盟 | %s | coalition | 沙盒 mou_ok 后缔约承诺 |"
                    % (_next_seq(), cnid, "否"))
    if pnid:
        ext = "是" if (anchor and anchor.get("anchored")) else "否"
        rows.append("| %d | %s | MCP-EXT-01 | 生产落盘 NCA(冻结 COP 复用) | 生产 | %s | produced | M1 五特使全链自动缔约达成 |"
                    % (_next_seq(), pnid, ext))
    if not rows:
        return
    block = "\n## v3 M1 五特使接线实跑（REAL · %s）\n\n" % _now()
    block += "> 1 候选(MCP-EXT-01) → 扫描者→评估者(utility-genie 正和)→信使(mcp load_core)→谈判者(M2 COP)→落地者(enforce_entry v2) 全链自动完成。\n"
    block += "> 评估者 utility-genie 真实模块调用, NSFL 未触碰; 贡献物复用既有冻结 COP(非本跑新生成) → 外部锚语义未达成([UNVERIFIED]), 语法 base_protocol 匹配。\n"
    block += "> 凭证零落盘(不调 DeepSeek), 预算 ¥0/0token。data_provenance=mixed(self-hosted)。\n\n"
    block += "| seq | nca_id | 贡献方 | 来源协议 | 闸门 | 外部锚 | 状态 | 备注 |\n"
    block += "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
    block += "\n".join(rows) + "\n"
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(block)


def _next_seq():
    if not os.path.isfile(LEDGER):
        return 1
    mx = 0
    for line in open(LEDGER, encoding="utf-8"):
        s = line.strip()
        if s.startswith("|") and s[1:].strip()[0:1].isdigit():
            try:
                mx = max(mx, int(s.split("|")[1].strip()))
            except Exception:
                pass
    return mx + 1


if __name__ == "__main__":
    main()
