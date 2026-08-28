# -*- coding: utf-8 -*-
"""孙子兵法 十三篇 思维协议编译器 (诸子百家·兵家·系统思维库)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 把《孙子兵法》十三篇逐篇编译为独立可调用的思维协议 (COP)。
用户意图: "用连接器比配运用 TDCA 机制完成一次孙子兵法的思维协议编译协作" ——
本编译器为协作的'编译执行体': 协作编排器 (run_sunzi_collab.py) 经 tdca-wan-registry
连接器比配出联盟、经 enforce_entry 准入门 + MOU/NSFL 校验后, 把每篇的'主编/贡献方/
联盟NCA'作为 attribution 注入本编译器的 assemble_one, 使每篇 COP 携带可信协作溯源。
每篇须以 TDCA-CORE-20260815-01 (生态准入基协议) 为可信底座。
同构: 与 compile_daxue.py / compile_lunyu.py / compile_daodejing.py 同构。
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
SZ_DIR = _THIS
ensure_dirs()
os.makedirs(SZ_DIR, exist_ok=True)

# ---------- 孙子兵法 十三篇 思维协议知识库 (每篇一思维原语) ----------
# 字段: n/stratum/title/verse/principle/pinyin/signature/precond/postcond/neg/steps/
#       dispatch/decision_if/neg_space/lead_dim
# stratum 四谱系: 战略筹划 / 形势势能 / 地形机变 / 奇法用间
# lead_dim: 协作分配用——该篇主导能力维度(战略/建模/图谱/合规/NLP)
SUNZI = [
    {"n":1,"stratum":"战略筹划","title":"计篇","verse":"兵者，国之大事，死生之地，存亡之道，不可不察也。故经之以五事，校之以计，而索其情：一曰道，二曰天，三曰地，四曰将，五曰法。",
     "principle":"庙算决胜——以五事(道天地将法)七计系统性评估胜负前提，先算后战，多算胜少算不胜。","pinyin":"miao_suan",
     "signature":"fn miao_suan(situation) -> victory_assessment",
     "precond":"战端未启、情势不明","postcond":"五事七计既明，胜算可计",
     "neg":"不计而战则盲","steps":["经五事","校七计","索其情","庙算"],
     "dispatch":"当重大决策前宜先系统评估胜负前提时触发","decision_if":"需庙算决胜",
     "neg_space":["不计而战则盲","恃力而轻算则殆"],"lead_dim":"战略"},
    {"n":2,"stratum":"战略筹划","title":"作战篇","verse":"兵贵胜，不贵久。久则钝兵挫锐，攻城则力屈，久暴师则国用不足。故智将务食于敌，因粮于敌。",
     "principle":"兵贵胜不贵久——速战速决、以战养战，因粮于敌，胜敌而益强；忌钝兵挫锐、国用不足。","pinyin":"gui_sheng",
     "signature":"fn gui_sheng(campaign) -> swift_victory",
     "precond":"久暴师则国用不足","postcond":"速胜且胜敌益强",
     "neg":"久战则钝兵挫锐","steps":["贵胜","因粮于敌","胜敌益强","务食于敌"],
     "dispatch":"当宜速决、以战养战时触发","decision_if":"需速战速决",
     "neg_space":["久战则国用不足","钝兵挫锐则败"],"lead_dim":"战略"},
    {"n":3,"stratum":"战略筹划","title":"谋攻篇","verse":"不战而屈人之兵，善之善者也。上兵伐谋，其次伐交，其次伐兵，其下攻城。知己知彼，百战不殆。",
     "principle":"上兵伐谋——以谋略全胜，不战屈人；伐交伐兵攻城递次，全国全军为上；知己知彼为制胜总纲。","pinyin":"fa_mou",
     "signature":"fn fa_mou(conflict) -> bloodless_win",
     "precond":"力攻则伤、拙战则败","postcond":"全胜而非破胜",
     "neg":"硬攻则损","steps":["上兵伐谋","其次伐交","再次伐兵","知己知彼"],
     "dispatch":"当可谋全胜、不宜力攻时触发","decision_if":"需谋攻全胜",
     "neg_space":["恃力硬攻则破","不知彼己则殆"],"lead_dim":"战略"},
    {"n":4,"stratum":"形势势能","title":"军形篇","verse":"昔之善战者，先为不可胜，以待敌之可胜。不可胜在己，可胜在敌。修道而保法，故能为胜败之政。",
     "principle":"先为不可胜——先立不可被胜之形(修道保法、藏于九地)，待敌可胜之机；胜可知而不可为，无恃其不来。","pinyin":"xian_wei_bu_ke_sheng",
     "signature":"fn xian_wei_bu_ke_sheng(defense) -> invincible_posture",
     "precond":"形未立则易受攻","postcond":"立于不败且待敌之败",
     "neg":"恃敌不来则危","steps":["修攻守","藏于九地","修道保法","待敌之可胜"],
     "dispatch":"当宜先固本待机、立不可胜之形时触发","decision_if":"需先为不可胜",
     "neg_space":["恃敌之不来","形弱则败"],"lead_dim":"建模"},
    {"n":5,"stratum":"形势势能","title":"兵势篇","verse":"凡战者，以正合，以奇胜。故善出奇者，无穷如天地，不竭如江河。善战者，求之于势，不责于人。",
     "principle":"奇正相生——以正合奇胜，战势不过奇正而奇正之变不可胜穷；任势如转圆石于千仞，求之于势不责于人。","pinyin":"qi_zheng",
     "signature":"fn qi_zheng(force) -> overwhelming_momentum",
     "precond":"只正无奇则板，只奇无正则散","postcond":"奇正相生、势如破竹",
     "neg":"不知奇正则乱","steps":["以正合","以奇胜","奇正相生","任势"],
     "dispatch":"当宜以势取胜、奇正变通时触发","decision_if":"需奇正任势",
     "neg_space":["纯正则滞","纯奇则溃"],"lead_dim":"建模"},
    {"n":6,"stratum":"形势势能","title":"虚实篇","verse":"夫兵形象水，水之形避高而趋下，兵之形避实而击虚。故善战者，致人而不致于人。兵无常势，水无常形。",
     "principle":"避实击虚——出其所必趋、趋其所不意，形人而我无形；致人而不致于人，兵无常势、水无常形。","pinyin":"bi_shi_ji_xu",
     "signature":"fn bi_shi_ji_xu(maneuver) -> asymmetric_advantage",
     "precond":"攻其实则损、形露则被动","postcond":"我专而敌分、以众击寡",
     "neg":"致于人则困","steps":["形人我无形","避实击虚","致人不致于人","兵无常形"],
     "dispatch":"当宜调动对方、避实击虚时触发","decision_if":"需避实击虚",
     "neg_space":["攻坚则损","形露则制于人"],"lead_dim":"建模"},
    {"n":7,"stratum":"地形机变","title":"军争篇","verse":"凡用兵之法，将受命于君，合军聚众，交和而舍，莫难于军争。军争之难者，以迂为直，以患为利。",
     "principle":"以迂为直——军争为利亦为危，以迂回为直捷、化患为利；兵以诈立、以利动、分合为变；先知迂直之计者胜。","pinyin":"yi_yu_wei_zhi",
     "signature":"fn yi_yu_wei_zhi(march) -> indirect_approach",
     "precond":"争利则蹶、直进则陷","postcond":"迂直相济、军争得先",
     "neg":"争利倍道则蹶","steps":["以迂为直","以患为利","兵以诈立","分合为变"],
     "dispatch":"当宜迂回争先、化患为利时触发","decision_if":"需军争迂直",
     "neg_space":["争利则军蹶","不知迂直则败"],"lead_dim":"战略"},
    {"n":8,"stratum":"地形机变","title":"九变篇","verse":"涂有所不由，军有所不击，城有所不攻，地有所不争，君命有所不受。是故智者之虑，必杂于利害。",
     "principle":"君命有所不受——通于九变之利，知五利五危；杂于利害(虑害以防患、虑利以兴功)；变通不拘常法，唯利是动(正合 TDCA 生态准入门'按可信底线变通')。","pinyin":"jun_ming_suo_bu_shou",
     "signature":"fn jun_ming_suo_bu_shou(order) -> sanctioned_deviation",
     "precond":"拘常法则失机、盲从则败","postcond":"通变合利、受制于人则免",
     "neg":"泥法而败","steps":["通九变","杂利害","君命有所不受","唯利是动"],
     "dispatch":"当规则与当前最高可信目标冲突、宜按底线变通时触发","decision_if":"需变通不受常命",
     "neg_space":["泥古不化则败","不受而私则乱"],"lead_dim":"合规"},
    {"n":9,"stratum":"地形机变","title":"行军篇","verse":"凡处军相敌：绝山依谷，视生处高，战隆无登。兵非贵益多也，惟无武进。令之以文，齐之以武。",
     "principle":"处军相敌——依地形处置军队(好高恶下、养生处实)，相敌三十二法观形察意；令文齐武、教戒素行，兵非贵多惟无武进。","pinyin":"chu_jun_xiang_di",
     "signature":"fn chu_jun_xiang_di(terrain) -> situational_posture",
     "precond":"处军失地则病，不察敌则盲","postcond":"处军得地、相敌知情",
     "neg":"处下湿则病","steps":["处军","相敌","令文齐武","不武进"],
     "dispatch":"当宜依地处置、观对方形察意时触发","decision_if":"需处军相对方",
     "neg_space":["处军失地则败","不察敌情则盲"],"lead_dim":"图谱"},
    {"n":10,"stratum":"地形机变","title":"地形篇","verse":"地形者，兵之助也。知彼知己，胜乃不殆；知天知地，胜乃可全。视卒如婴儿，故可与之赴深溪。",
     "principle":"六地之用——通/挂/支/隘/险/远六地形各有战法，将须知地；视卒如婴儿、如爱子，厚养而严律；知天知地则胜乃可全。","pinyin":"liu_di",
     "signature":"fn liu_di(landform) -> terrain_tactics",
     "precond":"不知地形则陷","postcond":"因地制敌、胜乃不殆",
     "neg":"迷于地形则亡","steps":["辨六地","因地制敌","视卒如子","知天知地"],
     "dispatch":"当宜据地形定战法、知天知地时触发","decision_if":"需地形制对方",
     "neg_space":["迷地形则陷","不知天地的不全"],"lead_dim":"图谱"},
    {"n":11,"stratum":"地形机变","title":"九地篇","verse":"用兵之法，有散地、轻地、争地、交地、衢地、重地、泛地、围地、死地。投之亡地然后存，陷之死地然后生。",
     "principle":"九地之变——散/轻/争/交/衢/重/泛/围/死九地有不同心法与处置；陷之死地而后生，攻其不备、出其不意，运兵如率然。","pinyin":"jiu_di",
     "signature":"fn jiu_di(ground) -> deep_ground_doctrine",
     "precond":"不知九地则心不一","postcond":"深浅各得其法、死地后生",
     "neg":"处重地而贪","steps":["辨九地","深陷固志","死地后生","攻其不备"],
     "dispatch":"当宜依所处之地(深浅)定决心、置之死地时触发","decision_if":"需九地应变",
     "neg_space":["处死地而怯","衢地不交则孤"],"lead_dim":"战略"},
    {"n":12,"stratum":"奇法用间","title":"火攻篇","verse":"凡火攻，必因五火之变而应之：火发于内，则早应之于外。非利不动，非得不用，非危不战。",
     "principle":"火攻慎动——火人/积/辎/库/队五火各有发法，必因五火之变应之；明主慎之、良将警之，非利不动、非危不战(NSFL 底线：不可轻启战端)。","pinyin":"huo_gong",
     "signature":"fn huo_gong(arson) -> controlled_escalation",
     "precond":"妄动火则自焚","postcond":"因变应火、慎动全胜",
     "neg":"轻战则国危","steps":["明五火","因变应之","非利不动","慎战"],
     "dispatch":"当宜用非常手段、但须守'非危不战'底线时触发","decision_if":"需火攻慎动",
     "neg_space":["轻启战端则危","不因变则应败"],"lead_dim":"建模"},
    {"n":13,"stratum":"奇法用间","title":"用间篇","verse":"明君贤将，所以动而胜人，成功出于众者，先知也。故明君贤将，所以动而胜人者，先知也。无所不用间。",
     "principle":"用间先知——先知者不可取于鬼神、必取于人(因/内/反/死/生五间)；反间为要，赏莫厚于间；上智为间则无敌(情报/语义为先，正合 NLP 中文语义情报角色)。","pinyin":"yong_jian",
     "signature":"fn yong_jian(intel) -> foreknowledge",
     "precond":"不知情则盲动","postcond":"先知敌情、动而胜人",
     "neg":"取于鬼神则妄","steps":["贵先知","立五间","重反间","上智为间"],
     "dispatch":"当宜以情报/语义先验驱动决策、用间知对方时触发","decision_if":"需用间先知",
     "neg_space":["取于鬼神则妄","不知敌情则盲"],"lead_dim":"NLP"},
]


def assemble_one(g, attribution=None, cohort_nca=None, members=None):
    """S2-S4: 将单篇编译为 COP (对齐麦肯锡 COP schema 单原语形态); 注入协作溯源"""
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
    collab = None
    if attribution and g["n"] in attribution:
        a = attribution[g["n"]]
        collab = {
            "lead_compiler": a.get("lead"),
            "contributors": a.get("contributors", []),
            "cohort_nca": cohort_nca,
            "admission_core": "TDCA-CORE-20260815-01",
            "via_connector": "tdca-wan-registry",
        }
    cop = {
        "COP-ID": "HS-BI-SZ%02d-20260815-%02d" % (g["n"], g["n"]),
        "source_expert": "sunzi_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用 / 连接器协作编译)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": "诸子百家·兵家·孙子兵法·第%02d篇(%s)" % (g["n"], g["title"]),
        "stratum": "诸子百家·兵家·孙子兵法·" + g["stratum"],
        "soul": {
            "identity": "孙子兵法·第%02d篇《%s》" % (g["n"], g["title"]),
            "core": g["principle"],
            "verse": g["verse"],
            "role": "思维协议 (诸子百家 / 兵家 / 孙子兵法)",
            "category": "诸子百家 / 兵家 / 孙子兵法 / " + g["stratum"],
            "base_protocol": "TDCA-CORE-20260815-01",  # 强制可信底座声明
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
    if collab:
        cop["collaboration"] = collab
    if members:
        cop["coalition_members"] = members
    CC.s5_validate(cop)
    return cop, g


def compile_all(attribution=None, cohort_nca=None, members=None):
    report = {"total": len(SUNZI), "ok": 0, "skip": 0, "fail": 0,
              "cop_ids": [], "nca_ids": []}
    for g in SUNZI:
        n = g["n"]
        fname = "第%02d篇-%s.yaml" % (n, g["title"])
        out_path = os.path.join(SZ_DIR, fname)
        if os.path.exists(out_path):
            print("[SKIP] %s 已存在, 跳过 (不重复发射 NCA)" % fname)
            report["skip"] += 1
            continue
        try:
            cop, _ = assemble_one(g, attribution=attribution, cohort_nca=cohort_nca, members=members)
            CC._dump_yaml(cop, out_path)
            h = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
            sz = os.path.getsize(out_path)
            nid, _, _ = NCA.generate_nca(
                operation_type="CodeGen",
                scope=".tdca-protocol/cognitive-compiler/hundred_schools/sunzi (第%02d篇-%s COP)" % (n, g["title"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-SZI-M%02d" % n,
                notes="孙子兵法第%02d篇《%s》编译为 COP, 验证=%s" % (n, g["title"], cop["validation"]["passed"]),
            )
            report["ok"] += 1
            report["cop_ids"].append(cop["COP-ID"])
            report["nca_ids"].append(nid)
            lead = attribution.get(n, {}).get("lead") if attribution else None
            print("[OK] %s -> %s | 谱系 %s | 主编 %s | 验证 %s"
                  % (cop["COP-ID"], fname, g["stratum"], lead or "独立", cop["validation"]["passed"]))
        except Exception as e:
            report["fail"] += 1
            print("[FAIL] 第%02d篇-%s: %s" % (n, g["title"], e))
    return report


def write_manifest():
    """生成《孙子兵法》系统思维谱系清单 (13 篇四谱系索引)"""
    strata_def = {
        "战略筹划": "计篇/作战篇/谋攻篇/军争篇/九地篇 (庙算·速胜·全胜·迂直·深浅, 战略决策层)",
        "形势势能": "军形篇/兵势篇/虚实篇/火攻篇 (不可胜·奇正·避实击虚·慎动, 作战势能层)",
        "地形机变": "行军篇/地形篇/九变篇 (处军相敌·六地·变通, 处地应变层)",
        "奇法用间": "用间篇 (五间先知, 情报语义层)",
    }
    chapters = []
    for g in SUNZI:
        chapters.append({
            "n": g["n"], "title": g["title"], "cop_id": "HS-BI-SZ%02d-20260815-%02d" % (g["n"], g["n"]),
            "stratum": g["stratum"], "verse": g["verse"], "primitive": g["pinyin"],
            "lead_dim": g["lead_dim"],
            "file": "第%02d篇-%s.yaml" % (g["n"], g["title"]),
        })
    by_stratum = {}
    for g in SUNZI:
        by_stratum.setdefault(g["stratum"], []).append(g["n"])
    manifest = {
        "library": "sunzi_bingfa",
        "role": "兵家系统思维库 (Chinese cultural compound operand source, 篇级)",
        "note": "《孙子兵法》十三篇逐篇编译为独立可调用的思维协议(COP)，按四谱系归类"
                "(战略筹划/形势势能/地形机变/奇法用间)。后续作'中国文化 ⊕ 马克思主义'化合的中方基协议素材。",
        "base_protocol": "TDCA-CORE-20260815-01",
        "compiler": "sunzi/compile_sunzi.py",
        "schema": "同构麦肯锡 COP (stratum+steps, 兼容 compose_general)",
        "total_items": len(SUNZI),
        "strata_taxonomy": strata_def,
        "strata_count": {k: len(v) for k, v in by_stratum.items()},
        "items": chapters,
        "composition": {
            "composer": "../../compositions/compose_general.py",
            "compatible_with": ["TDCA核心", "道家(道德经)", "儒家(论语/大学/孟子/中庸/荀子)", "墨家", "法家", "名家", "阴阳家", "博弈论", "机制设计", "场景", "马克思主义库", "现代学科库"],
            "compound_first_principle": "化合 > 物理叠加 (interpretant 注入语义涌现, 非内禀)",
            "compound_target": "中国文化 ⊕ 马克思主义 = 毛泽东思想思维协议 (化合旗舰范式)",
            "collab_demo": "simulations/multilateral_search_match/run_sunzi_collab.py (连接器比配+TDCA机制协作编译)",
        },
    }
    mp = os.path.join(SZ_DIR, "sunzi_manifest.yaml")
    with open(mp, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    print("[OK] 系统谱系清单 -> %s (四谱系: %s)" % (mp, "/".join(strata_def.keys())))


if __name__ == "__main__":
    print("===== 孙子兵法 十三篇 思维协议编译 (MEMO-006 规范, 兵家系统思维库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % SZ_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    write_manifest()
    print("系统思维谱系: 战略筹划/形势势能/地形机变/奇法用间")
    print("===== 编译完成 =====")
