# -*- coding: utf-8 -*-
"""核实 85 个化合目标的家族分布 + 抽验正典统一结果"""
import os, json, glob
import yaml

_THIS = os.path.dirname(os.path.abspath(__file__))
os.chdir(_THIS)

rep = json.load(open("unify_report_20260830.json", encoding="utf-8"))
changed = [c["file"] for c in rep["changed_files"]]

def fam(p):
    rel = os.path.relpath(p, _THIS).replace(os.sep, "/")
    parts = rel.split("/")
    return "/".join(parts[:-1]) if len(parts) > 1 else "(root)"

from collections import Counter
c1 = Counter(fam(p) for p in changed)
print("变更文件家族分布:")
for k, v in sorted(c1.items()):
    print("  %-40s %d" % (k, v))
print("变更总数:", len(changed))

# 复验: 全库 constitution == 正典 (除 coldstart 已知缺陷)
CANON_KEY = "NSFL 否决权 (F1.5, 用户裁定 2026-08-30 21:07)"
ok, bad, n_const = 0, 0, 0
bad_list = []
for p in sorted(glob.glob(os.path.join(_THIS, "**", "*.yaml"), recursive=True)):
    if "__pycache__" in p:
        continue
    try:
        d = yaml.safe_load(open(p, "r", encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    pol = d.get("composition_policy")
    if not isinstance(pol, dict) or "constitution" not in pol:
        continue
    n_const += 1
    c = pol["constitution"]
    if c.startswith(CANON_KEY) and "现在触犯不等于永远触犯" in c and "裁定 NCA 存证, 禁悬置" in c and "强制重评" in c:
        ok += 1
    else:
        bad += 1
        bad_list.append(os.path.relpath(p, _THIS))
print("\n复验: 含 constitution 文件 %d | 正典一致 %d | 不一致 %d" % (n_const, ok, bad))
for b in bad_list:
    print("  [BAD]", b)
