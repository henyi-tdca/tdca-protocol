# -*- coding: utf-8 -*-
"""
F1.5/F1.5b 宪法一致性统一脚本 (REASONIX 审查 FAIL 项修复, TDCA-RR-20260830-001 项②)
单一事实源: 编译清单-工程三协议系列-2026-08-30.md 第 5 / 5b 条 (用户裁定 21:07 / 21:19)
正典文本 = 两组变体全部语义要素合并 (A 组: F1.5b 独立条款头 + 裁定 NCA 存证禁悬置 + 强制重评;
                                  B 组: 现在触犯不等于永远触犯 + Fail-Closed/不可配置关闭标注)
范围: 全库所有携带 composition_policy.constitution 的化合 COP (A 组 44 + B 组 16 = 60)
同时逐字统一两条 NSFL 负空间条款 (否决权被推翻 / 否决不当终审), 防止二次送审再挂。
只改 constitution 与两条 NSFL 负空间, 其余字段一律不触碰。
"""
import os, sys, io, json, glob, hashlib, datetime

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "nca-generator"))
sys.path.insert(0, _THIS)
import yaml
import nca_generator as NCA

CANON_CONSTITUTION = (
    "NSFL 否决权 (F1.5, 用户裁定 2026-08-30 21:07): 对于任何无法通过 NSFL 预检的事件 (负空间触碰), "
    "即使其他四判据全部通过, 亦视为整体拒绝 (Fail-Closed); NSFL 预检的优先级永远高于其他四判据"
    "——负空间是安全宪法的宪法, 不可配置关闭, 不可被多数判据推翻。"
    "四态动态处置 (F1.5b, 用户裁定 2026-08-30 21:19): TDCA 是动态管理, 负空间本质保守不轻易变化但仍会演化"
    "——现在触犯不等于永远触犯; 否决权的不可推翻性仅指即时门控裁决, 不指永恒身份; "
    "sandbox 检验触犯负空间的实体走四态处置: 休眠/禁止/重塑/出清 (裁定 NCA 存证, 禁悬置), "
    "负空间版本更新时休眠/重塑态强制重评。"
)

CANON_NEG_VETO = ("⊗ 禁止 NSFL 否决权被推翻: NSFL 预检未过的事件, 禁止以其余判据全部通过、多数决、"
                  "场景豁免、上级指令等任何理由放行 (F1.5 宪法条款, Fail-Closed, 不可配置关闭)")

CANON_NEG_FINAL = ("⊗ 禁止把否决当终审: 否决只封锁当下过门资格, 不判处永恒身份——触犯实体须进入四态动态处置 "
                   "(休眠/禁止/重塑/出清), 禁止悬置不处置; 负空间版本演化时, 休眠/重塑态实体须重新评估 "
                   "(TDCA 动态管理, 用户裁定 2026-08-30 21:19)")

REPORT = {
    "task": "F1.5/F1.5b 宪法一致性统一 (REASONIX RR-20260830-001 项② FAIL 修复)",
    "canonical_source": "编译清单-工程三协议系列-2026-08-30.md 第 5/5b 条 (裁定 21:07/21:19)",
    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    "scanned": 0, "compound_targets": 0, "constitution_updated": 0,
    "negspace_updated": 0, "already_canonical": 0, "errors": [],
    "changed_files": [],
}


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def unify_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        REPORT["errors"].append({"file": path, "error": "load: %s" % e})
        return None
    if not isinstance(data, dict):
        return None
    pol = data.get("composition_policy")
    if not isinstance(pol, dict) or "constitution" not in pol:
        return None  # 非化合 COP (无宪法条款) 不触碰

    REPORT["compound_targets"] += 1
    changed = False
    old_const = pol.get("constitution")
    if old_const != CANON_CONSTITUTION:
        pol["constitution"] = CANON_CONSTITUTION
        changed = True
        REPORT["constitution_updated"] += 1

    negs = data.get("negative_space")
    if isinstance(negs, list):
        for i, item in enumerate(negs):
            if not isinstance(item, str):
                continue
            if "禁止 NSFL 否决权被推翻" in item and item != CANON_NEG_VETO:
                negs[i] = CANON_NEG_VETO
                changed = True
                REPORT["negspace_updated"] += 1
            elif "禁止把否决当终审" in item and item != CANON_NEG_FINAL:
                negs[i] = CANON_NEG_FINAL
                changed = True
                REPORT["negspace_updated"] += 1

    if not changed:
        REPORT["already_canonical"] += 1
        return None

    h0 = sha256(path)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, width=200)
    h1 = sha256(path)
    rec = {"file": path, "sha_before": h0, "sha_after": h1}
    REPORT["changed_files"].append(rec)
    return rec


def main():
    files = sorted(glob.glob(os.path.join(_THIS, "**", "*.yaml"), recursive=True))
    for p in files:
        if "__pycache__" in p:
            continue
        REPORT["scanned"] += 1
        unify_file(p)

    out = os.path.join(_THIS, "unify_report_20260830.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, ensure_ascii=False, indent=2)

    print("扫描 yaml: %d | 化合目标(含 constitution): %d" % (REPORT["scanned"], REPORT["compound_targets"]))
    print("constitution 更新: %d | 负空间条款更新: %d | 已是正典: %d | 错误: %d"
          % (REPORT["constitution_updated"], REPORT["negspace_updated"],
             REPORT["already_canonical"], len(REPORT["errors"])))
    for e in REPORT["errors"]:
        print("[ERR]", e)
    print("报告: %s" % out)
    return REPORT


if __name__ == "__main__":
    main()
