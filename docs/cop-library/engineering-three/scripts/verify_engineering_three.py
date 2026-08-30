# -*- coding: utf-8 -*-
"""工程三协议系列编译产物复验器 (验收标准第 1/3 条)
检查项: yaml 可解析 / COP-ID 与文件名一致 / schema 必备键 / negative_space>=3 /
        composition_policy 完整 / base_protocol=TDCA-CORE / nsfl_version /
        化合 COP 额外: type=COMPOUND-COP + fusion_spec(属性改变表>=2 + emergence 非空)
        原生 COP 额外: 原语签名含 fn + 组合调用 related 非空
"""
import os
import sys
import json
import hashlib

_THIS = os.path.dirname(os.path.abspath(__file__))
import yaml

BASE = os.path.join(_THIS, "engineering-three")
SUBS = ["trial", "grey", "dependability", "fusion", "fusion_scene", "fusion_tdca"]
EXPECT = {"trial": 8, "grey": 9, "dependability": 8, "fusion": 5, "fusion_scene": 7, "fusion_tdca": 4}

REQUIRED = ["COP-ID", "soul", "primitives", "dispatch", "decision", "negative_space", "nsfl_version"]
results = {"total": 0, "pass": 0, "fail": 0, "items": []}

for sub in SUBS:
    d = os.path.join(BASE, sub)
    files = sorted(f for f in os.listdir(d) if f.endswith(".yaml") and not f.startswith("COMPOSED-") or (sub in ("fusion", "fusion_scene", "fusion_tdca") and f.endswith(".yaml")))
    files = sorted(f for f in os.listdir(d) if f.endswith(".yaml"))
    n = 0
    for f in files:
        p = os.path.join(d, f)
        n += 1
        results["total"] += 1
        issues = []
        try:
            cop = yaml.safe_load(open(p, encoding="utf-8"))
            if not isinstance(cop, dict):
                issues.append("解析结果非 dict")
        except Exception as e:
            issues.append("yaml 解析失败: %s" % e)
            cop = None
        if cop:
            for k in REQUIRED:
                if k not in cop:
                    issues.append("缺必备键 %s" % k)
            # COP-ID 与文件名一致性: 化合组要求全等; 原生组按先例(第XX计-名.yaml)允许中文文件名,
            # 校验 前缀组别 + 文件名序号 与 COP-ID 尾号一致
            cid = cop.get("COP-ID") or ""
            stem = os.path.splitext(f)[0]
            if sub in ("fusion", "fusion_scene", "fusion_tdca"):
                if cid != stem:
                    issues.append("COP-ID 与文件名不一致: %s vs %s" % (cid, f))
            else:
                prefix = {"trial": "TRIAL", "grey": "GREY", "dependability": "DEP"}[sub]
                num_in_file = "".join(ch for ch in stem[:3] if ch.isdigit())
                if not cid.startswith(prefix + "-COP-20260830-"):
                    issues.append("COP-ID 前缀不符: %s (期望 %s)" % (cid, prefix))
                elif cid.endswith("-%02d" % int(num_in_file)) is False:
                    issues.append("COP-ID 尾号与文件名序号不一致: %s vs %s" % (cid, stem))
            # 负空间 >= 3
            if len(cop.get("negative_space") or []) < 3:
                issues.append("negative_space < 3")
            # 组合策略
            cp = cop.get("composition_policy") or {}
            if cp.get("standalone") is not False or not cp.get("tdca_native"):
                issues.append("composition_policy 不合规")
            if cop.get("base_protocol") != "TDCA-CORE":
                issues.append("base_protocol != TDCA-CORE")
            # F1.5 NSFL 否决权 (宪法条款, 用户裁定 2026-08-30 21:07) + 四态动态处置 (21:19 修正)
            if "否决权" not in (cp.get("constitution") or ""):
                issues.append("composition_policy 缺 NSFL 否决权宪法条款")
            if "四态动态处置" not in (cp.get("constitution") or ""):
                issues.append("constitution 缺四态动态处置修正 (休眠/禁止/重塑/出清)")
            if not any("否决权" in (n or "") for n in cop.get("negative_space") or []):
                issues.append("negative_space 缺否决权不可推翻条款")
            if not any("四态" in (n or "") for n in cop.get("negative_space") or []):
                issues.append("negative_space 缺四态动态处置条款")
            if cid == "COMPOSED-TDCAGATE-20260830-01":
                steps_f1 = (cop.get("primitives") or [{}])[0].get("steps") or []
                if not steps_f1 or "否决权" not in steps_f1[0]:
                    issues.append("F1 决策树第一步非 F1.5 否决权预检")
                if not any("四态" in (s or "") for s in steps_f1):
                    issues.append("F1 决策树缺 F1.5b 四态处置步")
            # 原语签名
            for prim in cop.get("primitives") or []:
                if "fn " not in (prim.get("signature") or ""):
                    issues.append("原语 %s 签名缺失" % prim.get("name"))
                if not prim.get("nca_emit"):
                    issues.append("原语 %s 未声明 nca_emit" % prim.get("name"))
            # 化合/原生分型检查
            is_compound = sub in ("fusion", "fusion_scene", "fusion_tdca")
            if is_compound:
                if cop.get("type") != "COMPOUND-COP":
                    issues.append("化合 COP type != COMPOUND-COP")
                fs = cop.get("fusion_spec") or {}
                if fs.get("fusion_type") != "化合":
                    issues.append("fusion_type != 化合")
                ac = fs.get("attribute_changes") or []
                if len(ac) < 2:
                    issues.append("attribute_changes < 2 条")
                else:
                    for a in ac:
                        if not a.get("before") or not a.get("after") or not a.get("attribute"):
                            issues.append("属性改变表条目不完整")
                if not (fs.get("emergence") or "").strip():
                    issues.append("emergence 涌现判据为空")
                interps = (cop.get("composition") or {}).get("interpretants") or []
                if not interps:
                    issues.append("interpretants 反应物为空")
            else:
                if cop.get("type") == "COMPOUND-COP":
                    issues.append("原生 COP 误标 COMPOUND-COP")
                g = (cop.get("dispatch") or {}).get("graph") or []
                if not g or not (g[0].get("to") or []):
                    issues.append("原生 COP 组合调用 to 为空 (组合性强制)")
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        ok = not issues
        results["pass" if ok else "fail"] += 1 if ok else 0
        if not ok:
            results["fail"] += 1
        results["items"].append({"sub": sub, "file": f, "sha256": h[:16], "pass": ok, "issues": issues})
    if n != EXPECT[sub]:
        results["items"].append({"sub": sub, "file": "<COUNT>", "pass": False,
                                 "issues": "文件数 %d != 预期 %d" % (n, EXPECT[sub])})
        results["fail"] += 1

out = os.path.join(BASE, "verify_report_20260830.json")
with open(out, "w", encoding="utf-8") as fo:
    json.dump(results, fo, ensure_ascii=False, indent=2)
print("复验: 总 %d | PASS %d | FAIL %d" % (results["total"], results["pass"], results["fail"]))
for it in results["items"]:
    if not it["pass"]:
        print("[FAIL]", it["sub"], it["file"], it["issues"])
print("报告:", out)
