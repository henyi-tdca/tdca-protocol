# -*- coding: utf-8 -*-
"""法家 思维协议编译器 (诸子百家·法术势)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 把《法家》(商鞅·法 / 申不害·术 / 慎到·势 / 韩非·法术势合一) 以"法术势"为系统骨架
逐条编译为独立可调用的思维协议 (COP)。用户立项: B. 续编诸子百家: 法家(法术势)。
法家以明法任势、循名责实为治术枢纽, 立君主南面之术与富强之基。逐条 = 一个独立思维原语,
按三谱系归类 (法度三器 / 刑名权柄 / 时变耕战)。每目以 TDCA-CORE-20260815-01 为可信底座。
同构: 与 compile_daxue.py 同构, 升级为"义理条目"。
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
FA_DIR = _THIS
ensure_dirs()
os.makedirs(FA_DIR, exist_ok=True)

# ---------- 法家 思维协议知识库 (每条一思维原语) ----------
# 三谱系: 法度三器 / 刑名权柄 / 时变耕战
FA = [
    {"n":1,"stratum":"法度三器","title":"法","verse":"壹赏壹刑壹教，明法而治。法令者，民之命也，为治之本也。",
     "principle":"法明令一、壹赏壹刑；以公开之法为治本，立可预期之秩序。","pinyin":"fa_du",
     "signature":"fn fa_du(rule) -> clear_law",
     "precond":"法乱、赏刑私","postcond":"明法而治，民知所从",
     "neg":"法私则乱","steps":["立壹法","壹赏刑","明示","民从"],
     "dispatch":"当宜立法公开一律、不宜任私时触发","decision_if":"需立法度",
     "neg_space":["法不公开则民惑","刑赏私则乖"]},
    {"n":2,"stratum":"法度三器","title":"术","verse":"术者，因任而授官，循名而责实，操杀生之柄，课群臣之能者也。藏于无事，示无为。",
     "principle":"术为御下之巧、循名责实；以潜御群臣，立考课之方。","pinyin":"shu_yu",
     "signature":"fn shu_yu(control) -> technique",
     "precond":"任非其能、名实乖","postcond":"循名责实，臣服",
     "neg":"无术则蔽","steps":["因任","授官","责实","课能"],
     "dispatch":"当宜考课群臣、不宜暗于下时触发","decision_if":"需用术",
     "neg_space":["无术则蔽于奸","术露则臣窥"]},
    {"n":3,"stratum":"法度三器","title":"势","verse":"贤未可必，而势位足以屈贤者也。尧为匹夫不能治三人，而桀为天子能乱天下。",
     "principle":"势位足恃、不专赖贤；以位设威，立必然之柄。","pinyin":"shi_wei",
     "signature":"fn shi_wei(power) -> positional_power",
     "precond":"无位、威不立","postcond":"乘势位，令行",
     "neg":"失势则痿","steps":["识势","设位","乘威","令行"],
     "dispatch":"当宜立威设位、不宜恃贤孤时触发","decision_if":"需立势",
     "neg_space":["弃势则痿","专恃贤则危"]},
    {"n":4,"stratum":"法度三器","title":"法术势合一","verse":"君执柄以处势，故令行禁止；法者，宪令著于官府；术者，藏之于胸中以偶众端。",
     "principle":"法术势相参、三位一体；以法立公开、术御暗、势设威，立君道全功。","pinyin":"fa_shu_shi_he_yi",
     "signature":"fn fa_shu_shi_he_yi(govern) -> trinity",
     "precond":"偏一器、不全","postcond":"法术势合，治成",
     "neg":"偏则失","steps":["立法","用术","乘势","相参"],
     "dispatch":"当宜三器并用、不宜偏废时触发","decision_if":"需法术势合一",
     "neg_space":["专任法则下欺","专任术则危","专任势则暴"]},
    {"n":5,"stratum":"刑名权柄","title":"刑名参同","verse":"循名责实，综核名实。言事者必以其名效其实，功当其事，事当其言。",
     "principle":"刑名参同、综核名实；以名课实、以实正名，立考核之准。","pinyin":"xing_ming_can_tong",
     "signature":"fn xing_ming_can_tong(audit) -> name_reality",
     "precond":"名实乖、言浮","postcond":"名实参同，功当",
     "neg":"名实乖则乱","steps":["立名","课实","参同","正名"],
     "dispatch":"当宜核名实、不宜言过其时触发","decision_if":"需刑名参同",
     "neg_space":["名实乖则赏罚滥","言浮则事乖"]},
    {"n":6,"stratum":"刑名权柄","title":"二柄","verse":"二柄者，刑德也。杀戮之谓刑，庆赏之谓德。为人臣者畏诛罚而利庆赏。",
     "principle":"二柄刑德、赏罚为君；以庆赏驱利、杀戮慑畏，立驭臣双刃。","pinyin":"er_bing",
     "signature":"fn er_bing(reward_punish) -> two_handles",
     "precond":"赏罚不明、柄移","postcond":"刑德立，臣畏利",
     "neg":"柄移则危","steps":["执赏","执罚","明二柄","臣服"],
     "dispatch":"当宜明赏罚二柄、不宜柄下移时触发","decision_if":"需用二柄",
     "neg_space":["柄移臣则篡","赏罚滥则怨"]},
    {"n":7,"stratum":"刑名权柄","title":"明主治吏不治民","verse":"圣人治吏不治民。吏者，所以治民也；明主治吏则官皆得其人。",
     "principle":"明主治吏不治民、以吏治民；以抓关键层级，立管理之要。","pinyin":"ming_zhu_zhi_li",
     "signature":"fn ming_zhu_zhi_li(manage) -> rule_officials",
     "precond":"亲民、纲乱","postcond":"治吏，官得人",
     "neg":"亲民则紊","steps":["识关键","治吏","择人","民自理"],
     "dispatch":"当宜抓管理节点、不宜事必亲时触发","decision_if":"需治吏不治民",
     "neg_space":["事必亲则紊","吏非其人则败"]},
    {"n":8,"stratum":"时变耕战","title":"耕战","verse":"国之所以兴者，农战也。利出于一孔，则国多物；出十孔，则国少物。",
     "principle":"耕战为本、利出一孔；以农战聚国力，立富强之基。","pinyin":"geng_zhan",
     "signature":"fn geng_zhan(state) -> agro_war",
     "precond":"利孔杂、国弱","postcond":"一孔利，国富兵强",
     "neg":"多孔则弱","steps":["重农","励战","一孔","国强"],
     "dispatch":"当宜聚国力于本、不宜分利时触发","decision_if":"需耕战为本",
     "neg_space":["利出多孔则弱","弃农战则危"]},
    {"n":9,"stratum":"时变耕战","title":"不法古不循今","verse":"世异则事异，事异则备变。圣人不法古，不修今，因世而为之治。",
     "principle":"世异事异、因时变法；不法古不循今，立变法之勇。","pinyin":"bu_fa_gu_bu_xun_jin",
     "signature":"fn bu_fa_gu_bu_xun_jin(reform) -> timely_reform",
     "precond":"泥古、法弊","postcond":"因世变法，治宜",
     "neg":"泥古则弊","steps":["察世异","识事变","变法","宜民"],
     "dispatch":"当宜因时变法、不宜泥古时触发","decision_if":"需不法古不循今",
     "neg_space":["泥古则法弊","骤变则民扰"]},
    {"n":10,"stratum":"时变耕战","title":"自利人性","verse":"人行事，非有名则利之也；挟自为心，故可得而用也。",
     "principle":"人挟自为心、趋利避害；以因利设制、用其自为，立制度之人性基。","pinyin":"zi_li_ren_xing",
     "signature":"fn zi_li_ren_xing(design) -> self_interest",
     "precond":"逆性设制、敝","postcond":"因利设制，用自为",
     "neg":"逆性则敝","steps":["识自为","因利","设制","成事"],
     "dispatch":"当宜顺人性设制、不宜强拂时触发","decision_if":"需因自利人性",
     "neg_space":["逆性设制则敝","纵利无度则争"]},
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
        "COP-ID": "HS-FA-%02d-20260815-%02d" % (g["n"], g["n"]),
        "source_expert": "fajia_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用 / 义理条目分解)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": "诸子百家·法家·第%02d条(%s)" % (g["n"], g["title"]),
        "stratum": "诸子百家·法家·" + g["stratum"],
        "soul": {
            "identity": "法家·第%02d条《%s》" % (g["n"], g["title"]),
            "core": g["principle"],
            "verse": g["verse"],
            "role": "思维协议 (诸子百家 / 法家 / 法术势)",
            "category": "诸子百家 / 法家 / " + g["stratum"],
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
    report = {"total": len(FA), "ok": 0, "skip": 0, "fail": 0, "cop_ids": [], "nca_ids": []}
    for g in FA:
        n = g["n"]
        fname = "第%02d条-%s.yaml" % (n, g["title"])
        out_path = os.path.join(FA_DIR, fname)
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
                scope=".tdca-protocol/cognitive-compiler/hundred_schools/fajia (第%02d条-%s COP)" % (n, g["title"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-FA-M%02d" % n,
                notes="法家第%02d条《%s》编译为 COP, 验证=%s" % (n, g["title"], cop["validation"]["passed"]),
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
        "法度三器": "法/术/势/法术势合一 (明法任势用术, 三位一体立君道)",
        "刑名权柄": "刑名参同/二柄/明主治吏不治民 (循名责实, 赏罚双刃, 抓关键层级)",
        "时变耕战": "耕战/不法古不循今/自利人性 (利出一孔富强, 因时变法, 顺性设制)",
    }
    items = []
    for g in FA:
        items.append({
            "n": g["n"], "title": g["title"], "cop_id": "HS-FA-%02d-20260815-%02d" % (g["n"], g["n"]),
            "stratum": g["stratum"], "verse": g["verse"], "primitive": g["pinyin"],
            "file": "第%02d条-%s.yaml" % (g["n"], g["title"]),
        })
    by_stratum = {}
    for g in FA:
        by_stratum.setdefault(g["stratum"], []).append(g["n"])
    manifest = {
        "library": "fajia_fashushi",
        "role": "诸子百家系统思维·法术势库 (Chinese cultural compound operand source, 义理条目级)",
        "note": "法家以明法任势、循名责实为治术枢纽, 立君主南面之术与富强之基。"
                "逐条编译为独立可调用的思维协议(COP), 按三谱系归类。后续作'中国文化 ⊕ 马克思主义'化合的中方基协议素材。",
        "base_protocol": "TDCA-CORE-20260815-01",
        "compiler": "fajia/compile_fajia.py",
        "schema": "同构麦肯锡 COP (stratum+steps, 兼容 compose_general)",
        "total_items": len(FA),
        "strata_taxonomy": strata_def,
        "strata_count": {k: len(v) for k, v in by_stratum.items()},
        "items": items,
        "composition": {
            "composer": "../../compositions/compose_general.py",
            "compatible_with": ["TDCA核心", "道家", "儒", "墨家", "名家", "阴阳家", "马克思主义", "兵法", "博弈论", "机制设计", "场景", "现代学科库"],
            "compound_first_principle": "化合 > 物理叠加 (interpretant 注入语义涌现, 非内禀)",
            "compound_target": "中国文化 ⊕ 马克思主义 = 毛泽东思想思维协议 (化合旗舰范式)",
            "verified_demo": "撰写中 (法家法术势/自利人性 ⟂ 马克思主义唯物史观/国家学说)",
        },
    }
    mp = os.path.join(FA_DIR, "fajia_manifest.yaml")
    with open(mp, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    print("[OK] 系统谱系清单 -> %s (三谱系: %s)" % (mp, "/".join(strata_def.keys())))


if __name__ == "__main__":
    print("===== 法家 思维协议编译 (MEMO-006 规范, 诸子百家·法术势库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % FA_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    write_manifest()
    print("系统思维谱系: 法度三器/刑名权柄/时变耕战")
    print("===== 编译完成 =====")
