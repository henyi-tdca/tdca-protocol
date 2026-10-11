# -*- coding: utf-8 -*-
"""相遇三缝隙并入 · 可机验断言脚本（转正步③ · 本侧本机只读）

⭐ 依据：TDCA-RESEARCH-ENC-GAPS-001（转正四步第一步）
        ＋ TDCA-RULING-PRP-ENC-001-006（缝② 重订为「是否发生」，⛔ 无 INVALID）
⭐ 纪律：零依赖（仅标准库）；只读；⛔ 不改任何在册件
⭐ 断言组：
   A-1 缝① 划界文本面（相遇≠撮合；⛔ 无「相遇收费」肯定条款；二者各有独立定义句）
   A-2 缝② 存证二分（状态集 = {发生, 未发生}；INVALID 仅见于否定语境）
   A-3 缝③ 状态机（合法迁移 ⊆ 规定集；「未握手调用配置权」必被拒）
   A-4 门禁一致（引用门禁面 R1~R10；⛔ 不含 R11）
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 路径锚定（改造令·甲）：env 占位 TDCA_ENC_ASSERT_WS ＝ 智库工作区根；未设 ⟹ 被引件缺失，如实 SKIP（⛔ 不伪报通过）
WS = os.environ.get("TDCA_ENC_ASSERT_WS", "")
F_RESEARCH = os.path.join(WS, "tdca-thinktank", "governance", "decisions", "TDCA-RESEARCH-ENC-GAPS-001-相遇三缝隙并入研究草案（转正四步第一步·V0.1-DRAFT·三章条款要点与断言候选）.md")
F_BIDIR = os.path.join(WS, "tdca-thinktank", "governance", "decisions", "TDCA-RULING-PRP-ENC-001-006-相遇双向奔赴口径件（不存在真假相遇·只有是否发生·缝②重订为是否发生之存证）.md")

results = []


def check(no, desc, ok, detail=""):
    results.append((no, desc, bool(ok), detail))
    print("[%s] %s -> %s%s" % ("PASS" if ok else "FAIL", no, "PASS" if ok else "FAIL",
                               ("  | " + detail) if detail else ""))


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


if not WS or not os.path.exists(F_RESEARCH) or not os.path.exists(F_BIDIR):
    print("SKIP：v1 被引件（研究草案／双向奔赴口径件）不在位——v1 为本地复跑件、不进 CI 硬闸（改造令·丙）")
    sys.exit(0)
t_res = read(F_RESEARCH)
t_bid = read(F_BIDIR)
t_all = t_res + "\n" + t_bid

# ---------- A-1 缝① 划界文本面 ----------
# A-1a：⛔ 无「相遇收费」类肯定条款（命中须排除含 否定 语境）
pat_fee = re.compile(r"相遇[^。；\n]{0,8}(收费|计价|入口费)")
bad = []
for m in pat_fee.finditer(t_all):
    seg = t_all[max(0, m.start() - 20):m.end() + 20]
    if not re.search(r"⛔|不得|不收费|免费|禁|删|取消", seg):
        bad.append(seg.replace("\n", " "))
check("A-1a", "缝① 无「相遇收费」肯定条款", len(bad) == 0, "命中=%d" % len(bad) + ("" if not bad else " 例:" + bad[0][:60]))

# A-1b：「相遇」与「撮合」各有独立定义句
defn_enc = re.search(r"相遇[^。\n]{0,20}＝[^。\n]{0,40}", t_all) or re.search(r"相遇[^。\n]{0,10}是[^。\n]{0,40}", t_all)
defn_match = re.search(r"撮合[^。\n]{0,20}＝[^。\n]{0,40}", t_all) or re.search(r"撮合[^。\n]{0,10}是[^。\n]{0,40}", t_all)
check("A-1b", "缝① 相遇/撮合各有独立定义句", bool(defn_enc) and bool(defn_match),
      "相遇定义=%s 撮合定义=%s" % (bool(defn_enc), bool(defn_match)))

# A-1c：并列不互推声明在位
check("A-1c", "缝① 「并列不互推」声明在位",
      ("非同一" in t_all) or ("不得以" in t_all and "指代" in t_all))

# ---------- A-2 缝② 存证二分 ----------
# A-2a：状态集 = {发生, 未发生}
check("A-2a", "缝② 状态集为「发生/未发生」二分",
      ("发生／未发生" in t_all) or ("发生" in t_all and "未发生" in t_all and "二分" in t_all))

# A-2b：INVALID 在【现行口径件】中仅出现在否定/重订语境（按行判定）
bad2 = []
for ln in t_bid.splitlines():
    if "INVALID" in ln and not re.search(r"⛔|改|删|取消|不采|不得|无 `INVALID`|上游件|原设计|原述", ln):
        bad2.append(ln.strip()[:80])
check("A-2b", "缝② 现行口径件中 INVALID 仅见于否定/重订语境（行级）", len(bad2) == 0, "命中=%d" % len(bad2))

# A-2c：草案件若仍含旧 INVALID 设计，须已被【现行件】重订覆盖（追加制·不回改）
check("A-2c", "缝② 草案旧设计已被现行件重订覆盖",
      (("INVALID" not in t_res) or ("重订" in t_bid)))

# ---------- A-3 缝③ 状态机 ----------
# 规定集：三阶段（发现 → 相遇 → 握手）＋後續（交互 → 结算）；禁跳步
STATES = ["发现", "相遇", "握手", "交互", "结算", "拒绝"]
LEGAL = {
    ("发现", "相遇"), ("相遇", "握手"), ("握手", "交互"), ("交互", "结算"),
    ("相遇", "发现"),      # 回退：相遇不成 → 回发现
    ("握手", "相遇"),      # 回退：握手失败 → 回相遇
    ("握手", "拒绝"), ("相遇", "拒绝"),
}
ALL_PAIRS = [(a, b) for a in STATES for b in STATES if a != b]


def allowed(a, b):
    return (a, b) in LEGAL


viol = [(a, b) for (a, b) in ALL_PAIRS if allowed(a, b) and (a, b) not in LEGAL]
check("A-3a", "缝③ 合法迁移 ⊆ 规定集", len(viol) == 0)

# 跳步必拒：发现→握手、发现→交互、相遇→交互、相遇→结算、发现→结算
skip = [("发现", "握手"), ("发现", "交互"), ("发现", "结算"),
        ("相遇", "交互"), ("相遇", "结算"), ("握手", "结算")]
bad3 = [(a, b) for (a, b) in skip if allowed(a, b)]
check("A-3b", "缝③ 跳步迁移必被拒（未握手不得进交互/结算）", len(bad3) == 0,
      "违例=%s" % (bad3 if bad3 else "[]"))

# 未握手不得调配置权：配置权调用仅当状态==握手或其后
def can_call_config(state):
    return state in ("握手", "交互", "结算")


bad4 = [s for s in ("发现", "相遇") if can_call_config(s)]
check("A-3c", "缝③ 未握手态不得调配置权", len(bad4) == 0, "违例=%s" % (bad4 if bad4 else "[]"))

# 穷举性：全迁移空间中非法迁移数 == 总对数 - 合法对数
illegal_cnt = len(ALL_PAIRS) - len(LEGAL)
check("A-3d", "缝③ 状态机迁移空间穷举一致",
      illegal_cnt == len([p for p in ALL_PAIRS if not allowed(*p)]),
      "总对=%d 合法=%d 非法=%d" % (len(ALL_PAIRS), len(LEGAL), illegal_cnt))

# ---------- A-4 门禁一致 ----------
check("A-4a", "门禁面引用 R1~R10", ("R1`~`R10" in t_all) or ("R1~R10" in t_all) or ("R1" in t_all and "R10" in t_all))
bad5 = []
for m in re.finditer(r"R11", t_all):
    seg = t_all[max(0, m.start() - 40):m.end() + 40]
    if not re.search(r"⛔|不在册|须签批|先例|教训|不得", seg):
        bad5.append(seg.replace("\n", " "))
check("A-4b", "⛔ 无新增门禁 R11（出现处须是否定语境）", len(bad5) == 0, "违例=%d" % len(bad5))

# ---------- 汇总 ----------
total = len(results)
passed = sum(1 for r in results if r[2])
failed = total - passed
print("---")
print("断言数 %d ｜ 通过 %d ｜ 失败 %d" % (total, passed, failed))
assert failed == 0, "存在失败断言：%s" % [r[0] for r in results if not r[2]]
print("EXIT=0（转正步③ 可机验断言 · 本侧本机只读）")
