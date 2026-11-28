#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NCA 封块体检器（只读）—— L1-SI-196 · 依 `TDCA-AMEND-OPS-MANUAL-001-003` §三

判四项（照手册 AMEND-3 之定期条目）：
  ① 链尾对齐：末块 coverage.gseq_to  对  台账 max(gseq)          → GAP(n)
     ①b 拆两值（OPS-002 题A，2026-11-28）：GAP 按记录日拆为
        GAP_CLOSED  跨已闭日漏封（= 时间戳日期早于今日之未封记录；真缺陷，非零告警）
        GAP_TODAY   当日待封（= 今日之未封记录；正常态，仅可见⛔告警）
     「已闭日」界定未改①之判据：仅对未封记录按时间戳日期分类，日历日以本机当地日为准。
  ② 重复块  ：同 prev + 同 root + 同区间 出现 ≥2 次                → DUP
  ③ 签名滞后：块未见于签名登记册                                  → UNSIGNED(n)
  ④ 缺日    ：台账有记录之日，无块覆盖该日之记录（且未标当日无锚）  → MISSING_DAY(n)

退出码三分（⛔ 混）：
  0 = 全 OK（含仅有当日待封之正常态）
  1 = 有差（GAP_CLOSED_NEW / DUP_NEW / UNSIGNED / MISSING_DAY 任一；
      GAP_CLOSED_NEW 系跨已闭日漏封扣除宽限余额后之余量；
      当日待封 GAP_TODAY 不计入——旧版之「GAP 任一大于零即 1」由此收敛为真缺陷告警）
  2 = 读数不可得（目录或台账或块文件缺失/不可解析）

用法：
  python nca_seal_check.py --nca-dir /path/to/.tdca-nca [--json]

只读：⛔ 写任何文件、⛔ 改块、⛔ 联网。
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime


def load_blocks(nca):
    out = []
    for p in sorted(glob.glob(os.path.join(nca, "reports", "_NCA-*BLOCK-*.json"))):
        base = os.path.basename(p)
        if "SIGNREG" in base:
            continue
        try:
            with open(p, encoding="utf-8") as f:
                j = json.load(f)
            out.append(dict(file=base, block_id=j.get("block_id"), kind=j.get("kind"),
                            height=j.get("height"),
                            prev=j.get("prev_block_hash"),
                            root=(j.get("merkle") or {}).get("root_sha256"),
                            f=(j.get("coverage") or {}).get("gseq_from"),
                            t=(j.get("coverage") or {}).get("gseq_to"),
                            n=(j.get("coverage") or {}).get("records")))
        except Exception:
            out.append(dict(file=base, error=True))
    return out


def load_records(nca):
    """极简读台账：只取每条的 gseq 与 timestamp（⛔ 依赖 yaml 库）。"""
    p = os.path.join(nca, "NCA-REGISTRY.yaml")
    recs = []
    cur = {}
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.startswith("  - gseq:") or line.startswith("- gseq:"):
                if cur.get("gseq"):
                    recs.append(cur)
                cur = {"gseq": line.split(":", 1)[1].strip().strip("'\""), "ts": None}
            elif cur and "timestamp:" in line and cur["ts"] is None:
                cur["ts"] = line.split(":", 1)[1].strip().strip("'\"")
    if cur.get("gseq"):
        recs.append(cur)
    return recs


def load_signreg(nca):
    # 须修#80（8/8）签名登记读失败须计数上报——原 except pass 使坏登记文件被当
    # 「该批未签名」之外的沉默缺口，校验面漏报；现返 (签名集, 读失败数)（BACKLOG-001 §二）
    signed = set()
    read_fail = 0
    for p in glob.glob(os.path.join(nca, "reports", "_NCA-BLOCK-SIGNREG-*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                j = json.load(f)
            for b in j.get("blocks") or []:
                signed.add(b.get("block_id"))
        except Exception:
            read_fail += 1
    return signed, read_fail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nca-dir", default=os.environ.get("TDCA_NCA_DIR", ".tdca-nca"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--known", default=None, help="已知项登记 JSON（默认 <nca>/reports/_NCA-SEAL-KNOWN.json）")
    a = ap.parse_args()
    nca = a.nca_dir

    if not os.path.isdir(os.path.join(nca, "reports")):
        print("UNKNOWN 读数不可得：reports 目录缺失 -> %s" % nca)
        return 2
    blocks = load_blocks(nca)
    if not blocks:
        print("UNKNOWN 读数不可得：未找到块文件")
        return 2
    if any(b.get("error") for b in blocks):
        print("UNKNOWN 读数不可得：块文件解析失败")
        return 2
    try:
        recs = load_records(nca)
    except Exception as e:                                    # noqa
        print("UNKNOWN 读数不可得：台账不可读 %s" % e)
        return 2

    res = {}
    # ① 链尾对齐
    sealed = [b for b in blocks if b.get("t")]
    tail_to = max(sealed, key=lambda b: int(b["t"][5:]))["t"] if sealed else None
    maxt = max(int(r["gseq"][5:]) for r in recs) if recs else 0
    gap = maxt - int(tail_to[5:]) if tail_to else maxt
    res["tail_block"] = tail_to
    res["ledger_max"] = "GSEQ-%04d" % maxt
    res["GAP"] = max(gap, 0)

    # ①b GAP 按记录日拆两值（OPS-002 题A）
    covered = set()
    for b in sealed:
        for r in recs:
            g = int(r["gseq"][5:])
            if int(b["f"][5:]) <= g <= int(b["t"][5:]):
                covered.add(r["gseq"])
    today = datetime.now().strftime("%Y-%m-%d")
    tail_n = int(tail_to[5:]) if tail_to else 0
    gap_today, gap_closed, gap_closed_days = 0, 0, {}
    for r in recs:
        if int(r["gseq"][5:]) <= tail_n:
            continue  # 已被链尾块覆盖，非 GAP
        d = (r.get("ts") or "????-??-??")[:10]
        if d == today:
            gap_today += 1
        else:
            gap_closed += 1
            gap_closed_days[d] = gap_closed_days.get(d, 0) + 1
    res["GAP_CLOSED"] = gap_closed
    res["GAP_CLOSED_DAYS"] = gap_closed_days
    res["GAP_TODAY"] = gap_today

    # ② 重复块
    seen, dup = {}, []
    for b in blocks:
        if b.get("kind") == "GENESIS":
            continue
        k = (b.get("prev"), b.get("root"), b.get("f"), b.get("t"))
        if k in seen:
            dup.append((seen[k], b["block_id"]))
        else:
            seen[k] = b["block_id"]
    res["DUP"] = dup

    # ③ 签名滞后
    signed, signreg_read_fail = load_signreg(nca)
    res["SIGNREG_READ_FAIL"] = signreg_read_fail
    uns = [b["block_id"] for b in blocks if b["block_id"] not in signed]
    res["UNSIGNED"] = uns

    # ④ 缺日（台账有记录之日，须有块覆盖该日内任一记录）
    #    covered 复用 ①b 已算之覆盖集
    days = {}
    for r in recs:
        if r.get("ts"):
            days.setdefault(r["ts"][:10], []).append(r["gseq"])
    missday = {}
    for d, gs in sorted(days.items()):
        if not any(g in covered for g in gs):
            missday[d] = len(gs)
    res["MISSING_DAY"] = missday

    # 已知项登记（⛔ 静默消差：命中者仍打印，仅不计入 DIFF）
    known_p = a.known or os.path.join(nca, "reports", "_NCA-SEAL-KNOWN.json")
    known = {}
    if os.path.isfile(known_p):
        try:
            with open(known_p, encoding="utf-8") as f:
                known = json.load(f) or {}
        except Exception:
            known = {}
    k_dup = {tuple(sorted(x)) for x in (known.get("dup") or [])}
    res["DUP_KNOWN"] = [d for d in res["DUP"] if tuple(sorted(d)) in k_dup]
    res["DUP_NEW"] = [d for d in res["DUP"] if tuple(sorted(d)) not in k_dup]
    res["GAP_KNOWN_MAX"] = int(known.get("gap_allow", 0) or 0)
    res["GAP_NEW"] = max(res["GAP"] - res["GAP_KNOWN_MAX"], 0)
    # 宽限先抵当日待封（正常态），余额抵跨已闭日漏封——真漏封必浮出
    allow_for_closed = max(res["GAP_KNOWN_MAX"] - res["GAP_TODAY"], 0)
    res["GAP_CLOSED_NEW"] = max(res["GAP_CLOSED"] - allow_for_closed, 0)

    ok = (res["GAP_CLOSED_NEW"] == 0 and not res["DUP_NEW"] and not res["UNSIGNED"]
          and not res["MISSING_DAY"])
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("tail_block=%s  ledger_max=%s" % (res["tail_block"], res["ledger_max"]))
        print("[%s] GAP=%d = 跨已闭日漏封 %d -> 告警 %d | 当日待封 %d 正常态" % (
              "OK" if res["GAP_CLOSED_NEW"] == 0 else "GAP",
              res["GAP"], res["GAP_CLOSED"], res["GAP_CLOSED_NEW"], res["GAP_TODAY"]))
        print("[%s] DUP=%d (新 %d / 已知 %d) %s" % ("OK" if not res["DUP_NEW"] else "DUP",
              len(res["DUP"]), len(res["DUP_NEW"]), len(res["DUP_KNOWN"]),
              res["DUP_NEW"] if res["DUP_NEW"] else ""))
        print("[%s] UNSIGNED=%d" % ("OK" if not res["UNSIGNED"] else "UNSIGNED", len(res["UNSIGNED"])))
        print("[%s] SIGNREG_READ_FAIL=%d" % ("OK" if signreg_read_fail == 0 else "WARN",
              signreg_read_fail))
        print("[%s] MISSING_DAY=%d %s" % ("OK" if not res["MISSING_DAY"] else "MISSING_DAY",
              len(res["MISSING_DAY"]), res["MISSING_DAY"]))
        print("VERDICT=%s" % ("OK" if ok else "DIFF"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
