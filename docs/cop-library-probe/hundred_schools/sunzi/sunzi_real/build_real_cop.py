# -*- coding: utf-8 -*-
"""真实执行: 编译《孙子兵法·计篇》real COP 并确权发射 NCA
执行体: 编译推理算力云 (subagent)
复用: cognitive_compiler.s5_validate ; nca_generator.generate_nca
"""
import os
import sys
import datetime
import hashlib

_THIS = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_THIS, "..", "..", "..", ".."))  # .tdca-protocol
sys.path.insert(0, os.path.join(_ROOT, "config"))
sys.path.insert(0, os.path.join(_ROOT, "nca-generator"))
sys.path.insert(0, os.path.join(_ROOT, "cognitive-compiler"))

import cognitive_compiler as CC
import nca_generator as NCA

SZ_REAL_DIR = _THIS
OUT_PATH = os.path.join(SZ_REAL_DIR, "第01篇-计篇-real.yaml")
COP_ID = "SUNZI-REAL-20260815-01"

# ---------- 真实 NLP 抽取结果 (中文语义与情报NLP所 · zh-nlp MCP · jieba 实算) ----------
nlp = {
    "proper": ["孙子", "兵者", "大事", "死生", "道者", "令民", "天者", "阴阳", "寒暑", "时制",
               "地者", "将者", "智信仁", "法者", "曲制", "官道", "主用", "诡道", "故能"],
    "classical_tokens": ["孙子", "兵者", "国", "大事", "死生", "事", "校", "情", "道者", "令民",
                         "天者", "阴阳", "寒暑", "时制", "地者", "将者", "智信仁", "法者",
                         "曲制", "官道", "主用", "诡道", "故能"],
    "keywords": ["兵者", "国之", "故经", "以五事", "校之以计", "而索", "其情", "五曰法", "道者", "令民"],
}

# ---------- S2-S4: 组装 COP (严格沿用 第01篇-计篇.yaml 字段结构, 内容来自真实产出) ----------
verse = ("兵者，国之大事，死生之地，存亡之道，不可不察也。故经之以五事，校之以计，而索其情："
         "一曰道，二曰天，三曰地，四曰将，五曰法。")

cop = {
    "COP-ID": COP_ID,
    "source_expert": "sunzi_canonical",
    "compiler": "编译推理算力云 (TDCA 编译推理算力云 · 真实校验执行)",
    "compiled_at": datetime.datetime.now().isoformat(),
    "branch": "诸子百家·兵家·孙子兵法·第01篇(计篇)",
    "stratum": "诸子百家·兵家·孙子兵法·战略筹划",
    "soul": {
        "identity": "孙子兵法·第01篇《计篇》",
        "core": ("庙算决胜——以五事(道天地将法)七计系统性评估胜负前提，先算后战，"
                 "多算胜少算不胜。"),
        "verse": verse,
        "role": "思维协议 (诸子百家 / 兵家 / 孙子兵法)",
        "category": "诸子百家 / 兵家 / 孙子兵法 / 战略筹划",
        "base_protocol": "TDCA-CORE-20260815-01",
        "nca_id": None,  # 由 generate_nca 回填
    },
    "primitives": [
        {
            "name": "jing_xiao_wu_shi_qi_ji",
            "method": "计篇·经校五事七计(庙算)",
            "signature": "fn jing_xiao_wu_shi_qi_ji(我方态势, 敌方态势) -> 胜负情实 -> 战/不战",
            "precond": "文本确证（训诂院定本 + 校记）、战端未启、情势不明",
            "postcond": ("五事七计既明，导出作战企图；若庙算不胜，转入'先为不可胜'蓄势"),
            "negative_space": "⊗ 不察而战则盲",
            "steps": [
                "经之以五事",
                "校之以七计",
                "而索其情",
                "庙算胜则战，不胜则不战",
            ],
            "nca_emit": True,
        }
    ],
    "dispatch": {
        "main_pipeline": "jing_xiao_wu_shi_qi_ji",
        "trigger": verse,
        "when": "当重大决策前宜先系统评估胜负前提时触发",
        "graph": [{"from": "jing_xiao_wu_shi_qi_ji", "to": []}],
    },
    "decision": [
        {"if": "我方得算 > 敌方", "call": "jing_xiao_wu_shi_qi_ji", "action": "可战（先胜后战）"},
        {"if": "势均", "call": "jing_xiao_wu_shi_qi_ji", "action": "伐谋/伐交优先，慎战"},
        {"if": "我方得算 < 敌方", "call": "jing_xiao_wu_shi_qi_ji", "action": "不战，先为不可胜（蓄势待变）"},
    ],
    "skills": ["计篇·顺势研判"],
    "negative_space": [
        "⊗ 不察而战：未行五事七计庙算即开战，违'不可不察'",
        "⊗ 以诡道为正道：混淆'政治正道(令民与上同意)'与'用兵权道(诡道)'，二道不可互替",
        "⊗ 庙算未胜而浪战：得算少/无算仍决战，直接否定篇旨",
        "⊗ 五事七计失真：比较所依信息(道/将/法等)造假或被欺，庙算前提崩塌",
        "⊗ 诡道溢出：权变用于政治正道领域(欺民/违盟)，越出战术负空间",
        "⊗ 本章协议须以 TDCA-CORE-20260815-01 为可信底座: 合作/组合/比配前须加载生态准入基协议",
    ],
    "nsfl_version": "V0.1",
    # 新增: 真实协作溯源 (不造假)
    "attribution": {
        "lead_compiler": "兵学战略研究院",
        "contributors": [
            {"name": "古籍训诂与文本校勘院", "resource_type": "expert",
             "expert_id": "guji-philology", "output": "计篇_训诂校勘.md"},
            {"name": "中文语义与情报NLP所", "resource_type": "mcp_connector",
             "server": "zh-nlp", "output": "proper/classical_tokens/keywords (jieba 实算)"},
            {"name": "编译推理算力云", "resource_type": "subagent",
             "output": "本 yaml 编译校验"},
            {"name": "智能系统建模实验室", "resource_type": "candidate_role",
             "note": "联盟互补方，未独立产出本篇内容"},
            {"name": "知识图谱与态势感知中心", "resource_type": "candidate_role",
             "note": "联盟互补方，未独立产出本篇内容"},
            {"name": "合规与可信决策审计院", "resource_type": "candidate_role",
             "note": "联盟互补方，未独立产出本篇内容"},
        ],
        "coalition_nca": None,  # 占位, 由后续编排器发射后回填
        "admission_core": "TDCA-CORE-20260815-01",
    },
    # 新增: 真实 NLP 抽取字段
    "nlp": nlp,
}

# ---------- S5: schema 校验 (复用 cognitive_compiler.s5_validate) ----------
CC.s5_validate(cop)
print("[S5] validation passed =", cop["validation"]["passed"], "| issues =", cop["validation"]["issues"])

# ---------- 落盘 (顶部注释 + YAML) ----------
header = (
    "# 本 COP 由真实多 agent 协作编译:\n"
    "#   兵学战略研究院(蒸馏主agent) + 古籍训诂与文本校勘院(校勘) + "
    "中文语义与情报NLP所(zh-nlp 连接器 jieba 实算) + 编译推理算力云(校验确权)\n"
    "#   内容取自 sunzi_real/ 上游真实产出, 非说明文档。\n"
)
body = CC.s5_validate.__module__  # noqa  (占位, 不使用)
import yaml
body = yaml.safe_dump(cop, allow_unicode=True, sort_keys=False)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(header)
    f.write(body)
print("[DUMP] %s" % OUT_PATH)

# ---------- 确权: 真实发射 NCA (参照 compile_sunzi.py 调用方式) ----------
h = hashlib.sha256(open(OUT_PATH, "rb").read()).hexdigest()
sz = os.path.getsize(OUT_PATH)
nid, npath, _ = NCA.generate_nca(
    operation_type="CodeGen",
    scope=".tdca-protocol/cognitive-compiler/hundred_schools/sunzi/sunzi_real (第01篇-计篇-real COP)",
    pre_state={"path": OUT_PATH, "hash": None, "size": 0, "exists": False, "backup": None},
    post_state={"path": OUT_PATH, "hash": h, "size": sz, "exists": True, "backup": None},
    function_call_id="TDCA-FC-SZI-REAL-01",
    notes="孙子兵法第01篇《计篇》real COP 编译校验, 验证=%s, attribution=兵学战略研究院等" % cop["validation"]["passed"],
)
print("[NCA] emitted id =", nid, "| path =", npath)

# ---------- 回填 nca_id 并重写 ----------
cop["soul"]["nca_id"] = nid
body2 = yaml.safe_dump(cop, allow_unicode=True, sort_keys=False)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(header)
    f.write(body2)

print("===== 完成 =====")
print("validation_passed:", cop["validation"]["passed"])
print("nca_id:", nid)
print("yaml_path:", OUT_PATH)
