# -*- coding: utf-8 -*-
"""TDCA 核心思维协议编译器 (生态基协议库, 强制加载门)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 本文件是"思维协议库"中 **TDCA 核心 (TDCA-Core)** 分支的编译入口。
与 兵法/博弈论/机制设计/场景 并列, 但本库是 **生态准入强制基协议**:
  - TDCA-CORE-20260815-01 生态准入与可信协作基协议 = MANDATORY (任何主体加入生态必须加载)
  - TDCA-CORE-20260815-02 可审计自主决策协议
  - TDCA-CORE-20260815-03 正和协作涌现协议
用户规则: "凡是加入 TDCA 生态, 必须加载 TDCA 思维协议" —— 由 manifest + enforce_entry.py 强制。

字段同构要求 (兼容 compose_general): 顶层 stratum 别名 = branch; 每原语含 steps。
"""
import os
import sys
import datetime
import hashlib

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "config"))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "nca-generator"))
sys.path.insert(0, os.path.join(_THIS, ".."))  # cognitive_compiler 根 (import cognitive_compiler as CC)
sys.path.insert(0, _THIS)

import tdca_config as TC
import cognitive_compiler as CC
import nca_generator as NCA

ensure_dirs = TC.ensure_dirs
NSFL_VERSION = TC.NSFL_VERSION
CORE_DIR = _THIS
ensure_dirs()
os.makedirs(CORE_DIR, exist_ok=True)

# ---------- TDCA 核心范式知识库 (dict 列表, 每范式自带调度骨架) ----------
# 字段: branch/idx/zh/en/pinyin/core/scene/primitives/decision/negative_space/skills/main_pipeline/graph
# primitives: 每原语 = dict(name, method, signature, precond, postcond, neg, steps)
CORE = [
    {
        "branch": "TDCA核心·生态准入与可信协作基协议",
        "idx": 1,
        "zh": "生态准入与可信协作基协议", "en": "Ecosystem Entry & Trusted Collaboration Base Protocol",
        "pinyin": "ecosystem_entry_base",
        "core": "TDCA 生态的准入与运行基协议 —— 任何主体加入生态必须加载本基协议。它确立四大可信支柱: "
                "认知资产确权(NCA)、负空间护栏(NSFL)、正和底线(MOU)、可审计自主决策; 并设生态准入门, "
                "未加载本基协议者不得在生态内协作/组合/比配。基协议即生态宪法。",
        "scene": "主体请求加入 TDCA 生态, 或在生态内发起协作/组合/比配",
        "primitives": [
            {"name": "nca_identity_attribution", "method": "认知资产确权(NCA)",
             "signature": "fn nca_identity_attribution(op) -> attributed_asset",
             "precond": "存在可执行的推理/决策/贡献操作",
             "postcond": "操作即确权, 每步生成不可篡改 NCA 权属链(可追溯/可回滚)",
             "neg": "无确权则贡献不可证、协作不可信",
             "steps": ["捕获操作", "生成NCA", "上链确权", "可审计追溯"]},
            {"name": "nsfl_guardrail", "method": "负空间护栏(NSFL)",
             "signature": "fn nsfl_guardrail(plan, redlines) -> guarded",
             "precond": "计划与认知安全/伦理/法律红线已知",
             "postcond": "越线即熔断, 在边界内渐进创新",
             "neg": "越 NSFL 认知安全/伦理/法律红线即熔断",
             "steps": ["标定红线", "预检", "越线熔断", "边界内放行"]},
            {"name": "mou_positive_sum_floor", "method": "正和底线(MOU)",
             "signature": "fn mou_positive_sum_floor(collab) -> positive_sum",
             "precond": "协作价值网络与参与者贡献可量化",
             "postcond": "协作须正和且经 TDCA 闭环结算(NCA/数字人民币DVP), 不得自建代币",
             "neg": "非正和或自建代币则拒",
             "steps": ["绘价值网络", "校验正和", "TDCA闭环结算"]},
            {"name": "auditable_decision_gate", "method": "可审计决策门",
             "signature": "fn auditable_decision_gate(trigger) -> gated_decision",
             "precond": "决策触发条件已知",
             "postcond": "决策经门控原语状态机, 全程可追溯可回滚",
             "neg": "无门控/无追溯则决策不可信",
             "steps": ["触发", "门控", "调度", "确权", "留痕"]},
            {"name": "trusted_collaboration_base", "method": "可信协作基",
             "signature": "fn trusted_collaboration_base(agents) -> trusted_alliance",
             "precond": "多主体接入 TDCA 可信基座(NCA/NSFL/MOU)",
             "postcond": "在可信基座之上形成可信协作",
             "neg": "脱离基座则协作无担保",
             "steps": ["接入基座", "确权", "护栏", "正和"]},
            {"name": "ecosystem_entry_gate", "method": "生态准入与协议加载门",
             "signature": "fn ecosystem_entry_gate(entity) -> admitted",
             "precond": "主体请求加入 TDCA 生态",
             "postcond": "已加载本基协议(TDCA-CORE-20260815-01)者准入, 否则拒绝协作/组合/比配",
             "neg": "未加载基协议则拒绝准入(强制)",
             "steps": ["验载基协议", "准入/拒", "发放生态身份"]},
        ],
        "decision": [
            {"if": "需确权操作", "call": "nca_identity_attribution"},
            {"if": "需守红线", "call": "nsfl_guardrail"},
            {"if": "需正和协作", "call": "mou_positive_sum_floor"},
            {"if": "需做决策", "call": "auditable_decision_gate"},
            {"if": "需多主体协作", "call": "trusted_collaboration_base"},
            {"if": "需加入生态", "call": "ecosystem_entry_gate"},
        ],
        "negative_space": [
            "⊗ 任何生态内协作/组合/比配必须先加载本基协议, 否则拒绝",
            "⊗ 决策须可审计(门控+留痕), 不可黑箱",
            "⊗ 越 NSFL 认知安全/伦理/法律红线即熔断",
            "⊗ 协作须正和且经 TDCA 闭环结算, 不得自建代币替代 NCA/数字人民币 DVP",
            "⊗ 认知资产须经 NCA 确权, 操作即确权",
        ],
        "skills": ["生态准入核验", "NCA确权自检", "NSFL预审", "MOU正和校验"],
        "main_pipeline": "nca_identity_attribution",
        "graph": [
            {"from": "nca_identity_attribution", "to": ["nsfl_guardrail", "mou_positive_sum_floor", "auditable_decision_gate"]},
            {"from": "auditable_decision_gate", "to": ["trusted_collaboration_base"]},
            {"from": "trusted_collaboration_base", "to": ["ecosystem_entry_gate"]},
            {"from": "nsfl_guardrail", "to": ["ecosystem_entry_gate"]},
            {"from": "mou_positive_sum_floor", "to": ["ecosystem_entry_gate"]},
        ],
    },
    {
        "branch": "TDCA核心·可审计自主决策",
        "idx": 2,
        "zh": "可审计自主决策协议", "en": "Auditable Autonomous Decision Protocol",
        "pinyin": "auditable_decision",
        "core": "把人类自主决策的原则编译为智能体可执行的门控决策协议: 决策门→原语状态机→下游skill调度→NCA确权"
                "→NSFL护栏→可回滚; 全程可追溯, 人类只需审计不必理解。这是 COP 作为'自主决策源泉层'的方法本体。",
        "scene": "智能体需在非黑箱前提下自主决策并承担责任",
        "primitives": [
            {"name": "decision_gate", "method": "决策门(必败不可战等)",
             "signature": "fn decision_gate(context) -> gate_verdict",
             "precond": "情境与决策门条件已知",
             "postcond": "触发门控给出 进/退/待 判定",
             "neg": "门条件缺失则误判",
             "steps": ["取情境", "对门", "判进/退/待"]},
            {"name": "primitive_state_machine", "method": "原语状态机",
             "signature": "fn primitive_state_machine(gate) -> plan",
             "precond": "门判定已知",
             "postcond": "按判定调度原语状态机生成方案",
             "neg": "状态跃迁非法则崩",
             "steps": ["入态", "迁态", "出方案"]},
            {"name": "skill_dispatch", "method": "下游skill调度",
             "signature": "fn skill_dispatch(plan) -> execution",
             "precond": "方案与原语就绪",
             "postcond": "调度下游 Skill(肌肉)执行",
             "neg": "调度越权则失控",
             "steps": ["选skill", "授权", "执行"]},
            {"name": "nca_attest", "method": "NCA确权留痕",
             "signature": "fn nca_attest(step) -> attested",
             "precond": "每步执行",
             "postcond": "每步生成 NCA 权属链",
             "neg": "无确权则不可审计",
             "steps": ["捕获", "确权", "链"]},
            {"name": "nsfl_fuse", "method": "NSFL熔断",
             "signature": "fn nsfl_fuse(plan) -> fused",
             "precond": "计划与红线",
             "postcond": "越线熔断",
             "neg": "越线不熔断则破底线",
             "steps": ["预检", "熔断/放行"]},
            {"name": "rollback", "method": "可回滚",
             "signature": "fn rollback(decision) -> rolled_back",
             "precond": "决策有 NCA 链",
             "postcond": "可经 NCA 链回滚到任一历史态",
             "neg": "无链则不可回",
             "steps": ["定位", "回滚", "复证"]},
        ],
        "decision": [
            {"if": "需门控判定", "call": "decision_gate"},
            {"if": "需生成方案", "call": "primitive_state_machine"},
            {"if": "需执行", "call": "skill_dispatch"},
            {"if": "需确权", "call": "nca_attest"},
            {"if": "需守红线", "call": "nsfl_fuse"},
            {"if": "需回滚", "call": "rollback"},
        ],
        "negative_space": [
            "⊗ 决策必须经门控, 黑箱决策不可信",
            "⊗ 状态机跃迁须合法, 非法跃迁致崩",
            "⊗ 调度 skill 不得越权",
            "⊗ 每步须 NCA 确权, 否则不可审计",
            "⊗ 越 NSFL 即熔断, 不可放行",
        ],
        "skills": ["决策门配置", "原语状态机编排", "NSFL熔断配置"],
        "main_pipeline": "decision_gate",
        "graph": [
            {"from": "decision_gate", "to": ["primitive_state_machine"]},
            {"from": "primitive_state_machine", "to": ["skill_dispatch"]},
            {"from": "skill_dispatch", "to": ["nca_attest", "nsfl_fuse"]},
            {"from": "nca_attest", "to": ["rollback"]},
            {"from": "nsfl_fuse", "to": ["rollback"]},
        ],
    },
    {
        "branch": "TDCA核心·正和协作涌现",
        "idx": 3,
        "zh": "正和协作涌现协议", "en": "Positive-Sum Collaboration Emergence Protocol",
        "pinyin": "positive_sum_emergence",
        "core": "把多主体正和协作编译为可计算涌现协议: 互补识别→缺口量化→正和增益→稳定联盟→夏普利分成→MOU校验→DVP结算; "
                "经 TDCA 闭环使共赢为可审计默认解。这是搜索比配引擎的协作方法论本体。",
        "scene": "多主体欲在 TDCA 生态内形成正和稳定联盟",
        "primitives": [
            {"name": "complement_identify", "method": "互补识别",
             "signature": "fn complement_identify(agents, need) -> complements",
             "precond": "主体能力与需求已知",
             "postcond": "识别互补缺口",
             "neg": "误判互补则错配",
             "steps": ["列能力", "对需求", "标互补"]},
            {"name": "gap_quantify", "method": "缺口量化",
             "signature": "fn gap_quantify(need, cover) -> gaps",
             "precond": "需求与覆盖",
             "postcond": "量化每维缺口与覆盖强度",
             "neg": "量错则比配失真",
             "steps": ["量化覆盖", "标缺口"]},
            {"name": "positive_gain", "method": "正和增益",
             "signature": "fn positive_gain(alliance) -> gain",
             "precond": "联盟互补",
             "postcond": "算协同正和增益",
             "neg": "非正和则弃",
             "steps": ["算协同", "验正和"]},
            {"name": "stable_coalition", "method": "稳定联盟撮合",
             "signature": "fn stable_coalition(cands) -> coalition",
             "precond": "候选与缺口",
             "postcond": "撮合稳定联盟(各方≥BATNA)",
             "neg": "不稳则散",
             "steps": ["枚举", "稳检", "成盟"]},
            {"name": "shapley_share", "method": "夏普利分成",
             "signature": "fn shapley_share(coalition) -> shares",
             "precond": "联盟价值",
             "postcond": "按边际贡献公平分成(满足效率/对称/加法公理)",
             "neg": "不公则叛",
             "steps": ["算边际", "分"]},
            {"name": "mou_dvp_settle", "method": "MOU校验与DVP结算",
             "signature": "fn mou_dvp_settle(shares) -> settled",
             "precond": "分成",
             "postcond": "经 MOU 正和校验 + 数字人民币 DVP 闭环结算(NCA确权)",
             "neg": "非正和或绕开DVP则拒",
             "steps": ["MOU校验", "DVP", "NCA确权"]},
        ],
        "decision": [
            {"if": "需识别互补", "call": "complement_identify"},
            {"if": "需量化缺口", "call": "gap_quantify"},
            {"if": "需算增益", "call": "positive_gain"},
            {"if": "需撮合联盟", "call": "stable_coalition"},
            {"if": "需公平分成", "call": "shapley_share"},
            {"if": "需结算", "call": "mou_dvp_settle"},
        ],
        "negative_space": [
            "⊗ 比配须基于真实互补, 误判则错配",
            "⊗ 增益须正和, 非正和联盟弃",
            "⊗ 联盟须稳定(各方≥BATNA), 否则散",
            "⊗ 分成须满足夏普利公理, 不公则叛",
            "⊗ 结算须经 MOU 校验 + 数字人民币 DVP, 不得绕开",
        ],
        "skills": ["互补扫描矩阵", "缺口量化器", "稳定联盟撮合器", "夏普利分成器"],
        "main_pipeline": "complement_identify",
        "graph": [
            {"from": "complement_identify", "to": ["gap_quantify"]},
            {"from": "gap_quantify", "to": ["positive_gain"]},
            {"from": "positive_gain", "to": ["stable_coalition"]},
            {"from": "stable_coalition", "to": ["shapley_share"]},
            {"from": "shapley_share", "to": ["mou_dvp_settle"]},
        ],
    },
]


def assemble_one(g):
    """S2-S4: 将单范式编译为 COP (对齐麦肯锡 COP schema 多原语形态)"""
    cop_primitives = []
    for p in g["primitives"]:
        cop_primitives.append({
            "name": p["name"],
            "method": p["method"],
            "signature": p["signature"],
            "precond": p["precond"],
            "postcond": p["postcond"],
            "negative_space": "⊗ " + p["neg"],
            "steps": p.get("steps", [p["method"]]),
            "nca_emit": True,
        })
    cop = {
        "COP-ID": "TDCA-CORE-20260815-%02d" % g["idx"],
        "source_expert": "tdca_core_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": g["branch"],
        "stratum": g["branch"],  # 顶层 stratum 别名, 兼容组合解析器字段约定
        "soul": {
            "identity": "%s (%s)" % (g["zh"], g["en"]),
            "core": g["core"],
            "role": "思维协议 (TDCA核心范式类)",
            "category": "TDCA核心 / " + g["branch"],
        },
        "primitives": cop_primitives,
        "dispatch": {
            "main_pipeline": g["main_pipeline"],
            "graph": g["graph"],
            "note": "TDCA 核心协议自带调度骨架",
        },
        "decision": g["decision"],
        "skills": g.get("skills", []),
        "negative_space": g["negative_space"],
        "nsfl_version": NSFL_VERSION,
    }
    CC.s5_validate(cop)
    return cop, g["pinyin"]


def compile_all():
    report = {"total": len(CORE), "ok": 0, "skip": 0, "fail": 0,
              "cop_ids": [], "nca_ids": []}
    for g in CORE:
        idx = g["idx"]
        fname = "第%02d核心-%s.yaml" % (idx, g["zh"])
        out_path = os.path.join(CORE_DIR, fname)
        if os.path.exists(out_path):
            print("[SKIP] %s 已存在, 跳过 (不重复发射 NCA)" % fname)
            report["skip"] += 1
            continue
        try:
            cop, pinyin = assemble_one(g)
            CC._dump_yaml(cop, out_path)
            h = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
            sz = os.path.getsize(out_path)
            nid, _, _ = NCA.generate_nca(
                operation_type="CodeGen",
                scope=".tdca-protocol/cognitive-compiler/tdca_core (第%02d核心-%s COP)" % (idx, g["zh"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-TDCACORE-%02d" % idx,
                notes="TDCA 核心思维协议 %s (%s) 编译为 COP, 验证=%s" % (g["zh"], g["en"], cop["validation"]["passed"]),
            )
            report["ok"] += 1
            report["cop_ids"].append(cop["COP-ID"])
            report["nca_ids"].append(nid)
            print("[OK] %s -> %s | 原语 %d | 验证 %s" % (cop["COP-ID"], fname, len(cop["primitives"]), cop["validation"]["passed"]))
        except Exception as e:
            report["fail"] += 1
            print("[FAIL] 第%02d核心-%s: %s" % (idx, g["zh"], e))
    return report


if __name__ == "__main__":
    print("===== TDCA 核心思维协议编译 (MEMO-006 规范, 生态基协议库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % CORE_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    print("强制基协议: TDCA-CORE-20260815-01 (凡是加入TDCA生态必须加载)")
    print("===== 编译完成 =====")
