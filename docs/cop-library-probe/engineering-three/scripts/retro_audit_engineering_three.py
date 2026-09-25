# -*- coding: utf-8 -*-
"""
engineering-three 全库回审：对既有编译产物逐个机检 2026-08-30 编译原则。
原则清单（用户当日裁定）:
  P1 组合性强制   —— 化合 COP 须 composition_policy.standalone=false
  P2 TDCA 强制    —— base_protocol=TDCA-CORE（体系内不可配置关闭）
  P3 原生可剥离   —— 剥离 TDCA 治理层后语义独立自洽（声明字段 detachable）
  P4 换绑自由     —— 绑定为运用层配置（bind_policy 声明）
  P5 化合判据     —— 化合 COP 须携带 fusion_spec（attribute_changes>=1 + emergence）
  P6 F1.5 否决权  —— composition_policy.constitution 含 NSFL 否决权
  P7 F1.5b 四态   —— constitution 含 休眠/禁止/重塑/出清 四态处置
范围：原生 COP 仅审计不修订（不涉及化合）；COMPOSED 化合 COP 全项机检。
"""
import os, sys, io, json, glob
sys.stdout.reconfigure(encoding="utf-8")
import yaml

_THIS = os.path.dirname(os.path.abspath(__file__))
FAMILIES = ["stratagems", "scenario", "compositions", "engineering-three",
            "games", "hundred_schools", "marxism", "mechanism_design",
            "microeconomics", "chengyu", "tdca_core", "coldstart", "emissary"]

def audit_one(cop):
    ctype = str(cop.get("type", "COP"))  # 老产物无 type 键, 默认视为原生
    is_composed = "COMPOSED" in ctype or "COMPOUND" in ctype
    cp = cop.get("composition_policy") or {}
    checks = {}
    if is_composed:
        checks["P1_组合性"] = cp.get("standalone") is False
        checks["P2_TDCA强制"] = cop.get("base_protocol") == "TDCA-CORE"
        checks["P3_可剥离声明"] = bool(cp.get("detachable"))
        checks["P4_换绑自由"] = bool(cp.get("bind_policy"))
        fs = cop.get("fusion_spec") or {}
        checks["P5_化合判据"] = bool(fs.get("attribute_changes")) and bool(fs.get("emergence"))
        checks["P6_否决权"] = "否决权" in str(cp.get("constitution") or "")
        checks["P7_四态"] = all(k in str(cp.get("constitution") or "") for k in ("休眠", "禁止", "重塑", "出清"))
    else:
        # 原生：仅审计基本结构（老产物无 type 键, 不计入必备键）
        checks["结构_必备键"] = all(k in cop for k in ("COP-ID", "soul", "primitives", "negative_space"))
        checks["结构_负空间"] = len(cop.get("negative_space") or []) >= 1
    return is_composed, checks

result = {"families": {}, "composed_total": 0, "composed_fail": [], "native_total": 0,
          "native_fail": [], "parse_fail": []}
for fam in FAMILIES:
    files = sorted(glob.glob(os.path.join(_THIS, fam, "**", "*.yaml"), recursive=True))
    if not files:
        continue
    fam_stat = {"files": len(files), "composed": 0, "native": 0}
    for f in files:
        try:
            cop = yaml.safe_load(io.open(f, encoding="utf-8"))
        except Exception as e:
            result["parse_fail"].append({"file": os.path.relpath(f, _THIS), "error": str(e)[:120]})
            continue
        if not isinstance(cop, dict) or "COP-ID" not in cop:
            continue
        is_composed, checks = audit_one(cop)
        rel = os.path.relpath(f, _THIS)
        if is_composed:
            fam_stat["composed"] += 1
            result["composed_total"] += 1
            bad = [k for k, v in checks.items() if not v]
            if bad:
                result["composed_fail"].append({"file": rel, "cop_id": cop.get("COP-ID"), "missing": bad})
        else:
            fam_stat["native"] += 1
            result["native_total"] += 1
            bad = [k for k, v in checks.items() if not v]
            if bad:
                result["native_fail"].append({"file": rel, "cop_id": cop.get("COP-ID"), "missing": bad})
    result["families"][fam] = fam_stat

out = os.path.join(_THIS, "engineering-three", "retro_audit_report_20260830.json")
json.dump(result, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("家族统计:", json.dumps(result["families"], ensure_ascii=False))
print("化合 COP:", result["composed_total"], "| 不合规:", len(result["composed_fail"]))
print("原生 COP:", result["native_total"], "| 结构缺陷:", len(result["native_fail"]))
print("解析失败:", len(result["parse_fail"]))
by_miss = {}
for x in result["composed_fail"]:
    for m in x["missing"]:
        by_miss[m] = by_miss.get(m, 0) + 1
print("化合缺失分布:", json.dumps(by_miss, ensure_ascii=False))
print("报告:", out)
