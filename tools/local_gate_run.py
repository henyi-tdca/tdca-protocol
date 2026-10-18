# -*- coding: utf-8 -*-
r"""本地门禁 · 一键跑法器 v1（L1-SI-137 · 退路 C）

用途：在「平台无强制门禁」条件下，把工程测试**在本地跑起来并留痕**（结果 JSON ＋ 文本两态）。
依据：TDCA-PLAN-CI-FALLBACK-C-LOCAL-001（退路 C 实施方案草案）§三 运行口径四要素。

纪律（不变量）：
  ⛔ 不改既有 workflow、⛔ 不改既有脚本、⛔ 不降门禁标准（判定逻辑即各工程自带测试，一字不改）。
  ⛔ 本器只「跑 + 记 + 汇总」，不含任何写仓/推送/合并动作。

用法：
  python _local_gate_run_v1.py --repo <主仓clone根> [--only NAME,NAME] [--out OUTDIR] [--timeout 900]

留痕：
  <OUTDIR>/local-gate-<UTC时间戳>.json   结构化（逐门：命令/退出码/耗时/结论/输出尾）
  <OUTDIR>/local-gate-<UTC时间戳>.txt    人读文本（逐门一行 + 尾部详情）
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 十一门（本轮新增）；此前既有八门可另补（本器只跑工程测试类）
TARGETS = [
    # (门名, 相对工作目录, 依赖件(相对仓根, 无则 None), 动作)
    ("toolchain",           "tdca-toolchain",                     "tdca-toolchain/pyproject.toml",         "pytest"),
    ("sbx-ops",             "tdca-sbx-ops/backend",               "tdca-sbx-ops/backend/requirements.txt", "pytest"),
    ("fos",                 "tdca-fos",                           "tdca-fos/requirements.txt",             "pytest"),
    ("workbuddy",           "tdca-workbuddy",                     None,                                    "pytest"),
    ("utility-genie",       "tdca-utility-genie",                 None,                                    "pytest"),
    ("cls",                 "tdca-cls",                           None,                                    "pytest"),
    ("ecoscan",             "ecoscan",                            None,                                    "pytest"),
    ("ns-ops",              "tdca-ns-ops/backend",                "tdca-ns-ops/backend/requirements.txt",  "pytest"),
    ("flow-orchestrator",   "tdca-flow-orchestrator",             None,                                    "compile"),
    ("gateway",             "true-source/tdca-web/gateway",       None,                                    "pytest"),
    ("frontend",            "true-source/tdca-web/tdca-frontend", None,                                    "npm"),
]


def _run(cmd, cwd, timeout):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=timeout)
        return p.returncode, (time.time() - t0), (p.stdout or b"").decode("utf-8", "replace"), \
               (p.stderr or b"").decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 124, (time.time() - t0), "", "TIMEOUT（%ss）" % timeout
    except FileNotFoundError as e:
        return 127, (time.time() - t0), "", "命令缺失：%s" % e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=".")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    only = [s.strip() for s in args.only.split(",") if s.strip()]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(args.out, exist_ok=True)
    rows, results = [], []

    for name, sub, dep, act in TARGETS:
        if only and name not in only:
            continue
        wd = os.path.join(args.repo, sub)
        row = {"gate": name, "cwd": sub, "action": act, "exists": os.path.isdir(wd)}
        if not row["exists"]:
            row.update({"rc": None, "verdict": "MISSING", "seconds": 0.0, "cmd": None})
            rows.append(row); results.append(row); continue

        if act == "pytest":
            py = sys.executable
            cmd = [py, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
        elif act == "compile":
            cmd = [sys.executable, "-m", "compileall", "-q", "src"]
        elif act == "npm":
            cmd = ["npm", "test", "--silent"]
        else:
            cmd = [sys.executable, "-c", "print('no-op')"]

        rc, sec, out, err = _run(cmd, wd, args.timeout)
        tail = (out + ("\n[stderr]\n" + err if err.strip() else "")).strip().splitlines()[-12:]
        row.update({"rc": rc, "seconds": round(sec, 1), "cmd": " ".join(cmd),
                    "dep_present": (os.path.isfile(os.path.join(args.repo, dep)) if dep else None),
                    "verdict": ("GREEN" if rc == 0 else ("RED" if rc else "RED")),
                    "tail": tail})
        rows.append(row); results.append(row)
        print("[%s] rc=%s %.1fs -> %s" % (name, rc, sec, row["verdict"]))

    summary = {
        "generated_at_utc": ts,
        "repo": os.path.basename(os.path.normpath(args.repo)),
        "note": "本地跑 · 无平台强制（退路 C）",
        "counts": {
            "green": sum(1 for r in results if r["verdict"] == "GREEN"),
            "red": sum(1 for r in results if r["verdict"] == "RED"),
            "missing": sum(1 for r in results if r["verdict"] == "MISSING"),
        },
        "gates": rows,
    }
    jp = os.path.join(args.out, "local-gate-%s.json" % ts)
    tp = os.path.join(args.out, "local-gate-%s.txt" % ts)
    with open(jp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    with open(tp, "w", encoding="utf-8", newline="\n") as f:
        f.write("本地门禁跑法结果（退路 C） %s\n" % ts)
        f.write("绿 %(green)s / 红 %(red)s / 缺 %(missing)s\n" % summary["counts"])
        for r in results:
            f.write("- %-20s %-8s %s\n" % (r["gate"], r.get("verdict"), r.get("cmd")))
    print("JSON:", jp)
    print("TXT :", tp)
    print("计数:", summary["counts"])
    return 0 if summary["counts"]["red"] == 0 and summary["counts"]["missing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
