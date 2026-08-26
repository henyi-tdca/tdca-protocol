# -*- coding: utf-8 -*-
"""大学 三纲八目 思维协议编译器 (诸子百家·儒家·系统思维纲领库)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 把《大学》以"三纲八目"为系统骨架逐目编译为独立可调用的思维协议 (COP)。
用户判断: "道德经文字虽少却是道家系统思维" → 同理，《大学》文字虽少、却是儒家
"修齐治平·内圣外王"系统思维的纲领体现。故三纲(明明德/亲民/止于至善) + 八目
(格物/致知/诚意/正心/修身/齐家/治国/平天下) 共 11 目，每目 = 一个独立思维原语，
共同构成"大学系统思维"基库，按三谱系归类 (三纲总摄 / 内圣阶梯 / 外王阶梯)。
每目须以 TDCA-CORE-20260815-01 (生态准入基协议) 为可信底座。
同构: 与 compile_lunyu.py / compile_daodejing.py / compile_hundred_schools.py 同构,
仅把"篇目系统"升级为"纲领目次"(大学天然以三纲八目为单元)。
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
DX_DIR = _THIS
ensure_dirs()
os.makedirs(DX_DIR, exist_ok=True)

# ---------- 大学 三纲八目 思维协议知识库 (每目一思维原语) ----------
# 字段: n/stratum/title/verse/principle/pinyin/signature/precond/postcond/neg/steps/dispatch/decision_if/neg_space
# stratum 三谱系: 三纲总摄 / 内圣阶梯 / 外王阶梯
DX = [
    {"n":1,"stratum":"三纲总摄","title":"明明德","verse":"大学之道，在明明德，在亲民，在止于至善。",
     "principle":"发明本有光明德性、自明而明；以明德为立身根基，不假外求。","pinyin":"ming_ming_de",
     "signature":"fn ming_ming_de(self) -> luminous_virtue",
     "precond":"德性昏蔽、自弃","postcond":"明德彰显，自昭明德",
     "neg":"自蔽则暗","steps":["识明德","自明","日新","昭著"],
     "dispatch":"当需发明本心德性、不宜外求时触发","decision_if":"需明明德",
     "neg_space":["自蔽其明则暗","外求明德则失"]},
    {"n":2,"stratum":"三纲总摄","title":"亲民","verse":"在亲民（程朱本作新民）。君子日新其德，新民教化。",
     "principle":"新民教化、日新又新；以教化使民自新，不假强制。","pinyin":"qin_min_xin_min",
     "signature":"fn qin_min_xin_min(educate) -> renewed_people",
     "precond":"民德旧染、不新","postcond":"日新其德，民自新",
     "neg":"因循则旧","steps":["识旧染","新民","日新","化成"],
     "dispatch":"当宜教化更新、不宜因循强制时触发","decision_if":"需新民教化",
     "neg_space":["因循则旧","强制改则怨"]},
    {"n":3,"stratum":"三纲总摄","title":"止于至善","verse":"在止于至善。知止而后有定，定而后能静，静而后能安，安而后能虑，虑而后能得。",
     "principle":"知止有定、确立至善目标；以止→定→静→安→虑→得成事（先明不可为边界，再可审计推进）。","pinyin":"zhi_yu_zhi_shan",
     "signature":"fn zhi_yu_zhi_shan(goal) -> supreme_good_rest",
     "precond":"无定止、逐物飘移","postcond":"知止有定，虑得安成",
     "neg":"无止则荡","steps":["知止","有定","静","安","虑","得"],
     "dispatch":"当目标飘移、宜立止境（明不可为界）时触发","decision_if":"需止于至善",
     "neg_space":["无定止则逐物荡","止非至善则偏"]},
    {"n":4,"stratum":"内圣阶梯","title":"格物","verse":"欲诚其意者，先致其知；致知在格物。物格而后知至。",
     "principle":"穷究事物之理、即物穷理；以格物致知，不臆度。","pinyin":"ge_wu",
     "signature":"fn ge_wu(inquire) -> things_investigated",
     "precond":"理未穷、知不明","postcond":"物格知至，理明",
     "neg":"臆度则妄","steps":["即物","穷理","格其理","知至"],
     "dispatch":"当需究理明事、不宜臆断时触发","decision_if":"需格物穷理",
     "neg_space":["臆度则妄","逐物丧志则迷"]},
    {"n":5,"stratum":"内圣阶梯","title":"致知","verse":"致知在格物。知至而后意诚。",
     "principle":"推极其知、扩充知识至极；以知致诚，不蔽不杂。","pinyin":"zhi_zhi",
     "signature":"fn zhi_zhi(extend) -> knowledge_pushed",
     "precond":"知有未尽、蔽","postcond":"知至意诚，明理",
     "neg":"知蔽则暗","steps":["格物","致知","推极","知至"],
     "dispatch":"当知识未透、宜推极时触发","decision_if":"需致知推极",
     "neg_space":["知蔽则暗","博而不约则杂"]},
    {"n":6,"stratum":"内圣阶梯","title":"诚意","verse":"欲正其心者，先诚其意。毋自欺也；如恶恶臭，如好好色。",
     "principle":"意念真诚、不自欺；以诚意正心，慎独为基。","pinyin":"cheng_yi",
     "signature":"fn cheng_yi(self) -> sincere_will",
     "precond":"自欺、意不实","postcond":"意诚心正，慎独",
     "neg":"自欺则伪","steps":["慎独","不自欺","诚意","如好好色"],
     "dispatch":"当意有欺瞒、宜慎独时触发","decision_if":"需诚意不自欺",
     "neg_space":["自欺则伪","掩恶则失"]},
    {"n":7,"stratum":"内圣阶梯","title":"正心","verse":"欲修其身者，先正其心。身有所忿懥，则不得其正。",
     "principle":"端正心思、去好恶偏私；以正心修身，中节不为情蔽。","pinyin":"zheng_xin",
     "signature":"fn zheng_xin(self) -> rectified_mind",
     "precond":"忿懥恐惧好乐忧患偏","postcond":"心正身修，中节",
     "neg":"偏私则失","steps":["察偏","去好恶","正心","中节"],
     "dispatch":"当心为情绪偏蔽、宜正时触发","decision_if":"需正心去偏",
     "neg_space":["忿懥则偏","好乐则溺"]},
    {"n":8,"stratum":"外王阶梯","title":"修身","verse":"自天子以至于庶人，壹是皆以修身为本。",
     "principle":"修养自身为一切根本、本立道生；以修身贯内外，为内圣外王枢纽。","pinyin":"xiu_shen",
     "signature":"fn xiu_shen(self) -> cultivated_self",
     "precond":"身不修、本不立","postcond":"身修家齐国治天下平",
     "neg":"本不立则溃","steps":["格致","诚正","修身","为本"],
     "dispatch":"当万事待举、宜先修身为本时触发","decision_if":"需修身为本",
     "neg_space":["舍本逐末则溃","身不修则家不齐"]},
    {"n":9,"stratum":"外王阶梯","title":"齐家","verse":"欲治其国者，先齐其家。",
     "principle":"整治家族、孝悌慈恕推于家；以齐家及国，风化自近。","pinyin":"qi_jia",
     "signature":"fn qi_jia(family) -> ordered_family",
     "precond":"家不齐、教不行","postcond":"家齐国治，风化",
     "neg":"家乱则国危","steps":["孝","悌","慈","齐家"],
     "dispatch":"当宜由家及国、先齐其家时触发","decision_if":"需齐家为本",
     "neg_space":["家不齐则国乱","溺爱则废"]},
    {"n":10,"stratum":"外王阶梯","title":"治国","verse":"欲平天下者，先治其国。君子不出家而成教于国。",
     "principle":"德治其国、絜矩之道推己及人；以治国平天下，德风自上。","pinyin":"zhi_guo",
     "signature":"fn zhi_guo(govern) -> ordered_state",
     "precond":"国不治、民不安","postcond":"国治天下平，德风",
     "neg":"聚敛则怨","steps":["絜矩","推己","德治","国治"],
     "dispatch":"当宜以德治国、推絜矩时触发","decision_if":"需治国以德",
     "neg_space":["聚敛则民怨","恶于下则反"]},
    {"n":11,"stratum":"外王阶梯","title":"平天下","verse":"国治而后天下平。君子有絜矩之道。",
     "principle":"协和天下、絜矩均平；以平天下为至用，万物各得其所。","pinyin":"ping_tian_xia",
     "signature":"fn ping_tian_xia(world) -> pacified_world",
     "precond":"天下不平、倾","postcond":"天下平，万物得所",
     "neg":"不均则倾","steps":["絜矩","均平","协和","天下平"],
     "dispatch":"当宜均平协和、推絜矩于天下时触发","decision_if":"需平天下",
     "neg_space":["不均则倾","私天下则失"]},
]


def assemble_one(g):
    """S2-S4: 将单目编译为 COP (对齐麦肯锡 COP schema 单原语形态)"""
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
        "COP-ID": "HS-RU-DX%02d-20260815-%02d" % (g["n"], g["n"]),
        "source_expert": "daxue_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用 / 纲领目次分解)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": "诸子百家·儒家·大学·第%02d目(%s)" % (g["n"], g["title"]),
        "stratum": "诸子百家·儒家·大学·" + g["stratum"],  # 顶层 stratum 别名
        "soul": {
            "identity": "大学·第%02d目《%s》" % (g["n"], g["title"]),
            "core": g["principle"],
            "verse": g["verse"],
            "role": "思维协议 (诸子百家 / 儒家 / 大学纲目)",
            "category": "诸子百家 / 儒家 / 大学 / " + g["stratum"],
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
    report = {"total": len(DX), "ok": 0, "skip": 0, "fail": 0,
              "cop_ids": [], "nca_ids": []}
    for g in DX:
        n = g["n"]
        fname = "第%02d目-%s.yaml" % (n, g["title"])
        out_path = os.path.join(DX_DIR, fname)
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
                scope=".tdca-protocol/cognitive-compiler/hundred_schools/daxue (第%02d目-%s COP)" % (n, g["title"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-DXUE-M%02d" % n,
                notes="大学第%02d目《%s》编译为 COP, 验证=%s" % (n, g["title"], cop["validation"]["passed"]),
            )
            report["ok"] += 1
            report["cop_ids"].append(cop["COP-ID"])
            report["nca_ids"].append(nid)
            print("[OK] %s -> %s | 谱系 %s | 验证 %s" % (cop["COP-ID"], fname, g["stratum"], cop["validation"]["passed"]))
        except Exception as e:
            report["fail"] += 1
            print("[FAIL] 第%02d目-%s: %s" % (n, g["title"], e))
    return report


def write_manifest():
    """生成《大学》系统思维谱系清单 (11 目三谱系索引)"""
    strata_def = {
        "三纲总摄": "明明德/亲民/止于至善 (立道方向·本体与目标·知止有定)",
        "内圣阶梯": "格物/致知/诚意/正心/修身 (即物穷理→推极知识→不自欺→去偏→为本, 自我修养递进)",
        "外王阶梯": "齐家/治国/平天下 (孝悌及国→絜矩德治→均平协和, 推己及人达用)",
    }
    chapters = []
    for g in DX:
        chapters.append({
            "n": g["n"], "title": g["title"], "cop_id": "HS-RU-DX%02d-20260815-%02d" % (g["n"], g["n"]),
            "stratum": g["stratum"], "verse": g["verse"], "primitive": g["pinyin"],
            "file": "第%02d目-%s.yaml" % (g["n"], g["title"]),
        })
    by_stratum = {}
    for g in DX:
        by_stratum.setdefault(g["stratum"], []).append(g["n"])
    manifest = {
        "library": "daxue_gangmu",
        "role": "儒家系统思维纲领库 (Chinese cultural compound operand source, 纲目级)",
        "note": "《大学》文字虽少，却是儒家'修齐治平·内圣外王'系统思维的纲领体现；"
                "以三纲(明明德/亲民/止于至善) + 八目(格物/致知/诚意/正心/修身/齐家/治国/平天下) "
                "共 11 目逐目编译为独立可调用的思维协议(COP)，按三谱系归类。"
                "后续作'中国文化 ⊕ 马克思主义'化合的中方基协议素材。",
        "base_protocol": "TDCA-CORE-20260815-01",  # 强制可信底座
        "compiler": "daxue/compile_daxue.py",
        "schema": "同构麦肯锡 COP (stratum+steps, 兼容 compose_general)",
        "total_items": len(DX),
        "strata_taxonomy": strata_def,
        "strata_count": {k: len(v) for k, v in by_stratum.items()},
        "items": chapters,
        "composition": {
            "composer": "../../compositions/compose_general.py",
            "compatible_with": ["TDCA核心", "道家(道德经)", "论语", "兵法", "博弈论", "机制设计", "场景", "现代学科库"],
            "compound_first_principle": "化合 > 物理叠加 (interpretant 注入语义涌现, 非内禀)",
            "compound_target": "中国文化 ⊕ 马克思主义 = 毛泽东思想思维协议 (化合旗舰范式)",
            "verified_demo": "compose_demo_dx.py (第03目 止于至善·知止有定 ⟂ TDCA核心-02 → 知止有界的可审计自主决策)",
        },
    }
    mp = os.path.join(DX_DIR, "daxue_manifest.yaml")
    with open(mp, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    print("[OK] 系统谱系清单 -> %s (三谱系: %s)" % (mp, "/".join(strata_def.keys())))


if __name__ == "__main__":
    print("===== 大学 三纲八目 思维协议编译 (MEMO-006 规范, 儒家系统思维纲领库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % DX_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    write_manifest()
    print("系统思维谱系: 三纲总摄/内圣阶梯/外王阶梯")
    print("===== 编译完成 =====")
