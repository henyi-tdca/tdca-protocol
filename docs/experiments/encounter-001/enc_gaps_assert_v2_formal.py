# -*- coding: utf-8 -*-
"""相遇专章 · 可机验断言【复跑版·对正式条文】（转正步③ 复跑 · 本侧本机只读）

⭐ 依据：TDCA-STD-SCENE-ENCOUNTER-001（生效 V1.0·人读版＋机读版）
⭐ 说明：v1 作用于「条款要点件」；本版作用于 ⭐【正式条文】（人读版 ＋ 机读版），
        且状态机/门禁/存证字段 ⭐ 直接自【机读版结构面】读取校验（硬面）。
⭐ 纪律：零依赖（标准库 + PyYAML）；只读；⛔ 不改任何在册件
"""
import os
import re
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 路径锚定（改造令·甲）：仓内相对——本脚本位 docs/experiments/encounter-001/，条文在 docs/regulations/
_HERE = os.path.dirname(os.path.abspath(__file__))
F_MD = os.path.normpath(os.path.join(_HERE, "..", "..", "regulations", "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（人读版·V0.9-DRAFT·待签批）.md"))
F_YM = os.path.normpath(os.path.join(_HERE, "..", "..", "regulations", "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（机读版·V0.9-DRAFT）.yaml"))

assert os.path.exists(F_MD), "缺人读版"
assert os.path.exists(F_YM), "缺机读版"
t_md = open(F_MD, encoding="utf-8").read()
doc = yaml.safe_load(open(F_YM, encoding="utf-8"))
mf = doc["machine_fields"]
t_all = t_md + "\n" + open(F_YM, encoding="utf-8").read()

results = []


def check(no, desc, ok, detail=""):
    results.append((no, desc, bool(ok)))
    print("[%s] %s -> %s%s" % ("PASS" if ok else "FAIL", no, "PASS" if ok else "FAIL",
                               ("  | " + detail) if detail else ""))


# ---------- A-1 缝① 划界（正式文本面） ----------
bad = []
for m in re.finditer(r"相遇[^。；\n]{0,8}(收费|计价|入口费)", t_all):
    seg = t_all[max(0, m.start() - 20):m.end() + 20]
    if not re.search(r"⛔|不得|不收费|免费|禁|删|取消", seg):
        bad.append(seg.replace("\n", " "))
check("A-1a", "缝① 正式文本 ⛔ 无「相遇收费」肯定条款", len(bad) == 0, "命中=%d" % len(bad))

check("A-1b", "缝① 相遇/撮合各有独立定义",
      (doc["definitions"]["encounter"]["text"] != doc["definitions"]["matchmaking"]["text"])
      and ("相遇 ＝" in t_md or "相遇＝" in t_md), "定义分列=%s" % ("encounter" in doc["definitions"]))

check("A-1c", "缝① 「并列不互推」在位（正式文本）",
      ("非同一" in t_md) and ("不得互为指代" in t_md))

# ---------- A-2 缝② 存证二分（机读版结构面） ----------
check("A-2a", "缝② 机读版 encounter_status.allowed == {发生, 未发生}",
      mf["encounter_status"]["allowed"] == ["发生", "未发生"], str(mf["encounter_status"]["allowed"]))

check("A-2b", "缝② 机读版 forbidden 含 INVALID/真相遇/假相遇",
      set(["INVALID", "真相遇", "假相遇"]).issubset(set(mf["encounter_status"]["forbidden"])),
      str(mf["encounter_status"]["forbidden"]))

bad2 = []
for ln in t_md.splitlines():
    if "INVALID" in ln and not re.search(r"⛔|改|删|取消|不采|不得|无 `INVALID`|上游件|原设计|原述", ln):
        bad2.append(ln.strip()[:80])
check("A-2c", "缝② 人读版中 INVALID 仅见于否定语境（若有）", len(bad2) == 0, "命中=%d" % len(bad2))

# ---------- A-3 缝③ 状态机（机读版结构面） ----------
STATES = set(mf["states"])
LEGAL = set(tuple(x) for x in mf["legal_transitions"])
SPEC = {("发现", "相遇"), ("相遇", "握手"), ("握手", "交互"), ("交互", "结算"),
        ("相遇", "发现"), ("握手", "相遇"), ("握手", "拒绝"), ("相遇", "拒绝")}
check("A-3a", "缝③ 机读版 legal_transitions ⊆ 规定集", LEGAL.issubset(SPEC),
      "差集=%s" % (LEGAL - SPEC if LEGAL - SPEC else "{}"))
check("A-3b", "缝③ 机读版 legal_transitions == 规定集（无缺无溢）", LEGAL == SPEC,
      "缺=%s 溢=%s" % (SPEC - LEGAL, LEGAL - SPEC))

skip = [("发现", "握手"), ("发现", "交互"), ("发现", "结算"),
        ("相遇", "交互"), ("相遇", "结算"), ("握手", "结算")]
leak = [p for p in skip if p in LEGAL]
check("A-3c", "缝③ 跳步迁移不在合法集（未握手不得进交互/结算）", len(leak) == 0,
      "泄漏=%s" % (leak if leak else "[]"))
check("A-3d", "缝③ 可调配置权状态 == {握手, 交互, 结算}",
      mf["config_call_requires_states"] == ["握手", "交互", "结算"],
      str(mf["config_call_requires_states"]))

# ---------- A-4 门禁一致（机读版结构面） ----------
check("A-4a", "门禁 gates.allowed == R1~R10",
      mf["gates"]["allowed"] == ["R%d" % i for i in range(1, 11)], str(mf["gates"]["allowed"]))
check("A-4b", "⛔ 无新增门禁（R11 仅见于 forbidden_add）",
      ("R11" in mf["gates"]["forbidden_add"]) and ("R11" not in mf["gates"]["allowed"]),
      str(mf["gates"]["forbidden_add"]))

# ---------- 汇总 ----------
total = len(results)
passed = sum(1 for r in results if r[2])
failed = total - passed
print("---")
print("断言【复跑·对正式条文】%d ｜ 通过 %d ｜ 失败 %d" % (total, passed, failed))
assert failed == 0, "存在失败断言：%s" % [r[0] for r in results if not r[2]]
print("EXIT=0（转正步③ 复跑 · 对正式条文 · 本侧本机只读）")
