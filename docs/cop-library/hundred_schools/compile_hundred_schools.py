# -*- coding: utf-8 -*-
"""诸子百家思维协议编译器 (中文化合基库)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 本文件是"思维协议库"中 **诸子百家 (Hundred Schools / 中国文化)** 分支的编译入口。
与 TDCA核心 / 兵法 / 博弈论 / 机制设计 / 场景 并列, 但本库是 **中文化合基库**:
  - 道德经 (道家) = 首个 operand, 后续作 "中国文化 ⊕ 辩证实践方法论" 化合的中方基协议
  - 预留儒家/墨家/法家/名家/兵家(互补)/阴阳家 等同构 slot
战略: 凡加入 TDCA 生态须先加载 TDCA-CORE-20260815-01 (生态准入基协议, 强制门);
      本库 COP 在其之上化合, 自身亦须以该基协议为可信底座。

字段同构要求 (兼容 compose_general): 顶层 stratum 别名 = branch; 每原语含 steps。
"""
import os
import sys
import datetime
import hashlib

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "config"))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "nca-generator"))
sys.path.insert(0, os.path.join(_THIS, ".."))  # cognitive_compiler 根
sys.path.insert(0, _THIS)

import tdca_config as TC
import cognitive_compiler as CC
import nca_generator as NCA

ensure_dirs = TC.ensure_dirs
NSFL_VERSION = TC.NSFL_VERSION
HS_DIR = _THIS
ensure_dirs()
os.makedirs(HS_DIR, exist_ok=True)

# ---------- 诸子百家范式知识库 (dict 列表, 每范式自带调度骨架) ----------
# 字段: cop_id/branch/idx/zh/en/pinyin/core/scene/primitives/decision/negative_space/skills/main_pipeline/graph
# primitives: 每原语 = dict(name, method, signature, precond, postcond, neg, steps)
HS = [
    {
        "cop_id": "HS-DAO-20260815-01",
        "branch": "诸子百家·道家·道德经",
        "idx": 1,
        "zh": "道德经 (道家根本经典)", "en": "Tao Te Ching (Daoist Foundational Canon)",
        "pinyin": "daodejing",
        "core": "《道德经》是人类'顺势·辩证·守弱·不争'智慧的范式化: 以'道'为万物根源与运行规律, "
                "提炼八大纲维思维——道法自然(顺应规律)、无为而治(不妄为/让系统自组织)、反者道之动(物极必反/"
                "对立转化)、柔弱胜刚强(守弱蓄势)、祸福相依(辩证损益)、上善若水(处下不争利他)、治大国若烹小鲜"
                "(轻扰动稳序)、见素抱朴(删繁归本)。它是'中文化合基库'首个 operand, 后续可作'中国文化 ⊕ 辩证实践方法论'"
                "化合的中方基协议; 本协议须以 TDCA-CORE-20260815-01 (生态准入基协议) 为可信底座, 经 NCA 确权、"
                "受 NSFL 护栏、依 MOU 正和底线运行。",
        "scene": "主体面对复杂系统治理/战略抉择/协作博弈, 需以'顺势辩证守弱不争'思维范式求解",
        "primitives": [
            {"name": "dao_fa_zi_ran", "method": "道法自然·顺应规律",
             "signature": "fn dao_fa_zi_ran(context) -> aligned_action",
             "precond": "情境与系统根本规律可观察",
             "postcond": "行动顺应'道'(根本规律), 不强为、不逆势",
             "neg": "逆规律妄为则败",
             "steps": ["观大势", "识道律", "顺因循理", "不强为"]},
            {"name": "wu_wei", "method": "无为而治·不妄为",
             "signature": "fn wu_wei(system) -> self_organized",
             "precond": "系统具备自组织能力",
             "postcond": "少干预、定方向放权, 让系统自组织达成目标",
             "neg": "过度干预则扰序",
             "steps": ["定方向", "简政放权", "不代庖", "观自组织"]},
            {"name": "fan_zhe_dao_zhi_dong", "method": "反者道之动·物极必反",
             "signature": "fn fan_zhe_dao_zhi_dong(trend) -> reversal_alert",
             "precond": "事物发展趋势已知",
             "postcond": "识别循环往复/盛极而衰, 提前预警并备反",
             "neg": "忽视对立转化则临危",
             "steps": ["察势", "判极", "预警转化", "备反制"]},
            {"name": "rou_ruo_sheng_gang_qiang", "method": "柔弱胜刚强·守弱",
             "signature": "fn rou_ruo_sheng_gang_qiang(force) -> soft_win",
             "precond": "存在对抗/竞争态势",
             "postcond": "居下守柔、蓄势待发, 以柔克刚",
             "neg": "逞强则折",
             "steps": ["守弱", "处下", "蓄势", "克刚"]},
            {"name": "huo_fu_xiang_yi", "method": "祸福相依·辩证风险",
             "signature": "fn huo_fu_xiang_yi(event) -> bifocal_view",
             "precond": "事件已定性(祸或福)",
             "postcond": "见祸中之福、福中之祸, 辩证权衡损益",
             "neg": "偏执一端则盲",
             "steps": ["定事件", "寻福机", "寻祸隐", "权衡"]},
            {"name": "shang_shan_ruo_shui", "method": "上善若水·不争利他",
             "signature": "fn shang_shan_ruo_shui(collab) -> non_compete_gain",
             "precond": "协作/竞争场景",
             "postcond": "处下不争、善利万物, 以不争成共赢",
             "neg": "争则两损",
             "steps": ["处下", "不争", "利他", "共赢"]},
            {"name": "zhi_da_guo", "method": "治大国若烹小鲜·轻扰动",
             "signature": "fn zhi_da_guo(governance) -> stable_order",
             "precond": "治理对象(组织/系统)已知",
             "postcond": "少折腾、徐清徐静, 秩序自稳",
             "neg": "频繁扰动则乱",
             "steps": ["定纲", "少翻动", "徐清静", "稳序"]},
            {"name": "jian_su_bao_pu", "method": "见素抱朴·返本去冗",
             "signature": "fn jian_su_bao_pu(complex) -> essence",
             "precond": "系统/方案存在冗余复杂",
             "postcond": "删繁就简、返本归真, 守住根本",
             "neg": "繁则惑",
             "steps": ["辨冗余", "删繁", "归朴", "守本"]},
        ],
        "decision": [
            {"if": "需顺应规律", "call": "dao_fa_zi_ran"},
            {"if": "系统可自组织", "call": "wu_wei"},
            {"if": "趋势将极", "call": "fan_zhe_dao_zhi_dong"},
            {"if": "对抗逞强", "call": "rou_ruo_sheng_gang_qiang"},
            {"if": "事件定性", "call": "huo_fu_xiang_yi"},
            {"if": "协作不争", "call": "shang_shan_ruo_shui"},
            {"if": "治理维稳", "call": "zhi_da_guo"},
            {"if": "删冗归本", "call": "jian_su_bao_pu"},
        ],
        "negative_space": [
            "⊗ 逆'道'规律妄为(违道法自然)则败",
            "⊗ 过度干预扰动系统自组织(违无为)",
            "⊗ 忽视物极必反/对立转化则临危",
            "⊗ 逞强冒进则折(违守弱)",
            "⊗ 偏执祸福一端则盲(违辩证)",
            "⊗ 争利两损(违不争)",
            "⊗ 频繁翻动致乱(违烹小鲜)",
            "⊗ 繁冗惑本(违归朴)",
            "⊗ 本协议须以 TDCA-CORE-20260815-01 为可信底座: 合作/组合/比配前须加载生态准入基协议",
        ],
        "skills": ["顺势研判", "自组织赋权", "极反预警", "守弱蓄势", "辩证损益", "不争协作", "轻扰动治理", "删繁归本"],
        "main_pipeline": "dao_fa_zi_ran",
        "graph": [
            {"from": "dao_fa_zi_ran", "to": ["wu_wei", "fan_zhe_dao_zhi_dong", "jian_su_bao_pu"]},
            {"from": "wu_wei", "to": ["zhi_da_guo"]},
            {"from": "fan_zhe_dao_zhi_dong", "to": ["rou_ruo_sheng_gang_qiang"]},
            {"from": "rou_ruo_sheng_gang_qiang", "to": ["shang_shan_ruo_shui"]},
            {"from": "huo_fu_xiang_yi", "to": ["shang_shan_ruo_shui"]},
            {"from": "shang_shan_ruo_shui", "to": ["zhi_da_guo"]},
            {"from": "jian_su_bao_pu", "to": ["dao_fa_zi_ran"]},
        ],
    },
    # —— 预留 slot: 儒家/墨家/法家/名家/阴阳家 同构扩展 ——
    # {
    #     "cop_id": "HS-RU-20260815-02", "branch": "诸子百家·儒家",
    #     "idx": 2, "zh": "论语 (儒家)", "en": "Analects (Confucian)",
    #     "pinyin": "lunyu", ...
    # },
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
        "COP-ID": g["cop_id"],
        "source_expert": "hundred_schools_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": g["branch"],
        "stratum": g["branch"],  # 顶层 stratum 别名, 兼容组合解析器字段约定
        "soul": {
            "identity": "%s (%s)" % (g["zh"], g["en"]),
            "core": g["core"],
            "role": "思维协议 (诸子百家 / 中国文化基库)",
            "category": "诸子百家 / " + g["branch"],
            "base_protocol": "TDCA-CORE-20260815-01",  # 强制可信底座声明
        },
        "primitives": cop_primitives,
        "dispatch": {
            "main_pipeline": g["main_pipeline"],
            "graph": g["graph"],
            "note": "诸子百家 COP 自带调度骨架; 须以 TDCA-CORE-20260815-01 为可信底座",
        },
        "decision": g["decision"],
        "skills": g.get("skills", []),
        "negative_space": g["negative_space"],
        "nsfl_version": NSFL_VERSION,
    }
    CC.s5_validate(cop)
    return cop, g["pinyin"]


def compile_all():
    report = {"total": len(HS), "ok": 0, "skip": 0, "fail": 0,
              "cop_ids": [], "nca_ids": []}
    for g in HS:
        idx = g["idx"]
        fname = "第%02d百家-%s.yaml" % (idx, g["zh"])
        out_path = os.path.join(HS_DIR, fname)
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
                scope=".tdca-protocol/cognitive-compiler/hundred_schools (第%02d百家-%s COP)" % (idx, g["zh"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-HS-%02d" % idx,
                notes="诸子百家思维协议 %s (%s) 编译为 COP, 验证=%s" % (g["zh"], g["en"], cop["validation"]["passed"]),
            )
            report["ok"] += 1
            report["cop_ids"].append(cop["COP-ID"])
            report["nca_ids"].append(nid)
            print("[OK] %s -> %s | 原语 %d | 验证 %s" % (cop["COP-ID"], fname, len(cop["primitives"]), cop["validation"]["passed"]))
        except Exception as e:
            report["fail"] += 1
            print("[FAIL] 第%02d百家-%s: %s" % (idx, g["zh"], e))
    return report


if __name__ == "__main__":
    print("===== 诸子百家思维协议编译 (MEMO-006 规范, 中文化合基库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % HS_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    print("中文化合基库 operand: HS-DAO-20260815-01 (道德经) — 后续作 中国文化⊕辩证实践方法论 化合中方基协议")
    print("===== 编译完成 =====")
