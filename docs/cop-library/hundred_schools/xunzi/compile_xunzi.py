# -*- coding: utf-8 -*-
"""荀子 思维协议编译器 (诸子百家·儒家·礼法大宗)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 把《荀子》以"性恶·礼法·劝学"为系统骨架逐条编译为独立可调用的思维协议 (COP)。
用户立项: A. 续编儒家四书: 荀子(礼法·劝学)。荀子宗孔子、主性恶, 以"化性起伪"立工夫、
"隆礼重法"立政术, 开儒法过渡之枢, 与孟学并立为儒门两大宗。逐条 = 一个独立思维原语,
按三谱系归类 (性伪之辨 / 劝学积德 / 礼法政术)。每目以 TDCA-CORE-20260815-01 为可信底座。
同构: 与 compile_daxue.py / compile_mengzi.py 同构, 仅把"篇目系统"升级为"义理条目"。
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
XZ_DIR = _THIS
ensure_dirs()
os.makedirs(XZ_DIR, exist_ok=True)

# ---------- 荀子 思维协议知识库 (每条一思维原语) ----------
# 三谱系: 性伪之辨 / 劝学积德 / 礼法政术
XZ = [
    {"n":1,"stratum":"性伪之辨","title":"性恶论","verse":"人之性恶，其善者伪也。今人之性，生而有好利焉……",
     "principle":"人性本恶、其善在伪（人为）；以性恶立师法礼义之需，不信自然向善。","pinyin":"xing_e_lun",
     "signature":"fn xing_e_lun(human) -> evil_nature",
     "precond":"信性善、废师法","postcond":"知性恶，立礼义",
     "neg":"纵性则乱","steps":["识性恶","知伪","立师法","兴礼义"],
     "dispatch":"当论人性根基、宜立礼法矫治时触发","decision_if":"需立性恶论",
     "neg_space":["纵性废法则乱","全信性善则弛"]},
    {"n":2,"stratum":"性伪之辨","title":"化性起伪","verse":"枸木必将待檃栝烝矫然后直……人之性恶，必将待师法之化，礼义之道，然后出于治。",
     "principle":"性恶如枸木钝金、待师法礼义矫化；以伪（人为教化）胜自然，立矫治之功。","pinyin":"hua_xing_qi_wei",
     "signature":"fn hua_xing_qi_wei(cultivate) -> remade_nature",
     "precond":"不矫、任其暴","postcond":"师法化，出于治",
     "neg":"不化则暴","steps":["识待矫","师法化","礼义道","出于治"],
     "dispatch":"当人性待矫治、宜立师法时触发","decision_if":"需化性起伪",
     "neg_space":["废师法则纵恶","矫过则戕"]},
    {"n":3,"stratum":"性伪之辨","title":"解蔽","verse":"凡人之患，蔽于一曲而暗于大理。蔽公者末得也。",
     "principle":"患在蔽于一曲、暗于大理；以兼陈中衡、解蔽见全，立认知之公。","pinyin":"jie_bi",
     "signature":"fn jie_bi(think) -> unbiased",
     "precond":"蔽一曲、暗大理","postcond":"兼陈中衡，见全",
     "neg":"蔽则暗","steps":["识蔽","陈众","中衡","见大理"],
     "dispatch":"当认知偏蔽、宜求全见时触发","decision_if":"需解蔽",
     "neg_space":["蔽一曲则暗","私则失公"]},
    {"n":4,"stratum":"劝学积德","title":"劝学","verse":"学不可以已。青，取之于蓝，而青于蓝；冰，水为之，而寒于水。",
     "principle":"学不可已、积渐胜自然；以博学参省、知明行无过，立为学之基。","pinyin":"quan_xue",
     "signature":"fn quan_xue(study) -> ever_study",
     "precond":"废学、不知省","postcond":"知明行无过",
     "neg":"废学则愚","steps":["学不已","参省","积渐","知明"],
     "dispatch":"当宜力学不已、不宜止息时触发","decision_if":"需劝学",
     "neg_space":["学止则退","不省则罔"]},
    {"n":5,"stratum":"劝学积德","title":"积善成德","verse":"积土成山，风雨兴焉……积善成德，而神明自得，圣心备焉。",
     "principle":"积微成著、积善成德；以渐积胜骤，立德性养成之序。","pinyin":"ji_shan_cheng_de",
     "signature":"fn ji_shan_cheng_de(accum) -> virtuous",
     "precond":"不积、欲速","postcond":"积善成德，圣心备",
     "neg":"不积则溃","steps":["积微","渐","成著","备圣心"],
     "dispatch":"当宜积渐养成、不宜躐等时触发","decision_if":"需积善成德",
     "neg_space":["不积则溃","躐等则败"]},
    {"n":6,"stratum":"劝学积德","title":"锲而不舍","verse":"锲而舍之，朽木不折；锲而不舍，金石可镂。",
     "principle":"持之以恒、不舍则金石镂；以恒心胜难，立坚毅之功。","pinyin":"qie_er_bu_she",
     "signature":"fn qie_er_bu_she(persist) -> carved",
     "precond":"舍之、中辍","postcond":"不舍，金石镂",
     "neg":"舍则废","steps":["持","锲","不舍","功成"],
     "dispatch":"当宜持恒克难、不宜中辍时触发","decision_if":"需锲而不舍",
     "neg_space":["一舍则前功弃","躁则不成"]},
    {"n":7,"stratum":"礼法政术","title":"隆礼","verse":"礼者，法之大分，类之纲纪也。故学至乎礼而止矣。",
     "principle":"礼为法之大分、类之纲纪；以礼统群伦，立秩序之本。","pinyin":"long_li",
     "signature":"fn long_li(order) -> ritual_first",
     "precond":"无礼、伦乱","postcond":"隆礼，纲纪立",
     "neg":"废礼则乱","steps":["识礼本","隆礼","定分","成纪"],
     "dispatch":"当宜立礼序、不宜无序时触发","decision_if":"需隆礼",
     "neg_space":["废礼则争乱","礼不下则乖"]},
    {"n":8,"stratum":"礼法政术","title":"礼法并施","verse":"治之经，礼与刑，君子以修百姓宁。明德慎罚，节威反文。",
     "principle":"礼刑并施、德主刑辅；以礼化于先、刑齐于后，立治之常经。","pinyin":"li_fa_bing_shi",
     "signature":"fn li_fa_bing_shi(govern) -> ritual_law",
     "precond":"偏礼或偏刑","postcond":"礼刑并，百姓宁",
     "neg":"偏则失","steps":["隆礼","明德","慎罚","节威"],
     "dispatch":"当宜礼法兼用、不宜偏废时触发","decision_if":"需礼法并施",
     "neg_space":["专任刑则酷","专任礼则纵"]},
    {"n":9,"stratum":"礼法政术","title":"隆礼重法","verse":"明礼义而壹法度，立公天下。由士以上则必以礼乐节之，众庶则必以法数制之。",
     "principle":"礼义法度一之、公私分明；以礼别贵贱、以法齐众庶，立儒法合一之治。","pinyin":"long_li_zhong_fa",
     "signature":"fn long_li_zhong_fa(rule) -> li_fa_unity",
     "precond":"礼法离、公私混","postcond":"壹法度，公天下",
     "neg":"离则溃","steps":["明礼义","壹法度","别士庶","公天下"],
     "dispatch":"当宜礼法合一、不宜离析时触发","decision_if":"需隆礼重法",
     "neg_space":["礼法离则溃","任私则乱"]},
    {"n":10,"stratum":"礼法政术","title":"制天命而用之","verse":"大天而思之，孰与物畜而制之？从天而颂之，孰与制天命而用之？",
     "principle":"不慕天思天、而物畜制天用之；以人制天、趋利避害，立戡天役物之能。","pinyin":"zhi_tian_ming_er_yong_zhi",
     "signature":"fn zhi_tian_ming_er_yong_zhi(act) -> mastery_nature",
     "precond":"听天、无所为","postcond":"制天命，用之",
     "neg":"听天则废","steps":["识天常","物畜","制用","趋利"],
     "dispatch":"当宜人定胜天、不宜听命时触发","decision_if":"需制天命而用之",
     "neg_space":["听天由命则废","虐用则反"]},
    {"n":11,"stratum":"礼法政术","title":"正名","verse":"名定而实辨，制名以指实也。王者之制名，名定而实辨，道行而志通。",
     "principle":"名以指实、名定实辨；以正名壹法、明分使群，立名实之辨。","pinyin":"zheng_ming",
     "signature":"fn zheng_ming(name) -> rectified_name",
     "precond":"名乱、实淆","postcond":"名定实辨，道行",
     "neg":"名乱则惑","steps":["制名","指实","定分","辨惑"],
     "dispatch":"当名实淆乱、宜正名时触发","decision_if":"需正名",
     "neg_space":["名实乱则惑","巧言乱名则奸"]},
    {"n":12,"stratum":"礼法政术","title":"群分","verse":"人能群，彼不能群也……分何以能行？曰：义。故义以分则和。",
     "principle":"人能群、以义分而和；以明分使群、义胜则和，立群居和一之理。","pinyin":"qun_fen",
     "signature":"fn qun_fen(society) -> harmonious_group",
     "precond":"无分、争乱","postcond":"义分，群和",
     "neg":"无分则争","steps":["识能群","明分","以义","群和"],
     "dispatch":"当群体待组织、宜以义明分时触发","decision_if":"需群分",
     "neg_space":["无分则争乱","分不公则离"]},
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
        "COP-ID": "HS-RU-XZ%02d-20260815-%02d" % (g["n"], g["n"]),
        "source_expert": "xunzi_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用 / 义理条目分解)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": "诸子百家·儒家·荀子·第%02d条(%s)" % (g["n"], g["title"]),
        "stratum": "诸子百家·儒家·荀子·" + g["stratum"],
        "soul": {
            "identity": "荀子·第%02d条《%s》" % (g["n"], g["title"]),
            "core": g["principle"],
            "verse": g["verse"],
            "role": "思维协议 (诸子百家 / 儒家 / 荀子义理)",
            "category": "诸子百家 / 儒家 / 荀子 / " + g["stratum"],
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
    report = {"total": len(XZ), "ok": 0, "skip": 0, "fail": 0, "cop_ids": [], "nca_ids": []}
    for g in XZ:
        n = g["n"]
        fname = "第%02d条-%s.yaml" % (n, g["title"])
        out_path = os.path.join(XZ_DIR, fname)
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
                scope=".tdca-protocol/cognitive-compiler/hundred_schools/xunzi (第%02d条-%s COP)" % (n, g["title"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-XZ-M%02d" % n,
                notes="荀子第%02d条《%s》编译为 COP, 验证=%s" % (n, g["title"], cop["validation"]["passed"]),
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
        "性伪之辨": "性恶论/化性起伪/解蔽 (立人性待矫、认知求全, 与孟学并立)",
        "劝学积德": "劝学/积善成德/锲而不舍 (积渐胜自然, 德性养成之序)",
        "礼法政术": "隆礼/礼法并施/隆礼重法/制天命而用之/正名/群分 (儒法合一, 礼法秩序)",
    }
    items = []
    for g in XZ:
        items.append({
            "n": g["n"], "title": g["title"], "cop_id": "HS-RU-XZ%02d-20260815-%02d" % (g["n"], g["n"]),
            "stratum": g["stratum"], "verse": g["verse"], "primitive": g["pinyin"],
            "file": "第%02d条-%s.yaml" % (g["n"], g["title"]),
        })
    by_stratum = {}
    for g in XZ:
        by_stratum.setdefault(g["stratum"], []).append(g["n"])
    manifest = {
        "library": "xunzi_lifa",
        "role": "儒家系统思维·礼法大宗库 (Chinese cultural compound operand source, 义理条目级)",
        "note": "《荀子》宗孔子、主性恶, 以'化性起伪'立工夫、'隆礼重法'立政术, 开儒法过渡之枢。"
                "逐条编译为独立可调用的思维协议(COP), 按三谱系归类。后续作'中国文化 ⊕ 辩证实践方法论'化合的中方基协议素材。",
        "base_protocol": "TDCA-CORE-20260815-01",
        "compiler": "xunzi/compile_xunzi.py",
        "schema": "同构麦肯锡 COP (stratum+steps, 兼容 compose_general)",
        "total_items": len(XZ),
        "strata_taxonomy": strata_def,
        "strata_count": {k: len(v) for k, v in by_stratum.items()},
        "items": items,
        "composition": {
            "composer": "../../compositions/compose_general.py",
            "compatible_with": ["TDCA核心", "道家(道德经)", "论语", "大学", "孟子", "中庸", "墨法名阴阳", "辩证实践方法论", "兵法", "博弈论", "机制设计", "场景", "现代学科库"],
            "compound_first_principle": "化合 > 物理叠加 (interpretant 注入语义涌现, 非内禀)",
            "compound_target": "中国文化 ⊕ 辩证实践方法论 = 辩证实践思维协议 (化合旗舰范式)",
            "verified_demo": "撰写中 (荀子礼法 ⟂ 法家/辩证实践方法论唯物史观)",
        },
    }
    mp = os.path.join(XZ_DIR, "xunzi_manifest.yaml")
    with open(mp, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    print("[OK] 系统谱系清单 -> %s (三谱系: %s)" % (mp, "/".join(strata_def.keys())))


if __name__ == "__main__":
    print("===== 荀子 思维协议编译 (MEMO-006 规范, 儒家·礼法大宗库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % XZ_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    write_manifest()
    print("系统思维谱系: 性伪之辨/劝学积德/礼法政术")
    print("===== 编译完成 =====")
