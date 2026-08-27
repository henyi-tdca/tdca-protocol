# -*- coding: utf-8 -*-
"""M3b 联盟组建演示 (GSEQ-0546)
=========================================================
组织者(CA-00) + N=2 代表集候选(CA-01 协议编译器手 / CA-02 高校NLP实验室agent)
自主组建多边协作联盟并准入。复用 v3 M1 机制(零新核心逻辑):
  - 多候选并行准入: enforce_entry v2 (loaded_core=true → EcosystemAdmit)
  - 联盟组建: form_coalition 多方 φ≥BATNA + shapley 分配
  - 联盟级生产: 多成员 CoalitionCommit NCA + COPCompile NCA + 贡献物联盟归属

纪律(同动作1护栏): 预算 ¥100 余额内 | ≤2 条/周/目标 | 拒绝零容忍转向 |
mixed 口径 | 凭证零落盘 | NCA 走 generate_nca(max+1, GSEQ-0551) | NSFL 先于一切。
"""
import os
import sys
import json
import time
import datetime
import yaml

REPO = r"C:/Users/22850/Desktop/开发会话文件/tdca-protocol"
_CC = os.path.join(REPO, "docs", "cognitive-compiler")
_HERE = os.path.join(_CC, "coldstart")
_SIM = os.path.join(_CC, "simulations", "multilateral_search_match")

for p in (_CC, _SIM, os.path.join(REPO, "config"), os.path.join(REPO, "nca-generator")):
    if p not in sys.path:
        sys.path.insert(0, p)

import run_coldstart_threephase as C
from tdca_core import enforce_entry as EE
import nca_generator as NCA
from providers.base import Candidate

LEDGER = os.path.join(REPO, "..", "..", ".tdca-nca", "NCA-COMMUNITY-台账.md")
DIMS = C.DIMS


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_candidates():
    with open(os.path.join(_HERE, "coldstart_candidates.json"), encoding="utf-8") as f:
        d = json.load(f)
    org = d["organizer"]
    organizer = Candidate(id=org["id"], name=org["name"], cop=org["cop"],
                          res=org["res"], batna=org["batna"], source="organizer")
    cands = {c["id"]: c for c in d["candidates"]}
    return organizer, cands


def _write_coalition_cop(path, organizer, members, sb):
    """联盟级贡献 COP(六要素 + 多成员归属), yaml.safe_dump 避免格式事故。"""
    member_block = []
    for m in members:
        ph = sb["phi"].get(m.id)
        member_block.append({
            "id": m.id,
            "name": m.name,
            "resource_type": m.source,
            "shapley_phi": round(ph, 2) if ph is not None else None,
            "batna": m.batna,
        })
    cop = {
        "stratum": "多边联盟贡献",
        "verse": "众智所成，功归其分；联盟共担，正和可续。",
        "core": ("组织者(%s)与 %d 名代表集成员(%s)自主组建协作联盟: 以 TDCA 开源社区冷启动·"
                 "正和准入为共同目标, 成员按能力维度贡献(范式编译/工程实现/文档教程/NLP 等), "
                 "贡献与收益分配由六要素约束, 全程 NCA 可审计。"
                 % (organizer.name, len(members), "、".join(m.name for m in members))),
        "origin": "TDCA-COALITION-AUTO-001（M3b 联盟组建演示 GSEQ-0546）| 实例化: 多边联盟 CA-01+CA-02",
        "coalition": {
            "organizer": {"id": organizer.id, "name": organizer.name},
            "members": member_block,
            "member_count": len(members),
            "formed_at": _now(),
        },
        "negative_space": [
            "不得违反数据合规（隐私/伦理/授权范围）",
            "不得剽窃或冒名署名",
            "不得单方越权使用联盟资源",
            "不得转向零和掠夺(NSFL 熔断)",
        ],
        "primitive": "fn form_coalition(organizer, members) -> CoalitionCommit",
        "soul": {"base_protocol": "TDCA-CORE-20260815-01"},
        "dispatch": "多边联盟组建 / 多代表集候选并行准入时触发",
        "decision": (
            "目标函数: max(正和协作产出 | 主题=TDCA 开源社区冷启动)\n"
            "约束矩阵: [数据合规] [署名规则: 贡献者署名] [授权: 联盟内共享]\n"
            "配置权边界: 资源仅限联盟目标使用; 成果归属按贡献确权\n"
            "预期分配: Shapley 按贡献分配署名/收益(模拟态 NCA 记账)\n"
            "审计轨迹: 每阶段产出 NCA 落链(准入/联盟/生产)\n"
            "if 任一方 φ<BATNA: -> BATNA 存疑熔断(禁止生产)\n"
        ),
        "topic": "联盟模板 · 多边联盟组建(M3b)",
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cop, f, allow_unicode=True, sort_keys=False)
    return cop


def main():
    L = []
    L.append("# M3b 联盟组建演示报告 (GSEQ-0546 · 多边联盟 · N=2 代表集成员)")
    L.append("> 生成时间: %s" % _now())
    L.append("> 复用 v3 M1 机制(零新核心逻辑): 准入=enforce_entry v2 | 联盟=form_coalition+shapley | 生产=generate_nca(max+1)")
    L.append("> 纪律: mixed 口径 | 分润模拟态 | 凭证零落盘 | NSFL 先于一切 | 预算 ¥100 余额内 | 产物不推送")
    L.append("")

    t0 = time.time()
    organizer, cands = _load_candidates()

    # ============ 多候选并行准入 ============
    L.append("## 1. 多候选并行准入 (Admission · v2, loaded_core=true → EcosystemAdmit)")
    member_ids = ["CA-01", "CA-02"]  # N=2 代表集成员, 均 loaded_core=true
    members = []
    for mid in member_ids:
        c = cands[mid]
        members.append(Candidate(id=c["id"], name=c["name"], cop=c.get("cop", ""),
                                  res=c["res"], batna=c["batna"], source="coldstart"))
    C._RAW_CAND = {mid: {"loaded_core": cands[mid]["loaded_core"]} for mid in cands}
    admitted, rejected, admission_ncas, l1 = C.admission_phase(organizer, members)
    L.extend(l1)
    L.append("")
    if len(admitted) < 2:
        L.append("⛔ 准入成员不足 2, M3b 未达成")
        _write("\n".join(L) + "\n", _HERE)
        return None
    t1 = time.time()

    # ============ 联盟组建(沙盒, 只算不写) ============
    L.append("## 2. 联盟组建 (Coalition · form_coalition 多方 φ≥BATNA + shapley, 只算不写)")
    sb, l2 = C.sandbox_phase(organizer, admitted)
    L.extend(l2)
    L.append("- 联盟成员数(不含组织者): %d (≥2 ✅)" % len(admitted))
    if not sb["mou_ok"]:
        L.append("⛔ 沙盒 MOU 不可行, 禁止生产")
        _write("\n".join(L) + "\n", _HERE)
        return None
    t2 = time.time()

    # ============ 联盟级生产(贡献物联盟归属) ============
    L.append("")
    L.append("## 3. 联盟级生产 (Production · 多成员 CoalitionCommit + COPCompile + 贡献物联盟归属)")
    cop_path = os.path.join(_HERE, "community", "M3B-联盟贡献COP.yaml")
    _write_coalition_cop(cop_path, organizer, admitted, sb)
    anchor = EE.anchor_vb_to_cop(cop_path)
    if anchor and anchor.get("anchored"):
        L.append("- 🔗 VB 外部锚达成: base_protocol 匹配, anchored=True")
    else:
        L.append("- ⚠️ VB 仍处 [UNVERIFIED-NO-EXTERNAL-ANCHOR] (贡献物非 DeepSeek 实时生成语义锚未达成, 语法 base_protocol 匹配)")

    # 多成员 CoalitionCommit NCA(记录全部成员)
    member_ids_real = [m.id for m in admitted]
    cnid, _, _ = NCA.generate_nca(
        operation_type="CoalitionCommit",
        scope=".tdca-protocol/cognitive-compiler/coldstart (M3b 多边联盟承诺, %d 成员)" % len(admitted),
        pre_state={"path": None, "hash": None, "size": 0, "exists": False, "backup": None},
        post_state={"path": None, "hash": None, "size": 0, "exists": True, "backup": None},
        function_call_id="TDCA-FC-M3B-COALITION",
        notes=("M3b 多边联盟承诺: 组织者=%s + 成员=%s (共 %d 成员, ≥2 ✅); "
               "data_provenance=mixed(候选res/batna自报未确权); "
               "沙盒 MOU 正和可行(V=%s, VB=%.1f, φ≥BATNA 全满足)后正式联盟承诺"
               % (organizer.id, "+".join(member_ids_real), len(admitted), sb["V"], sb["vb"])),
    )
    # 联盟级生产确权 NCA(贡献物联盟归属)
    pnid, _, _ = NCA.generate_nca(
        operation_type="COPCompile",
        scope=".tdca-protocol/cognitive-compiler/coldstart/community/M3B-联盟贡献COP.yaml (联盟级贡献物, 多成员归属)",
        pre_state={"path": None, "hash": None, "size": 0, "exists": False, "backup": None},
        post_state={"path": "community/M3B-联盟贡献COP.yaml", "hash": None,
                    "size": 0, "exists": True, "backup": None},
        function_call_id="TDCA-FC-M3B-PROD",
        notes="M3b 沙盒(mou_ok=True)通过后, 多边联盟(%s)交付联盟级贡献 COP, 归属联盟全体成员, 关联联盟 %s"
              % ("+".join(member_ids_real), cnid),
    )
    L.append("- 准入 NCA(成员): %s" % ", ".join("%s→%s" % (i, n) for i, n in admission_ncas))
    L.append("- 多成员联盟 NCA(CoalitionCommit): `%s` (成员数=%d)" % (cnid, len(admitted)))
    L.append("- 联盟级生产 NCA(COPCompile): `%s`" % pnid)
    L.append("- 贡献物(联盟归属): `%s`" % cop_path)
    t3 = time.time()

    # ============ 验收判定 ============
    L.append("")
    L.append("## 4. 验收判定 (M3b)")
    L.append("- 多成员联盟 NCA 落链(≥2 成员): ✅ (%d 成员, CoalitionCommit `%s`)" % (len(admitted), cnid))
    L.append("- 贡献物联盟归属: ✅ (%s 多成员归属字段)" % cop_path)
    L.append("- mixed 标注: ✅ (data_provenance=mixed, 自报 res/batna 未确权)")
    L.append("- **M3b 验收: ✅ 达成**")
    L.append("")
    L.append("## 5. 诚实性质声明")
    L.append("- 机制全真实: enforce_entry v2 / form_coalition / shapley / nca_generator 均平台真实代码实跑。")
    L.append("- 候选 res/batna 自报未确权(代表集) → data_provenance=mixed; VB 无外部锚标 [UNVERIFIED]。")
    L.append("- 分润模拟态(NCA 记账, 不承诺打款); 凭证零落盘(未调 DeepSeek, 预算 ¥0/0token)。")
    L.append("- NSFL 未触碰(沙盒无 φ<BATNA 触发熔断)。")
    L.append("- 产物不推送(待签批走 PR)。")

    out = "\n".join(L) + "\n"
    rep = os.path.join(_HERE, "M3B-COALITION-REPORT.md")
    with open(rep, "w", encoding="utf-8") as f:
        f.write(out)

    # 台账 REAL 回填
    _ledger_append(admission_ncas, cnid, pnid, sb, anchor)

    print(out)
    print(">>> 报告已写: %s" % rep)
    return {"admission": admission_ncas, "coalition": cnid, "production": pnid,
            "members": len(admitted), "m3b_ok": True}


def _write(text, here):
    rep = os.path.join(here, "M3B-COALITION-REPORT.md")
    with open(rep, "w", encoding="utf-8") as f:
        f.write(text)


def _ledger_append(admission_ncas, cnid, pnid, sb, anchor):
    if not os.path.isfile(LEDGER):
        return
    rows = []
    for i, n in admission_ncas:
        rows.append("| %d | %s | %s | v2 机读证据过核验(loaded_core=true) | 准入 | 否 | admitted | M3b 多候选并行准入 |"
                    % (_next_seq(), n, i))
    rows.append("| %d | %s | CA-01+CA-02 | 多边联盟 Shapley 分配(%d 成员) | 联盟 | 否 | coalition | 沙盒 mou_ok 后多边联盟承诺 |"
                % (_next_seq(), cnid, len(admission_ncas)))
    ext = "是" if (anchor and anchor.get("anchored")) else "否"
    rows.append("| %d | %s | CA-01+CA-02 | 联盟级生产落盘 NCA(贡献物联盟归属) | 生产 | %s | produced | M3b 多边联盟组建达成 |"
                % (_next_seq(), pnid, ext))
    block = "\n## M3b 联盟组建演示（REAL · %s）\n\n" % _now()
    block += "> 组织者 CA-00 + N=2 代表集成员(CA-01 协议编译器手 / CA-02 高校NLP实验室agent) 自主组建多边联盟并准入。\n"
    block += "> 复用 v3 M1 机制: 准入 enforce_entry v2 → 联盟 form_coalition+shapley(只算不写) → 生产 多成员 CoalitionCommit+COPCompile。\n"
    block += "> data_provenance=mixed(自报 res/batna 未确权); VB 外部锚=%s([UNVERIFIED]); 凭证零落盘(预算 ¥0/0token)。\n\n" % ext
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
        if s.startswith("|") and s[1:].strip() and s[1:].strip()[0:1].isdigit():
            try:
                mx = max(mx, int(s.split("|")[1].strip()))
            except Exception:
                pass
    return mx + 1


if __name__ == "__main__":
    main()
