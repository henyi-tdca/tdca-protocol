# -*- coding: utf-8 -*-
"""阴阳家 思维协议编译器 (诸子百家·五行)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 把《阴阳家》(邹衍·五德终始) 以"五行"为系统骨架逐条编译为独立可调用的思维协议 (COP)。
用户立项: B. 续编诸子百家: 阴阳家(五行)。阴阳家以阴阳消息、五行相生克、五德终始为宇宙与
历史之序, 开中国气化学说与系统循环论。逐条 = 一个独立思维原语, 按三谱系归类 (五行本体 / 德运终始 / 天人感应)。
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
YY_DIR = _THIS
ensure_dirs()
os.makedirs(YY_DIR, exist_ok=True)

# ---------- 阴阳家 思维协议知识库 (每条一思维原语) ----------
# 三谱系: 五行本体 / 德运终始 / 天人感应
YY = [
    {"n":1,"stratum":"五行本体","title":"五行","verse":"水火木金土，五材欢用。五行：一曰水，二曰火，三曰木，四曰金，五曰土。",
     "principle":"五行五材、万物所由；以五性类万物，立元素归类之基。","pinyin":"wu_xing",
     "signature":"fn wu_xing(classify) -> five_phases",
     "precond":"类杂、无统","postcond":"五行立，物有归",
     "neg":"失统则散","steps":["识水火","识木金土","类万物","归五"],
     "dispatch":"当宜对事物作元素归类、不宜杂时触发","decision_if":"需五行归类",
     "neg_space":["类杂则失统","执一废四则偏"]},
    {"n":2,"stratum":"五行本体","title":"相生相克","verse":"水生木，木生火，火生土，土生金，金生水。克者：水克火，火克金，金克木，木克土，土克水。",
     "principle":"五行相生相克、生克互济；以生克为机枢，立动态平衡之环。","pinyin":"xiang_sheng_xiang_ke",
     "signature":"fn xiang_sheng_xiang_ke(cycle) -> generate_restrain",
     "precond":"偏生或偏克","postcond":"生克衡，机运",
     "neg":"偏则乖","steps":["明生","明克","衡生克","成环"],
     "dispatch":"当系统待调、宜察生克平衡时触发","decision_if":"需相生相克",
     "neg_space":["偏生则壅","偏克则伤"]},
    {"n":3,"stratum":"五行本体","title":"阴阳消息","verse":"阴阳之化，寒暑推移。阳极生阴，阴极生阳，消息盈虚，与时偕行。",
     "principle":"阴阳消息、寒暑推移；以消长循环、盈虚有时，立对待转化的常。","pinyin":"yin_yang_xiao_xi",
     "signature":"fn yin_yang_xiao_xi(transform) -> yin_yang_shift",
     "precond":"执阴或执阳","postcond":"消息和，转化常",
     "neg":"执一则蔽","steps":["识阴阳","察消息","顺推移","偕时"],
     "dispatch":"当宜顺阴阳消长、不宜执一边时触发","decision_if":"需阴阳消息",
     "neg_space":["执阳则亢","执阴则沉"]},
    {"n":4,"stratum":"五行本体","title":"四时","verse":"四时行焉，百物生焉。春生夏长秋收冬藏，时使然也。",
     "principle":"四时行、百物生；以春生夏长秋收冬藏为序，立时令节律之则。","pinyin":"si_shi",
     "signature":"fn si_shi(season) -> four_seasons",
     "precond":"逆时、失序","postcond":"时行，物生",
     "neg":"逆时则伤","steps":["识四时","顺生藏","因时","物成"],
     "dispatch":"当宜因时作息、不宜逆时令时触发","decision_if":"需顺四时",
     "neg_space":["逆时则伤物","乱序则败"]},
    {"n":5,"stratum":"德运终始","title":"五德终始","verse":"五德之运，各以所胜为行。虞土、夏木、殷金、周火，代各乘其德而王。",
     "principle":"五德终始、各以所胜代兴；以德运循环论王朝更替，立历史系统之序。","pinyin":"wu_de_zhong_shi",
     "signature":"fn wu_de_zhong_shi(history) -> dynastic_cycle",
     "precond":"昧运、代无序","postcond":"德运明，代有常",
     "neg":"昧运则乱","steps":["识五德","明所胜","察代兴","立序"],
     "dispatch":"当宜以系统循环观历史更替、不宜线性时触发","decision_if":"需五德终始",
     "neg_space":["昧运则失序","泥循环则蔽"]},
    {"n":6,"stratum":"德运终始","title":"大九州","verse":"儒者所谓中国者，于天下乃八十一分居其一分耳。赤县神州内自有九州。",
     "principle":"大九州、天下广远；以宏阔空间观破中国中心，立世界系统之格局。","pinyin":"da_jiu_zhou",
     "signature":"fn da_jiu_zhou(space) -> greater_nine",
     "precond":"囿于一隅","postcond":"眼界阔，格局立",
     "neg":"囿则狭","steps":["破中心","识大九","宏观","格局"],
     "dispatch":"当宜拓空间格局、不宜囿一隅时触发","decision_if":"需大九州观",
     "neg_space":["囿一隅则狭","虚夸则妄"]},
    {"n":7,"stratum":"天人感应","title":"天人感应","verse":"类固相召，气同则合。灾异祯祥，皆类之所感，天人之际未有不相酬者。",
     "principle":"类固相召、天人相酬；以气类感通立天人相应之论（及其灾异戒惧）。","pinyin":"tian_ren_gan_ying",
     "signature":"fn tian_ren_gan_ying(resonate) -> cosmic_resonance",
     "precond":"天人隔、不省","postcond":"感通明，戒惧立",
     "neg":"隔绝则昧","steps":["识类召","察气同","观灾祥","自省"],
     "dispatch":"当宜察天人相应、以灾异自省时触发","decision_if":"需天人感应",
     "neg_space":["天人隔则昧","附会灾异则诬"]},
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
        "COP-ID": "HS-YY-%02d-20260815-%02d" % (g["n"], g["n"]),
        "source_expert": "yinyangjia_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用 / 义理条目分解)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": "诸子百家·阴阳家·第%02d条(%s)" % (g["n"], g["title"]),
        "stratum": "诸子百家·阴阳家·" + g["stratum"],
        "soul": {
            "identity": "阴阳家·第%02d条《%s》" % (g["n"], g["title"]),
            "core": g["principle"],
            "verse": g["verse"],
            "role": "思维协议 (诸子百家 / 阴阳家 / 五行)",
            "category": "诸子百家 / 阴阳家 / " + g["stratum"],
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
    report = {"total": len(YY), "ok": 0, "skip": 0, "fail": 0, "cop_ids": [], "nca_ids": []}
    for g in YY:
        n = g["n"]
        fname = "第%02d条-%s.yaml" % (n, g["title"])
        out_path = os.path.join(YY_DIR, fname)
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
                scope=".tdca-protocol/cognitive-compiler/hundred_schools/yinyangjia (第%02d条-%s COP)" % (n, g["title"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-YY-M%02d" % n,
                notes="阴阳家第%02d条《%s》编译为 COP, 验证=%s" % (n, g["title"], cop["validation"]["passed"]),
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
        "五行本体": "五行/相生相克/阴阳消息/四时 (元素归类, 生克循环, 对待转化, 时令节律)",
        "德运终始": "五德终始/大九州 (德运代兴论史, 宏阔空间破中心)",
        "天人感应": "天人感应 (类固相召, 气类感通与灾异自省)",
    }
    items = []
    for g in YY:
        items.append({
            "n": g["n"], "title": g["title"], "cop_id": "HS-YY-%02d-20260815-%02d" % (g["n"], g["n"]),
            "stratum": g["stratum"], "verse": g["verse"], "primitive": g["pinyin"],
            "file": "第%02d条-%s.yaml" % (g["n"], g["title"]),
        })
    by_stratum = {}
    for g in YY:
        by_stratum.setdefault(g["stratum"], []).append(g["n"])
    manifest = {
        "library": "yinyangjia_wuxing",
        "role": "诸子百家系统思维·五行库 (Chinese cultural compound operand source, 义理条目级)",
        "note": "阴阳家以阴阳消息、五行相生克、五德终始为宇宙与历史之序, 开中国气化学说与系统循环论。"
                "逐条编译为独立可调用的思维协议(COP), 按三谱系归类。后续作'中国文化 ⊕ 马克思主义'化合的中方基协议素材。",
        "base_protocol": "TDCA-CORE-20260815-01",
        "compiler": "yinyangjia/compile_yinyangjia.py",
        "schema": "同构麦肯锡 COP (stratum+steps, 兼容 compose_general)",
        "total_items": len(YY),
        "strata_taxonomy": strata_def,
        "strata_count": {k: len(v) for k, v in by_stratum.items()},
        "items": items,
        "composition": {
            "composer": "../../compositions/compose_general.py",
            "compatible_with": ["TDCA核心", "道家", "儒", "墨家", "法家", "名家", "马克思主义", "控制论", "数学", "兵法", "博弈论", "机制设计", "场景", "现代学科库"],
            "compound_first_principle": "化合 > 物理叠加 (interpretant 注入语义涌现, 非内禀)",
            "compound_target": "中国文化 ⊕ 马克思主义 = 毛泽东思想思维协议 (化合旗舰范式)",
            "verified_demo": "撰写中 (阴阳家五行相生克/阴阳消息 ⟂ 马克思主义质量互变/对立统一)",
        },
    }
    mp = os.path.join(YY_DIR, "yinyangjia_manifest.yaml")
    with open(mp, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    print("[OK] 系统谱系清单 -> %s (三谱系: %s)" % (mp, "/".join(strata_def.keys())))


if __name__ == "__main__":
    print("===== 阴阳家 思维协议编译 (MEMO-006 规范, 诸子百家·五行库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % YY_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    write_manifest()
    print("系统思维谱系: 五行本体/德运终始/天人感应")
    print("===== 编译完成 =====")
