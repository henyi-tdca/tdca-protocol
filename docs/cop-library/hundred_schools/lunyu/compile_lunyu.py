# -*- coding: utf-8 -*-
"""论语 20 篇思维协议编译器 (诸子百家·儒家·系统思维篇目库)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 把《论语》20 篇逐篇编译为独立可调用的思维协议 (COP)。
用户判断: "道德经文字虽少却是道家系统思维" → 同理，《论语》20 篇每篇是儒家系统思维单元。
故每篇 = 一个独立思维原语，20 篇共同构成"儒家系统思维"基库，按六谱系归类
(为学教育/仁本忠恕/为政德治/礼乐文质/知人评士/出处大节)。
每篇须以 TDCA-CORE-20260815-01 (生态准入基协议) 为可信底座。
同构: 与 compile_daodejing.py / compile_hundred_schools.py / compile_tdca_core.py 同构,
仅把"单经概览"升级为"篇目系统"(论语天然以 20 篇为单元)。
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
LYU_DIR = _THIS
ensure_dirs()
os.makedirs(LYU_DIR, exist_ok=True)

# ---------- 论语 20 篇思维协议知识库 (每篇一思维原语) ----------
# 字段: n/stratum/title/verse/principle/pinyin/signature/precond/postcond/neg/steps/dispatch/decision_if/neg_space
# stratum 六谱系: 为学教育 / 仁本忠恕 / 为政德治 / 礼乐文质 / 知人评士 / 出处大节
LYU = [
    {"n":1,"stratum":"为学教育","title":"学而","verse":"学而时习之，不亦说乎？巧言令色，鲜矣仁。",
     "principle":"学思时习、孝悌为仁之本、务本而立；以本立道生筑为学修身起点。","pinyin":"xue_er_shi_xi",
     "signature":"fn xue_er_shi_xi(learn) -> rooted_practice",
     "precond":"学而不习、本末倒置","postcond":"时习体仁，本立道生",
     "neg":"务末则本失","steps":["学","时习","孝悌本","本立道生"],
     "dispatch":"当学习只积累不践行、宜务本时触发","decision_if":"需学思时习务本",
     "neg_space":["巧言令色则鲜仁","学而不习则罔"]},
    {"n":2,"stratum":"为政德治","title":"为政","verse":"为政以德，譬如北辰，居其所而众星共之。",
     "principle":"为政以德、德治垂范，上行下效；以垂范代苛令。","pinyin":"wei_zheng_yi_de",
     "signature":"fn wei_zheng_yi_de(govern) -> virtuous_model",
     "precond":"政令严苛、民不从","postcond":"德治垂范，众星共之",
     "neg":"恃法不德则怨","steps":["立德","垂范","导民","共之"],
     "dispatch":"当治理靠威权法令、宜以德垂范时触发","decision_if":"需为政以德",
     "neg_space":["恃刑政则民免而无耻","德不立则令不从"]},
    {"n":3,"stratum":"礼乐文质","title":"八佾","verse":"人而不仁，如礼何？人而不仁，如乐何？",
     "principle":"礼以仁为本，无仁之礼为虚文；以仁实礼。","pinyin":"ba_yi_li_ben",
     "signature":"fn ba_yi_li_ben(rite) -> rite_with_ren",
     "precond":"徒具仪式、失礼之本","postcond":"仁为礼本，礼实情显",
     "neg":"虚礼则伪","steps":["识礼本","立仁","实礼","去僭"],
     "dispatch":"当重形式轻根本、宜返礼之本时触发","decision_if":"需以仁实礼",
     "neg_space":["无仁之礼则虚","僭礼则乱"]},
    {"n":4,"stratum":"仁本忠恕","title":"里仁","verse":"里仁为美；君子喻于义，小人喻于利。朝闻道，夕死可矣。",
     "principle":"居仁处义、喻义不喻利；以仁安身、以义决疑。","pinyin":"li_ren_wei_mei",
     "signature":"fn li_ren_wei_mei(choose) -> dwell_in_ren",
     "precond":"趋利弃义、失安","postcond":"里仁安仁，喻义决行",
     "neg":"喻利则失仁","steps":["择仁里","安仁","喻义","闻道"],
     "dispatch":"当取舍在义利之间、宜居仁由义时触发","decision_if":"需里仁喻义",
     "neg_space":["喻利则溺","不仁则罔"]},
    {"n":5,"stratum":"知人评士","title":"公冶长","verse":"始吾于人也，听其言而信其行；今吾于人也，听其言而观其行。",
     "principle":"听言观行、知行合一验人；以行实言。","pinyin":"ting_yan_guan_xing",
     "signature":"fn ting_yan_guan_xing(judge) -> act_verified",
     "precond":"信言轻行、误判","postcond":"听言观行，知人善任",
     "neg":"信言不验则误","steps":["听言","观行","核验","任人"],
     "dispatch":"当需识人、不可只听其言时触发","decision_if":"需听言观行",
     "neg_space":["偏信言则误","行不副言则伪"]},
    {"n":6,"stratum":"礼乐文质","title":"雍也","verse":"质胜文则野，文胜质则史；文质彬彬，然后君子。",
     "principle":"文质相济、中庸得中；以彬彬成君子之度。","pinyin":"wen_zhi_bin_bin",
     "signature":"fn wen_zhi_bin_bin(self) -> balanced_culture",
     "precond":"偏质野或偏文史","postcond":"文质彬彬，得中成君子",
     "neg":"偏一则失中","steps":["识质","饰文","彬彬","得中"],
     "dispatch":"当质文偏胜、宜取中时触发","decision_if":"需文质彬彬",
     "neg_space":["质胜则野","文胜则史"]},
    {"n":7,"stratum":"为学教育","title":"述而","verse":"述而不作，信而好古；学而不厌，诲人不倦。",
     "principle":"述而不作、传述非创制、信古好学；以述承道。","pinyin":"shu_er_bu_zuo",
     "signature":"fn shu_er_bu_zuo(transmit) -> faithful_transmit",
     "precond":"好妄作、失传承","postcond":"述而不作，信古传道",
     "neg":"妄作则失本","steps":["信古","述承","不厌","不倦"],
     "dispatch":"当宜传述守统、不宜标新妄作时触发","decision_if":"需述而不作",
     "neg_space":["妄作则失统","好古不化则泥"]},
    {"n":8,"stratum":"出处大节","title":"泰伯","verse":"泰伯，其可谓至德也已矣；三以天下让，民无得而称焉。",
     "principle":"至德谦让、以让成天下；以不争而全德。","pinyin":"san_rang_tian_xia",
     "signature":"fn san_rang_tian_xia(yield) -> supreme_yield",
     "precond":"争位失德、乱","postcond":"三让天下，至德无称",
     "neg":"争位则失德","steps":["识至德","让","不居","民化"],
     "dispatch":"当宜谦让全德、不宜争位时触发","decision_if":"需至德谦让",
     "neg_space":["争位则乱","居功则失让"]},
    {"n":9,"stratum":"为学教育","title":"子罕","verse":"子罕言利，与命与仁；君子不器。",
     "principle":"君子不器、通才守道，罕言利而语命仁；以不器成通。","pinyin":"jun_zi_bu_qi",
     "signature":"fn jun_zi_bu_qi(self) -> non_vessel",
     "precond":"专器一隅、失通","postcond":"不器通达，志于道",
     "neg":"器则局限","steps":["识器","不器","志道","通方"],
     "dispatch":"当局限于专才、宜通才守道时触发","decision_if":"需君子不器",
     "neg_space":["成器则局限","言利则溺"]},
    {"n":10,"stratum":"礼乐文质","title":"乡党","verse":"孔子于乡党，恂恂如也；其在宗庙朝廷，便便言。",
     "principle":"礼在践行、容止中节；以身体礼而非口说。","pinyin":"rong_zhi_zhong_li",
     "signature":"fn rong_zhi_zhong_li(act) -> embodied_rite",
     "precond":"言礼不行礼、失实","postcond":"容止中礼，身体力践",
     "neg":"空言则虚","steps":["识礼","中节","践行","身教"],
     "dispatch":"当重言说轻践行、宜以身行礼时触发","decision_if":"需礼在践行",
     "neg_space":["言礼不行则虚","失节则僭"]},
    {"n":11,"stratum":"礼乐文质","title":"先进","verse":"过犹不及；先进于礼乐，野人也。",
     "principle":"过犹不及、取中允当；以无过不及行礼乐。","pinyin":"guo_you_bu_ji",
     "signature":"fn guo_you_bu_ji(act) -> gold_mean",
     "precond":"过或不及、失中","postcond":"过犹不及，各得其中",
     "neg":"偏颇则失宜","steps":["察过","察不及","取中","允当"],
     "dispatch":"当行事过或不及、宜守中庸时触发","decision_if":"需过犹不及",
     "neg_space":["过则失中","不及则废"]},
    {"n":12,"stratum":"仁本忠恕","title":"颜渊","verse":"克己复礼为仁；非礼勿视，非礼勿听，非礼勿言，非礼勿动。",
     "principle":"克己复礼、为仁由己，视听言动归礼；以克己成仁。","pinyin":"ke_ji_fu_li",
     "signature":"fn ke_ji_fu_li(self) -> self_restraint_ren",
     "precond":"纵己逾礼、失仁","postcond":"克己复礼，天下归仁",
     "neg":"纵己则失礼","steps":["克己","复礼","四勿","归仁"],
     "dispatch":"当需自律归礼、不宜放任时触发","decision_if":"需克己复礼",
     "neg_space":["纵己则逾礼","外求仁则远"]},
    {"n":13,"stratum":"为政德治","title":"子路","verse":"必也正名乎！名不正则言不顺，言不顺则事不成。",
     "principle":"正名先行、名实相称，政自顺；以正名立序。","pinyin":"zheng_ming_xian_xing",
     "signature":"fn zheng_ming_xian_xing(govern) -> correct_naming",
     "precond":"名实乖乱、事不成","postcond":"正名顺言，事乃成",
     "neg":"名不正则溃","steps":["正名","顺言","成事","立序"],
     "dispatch":"当名实混乱、宜先正名时触发","decision_if":"需正名先行",
     "neg_space":["名不正则言不顺","实不副名则乱"]},
    {"n":14,"stratum":"知人评士","title":"宪问","verse":"君子耻其言而过其行；邦有道，谷；邦无道，谷，耻也。",
     "principle":"耻言过行、言行相顾；以行实言、不居位贪禄。","pinyin":"chi_guo_qi_xing",
     "signature":"fn chi_guo_qi_xing(self) -> shame_overact",
     "precond":"言过其实、尸位","postcond":"耻过其行，言行相顾",
     "neg":"言过则耻","steps":["察言","验行","耻过","顾行"],
     "dispatch":"当言行脱节、宜耻其言过时触发","decision_if":"需耻言过行",
     "neg_space":["言过其行则耻","无道窃禄则辱"]},
    {"n":15,"stratum":"为政德治","title":"卫灵公","verse":"工欲善其事，必先利其器；无为而治者，其舜也与？",
     "principle":"工利其器、先备后成；儒家式无为在任贤(舜)；以器利事成。","pinyin":"gong_yu_shan_shi",
     "signature":"fn gong_yu_shan_shi(prep) -> sharpen_tool",
     "precond":"器不利、事难成","postcond":"利器善事，任贤无为",
     "neg":"器钝则事废","steps":["识器","利之","备而后动","任贤"],
     "dispatch":"当欲成事先备具、宜利器任贤时触发","decision_if":"需工利其器",
     "neg_space":["器不利则事废","不任贤则劳"]},
    {"n":16,"stratum":"为政德治","title":"季氏","verse":"不患寡而患不均，不患贫而患不安；均无贫，和无寡，安无倾。",
     "principle":"不患寡患不均、均安和；以均调安邦。","pinyin":"bu_huan_bu_jun",
     "signature":"fn bu_huan_bu_jun(justice) -> equitable_peace",
     "precond":"贫富悬殊、不安","postcond":"均无贫，和无寡，安无倾",
     "neg":"不均则倾","steps":["察不均","均之","安之","和无寡"],
     "dispatch":"当分配失衡、宜均平安民时触发","decision_if":"需不患不均",
     "neg_space":["不均则倾","聚敛则怨"]},
    {"n":17,"stratum":"为学教育","title":"阳货","verse":"性相近也，习相远也；唯上知与下愚不移。",
     "principle":"性近习远、习染成性；以教移习、化性起伪。","pinyin":"xing_jin_xi_yuan",
     "signature":"fn xing_jin_xi_yuan(educate) -> nurture_habit",
     "precond":"纵习失教、性远","postcond":"性近习远，教以移习",
     "neg":"纵习则远","steps":["识性近","察习","施教","移习"],
     "dispatch":"当性习可塑、宜以教化习时触发","decision_if":"需性近习远",
     "neg_space":["纵恶习则远","教不得法则泥"]},
    {"n":18,"stratum":"出处大节","title":"微子","verse":"殷有三仁焉：微子去之，箕子为之奴，比干谏而死；道之不行，已知之矣。",
     "principle":"出处有义、道不行则洁身；以义决去留。","pinyin":"chu_chu_zhi_yi",
     "signature":"fn chu_chu_zhi_yi(exit) -> principled_exit",
     "precond":"道不行、宜去留两难","postcond":"出处以义，洁身存道",
     "neg":"枉道则辱","steps":["察道行","量去留","守义","洁身"],
     "dispatch":"当道不行、宜决出处去留时触发","decision_if":"需出处以义",
     "neg_space":["枉道苟容则辱","弃义则失节"]},
    {"n":19,"stratum":"知人评士","title":"子张","verse":"士见危致命，见得思义；执德不弘，信道不笃，焉能为有，焉能为亡。",
     "principle":"执德弘道、见危致命、见得思义；以弘道守士节。","pinyin":"zhi_de_hong_dao",
     "signature":"fn zhi_de_hong_dao(scholar) -> broad_virtue",
     "precond":"执德不弘、信道不笃","postcond":"执德弘、信道笃，士之节",
     "neg":"不弘则亡","steps":["见危","致命","见得","思义"],
     "dispatch":"当士临危得、宜守节思义时触发","decision_if":"需执德弘道",
     "neg_space":["执德不弘则若无","见得忘义则失"]},
    {"n":20,"stratum":"为政德治","title":"尧曰","verse":"尧曰：咨！尔舜，天之历数在尔躬，允执厥中；四海困穷，天禄永终。",
     "principle":"允执厥中、天命所归在允中；以中道承天命。","pinyin":"yun_zhi_jue_zhong",
     "signature":"fn yun_zhi_jue_zhong(rule) -> hold_the_mean",
     "precond":"偏倚失中、天命去","postcond":"允执厥中，安民永终",
     "neg":"失中则倾","steps":["受命","执中","安民","永终"],
     "dispatch":"当执政宜守中、不可偏倚时触发","decision_if":"需允执厥中",
     "neg_space":["失中则天命去","偏则倾"]},
]


def assemble_one(g):
    """S2-S4: 将单篇编译为 COP (对齐麦肯锡 COP schema 单原语形态)"""
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
        "COP-ID": "HS-RU-P%02d-20260815-%02d" % (g["n"], g["n"]),
        "source_expert": "lunyu_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用 / 篇目分解)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": "诸子百家·儒家·论语·第%02d篇(%s)" % (g["n"], g["title"]),
        "stratum": "诸子百家·儒家·论语·" + g["stratum"],  # 顶层 stratum 别名
        "soul": {
            "identity": "论语·第%02d篇《%s》" % (g["n"], g["title"]),
            "core": g["principle"],
            "verse": g["verse"],
            "role": "思维协议 (诸子百家 / 儒家 / 论语篇目)",
            "category": "诸子百家 / 儒家 / 论语 / " + g["stratum"],
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
    CC.s5_validate(cop)
    return cop, g


def compile_all():
    report = {"total": len(LYU), "ok": 0, "skip": 0, "fail": 0,
              "cop_ids": [], "nca_ids": []}
    for g in LYU:
        n = g["n"]
        fname = "第%02d篇-%s.yaml" % (n, g["title"])
        out_path = os.path.join(LYU_DIR, fname)
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
                scope=".tdca-protocol/cognitive-compiler/hundred_schools/lunyu (第%02d篇-%s COP)" % (n, g["title"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-LYU-P%02d" % n,
                notes="论语第%02d篇《%s》编译为 COP, 验证=%s" % (n, g["title"], cop["validation"]["passed"]),
            )
            report["ok"] += 1
            report["cop_ids"].append(cop["COP-ID"])
            report["nca_ids"].append(nid)
            print("[OK] %s -> %s | 谱系 %s | 验证 %s" % (cop["COP-ID"], fname, g["stratum"], cop["validation"]["passed"]))
        except Exception as e:
            report["fail"] += 1
            print("[FAIL] 第%02d篇-%s: %s" % (n, g["title"], e))
    return report


def write_manifest():
    """生成《论语》系统思维谱系清单 (20 篇六谱系索引)"""
    strata_def = {
        "为学教育": "学而时习/述而不作/性近习远/君子不器 (为学·教化·人性·通才)",
        "仁本忠恕": "里仁为美/克己复礼 (仁本体·忠恕·为仁由己)",
        "为政德治": "为政以德/正名/均安/工利其器/允执厥中 (德治·正名·均平·天命)",
        "礼乐文质": "礼以仁本/文质彬彬/过犹不及/容止中礼 (礼·文质·中庸践行)",
        "知人评士": "听言观行/耻言过行/执德弘道 (知人·士节·言行)",
        "出处大节": "三让天下/道之不行则洁身 (谦让·出处·守义)",
    }
    chapters = []
    for g in LYU:
        chapters.append({
            "n": g["n"], "title": g["title"], "cop_id": "HS-RU-P%02d-20260815-%02d" % (g["n"], g["n"]),
            "stratum": g["stratum"], "verse": g["verse"], "primitive": g["pinyin"],
            "file": "第%02d篇-%s.yaml" % (g["n"], g["title"]),
        })
    by_stratum = {}
    for g in LYU:
        by_stratum.setdefault(g["stratum"], []).append(g["n"])
    manifest = {
        "library": "lunyu_books",
        "role": "儒家系统思维篇目库 (Chinese cultural compound operand source, 篇目级)",
        "note": "《论语》20 篇每篇是儒家系统思维单元，逐篇编译为独立可调用的思维协议(COP)，"
                "共同构成儒家系统思维基库，按六谱系归类。后续作'中国文化 ⊕ 辩证实践方法论'化合的中方基协议素材。",
        "base_protocol": "TDCA-CORE-20260815-01",  # 强制可信底座
        "compiler": "lunyu/compile_lunyu.py",
        "schema": "同构麦肯锡 COP (stratum+steps, 兼容 compose_general)",
        "total_books": len(LYU),
        "strata_taxonomy": strata_def,
        "strata_count": {k: len(v) for k, v in by_stratum.items()},
        "books": chapters,
        "composition": {
            "composer": "../../compositions/compose_general.py",
            "compatible_with": ["TDCA核心", "道家(道德经)", "兵法", "博弈论", "机制设计", "场景", "现代学科库"],
            "compound_first_principle": "化合 > 物理叠加 (interpretant 注入语义涌现, 非内禀)",
            "compound_target": "中国文化 ⊕ 辩证实践方法论 = 辩证实践思维协议 (化合旗舰范式)",
            "verified_demo": "compose_demo_ly.py (第12篇 颜渊·克己复礼 ⟂ TDCA核心-02 → 克己守礼的可审计自主决策)",
        },
    }
    mp = os.path.join(LYU_DIR, "lunyu_manifest.yaml")
    with open(mp, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    print("[OK] 系统谱系清单 -> %s (六谱系: %s)" % (mp, "/".join(strata_def.keys())))


if __name__ == "__main__":
    print("===== 论语 20 篇思维协议编译 (MEMO-006 规范, 儒家系统思维篇目库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % LYU_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    write_manifest()
    print("系统思维谱系: 为学教育/仁本忠恕/为政德治/礼乐文质/知人评士/出处大节")
    print("===== 编译完成 =====")
