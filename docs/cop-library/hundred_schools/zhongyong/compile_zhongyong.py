# -*- coding: utf-8 -*-
"""中庸 思维协议编译器 (诸子百家·儒家·孔门心法)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 把《中庸》以"中和·诚"为系统骨架逐条编译为独立可调用的思维协议 (COP)。
用户立项: A. 续编儒家四书: 中庸(中和·诚)。《中庸》为孔门心法, 子思述孔子"中庸"之传,
以"中和"立体用、以"诚"立天道人道合一, 是儒家心性论的中枢。逐条 = 一个独立思维原语,
按三谱系归类 (中和本体 / 诚体工夫 / 时中达道)。每目以 TDCA-CORE-20260815-01 为可信底座。
同构: 与 compile_daxue.py / compile_mengzi.py 同构, 仅把"篇目系统"升级为"心法条目"。
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
ZY_DIR = _THIS
ensure_dirs()
os.makedirs(ZY_DIR, exist_ok=True)

# ---------- 中庸 思维协议知识库 (每条一思维原语) ----------
# 三谱系: 中和本体 / 诚体工夫 / 时中达道
ZY = [
    {"n":1,"stratum":"中和本体","title":"天命之谓性","verse":"天命之谓性，率性之谓道，修道之谓教。",
     "principle":"性自天授、率性为道、修道为教；以性—道—教一贯，立人文化成之根。","pinyin":"tian_ming_zhi_xing",
     "signature":"fn tian_ming_zhi_xing(self) -> heaven_given_nature",
     "precond":"性蔽、教弛","postcond":"率性成道，教立",
     "neg":"悖性则失道","steps":["识天命","率性","修道","设教"],
     "dispatch":"当论心性本源、宜立性道教一贯时触发","decision_if":"需明天命之谓性",
     "neg_space":["悖性立教则伪","率非其性则乖"]},
    {"n":2,"stratum":"中和本体","title":"致中和","verse":"喜怒哀乐之未发谓之中，发而皆中节谓之和。致中和，天地位焉，万物育焉。",
     "principle":"未发之中、发而中节之和；致中和则天地位、万物育，立境域圆融之体。","pinyin":"zhi_zhong_he",
     "signature":"fn zhi_zhong_he(state) -> harmonized",
     "precond":"失中、发不中节","postcond":"致中和，天地位",
     "neg":"过不及则乖","steps":["守未发","中节","致和","位育"],
     "dispatch":"当情绪/举措偏颇、宜求中节时触发","decision_if":"需致中和",
     "neg_space":["过犹不及","拂性则乱"]},
    {"n":3,"stratum":"中和本体","title":"中庸","verse":"中庸其至矣乎！民鲜能久矣。不偏之谓中，不易之谓庸。",
     "principle":"中庸为至德、不偏不倚不易；以中为正、以庸为常，立常道不移之则。","pinyin":"zhong_yong",
     "signature":"fn zhong_yong(act) -> golden_mean",
     "precond":"偏倚、逐奇","postcond":"中行常道，民鲜能",
     "neg":"偏则失中","steps":["识中","去偏","守庸","常行"],
     "dispatch":"当宜执中守常、不宜偏奇时触发","decision_if":"需行中庸",
     "neg_space":["执一偏则失中","务奇则倾"]},
    {"n":4,"stratum":"诚体工夫","title":"慎独","verse":"莫见乎隐，莫显乎微，故君子慎其独也。",
     "principle":"隐微处尤当慎、独知中不苟；以慎独为诚之始功，不欺暗室。","pinyin":"shen_du",
     "signature":"fn shen_du(self) -> solitary_care",
     "precond":"欺暗室、慢隐微","postcond":"慎独不欺，诚立",
     "neg":"慢微则亏","steps":["察隐","谨微","慎独","不欺"],
     "dispatch":"当无人独处、宜谨隐微时触发","decision_if":"需慎独",
     "neg_space":["慢隐则亏德","欺独则伪"]},
    {"n":5,"stratum":"诚体工夫","title":"诚者天之道","verse":"诚者，天之道也；诚之者，人之道也。诚者不勉而中，不思而得。",
     "principle":"诚为天道本体、不勉中不思得；诚之（人之道）择善固执以合天。","pinyin":"cheng_zhe_tian_zhi_dao",
     "signature":"fn cheng_zhe_tian_zhi_dao(self) -> heavenly_cheng",
     "precond":"伪妄、不合天","postcond":"诚合天，不勉中",
     "neg":"伪则失天","steps":["识天道","体诚","诚之","合天"],
     "dispatch":"当宜立诚合天、不宜伪妄时触发","decision_if":"需立诚者天之道",
     "neg_space":["伪妄则背天","诚之不至则浮"]},
    {"n":6,"stratum":"诚体工夫","title":"诚明","verse":"自诚明，谓之性；自明诚，谓之教。诚则明矣，明则诚矣。",
     "principle":"诚明相生、性教互成；以诚致明、以明归诚，立心性开显之环。","pinyin":"cheng_ming",
     "signature":"fn cheng_ming(self) -> luminous_cheng",
     "precond":"暗塞、明诚隔","postcond":"诚明相生，性教成",
     "neg":"隔则两失","steps":["诚","明","相生","归一"],
     "dispatch":"当心性未明、宜诚明互发时触发","decision_if":"需诚明相生",
     "neg_space":["明而不诚则妄","诚而不明则暗"]},
    {"n":7,"stratum":"诚体工夫","title":"择善固执","verse":"博学之，审问之，慎思之，明辨之，笃行之……诚之者，择善而固执之者也。",
     "principle":"学—问—思—辨—行五序、择善而固执；以笃行到底，立为学入诚之方。","pinyin":"ze_shan_gu_zhi",
     "signature":"fn ze_shan_gu_zhi(study) -> firm_good",
     "precond":"学杂、行不笃","postcond":"择善固执，诚成",
     "neg":"不笃则废","steps":["博学","审问","慎思","明辨","笃行"],
     "dispatch":"当为学未定、宜博学笃行时触发","decision_if":"需择善固执",
     "neg_space":["学而不笃则浮","择非其善则误"]},
    {"n":8,"stratum":"诚体工夫","title":"诚则形","verse":"诚则形，形则著，著则明，明则动，动则变，变则化，唯天下至诚为能化。",
     "principle":"诚由内形外、由著及化；以至诚感通万物，立感化流行之序。","pinyin":"cheng_ze_xing",
     "signature":"fn cheng_ze_xing(inner) -> transforming",
     "precond":"诚匮、感不通","postcond":"至诚能化，物化",
     "neg":"不诚则隔","steps":["诚","形","著","明","动","变","化"],
     "dispatch":"当宜以诚感化、不宜强为时触发","decision_if":"需诚则形",
     "neg_space":["不诚则隔","强为则逆"]},
    {"n":9,"stratum":"时中达道","title":"时中","verse":"君子之中庸也，君子而时中；小人之中庸也，小人而无忌惮也。",
     "principle":"君子随时处中、权变不离经；以时中行常道，立经权合一之智。","pinyin":"shi_zhong",
     "signature":"fn shi_zhong(context) -> timely_mean",
     "precond":"胶柱、失时宜","postcond":"随时处中，无忌惮",
     "neg":"胶则失宜","steps":["识时","权变","处中","不离经"],
     "dispatch":"当情境流变、宜权变守中时触发","decision_if":"需时中",
     "neg_space":["胶柱鼓瑟则僵","无忌惮则滥"]},
    {"n":10,"stratum":"时中达道","title":"素位而行","verse":"君子素其位而行，不愿乎其外。在上位不陵下，在下位不援上。",
     "principle":"素位而行、安分尽责；以上不陵下不援，立本位尽分之德。","pinyin":"su_wei_er_xing",
     "signature":"fn su_wei_er_xing(self) -> station_act",
     "precond":"愿乎外、援陵","postcond":"素位尽分，安",
     "neg":"愿外则妄","steps":["安位","不援","不陵","尽分"],
     "dispatch":"当宜守本位尽责、不宜攀援时触发","decision_if":"需素位而行",
     "neg_space":["愿乎其外则妄","陵下援上则失"]},
    {"n":11,"stratum":"时中达道","title":"至诚如神","verse":"至诚之道，可以前知。国家将兴，必有祯祥；见乎蓍龟，动乎四体。",
     "principle":"至诚能前知、于几微见祯祥；以诚通几，立先知先觉之境。","pinyin":"zhi_cheng_ru_shen",
     "signature":"fn zhi_cheng_ru_shen(omen) -> foreknow",
     "precond":"昧几、诚不至","postcond":"至诚前知，几先",
     "neg":"昧则失几","steps":["至诚","察几","见祥","前知"],
     "dispatch":"当宜察几先、不宜昧于征兆时触发","decision_if":"需至诚如神",
     "neg_space":["昧几则失机","穿凿则妄"]},
    {"n":12,"stratum":"时中达道","title":"中庸不可能","verse":"天下国家可均也，爵禄可辞也，白刃可蹈也，中庸不可能也。",
     "principle":"中庸极难、非强力可至；君子依乎中庸、遁世不见知而不悔，立恒守之难。","pinyin":"zhong_yong_bu_ke_neng",
     "signature":"fn zhong_yong_bu_ke_neng(self) -> persevere_mean",
     "precond":"易退、难恒","postcond":"依中庸不悔，恒",
     "neg":"易退则失","steps":["知难","依中庸","遁世不悔","恒守"],
     "dispatch":"当宜恒守常道、不宜因难退时触发","decision_if":"需中庸不可能而守",
     "neg_space":["遇难则退则失","炫则非中庸"]},
    {"n":13,"stratum":"时中达道","title":"三重","verse":"王天下有三重焉：议礼、制度、考文。故君子笃恭而天下平。",
     "principle":"议礼制度考文三重、立天下法度；以笃恭化天下，立制度化成之纲。","pinyin":"san_zhong",
     "signature":"fn san_zhong(rule) -> triple_order",
     "precond":"礼废、度乱","postcond":"三重立，天下平",
     "neg":"废礼则乱","steps":["议礼","制度","考文","天下平"],
     "dispatch":"当宜立法度、不宜废礼时触发","decision_if":"需立三重",
     "neg_space":["废礼则乱","度不一则争"]},
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
        "COP-ID": "HS-RU-ZY%02d-20260815-%02d" % (g["n"], g["n"]),
        "source_expert": "zhongyong_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用 / 心法条目分解)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": "诸子百家·儒家·中庸·第%02d条(%s)" % (g["n"], g["title"]),
        "stratum": "诸子百家·儒家·中庸·" + g["stratum"],
        "soul": {
            "identity": "中庸·第%02d条《%s》" % (g["n"], g["title"]),
            "core": g["principle"],
            "verse": g["verse"],
            "role": "思维协议 (诸子百家 / 儒家 / 中庸心法)",
            "category": "诸子百家 / 儒家 / 中庸 / " + g["stratum"],
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
    report = {"total": len(ZY), "ok": 0, "skip": 0, "fail": 0, "cop_ids": [], "nca_ids": []}
    for g in ZY:
        n = g["n"]
        fname = "第%02d条-%s.yaml" % (n, g["title"])
        out_path = os.path.join(ZY_DIR, fname)
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
                scope=".tdca-protocol/cognitive-compiler/hundred_schools/zhongyong (第%02d条-%s COP)" % (n, g["title"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-ZY-M%02d" % n,
                notes="中庸第%02d条《%s》编译为 COP, 验证=%s" % (n, g["title"], cop["validation"]["passed"]),
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
        "中和本体": "天命之谓性/致中和/中庸 (立体用、立常道, 性道教一贯)",
        "诚体工夫": "慎独/诚者天之道/诚明/诚则形/择善固执 (诚为天道人道合一, 心性开显)",
        "时中达道": "时中/素位而行/至诚如神/中庸不可能/三重 (权变守中, 经权合一, 制度化成)",
    }
    items = []
    for g in ZY:
        items.append({
            "n": g["n"], "title": g["title"], "cop_id": "HS-RU-ZY%02d-20260815-%02d" % (g["n"], g["n"]),
            "stratum": g["stratum"], "verse": g["verse"], "primitive": g["pinyin"],
            "file": "第%02d条-%s.yaml" % (g["n"], g["title"]),
        })
    by_stratum = {}
    for g in ZY:
        by_stratum.setdefault(g["stratum"], []).append(g["n"])
    manifest = {
        "library": "zhongyong_xinfa",
        "role": "儒家系统思维·孔门心法库 (Chinese cultural compound operand source, 心法条目级)",
        "note": "《中庸》为孔门心法, 以'中和'立体用、以'诚'立天道人道合一, 是儒家心性论中枢。"
                "逐条编译为独立可调用的思维协议(COP), 按三谱系归类。后续作'中国文化 ⊕ 马克思主义'化合的中方基协议素材。",
        "base_protocol": "TDCA-CORE-20260815-01",
        "compiler": "zhongyong/compile_zhongyong.py",
        "schema": "同构麦肯锡 COP (stratum+steps, 兼容 compose_general)",
        "total_items": len(ZY),
        "strata_taxonomy": strata_def,
        "strata_count": {k: len(v) for k, v in by_stratum.items()},
        "items": items,
        "composition": {
            "composer": "../../compositions/compose_general.py",
            "compatible_with": ["TDCA核心", "道家(道德经)", "论语", "大学", "孟子", "荀子", "墨法名阴阳", "马克思主义", "兵法", "博弈论", "机制设计", "场景", "现代学科库"],
            "compound_first_principle": "化合 > 物理叠加 (interpretant 注入语义涌现, 非内禀)",
            "compound_target": "中国文化 ⊕ 马克思主义 = 毛泽东思想思维协议 (化合旗舰范式)",
            "verified_demo": "compose_mao.py (马克思主义·实践论 经 中庸·中和/诚 解释 → 实事求是·两结合的活的灵魂)",
        },
    }
    mp = os.path.join(ZY_DIR, "zhongyong_manifest.yaml")
    with open(mp, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    print("[OK] 系统谱系清单 -> %s (三谱系: %s)" % (mp, "/".join(strata_def.keys())))


if __name__ == "__main__":
    print("===== 中庸 思维协议编译 (MEMO-006 规范, 儒家·孔门心法库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % ZY_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    write_manifest()
    print("系统思维谱系: 中和本体/诚体工夫/时中达道")
    print("===== 编译完成 =====")
