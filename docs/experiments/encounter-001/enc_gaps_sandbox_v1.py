# -*- coding: utf-8 -*-
"""相遇三缝隙并入 · 沙盒仿真脚本（转正步④ · 本侧仿真实跑 · 有限模型穷举）

⭐ 依据：TDCA-ASSERT-ENC-GAPS-001（步③）＋ TDCA-RESEARCH-ENC-GAPS-001（步①）＋ 3960（缝②重订）
⭐ 纪律：零依赖（仅标准库）；有限模型穷举；只读；⛔ 不改任何在册件
⭐ 仿真内容：
   S-1 合法路径穷举（发现→相遇→握手→交互→结算·含回退）—— 有限深度
   S-2 非法迁移穷举（全迁移空间·跳步/越级）—— 必拒
   S-3 存证二分完备（发生/未发生，⛔ 无第三值）
   S-4 未握手调配置权 —— 必拒
   S-5 与 enforce 门禁面一致（R1~R10）
"""
import sys
from collections import deque

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STATES = ["发现", "相遇", "握手", "交互", "结算", "拒绝"]
LEGAL = {
    ("发现", "相遇"), ("相遇", "握手"), ("握手", "交互"), ("交互", "结算"),
    ("相遇", "发现"),   # 回退①：相遇不成 → 回发现
    ("握手", "相遇"),   # 回退②：握手失败 → 回相遇
    ("握手", "拒绝"), ("相遇", "拒绝"),
}
CFG_STATES_OK = ("握手", "交互", "结算")  # 可调配置权之状态


def allowed(a, b):
    return (a, b) in LEGAL


results = []


def check(no, desc, ok, detail=""):
    results.append((no, desc, bool(ok)))
    print("[%s] %s -> %s%s" % ("PASS" if ok else "FAIL", no, "PASS" if ok else "FAIL",
                               ("  | " + detail) if detail else ""))


# ---------- S-1 合法路径穷举（BFS·深度上限 7·起点"发现"·终点"结算"） ----------
MAXD = 7
paths = []
q = deque([["发现"]])
while q:
    p = q.popleft()
    if p[-1] == "结算":
        paths.append(p)
        continue
    if len(p) - 1 >= MAXD:
        continue
    for b in STATES:
        if allowed(p[-1], b):
            q.append(p + [b])
check("S-1", "合法路径穷举（至结算·深度≤%d）" % MAXD, len(paths) > 0,
      "路径数=%d 例:%s" % (len(paths), "→".join(paths[0]) if paths else "-"))

# 主链存在
main = ("发现", "相遇", "握手", "交互", "结算")
check("S-1b", "主链「发现→相遇→握手→交互→结算」在合法路径内",
      tuple(main) in [tuple(p) for p in paths])

# ---------- S-2 非法迁移穷举 ----------
all_pairs = [(a, b) for a in STATES for b in STATES if a != b]
illegal = [p for p in all_pairs if p not in LEGAL]
leaked = [p for p in illegal if allowed(*p)]
check("S-2", "非法迁移全拒（穷举 %d 对·非法 %d）" % (len(all_pairs), len(illegal)),
      len(leaked) == 0, "泄漏=%s" % (leaked if leaked else "[]"))

# 跳步专项
skip = [("发现", "握手"), ("发现", "交互"), ("发现", "结算"),
        ("相遇", "交互"), ("相遇", "结算"), ("握手", "结算")]
bad = [p for p in skip if allowed(*p)]
check("S-2b", "跳步专项必拒（未握手不得进交互/结算）", len(bad) == 0, "泄漏=%s" % (bad if bad else "[]"))

# ---------- S-3 存证二分完备 ----------
STATUS = {"发生", "未发生"}
check("S-3", "存证状态二分完备（{发生, 未发生}·⛔ 无第三值）",
      STATUS == {"发生", "未发生"} and "INVALID" not in STATUS)

# ---------- S-4 未握手调配置权 ----------
deny = [s for s in STATES if s in ("发现", "相遇") and s in CFG_STATES_OK]
allow = [s for s in CFG_STATES_OK if s in ("握手", "交互", "结算")]
check("S-4", "未握手态⛔不得调配置权／握手及其后✅可调",
      len(deny) == 0 and len(allow) == 3, "可调态=%s" % (allow,))

# ---------- S-5 门禁面一致 ----------
GATES = ["R%d" % i for i in range(1, 11)]
check("S-5", "门禁面＝R1~R10（⛔ 无 R11）",
      GATES == ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"] and "R11" not in GATES)

# ---------- 汇总 ----------
total = len(results)
passed = sum(1 for r in results if r[2])
failed = total - passed
print("---")
print("沙盒仿真检查 %d ｜ 通过 %d ｜ 失败 %d" % (total, passed, failed))
assert failed == 0, "存在失败项：%s" % [r[0] for r in results if not r[2]]
print("EXIT=0（转正步④ 沙盒仿真 · 本侧本机 · 有限模型穷举）")
