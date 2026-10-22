# -*- coding: utf-8 -*-
"""相遇专章 · 可机验断言【复跑版·对正式条文】（转正步③ 复跑 · 本侧本机只读）

⭐ 依据：TDCA-STD-SCENE-ENCOUNTER-001（生效 V1.0·人读版＋机读版）
⭐ 说明：v1 作用于「条款要点件」；本版作用于 ⭐【正式条文】（人读版 ＋ 机读版）。
⭐ 分档（承 TDCA-HANDOFF-EXEC-ENC-ASSERT-TIER-001 · 2026-10-22）：
   - 默认档 v1.0：对 V1.0 正式件——A-1a／A-1c／A-2c 三验实跑；
     其余九条（A-1b／A-2a／A-2b／A-3a~d／A-4a~b）记 SKIP-DRAFT-ERA（草案时代结构面断言，
     V1.0 机读改 chapters 制无对应结构；⛔ 记 PASS、⛔ 记 FAIL、⛔ 删代码，沿革仍可由 v0.9 档复现）。
   - 沿革档 v0.9：`--target v0.9`（或裸 `v0.9`）——对 archive/ 之 V0.9 机读草案 12 条全实跑。
⭐ 纪律：零依赖（标准库 + PyYAML）；只读；⛔ 不改任何在册件
"""
import os
import re
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 档选择：--target v0.9 / 裸 v0.9 → 沿革档；否则默认 v1.0 正式档
TARGET = "v1.0"
for i, a in enumerate(sys.argv[1:]):
    if a == "--target" and i + 2 <= len(sys.argv):
        TARGET = sys.argv[i + 2]
    elif a in ("v0.9", "v1.0"):
        TARGET = a
assert TARGET in ("v1.0", "v0.9"), "未知档：%s（只认 v1.0 / v0.9）" % TARGET

# 路径锚定（改造令·甲）：仓内相对——本脚本位 docs/experiments/encounter-001/
_HERE = os.path.dirname(os.path.abspath(__file__))
F_MD = os.path.normpath(os.path.join(_HERE, "..", "..", "regulations", "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（人读版·V1.0已生效）.md"))
if TARGET == "v0.9":
    F_YM = os.path.normpath(os.path.join(_HERE, "..", "..", "..", "archive", "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（机读版·V0.9-DRAFT）.yaml"))
else:
    F_YM = os.path.normpath(os.path.join(_HERE, "..", "..", "regulations", "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（机读版·V1.0已生效）.yaml"))

assert os.path.exists(F_MD), "缺人读版"
assert os.path.exists(F_YM), "缺机读版"
t_md = open(F_MD, encoding="utf-8").read()
doc = yaml.safe_load(open(F_YM, encoding="utf-8"))
mf = doc.get("machine_fields")  # V0.9 草案有；V1.0 机读为 chapters 制，无此键（正常，勿判错）
t_all = t_md + "\n" + open(F_YM, encoding="utf-8").read()

results = []


def check(no, desc, ok, detail=""):
    results.append((no, desc, bool(ok)))
    print("[%s] %s -> %s%s" % ("PASS" if ok else "FAIL", no, "PASS" if ok else "FAIL",
                               ("  | " + detail) if detail else ""))


# 九条草案时代结构面断言之退役理由（v1.0 档记 SKIP-DRAFT-ERA 用；v0.9 档仍实跑）
RETIRED = {
    "A-1b": "V1.0 机读改 chapters 制、无 definitions 结构面；定义/划界语义由人读 art.4/5 文本承载（A-1a/A-1c 续验）",
    "A-2a": "V1.0 机读无 encounter_status 结构面；二分语义由 art.8 文本承载（A-2c 续验否定语境）",
    "A-2b": "INVALID/真相遇/假相遇为 V0.9 状态值设计，V1.0 正式文本已弃（art.8「不设真假相遇判定」）",
    "A-3a": "V1.0 机读无 legal_transitions 结构面；流程语义由 art.11/12 文本承载",
    "A-3b": "同上；且 SPEC 含（握手/相遇→拒绝）两对，V1.0 文本无拒绝迁移表述，等值判定必失败",
    "A-3c": "V1.0 机读无合法集结构面；「其余迁移一律拒绝」由 art.12 文本承载",
    "A-3d": "config_call_requires_states 为 V0.9 字段；V1.0 文本仅 art.13「未握手不得调用配置权」",
    "A-4a": "gates.allowed R1~R10 为 V0.9 枚举；V1.0 全文无 R 编号（art.13「沿用既有条目，不新增」）",
    "A-4b": "R11 为 V0.9 设计值；V1.0 全文无 R11 表述",
}


def skip_retired(no):
    desc = RETIRED.get(no, "")
    results.append((no, "SKIP-DRAFT-ERA", None))
    print("[SKIP-DRAFT-ERA] %s -> SKIP-DRAFT-ERA  | 退役理由：%s" % (no, desc))


# ---------- A-1 缝① 划界（正式文本面） ----------
bad = []
for m in re.finditer(r"相遇[^。；\n]{0,8}(收费|计价|入口费)", t_all):
    seg = t_all[max(0, m.start() - 20):m.end() + 20]
    if not re.search(r"⛔|不得|不收费|免费|禁|删|取消", seg):
        bad.append(seg.replace("\n", " "))
check("A-1a", "缝① 正式文本 ⛔ 无「相遇收费」肯定条款", len(bad) == 0, "命中=%d" % len(bad))

if TARGET == "v0.9":
    check("A-1b", "缝① 相遇/撮合各有独立定义",
          (doc["definitions"]["encounter"]["text"] != doc["definitions"]["matchmaking"]["text"])
          and ("相遇 ＝" in t_md or "相遇＝" in t_md), "定义分列=%s" % ("encounter" in doc["definitions"]))
else:
    skip_retired("A-1b")

check("A-1c", "缝① 「并列不互推」在位（正式文本）",
      ("非同一" in t_md) and ("不得互为指代" in t_md))

# ---------- A-2 缝② 存证二分（机读版结构面） ----------
if TARGET == "v0.9":
    check("A-2a", "缝② 机读版 encounter_status.allowed == {发生, 未发生}",
          mf["encounter_status"]["allowed"] == ["发生", "未发生"], str(mf["encounter_status"]["allowed"]))
    check("A-2b", "缝② 机读版 forbidden 含 INVALID/真相遇/假相遇",
          set(["INVALID", "真相遇", "假相遇"]).issubset(set(mf["encounter_status"]["forbidden"])),
          str(mf["encounter_status"]["forbidden"]))
else:
    skip_retired("A-2a")
    skip_retired("A-2b")

bad2 = []
for ln in t_md.splitlines():
    if "INVALID" in ln and not re.search(r"⛔|改|删|取消|不采|不得|无 `INVALID`|上游件|原设计|原述", ln):
        bad2.append(ln.strip()[:80])
check("A-2c", "缝② 人读版中 INVALID 仅见于否定语境（若有）", len(bad2) == 0, "命中=%d" % len(bad2))

# ---------- A-3 缝③ 状态机（机读版结构面） ----------
if TARGET == "v0.9":
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
else:
    for _no in ("A-3a", "A-3b", "A-3c", "A-3d"):
        skip_retired(_no)

# ---------- A-4 门禁一致（机读版结构面） ----------
if TARGET == "v0.9":
    check("A-4a", "门禁 gates.allowed == R1~R10",
          mf["gates"]["allowed"] == ["R%d" % i for i in range(1, 11)], str(mf["gates"]["allowed"]))
    check("A-4b", "⛔ 无新增门禁（R11 仅见于 forbidden_add）",
          ("R11" in mf["gates"]["forbidden_add"]) and ("R11" not in mf["gates"]["allowed"]),
          str(mf["gates"]["forbidden_add"]))
else:
    skip_retired("A-4a")
    skip_retired("A-4b")

# ---------- 汇总 ----------
total = len(results)
passed = sum(1 for r in results if r[2] is True)
skipped = sum(1 for r in results if r[2] is None)
failed = sum(1 for r in results if r[2] is False)
print("---")
print("断言【复跑·%s档】%d ｜ PASS %d ｜ SKIP-DRAFT-ERA %d ｜ FAIL %d"
      % (TARGET, total, passed, skipped, failed))
assert failed == 0, "存在失败断言：%s" % [r[0] for r in results if r[2] is False]
if TARGET == "v1.0":
    assert passed == 3 and skipped == 9, \
        "v1.0 档形态不符：应 3 PASS + 9 SKIP-DRAFT-ERA（实 %d PASS / %d SKIP）" % (passed, skipped)
else:
    assert skipped == 0, "v0.9 沿革档不应出现 SKIP"
print("EXIT=0（%s档 · 本侧本机只读）" % TARGET)
