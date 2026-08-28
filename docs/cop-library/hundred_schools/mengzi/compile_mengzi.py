# -*- coding: utf-8 -*-
"""孟子 思维协议编译器 (诸子百家·儒家·亚圣系统思维)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 把《孟子》以"性善·养气·王道"三支为系统骨架逐条编译为独立可调用的思维协议 (COP)。
用户立项: A. 续编儒家四书: 孟子(性善·养气·王道)。孟子承孔子、启道统, 以"性善"立本体、
"养气"立工夫、"王道"立政术, 构成儒家内圣外王的第二座纲领。逐条 = 一个独立思维原语,
共同构成"孟子系统思维"基库, 按三谱系归类 (性善本体 / 养气工夫 / 王道政术)。
每目须以 TDCA-CORE-20260815-01 (生态准入基协议) 为可信底座。
同构: 与 compile_lunyu.py / compile_daodejing.py / compile_daxue.py 同构, 仅把"篇目系统"升级为"义理条目"。
"""
import os
import sys
import datetime
import hashlib
import yaml

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "..", "config"))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "..", "nca-generator"))
sys.path.insert(0, os.path.join(_THIS, "..", ".."))  # cognitive_compiler 根
sys.path.insert(0, _THIS)

import tdca_config as TC
import cognitive_compiler as CC
import nca_generator as NCA

ensure_dirs = TC.ensure_dirs
NSFL_VERSION = TC.NSFL_VERSION
MZ_DIR = _THIS
ensure_dirs()
os.makedirs(MZ_DIR, exist_ok=True)

# ---------- 孟子 思维协议知识库 (每条一思维原语) ----------
# 三谱系: 性善本体 / 养气工夫 / 王道政术
MZ = [
    {"n":1,"stratum":"性善本体","title":"性善论","verse":"人性之善也，犹水之就下也。人无有不善，水无有不下。",
     "principle":"人性本善、向善如水流下；以性善为教化与政治的根基，不信性恶而信可教。","pinyin":"xing_shan_lun",
     "signature":"fn xing_shan_lun(human) -> good_nature",
     "precond":"疑人性、以恶设防","postcond":"信性善，立教可成",
     "neg":"以恶设防则失本","steps":["观性善","顺其下","立教","扩充"],
     "dispatch":"当论人性根基、宜立性善为教本时触发","decision_if":"需立性善本体",
     "neg_space":["以性恶立法则背教化","放其心而不知求则陷"]},
    {"n":2,"stratum":"性善本体","title":"四端说","verse":"恻隐之心，仁之端也；羞恶之心，义之端也；辞让之心，礼之端也；是非之心，智之端也。",
     "principle":"性善具四端（恻隐/羞恶/辞让/是非），扩而充之即仁义礼智；以端为种、充为功。","pinyin":"si_duan_shuo",
     "signature":"fn si_duan_shuo(heart) -> four_sprouts",
     "precond":"端蔽、充之不力","postcond":"四端充为仁义礼智",
     "neg":"自贼则其端涸","steps":["识四端","知端为种","扩充","成德"],
     "dispatch":"当见人微善、宜扩其端时触发","decision_if":"需扩四端",
     "neg_space":["自谓不能则自贼","端萌而抑则枯"]},
    {"n":3,"stratum":"性善本体","title":"良知良能","verse":"人之所不学而能者，其良能也；所不虑而知者，其良知也。",
     "principle":"良知良能不假外求、本具于心；以反身而诚、不学而知，为直觉之善的源头。","pinyin":"liang_zhi_neng",
     "signature":"fn liang_zhi_neng(self) -> innate_good",
     "precond":"外求知识、昧其良","postcond":"反身诚，良知显",
     "neg":"外求则失其良","steps":["反身","诚之","识良知","行不虑"],
     "dispatch":"当宜信本心直觉之善、不宜徇外时触发","decision_if":"需致良知",
     "neg_space":["徇外忘内则昧","以知为蔽则伪"]},
    {"n":4,"stratum":"性善本体","title":"不忍人之心","verse":"先王有不忍人之心，斯有不忍人之政矣。以不忍人之心，行不忍人之政。",
     "principle":"不忍人之心（恻隐）推而为政即仁政；以推恩及物，由一体之仁达于天下。","pinyin":"bu_ren_zhi_xin",
     "signature":"fn bu_ren_zhi_xin(extend) -> humane_govern",
     "precond":"忍心残忍、不推","postcond":"推恩保四海",
     "neg":"忍则失其端","steps":["识不忍","推恩","及物","保四海"],
     "dispatch":"当宜以仁心推政、不宜苛酷时触发","decision_if":"需行不忍人之政",
     "neg_space":["忍心行虐则失位","推而不遍则狭"]},
    {"n":5,"stratum":"养气工夫","title":"浩然之气","verse":"我善养吾浩然之气……其为气也，至大至刚，以直养而无害，则塞于天地之间。",
     "principle":"浩然之气配义与道、集义所生；以直养无害、积义成刚，立大丈夫之躯。","pinyin":"hao_ran_zhi_qi",
     "signature":"fn hao_ran_zhi_qi(cultivate) -> vast_qi",
     "precond":"气馁、义不集","postcond":"至大至刚，塞天地",
     "neg":"袭义则馁","steps":["知配义道","集义","直养","无害"],
     "dispatch":"当宜养刚大正直之气、不宜苟且时触发","decision_if":"需养浩然之气",
     "neg_space":["袭义而取则馁","无养则散"]},
    {"n":6,"stratum":"养气工夫","title":"养气知言","verse":"我知言，我善养吾浩然之气。何谓知言？曰：诐辞知其所蔽……",
     "principle":"知言（诐/淫/邪/遁各知其蔽陷离穷）以养气相须；以明辨言辞偏蔽、正心养气。","pinyin":"yang_qi_zhi_yan",
     "signature":"fn yang_qi_zhi_yan(hear) -> discern_words",
     "precond":"言辞眩、心随蔽","postcond":"知言正心，气自养",
     "neg":"徇辞则蔽","steps":["听辞","辨蔽陷","知离穷","正心"],
     "dispatch":"当言辞纷杂、宜辨其偏蔽时触发","decision_if":"需知言辨蔽",
     "neg_space":["徇辞则心随转","不辨则陷"]},
    {"n":7,"stratum":"养气工夫","title":"大丈夫人格","verse":"富贵不能淫，贫贱不能移，威武不能屈，此之谓大丈夫。",
     "principle":"大丈夫立乎其大、不为境迁；以志帅气、守道不屈，成独立人格。","pinyin":"da_zhang_fu",
     "signature":"fn da_zhang_fu(self) -> great_man",
     "precond":"随境迁、志移","postcond":"立乎其大，不屈",
     "neg":"移屈则失大","steps":["立其大","守道","不淫移屈","成丈夫"],
     "dispatch":"当宜守节不屈、不宜徇势时触发","decision_if":"需立大丈夫人格",
     "neg_space":["徇势则贱","志移则溃"]},
    {"n":8,"stratum":"王道政术","title":"王道仁政","verse":"保民而王，莫之能御也。老吾老以及人之老，幼吾幼以及人之幼。",
     "principle":"王道以保民为本、推不忍之心于政；以德服人、不恃力假仁。","pinyin":"wang_dao_ren_zheng",
     "signature":"fn wang_dao_ren_zheng(govern) -> true_kingdom",
     "precond":"力假仁、民不保","postcond":"保民而王，莫御",
     "neg":"霸术则暂","steps":["保民","推恩","以德服","王天下"],
     "dispatch":"当宜行仁政王道、不宜霸术时触发","decision_if":"需行王道仁政",
     "neg_space":["以力假仁则暂","虐民则失"]},
    {"n":9,"stratum":"王道政术","title":"民贵君轻","verse":"民为贵，社稷次之，君为轻。是故得乎丘民而为天子。",
     "principle":"民贵君轻、得民为天；以民为本位，政权合法性系于民心。","pinyin":"min_gui_jun_qing",
     "signature":"fn min_gui_jun_qing(polity) -> people_first",
     "precond":"君贵民贱、失本","postcond":"得丘民为天子",
     "neg":"轻民则危","steps":["立民本","得民心","正名位","安社稷"],
     "dispatch":"当宜以民为本、不宜独尊君时触发","decision_if":"需立民贵君轻",
     "neg_space":["虐民失位","独夫则倾"]},
    {"n":10,"stratum":"王道政术","title":"义利之辨","verse":"王何必曰利？亦有仁义而已矣。上下交征利而国危矣。",
     "principle":"先义后利、以义制利；上下交征利则危，以仁义为纲则安。","pinyin":"yi_li_zhi_bian",
     "signature":"fn yi_li_zhi_bian(weigh) -> righteousness_first",
     "precond":"唯利是图、交征","postcond":"仁义为纲，国安",
     "neg":"唯利则危","steps":["辨义利","先义","制利","安上下"],
     "dispatch":"当宜先义后利、不宜唯利时触发","decision_if":"需明义利之辨",
     "neg_space":["交征利则危","见利忘义则溃"]},
    {"n":11,"stratum":"王道政术","title":"与民同乐","verse":"乐民之乐者，民亦乐其乐；忧民之忧者，民亦忧其忧。",
     "principle":"与民同乐忧、共其好恶；以同乐得民心，不独乐而天下怨。","pinyin":"yu_min_tong_le",
     "signature":"fn yu_min_tong_le(share) -> shared_joy",
     "precond":"独乐民怨","postcond":"同乐，民归",
     "neg":"独乐则怨","steps":["识民乐","同其乐","共其忧","得民心"],
     "dispatch":"当宜与民同乐、不宜独享时触发","decision_if":"需与民同乐",
     "neg_space":["独乐则天下怨","违民欲则叛"]},
    {"n":12,"stratum":"王道政术","title":"仁政井田","verse":"明君制民之产，必使仰足以事父母，俯足以畜妻子……恒产者有恒心。",
     "principle":"制民之产、使有恒产恒心；以井田均产、教以人伦，养教相成。","pinyin":"ren_zheng_jing_tian",
     "signature":"fn ren_zheng_jing_tian(plan) -> settled_people",
     "precond":"无恒产、心放","postcond":"有恒产恒心，教成",
     "neg":"无产则放","steps":["制产","均田","立恒心","施教"],
     "dispatch":"当宜富民教民、不宜聚敛时触发","decision_if":"需制民之产",
     "neg_space":["聚敛则民散","无教则野"]},
]


def assemble_one(g):
    """S2-S4: 将单条编译为 COP (对齐麦肯锡 COP schema 单原语形态)"""
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
        "COP-ID": "HS-RU-MZ%02d-20260815-%02d" % (g["n"], g["n"]),
        "source_expert": "mengzi_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用 / 义理条目分解)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": "诸子百家·儒家·孟子·第%02d条(%s)" % (g["n"], g["title"]),
        "stratum": "诸子百家·儒家·孟子·" + g["stratum"],
        "soul": {
            "identity": "孟子·第%02d条《%s》" % (g["n"], g["title"]),
            "core": g["principle"],
            "verse": g["verse"],
            "role": "思维协议 (诸子百家 / 儒家 / 孟子义理)",
            "category": "诸子百家 / 儒家 / 孟子 / " + g["stratum"],
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
    report = {"total": len(MZ), "ok": 0, "skip": 0, "fail": 0,
              "cop_ids": [], "nca_ids": []}
    for g in MZ:
        n = g["n"]
        fname = "第%02d条-%s.yaml" % (n, g["title"])
        out_path = os.path.join(MZ_DIR, fname)
        if os.path.exists(out_path):
            print("[SKIP] %s 已存在, 跳过 (不重复发射 NCA)" % fname)
            report["skip"] += 1
            continue
        try:
            cop, _ = assemble_one(g)
            CC._dump_yaml(cop, out_path)
            h = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
            sz = os.path.getsize(out_path)
            nid, _, _ = NCA.generate_nca(
                operation_type="CodeGen",
                scope=".tdca-protocol/cognitive-compiler/hundred_schools/mengzi (第%02d条-%s COP)" % (n, g["title"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-MENG-M%02d" % n,
                notes="孟子第%02d条《%s》编译为 COP, 验证=%s" % (n, g["title"], cop["validation"]["passed"]),
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
        "性善本体": "性善论/四端说/良知良能/不忍人之心 (立人性本善根基, 为教化政术之源)",
        "养气工夫": "浩然之气/养气知言/大丈夫人格 (以直养无害、集义成刚, 立独立人格)",
        "王道政术": "王道仁政/民贵君轻/义利之辨/与民同乐/仁政井田 (保民而王, 推不忍之心于政)",
    }
    items = []
    for g in MZ:
        items.append({
            "n": g["n"], "title": g["title"], "cop_id": "HS-RU-MZ%02d-20260815-%02d" % (g["n"], g["n"]),
            "stratum": g["stratum"], "verse": g["verse"], "primitive": g["pinyin"],
            "file": "第%02d条-%s.yaml" % (g["n"], g["title"]),
        })
    by_stratum = {}
    for g in MZ:
        by_stratum.setdefault(g["stratum"], []).append(g["n"])
    manifest = {
        "library": "mengzi_yishan",
        "role": "儒家系统思维·亚圣义理库 (Chinese cultural compound operand source, 义理条目级)",
        "note": "《孟子》承孔子、启道统, 以'性善'立本体、'养气'立工夫、'王道'立政术, "
                "构成儒家内圣外王第二座纲领。逐条编译为独立可调用的思维协议(COP), 按三谱系归类。"
                "后续作'中国文化 ⊕ 辩证实践方法论'化合的中方基协议素材。",
        "base_protocol": "TDCA-CORE-20260815-01",
        "compiler": "mengzi/compile_mengzi.py",
        "schema": "同构麦肯锡 COP (stratum+steps, 兼容 compose_general)",
        "total_items": len(MZ),
        "strata_taxonomy": strata_def,
        "strata_count": {k: len(v) for k, v in by_stratum.items()},
        "items": items,
        "composition": {
            "composer": "../../compositions/compose_general.py",
            "compatible_with": ["TDCA核心", "道家(道德经)", "论语", "大学", "中庸", "荀子", "墨法名阴阳", "辩证实践方法论", "兵法", "博弈论", "机制设计", "场景", "现代学科库"],
            "compound_first_principle": "化合 > 物理叠加 (interpretant 注入语义涌现, 非内禀)",
            "compound_target": "中国文化 ⊕ 辩证实践方法论 = 辩证实践思维协议 (化合旗舰范式)",
            "verified_demo": "撰写中 (孟子性善/养气 ⟂ 辩证实践方法论实践论/矛盾论)",
        },
    }
    mp = os.path.join(MZ_DIR, "mengzi_manifest.yaml")
    with open(mp, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    print("[OK] 系统谱系清单 -> %s (三谱系: %s)" % (mp, "/".join(strata_def.keys())))


if __name__ == "__main__":
    print("===== 孟子 思维协议编译 (MEMO-006 规范, 儒家·亚圣义理库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % MZ_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    write_manifest()
    print("系统思维谱系: 性善本体/养气工夫/王道政术")
    print("===== 编译完成 =====")
