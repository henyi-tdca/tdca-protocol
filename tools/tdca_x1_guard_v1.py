# -*- coding: utf-8 -*-
"""TDCA 可判子集 X-1 · **A 级六条守卫**（CI 可挂 · 只读 · 无外部依赖）

⭐ 验什么：`E-01` `E-02` `E-08` `E-09` `E-11` `E-12` 六条**判定式**（本侧可完全机验、不需产品实例）。
⭐ 用法：
    python tdca_x1_guard_v1.py <samples_dir> [--strict]
    samples_dir 下按条号放样本：E-01.json … E-12.json（**只认这六条**；缺者记 SKIP）
⭐ 退出码：0 = 已有样本全过（GREEN）／1 = 有败（RED）／2 = 目录不存在
⭐ ⛔ 纪律：缺样本记 SKIP、**⛔ 假绿**；`--strict` 下 SKIP 亦判 RED（样本应齐时用）。
⭐ 依据：TDCA-DESIGN-L1SI168-ASSERT-X1-001（GSEQ-5846）／X1V2-001（GSEQ-5855）
"""
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EPS = 1e-9
LEVEL = "A"


def e01(s):
    bal = dict(s["open"])
    for t in s["tx"]:
        bal[t["from"]] -= t["amt"]
        bal[t["to"]] += t["amt"]
    close_ok = all(abs(bal[p] - s["close"][p]) < EPS for p in bal)
    net_ok = abs(sum(s["net"].values())) < EPS
    each = all(abs(s["net"][p] - (s["close"][p] - s["open"][p])) < EPS for p in bal)
    return close_ok and net_ok and each


def e02(s):
    def bracket(x):
        for lo, hi, rate in s["table"]:
            if lo <= x < hi:
                return round(x * rate, 2)
        return 0.0

    calc = {k: bracket(v) for k, v in s["income"].items()}
    if any(abs(calc[k] - s["tax"][k]) > 1e-6 for k in calc):
        return False
    return abs(sum(s["income"].values()) - sum(s["tax"].values()) - s["declared_net"]) < 1e-6


def e08(s):
    f, g = s["f"], s["g"]
    inv_ok = all(g[v] == k for k, v in f.items())
    back_ok = all(f[g[y]] == y for y in g)
    return inv_ok and back_ok and bool(s["receipt_ok"])


def e09(s):
    labels = [x["label"] for x in s["steps"]]
    if len(s["steps"]) != 14 or len(set(labels)) != 14:
        return False
    return abs(sum(s["allocation"].values()) - s["surplus"]) < 1e-6


def e11(s):
    for q in s["questions"]:
        if q["chapter"] not in s["chapters"]:
            return False
        if not (0 <= q["score"] <= q["full"]):
            return False
    return True


def e12(s):
    a, b = s["labeler_a"], s["labeler_b"]
    diff = {k for k in a if k in b and a[k] != b[k]}
    return diff == set(s["reported_diff"])


CASES = [
    ("E-01", "净额结算（守恒＋余额闭合）", e01),
    ("E-02", "微交付税额（档位＝表＋守恒）", e02),
    ("E-08", "身份双向映射（互逆＋存证）", e08),
    ("E-09", "S-Right 十四步（计数＋分配闭合）", e09),
    ("E-11", "出题评分（可溯源＋界内）", e11),
    ("E-12", "标注初筛分歧（集合相等）", e12),
]


def main(argv):
    if len(argv) < 2:
        print("用法: python tdca_x1_guard_v1.py <samples_dir> [--strict]")
        return 2
    d = argv[1]
    strict = "--strict" in argv[2:]
    if not os.path.isdir(d):
        print(f"⛔ 样本目录不存在：{d}")
        return 2
    n_pass = n_fail = n_skip = 0
    print("=== TDCA X-1 · A 级六条守卫（" + LEVEL + " 级）===")
    for cid, name, fn in CASES:
        p = os.path.join(d, cid + ".json")
        if not os.path.isfile(p):
            n_skip += 1
            print(f"{cid}  SKIP  缺样本（⛔ 不假绿）  {name}")
            continue
        try:
            s = json.load(open(p, encoding="utf-8"))
            ok = bool(fn(s))
        except Exception as e:
            ok = False
            print(f"      ↳ 样本解析或判定异常：{type(e).__name__}: {e}")
        if ok:
            n_pass += 1
            print(f"{cid}  PASS  {name}")
        else:
            n_fail += 1
            print(f"{cid}  FAIL  {name}")
    total = len(CASES)
    print()
    print(f"PASS {n_pass}/{total}｜FAIL {n_fail}｜SKIP {n_skip}"
          + ("（--strict：SKIP 计 RED）" if strict else ""))
    red = n_fail > 0 or (strict and n_skip > 0)
    print("X1-GUARD=" + ("RED" if red else "GREEN"))
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
