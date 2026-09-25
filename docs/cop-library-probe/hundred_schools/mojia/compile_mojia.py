# -*- coding: utf-8 -*-
"""墨家 思维协议编译器 (诸子百家·墨翟十事)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2

定位: 把《墨子》以"兼爱·非攻"为系统骨架逐条编译为独立可调用的思维协议 (COP)。
用户立项: B. 续编诸子百家: 墨家(兼爱非攻)。墨翟主兼爱交利、非攻节用，以天志为法仪、
三表为认识准的，与儒并号为显学。逐条 = 一个独立思维原语, 按三谱系归类 (兼爱本原 / 尚贤尚同 / 节用三表)。
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
MO_DIR = _THIS
ensure_dirs()
os.makedirs(MO_DIR, exist_ok=True)

# ---------- 墨家 思维协议知识库 (每条一思维原语) ----------
# 三谱系: 兼爱本原 / 尚贤尚同 / 节用三表
MO = [
    {"n":1,"stratum":"兼爱本原","title":"兼爱","verse":"兼相爱，交相利。视人之国若视其国，视人之家若视其家，视人之身若视其身。",
     "principle":"兼相爱交相利、视人犹己；以去别立兼，根除攻夺之患。","pinyin":"jian_ai",
     "signature":"fn jian_ai(relate) -> universal_love",
     "precond":"别相恶、交贼","postcond":"兼相爱，交相利",
     "neg":"别则相攻","steps":["去别","兼","视犹己","交利"],
     "dispatch":"当群体相争、宜视人犹己时触发","decision_if":"需兼爱",
     "neg_space":["别爱则相攻","兼而不交利则虚"]},
    {"n":2,"stratum":"兼爱本原","title":"非攻","verse":"今攻伐并兼，则不可。杀所不足而争所有余，不可谓智。",
     "principle":"非不义之战、攻伐夺生；以义利辨战，立反侵略之则。","pinyin":"fei_gong",
     "signature":"fn fei_gong(war) -> anti_aggression",
     "precond":"攻伐、夺生","postcond":"非攻，义立",
     "neg":"攻则失义","steps":["辨义","察攻非","非不义","保生"],
     "dispatch":"当宜止不义之战、不宜攻伐时触发","decision_if":"需非攻",
     "neg_space":["攻伐则失义","以战济私则暴"]},
    {"n":3,"stratum":"兼爱本原","title":"天志","verse":"天之志者，义之经也。顺天之意何若？曰：兼相爱交相利。",
     "principle":"天有志、欲义恶不义；以天志为法仪，立兼爱之宗教根据。","pinyin":"tian_zhi",
     "signature":"fn tian_zhi(rule) -> heavenly_will",
     "precond":"背天志、行不义","postcond":"顺天志，义行",
     "neg":"背天则凶","steps":["识天志","法天","欲义","恶不义"],
     "dispatch":"当宜立价值法仪、不宜私是时触发","decision_if":"需立天志",
     "neg_space":["背天志则失法","以私僭天则妄"]},
    {"n":4,"stratum":"兼爱本原","title":"明鬼","verse":"鬼神之能，赏贤而罚暴也。使天下之人皆恐惧振动。",
     "principle":"鬼神赏贤罚暴、彰善瘅恶；以明鬼辅天志，立威慑劝善之教。","pinyin":"ming_gui",
     "signature":"fn ming_gui(teach) -> visible_ghosts",
     "precond":"无惧、恶不惩","postcond":"明鬼，善彰",
     "neg":"废鬼则纵","steps":["立鬼神","赏贤","罚暴","劝善"],
     "dispatch":"当宜立劝善威慑、不宜纵恶时触发","decision_if":"需明鬼",
     "neg_space":["废鬼则纵恶","滥罚则失民"]},
    {"n":5,"stratum":"尚贤尚同","title":"尚贤","verse":"官无常贵，而民无终贱。有能则举之，无能则下之。",
     "principle":"尚贤使能、不党父兄；以能举下，立公天下之选。","pinyin":"shang_xian",
     "signature":"fn shang_xian(select) -> meritocracy",
     "precond":"亲贵、贤壅","postcond":"尚贤，能举",
     "neg":"党亲则壅","steps":["破常贵","察能","举贤","下不肖"],
     "dispatch":"当宜唯才是举、不宜任亲时触发","decision_if":"需尚贤",
     "neg_space":["任亲则壅贤","举非其能则败"]},
    {"n":6,"stratum":"尚贤尚同","title":"尚同","verse":"上同而不下比，一同天下之义。天子唯能壹同天下之义。",
     "principle":"尚同壹义、上同不下比；以一同天下义，立政令归一之纲。","pinyin":"shang_tong",
     "signature":"fn shang_tong(unify) -> unified_will",
     "precond":"义歧、下比","postcond":"一同天下义",
     "neg":"下比则乱","steps":["立通","上同","壹义","不比"],
     "dispatch":"当宜政令归一、不宜歧义时触发","decision_if":"需尚同",
     "neg_space":["下比则乖","同而失兼则暴"]},
    {"n":7,"stratum":"节用三表","title":"节用","verse":"节用而爱人，使民以时。诸加费不加利于民者，弗为。",
     "principle":"节用爱人、费必利于民；以功利节度，立生财足用之本。","pinyin":"jie_yong",
     "signature":"fn jie_yong(spend) -> frugal",
     "precond":"奢费、民困","postcond":"节用，民足",
     "neg":"奢则竭","steps":["核利","去浮费","节用","爱人"],
     "dispatch":"当宜节用足民、不宜奢费时触发","decision_if":"需节用",
     "neg_space":["奢费则民竭","苛节则伤"]},
    {"n":8,"stratum":"节用三表","title":"节葬","verse":"节葬短丧，反厚葬久丧。衣衾三领，足以朽肉；棺椁三寸，足以朽骨。",
     "principle":"节葬短丧、反厚丧久哀；以省民力，立丧制之俭。","pinyin":"jie_zang",
     "signature":"fn jie_zang(rite) -> simple_burial",
     "precond":"厚葬、久丧废业","postcond":"节葬，民力省",
     "neg":"厚丧则废","steps":["约丧","短哀","省费","复业"],
     "dispatch":"当宜简丧、不宜厚费时触发","decision_if":"需节葬",
     "neg_space":["厚葬则竭家","久丧则废业"]},
    {"n":9,"stratum":"节用三表","title":"非乐","verse":"为乐非所以治天下也。夺民衣食之财以拊乐，废民之从事。",
     "principle":"非大钟鸣鼓之侈乐、劳民费财；以实务为先，立黜奢之戒。","pinyin":"fei_yue",
     "signature":"fn fei_yue(amuse) -> anti_luxury",
     "precond":"侈乐、夺财","postcond":"非乐，务本",
     "neg":"乐则废","steps":["辨奢","去侈乐","务本","足财"],
     "dispatch":"当宜务本黜奢、不宜耽乐时触发","decision_if":"需非乐",
     "neg_space":["侈乐则夺财","全废乐则枯"]},
    {"n":10,"stratum":"节用三表","title":"非命","verse":"命者，暴王所作，穷人所述也。强力而为，则生；怠倦则死。",
     "principle":"非命、立强力而为；以人力胜命定，立人定胜天之志。","pinyin":"fei_ming",
     "signature":"fn fei_ming(act) -> anti_fatalism",
     "precond":"信命、怠","postcond":"非命，强力成",
     "neg":"信命则怠","steps":["破命","强力","疾作","有成"],
     "dispatch":"当宜奋起力行、不宜诿命时触发","decision_if":"需非命",
     "neg_space":["信命则怠废","强为而无度则竭"]},
    {"n":11,"stratum":"节用三表","title":"三表法","verse":"言必立仪：本之（上本之于古者圣王之事）；原之（下原察百姓耳目之实）；用之（发以为刑政，观其中国家百姓人民之利）。",
     "principle":"言必三表：本古事、原民情、用利国；以本原用立认识与言论之准。","pinyin":"san_biao_fa",
     "signature":"fn san_biao_fa(judge) -> three_tables",
     "precond":"言无准、妄议","postcond":"三表立，言可征",
     "neg":"无仪则妄","steps":["本古","原民","用利","定言"],
     "dispatch":"当宜立言论准的、不宜虚论时触发","decision_if":"需三表法",
     "neg_space":["无仪则妄议","偏一表则失"]},
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
        "COP-ID": "HS-MO-%02d-20260815-%02d" % (g["n"], g["n"]),
        "source_expert": "mojing_canonical",
        "compiler": "cognitive_compiler (T1+T2 规范复用 / 义理条目分解)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "branch": "诸子百家·墨家·第%02d条(%s)" % (g["n"], g["title"]),
        "stratum": "诸子百家·墨家·" + g["stratum"],
        "soul": {
            "identity": "墨家·第%02d条《%s》" % (g["n"], g["title"]),
            "core": g["principle"],
            "verse": g["verse"],
            "role": "思维协议 (诸子百家 / 墨家 / 墨翟十事)",
            "category": "诸子百家 / 墨家 / " + g["stratum"],
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
    report = {"total": len(MO), "ok": 0, "skip": 0, "fail": 0, "cop_ids": [], "nca_ids": []}
    for g in MO:
        n = g["n"]
        fname = "第%02d条-%s.yaml" % (n, g["title"])
        out_path = os.path.join(MO_DIR, fname)
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
                scope=".tdca-protocol/cognitive-compiler/hundred_schools/mojia (第%02d条-%s COP)" % (n, g["title"]),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-MO-M%02d" % n,
                notes="墨家第%02d条《%s》编译为 COP, 验证=%s" % (n, g["title"], cop["validation"]["passed"]),
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
        "兼爱本原": "兼爱/非攻/天志/明鬼 (去别立兼, 天志为法仪, 反侵略爱交利)",
        "尚贤尚同": "尚贤/尚同 (唯才是举, 政令壹义归一)",
        "节用三表": "节用/节葬/非乐/非命/三表法 (功利节度, 强力非命, 本原用立言准)",
    }
    items = []
    for g in MO:
        items.append({
            "n": g["n"], "title": g["title"], "cop_id": "HS-MO-%02d-20260815-%02d" % (g["n"], g["n"]),
            "stratum": g["stratum"], "verse": g["verse"], "primitive": g["pinyin"],
            "file": "第%02d条-%s.yaml" % (g["n"], g["title"]),
        })
    by_stratum = {}
    for g in MO:
        by_stratum.setdefault(g["stratum"], []).append(g["n"])
    manifest = {
        "library": "mojia_jianai",
        "role": "诸子百家系统思维·墨翟十事库 (Chinese cultural compound operand source, 义理条目级)",
        "note": "《墨子》主兼爱交利、非攻节用, 以天志为法仪、三表为认识准的, 与儒并号显学。"
                "逐条编译为独立可调用的思维协议(COP), 按三谱系归类。后续作'中国文化 ⊕ 辩证实践方法论'化合的中方基协议素材。",
        "base_protocol": "TDCA-CORE-20260815-01",
        "compiler": "mojia/compile_mojia.py",
        "schema": "同构麦肯锡 COP (stratum+steps, 兼容 compose_general)",
        "total_items": len(MO),
        "strata_taxonomy": strata_def,
        "strata_count": {k: len(v) for k, v in by_stratum.items()},
        "items": items,
        "composition": {
            "composer": "../../compositions/compose_general.py",
            "compatible_with": ["TDCA核心", "道家", "儒(论孟学庸)", "法家", "名家", "阴阳家", "辩证实践方法论", "兵法", "博弈论", "机制设计", "场景", "现代学科库"],
            "compound_first_principle": "化合 > 物理叠加 (interpretant 注入语义涌现, 非内禀)",
            "compound_target": "中国文化 ⊕ 辩证实践方法论 = 辩证实践思维协议 (化合旗舰范式)",
            "verified_demo": "撰写中 (墨家兼爱交利 ⟂ 辩证实践方法论统一战线/群众路线)",
        },
    }
    mp = os.path.join(MO_DIR, "mojia_manifest.yaml")
    with open(mp, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    print("[OK] 系统谱系清单 -> %s (三谱系: %s)" % (mp, "/".join(strata_def.keys())))


if __name__ == "__main__":
    print("===== 墨家 思维协议编译 (MEMO-006 规范, 诸子百家·墨翟十事库) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 跳过: %d | 失败: %d" % (rep["total"], rep["ok"], rep["skip"], rep["fail"]))
    print("COP 目录: %s" % MO_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    write_manifest()
    print("系统思维谱系: 兼爱本原/尚贤尚同/节用三表")
    print("===== 编译完成 =====")
