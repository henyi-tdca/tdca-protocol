# -*- coding: utf-8 -*-
"""名家 思维协议编译器 (诸子百家·名实之辨)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 把《名家》(公孙龙·离坚白 / 惠施·合同异) 以"名实"为系统骨架逐条编译为独立可调用的
思维协议 (COP)。用户立项: B. 续编诸子百家: 名家(名实)。名家专攻名实关系与概念辨析,
以逻辑析取开中国名辩之学。逐条 = 一个独立思维原语, 按三谱系归类 (名实本体 / 离坚白 / 合同异)。
每目以 TDCA-CORE-20260815-01 为可信底座。同构: 与 compile_daxue.py 同构, 升级为"义理条目"。
"""
import os
import sys
import datetime
import hashlib
import yaml

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "..", "config"))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "..", "nca-generator"))
sys.path.insert(0, os.path.join(_THIS, "..", ".."))
sys.path.insert(0, _THIS)

import tdca_config as TC
import cognitive_compiler as CC
import nca_generator as NCA

ensure_dirs = TC.ensure_dirs
NSFL_VERSION = TC.NSFL_VERSION
MG_DIR = _THIS
ensure_dirs()
os.makedirs(MG_DIR, exist_ok=True)

# ---------- 名家 思维协议知识库 (每条一思维原语) ----------
# 三谱系: 名实本体 / 离坚白 / 合同异
MG = [
    {"n":1,"stratum":"名实本体","title":"名实之辨","verse":"名以指实，实名相符。制名以指实，实定而名正。",
     "principle":"名以指实、实为正名之本；以名实相符立概念与言说之基。","pinyin":"ming_shi_zhi_bian",
     "signature":"fn ming_shi_zhi_bian(name) -> name_reality",
     "precond":"名实乖、言乱","postcond":"名实相符，言正",
     "neg":"名实乖则惑","steps":["识名用","指实","正名","符实"],
     "dispatch":"当概念淆乱、宜正名实关系时触发","decision_if":"需名实之辨",
     "neg_space":["名实乖则言乱","滥名则奸生"]},
    {"n":2,"stratum":"名实本体","title":"指物论","verse":"物莫非指，而指非指。天下无指，物无可以谓物。",
     "principle":"物莫非指、指非指；以指称构造对象，立概念指称之元理。","pinyin":"zhi_wu_lun",
     "signature":"fn zhi_wu_lun(refer) -> reference",
     "precond":"昧指物、混称","postcond":"指物明，称当",
     "neg":"昧指则混","steps":["识指","指物","别指非指","称当"],
     "dispatch":"当宜明概念指称、不宜混称时触发","decision_if":"需指物论",
     "neg_space":["昧指则混称","指非指而执则妄"]},
    {"n":3,"stratum":"离坚白","title":"白马非马","verse":"白马者，马与白也，马与白非马也。求马，黄黑马皆可致；求白马，黄黑马不可致。",
     "principle":"白马非马、种属与属性析取；以概念析取破混同，立逻辑区别的严格性。","pinyin":"bai_ma_fei_ma",
     "signature":"fn bai_ma_fei_ma(concept) -> not_horse",
     "precond":"混种属属性","postcond":"析取明，概念严",
     "neg":"混同则谬","steps":["析属","析色","别白马","严概念"],
     "dispatch":"当宜严格析取概念、不宜混同种属时触发","decision_if":"需白马非马",
     "neg_space":["混种属则谬","析过则碎"]},
    {"n":4,"stratum":"离坚白","title":"坚白论","verse":"坚白石二。视不得其所坚，拊不得其所白。坚白离焉，不相盈也。",
     "principle":"坚白石二、感官各得一端；以属性相离、认识有界，立分析之严。","pinyin":"jian_bai_lun",
     "signature":"fn jian_bai_lun(perceive) -> separate_attrs",
     "precond":"混属性、笼统","postcond":"坚白离，分析明",
     "neg":"笼统则昧","steps":["分坚","分白","识相离","明限"],
     "dispatch":"当宜分属性析认识、不宜笼统时触发","decision_if":"需坚白论",
     "neg_space":["混属性则昧","离过则散"]},
    {"n":5,"stratum":"离坚白","title":"通变论","verse":"二无一，左与右可谓二。鸡足一，数足二，二而一。",
     "principle":"二无一、数术非直加；以名数相生、变中有常，立概念数量之变。","pinyin":"tong_bian_lun",
     "signature":"fn tong_bian_lun(vary) -> change_logic",
     "precond":"混加、昧变","postcond":"通变明，数当",
     "neg":"混加则误","steps":["识二无","析左右","明数变","得常"],
     "dispatch":"当宜明数量概念之变、不宜直加时触发","decision_if":"需通变论",
     "neg_space":["混加则数误","变而无常则乱"]},
    {"n":6,"stratum":"合同异","title":"合同异","verse":"大同而与小同异，此之谓小同异；万物毕同毕异，此之谓大同异。",
     "principle":"合同异、毕同毕异；以同异相对、类聚有阶，立分类之辨。","pinyin":"he_tong_yi",
     "signature":"fn he_tong_yi(classify) -> same_diff",
     "precond":"执同或执异","postcond":"同异明，类分",
     "neg":"执一则蔽","steps":["识小同","识大同","毕同异","分类"],
     "dispatch":"当宜辨同异层级、不宜执一边时触发","decision_if":"需合同异",
     "neg_space":["执同则混","执异则裂"]},
    {"n":7,"stratum":"合同异","title":"历物十事","verse":"至大无外谓之大一，至小无内谓之小一。天与地卑，山与泽平。",
     "principle":"历物十事、极观相对；以大一至小、天地相卑，破常识对待之执。","pinyin":"li_wu_shi_shi",
     "signature":"fn li_wu_shi_shi(observe) -> extreme_view",
     "precond":"执常对待","postcond":"极观明，对待破",
     "neg":"执常则蔽","steps":["观极大","观极小","识相对","破执"],
     "dispatch":"当宜破常识对待、作极观时触发","decision_if":"需历物十事",
     "neg_space":["执常对待则蔽","相对论无边则滑"]},
]


def assemble_one(g):
    cop_primitive = {
        "name": g["pinyin"],
        "method": g["title"],
        "signature": g["signature"],
        "precond": g["precond"],
        "postcond": g["postcond"],
        "negative_space": "⊗ " + g["neg"],
        "steps": g["steps"],
        "nca_emit": True,
    }
    cop = {
        "COP-ID": "HS-MG-%02d-20260815-%02d" % (g["n"], g["n"]),
        "source_expert": "mingjia_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用 / 义理条目分解)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": "诸子百家·名家·第%02d条(%s)" % (g["n"], g["title"]),
        "stratum": "诸子百家·名家·" + g["stratum"],
        "soul": {
            "identity": "名家·第%02d条《%s》" % (g["n"], g["title"]),
            "core": g["principle"],
            "verse": g["verse"],
            "role": "思维协议 (诸子百家 / 名家 / 名实之辨)",
            "category": "诸子百家 / 名家 / " + g["stratum"],
            "base_protocol": "TDCA-CORE-20260815-01",
        },
        "primitives": [cop_primitive],
        "dispatch": {
            "main_pipeline": g["pinyin"],
            "trigger": g["verse"],
            "when": g["dispatch"],
            "graph": [{"from": g["pinyin"], "to": []}],
        },
        "decision": [{"if": g["decision_if"], "call": g["pinyin"]}],
        "skills": [g["title"] + "·顺势研判"],
        "negative_space": g["neg_space"] + [
            "⊗ 本章协议须以 TDCA-CORE-20260815-01 为可信底座: 合作/组合/比配前须加载生态准入基协议",
        ],
        "nsfl_version": NSFL_VERSION,
    }
    CC.s5_validate(cop)
    return cop, g


def compile_all():
    report = {"total": len(MG), "ok": 0, "skip": 0, "fail": 0, "cop_ids": [], "nca_ids": []}
    for g in MG:
        n = g["n"]
        fname = "第%02d条-%s.yaml" % (n, g["title"])
        out_path = os.path.join(MG_DIR, fname)
        if os.path.exists(out_path):
            print("[SKIP] %s 已存在, 跳过" % fname)
            report["skip"] += 1
            continue
        try:
            cop, _ = assemble_one(g)
            CC._dump_yaml(cop, out_path)
            h = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
            sz = os.path.getsize(out_path)
            nid, _, _ = NCA.generate_nca(
                operation_type="CodeGen",
                scope=".tdca-protocol/cognitive-compiler/hundred_schools/mingjia (第%02d条-%s COP)" % (n, g["title"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-MG-M%02d" % n,
                notes="名家第%02d条《%s》编译为 COP, 验证=%s" % (n, g["title"], cop["validation"]["passed"]),
            )
            report["ok"] += 1
            report["cop_ids"].append(cop["COP-ID"])
            report["nca_ids"].append(nid)
            print("[OK] %s -> %s | 谱系 %s | 验证 %s" % (cop["COP-ID"], fname, g["stratum"], cop["validation"]["passed"]))
        except Exception as e:
            report["fail"] += 1
            print("[FAIL] 第%02d条-%s: %s" % (n, g["title"], e))
    return report


def write_manifest():
    strata_def = {
        "名实本体": "名实之辨/指物论 (名以指实, 概念指称之元理)",
        "离坚白": "白马非马/坚白论/通变论 (析取种属属性, 概念数量之变, 分析之严)",
        "合同异": "合同异/历物十事 (同异相对分类, 极观破对待, 名辩相对)",
    }
    items = []
    for g in MG:
        items.append({
            "n": g["n"], "title": g["title"], "cop_id": "HS-MG-%02d-20260815-%02d" % (g["n"], g["n"]),
            "stratum": g["stratum"], "verse": g["verse"], "primitive": g["pinyin"],
            "file": "第%02d条-%s.yaml" % (g["n"], g["title"]),
        })
    by_stratum = {}
    for g in MG:
        by_stratum.setdefault(g["stratum"], []).append(g["n"])
    manifest = {
        "library": "mingjia_mingshi",
        "role": "诸子百家系统思维·名实之辨库 (Chinese cultural compound operand source, 义理条目级)",
        "note": "名家专攻名实关系与概念辨析, 以逻辑析取开中国名辩之学(公孙龙离坚白、惠施合同异)。"
                "逐条编译为独立可调用的思维协议(COP), 按三谱系归类。后续作'中国文化 ⊕ 辩证实践方法论'化合的中方基协议素材。",
        "base_protocol": "TDCA-CORE-20260815-01",
        "compiler": "mingjia/compile_mingjia.py",
        "schema": "同构麦肯锡 COP (stratum+steps, 兼容 compose_general)",
        "total_items": len(MG),
        "strata_taxonomy": strata_def,
        "strata_count": {k: len(v) for k, v in by_stratum.items()},
        "items": items,
        "composition": {
            "composer": "../../compositions/compose_general.py",
            "compatible_with": ["TDCA核心", "道家", "儒", "墨家", "法家", "阴阳家", "辩证实践方法论", "逻辑学", "兵法", "博弈论", "机制设计", "场景", "现代学科库"],
            "compound_first_principle": "化合 > 物理叠加 (interpretant 注入语义涌现, 非内禀)",
            "compound_target": "中国文化 ⊕ 辩证实践方法论 = 辩证实践思维协议 (化合旗舰范式)",
            "verified_demo": "撰写中 (名家名实/合同异 ⟂ 辩证实践方法论矛盾特殊性/逻辑学)",
        },
    }
    mp = os.path.join(MG_DIR, "mingjia_manifest.yaml")
    with open(mp, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    print("[OK] 系统谱系清单 -> %s (三谱系: %s)" % (mp, "/".join(strata_def.keys())))


if __name__ == "__main__":
    print("===== 名家 思维协议编译 (MEMO-006 规范, 诸子百家·名实之辨库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % MG_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    write_manifest()
    print("系统思维谱系: 名实本体/离坚白/合同异")
    print("===== 编译完成 =====")
