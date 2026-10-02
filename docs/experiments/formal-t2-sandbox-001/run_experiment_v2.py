"""TDCA 沙盒实验 T3 · 第二实现重跑跑法脚本（run_experiment_v2.py）

T3 步骤 B/C/D 之执行件（新建；不改 gate.py / run_experiment.py，仅只读导入复用）：
- 默认档：以 gate_v2（表驱动＋位掩码）重跑原 26 包，输出与 run_experiment.py
  同格式之确定性结果（无时间戳；供同实现两次运行逐字节比对）；
- --compare 档：同输入分别过 gate.py（第一实现）与 gate_v2.py（第二实现），
  逐包比对判定与理由码，输出比对记录；
- --shuffle 档：换枚举顺序（申请包逆序＋登记簿载入逆序）以第二实现重跑，
  核结果集是否不变（换环境/换精度之可行替代）。

退出码语义：0＝档位目标达成且无失守/无不一致；非 0＝反之。
"""

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

sys.path.insert(0, HERE)
from gate import gate as gate_v1  # noqa: E402  第一实现（只读导入）
from gate_v2 import gate as gate_v2  # noqa: E402  第二实现
from run_experiment import build_bundles, read_bytes  # noqa: E402  只读复用取数


def evaluate(gate_fn, bundles, registries, h, order=None):
    seq = order(bundles) if order else bundles
    out = []
    for b in seq:
        verdict, reasons = gate_fn(b, registries[b["registry"]], h, read_bytes)
        out.append({"case_id": b["case_id"], "branch": b["branch"],
                    "expected": b["expected"], "verdict": verdict,
                    "reasons": list(reasons)})
    return out


def render_lines(results, head, title="T2-SANDBOX-EXP v1"):
    lines = [f"{title} | head={head}"]
    fp = br = 0
    for r in results:
        ok = r["verdict"] == r["expected"]
        if r["expected"] == "ALLOW" and r["verdict"] != "ALLOW":
            fp += 1
        if r["expected"] == "BLOCK" and r["verdict"] != "BLOCK":
            br += 1
        lines.append(f"{r['case_id']} | {r['branch']} | expected={r['expected']} "
                     f"| verdict={r['verdict']} | reasons={','.join(r['reasons']) if r['reasons'] else '-'} "
                     f"| {'OK' if ok else 'MISMATCH'}")
    lines.append(f"SUMMARY | total={len(results)} false_positive={fp} breach={br}")
    return lines, fp, br


def seq_digest(results):
    canonical = json.dumps(results, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main():
    mode = sys.argv[1].lstrip("-") if len(sys.argv) > 1 else "default"
    bundles, real_rows, sim_rows, h = build_bundles()
    registries = {"REAL": real_rows, "FIXTURE": sim_rows}

    if mode == "default":
        results = evaluate(gate_v2, bundles, registries, h)
        lines, fp, br = render_lines(results, h, title="T2-SANDBOX-EXP v2")
        sys.stdout.write("\n".join(lines) + "\n")
        return 0 if (fp == 0 and br == 0) else 1

    if mode == "compare":
        r1 = evaluate(gate_v1, bundles, registries, h)
        r2 = evaluate(gate_v2, bundles, registries, h)
        lines = [f"T3-COMPARE | head={h}"]
        identical = True
        for a, b in zip(r1, r2):
            same = (a["verdict"] == b["verdict"] and a["reasons"] == b["reasons"])
            identical = identical and same
            lines.append(f"{a['case_id']} | v1={a['verdict']}[{','.join(a['reasons']) if a['reasons'] else '-'}] "
                         f"| v2={b['verdict']}[{','.join(b['reasons']) if b['reasons'] else '-'}] "
                         f"| {'SAME' if same else 'DIFF'}")
        d1, d2 = seq_digest(r1), seq_digest(r2)
        lines.append(f"COMPARE | identical={identical} | seq_sha_v1={d1} | seq_sha_v2={d2}")
        sys.stdout.write("\n".join(lines) + "\n")
        return 0 if identical else 2

    if mode == "shuffle":
        fwd = evaluate(gate_v2, bundles, registries, h)
        rev_regs = {k: dict(reversed(list(v.items()))) for k, v in registries.items()}
        rev = evaluate(gate_v2, bundles, rev_regs, h, order=lambda bs: list(reversed(bs)))
        # 结果集与载入/枚举顺序无关：按 case_id 重排后两序列须逐位一致
        key = lambda rs: sorted(rs, key=lambda r: r["case_id"])  # noqa: E731
        invariant = (key(fwd) == key(rev))
        lines = [f"T3-SHUFFLE | head={h}",
                 f"SHUFFLE | invariant={invariant} | fwd_sha={seq_digest(key(fwd))} | rev_sha={seq_digest(key(rev))}"]
        sys.stdout.write("\n".join(lines) + "\n")
        return 0 if invariant else 3

    sys.stderr.write(f"unknown mode: {mode}\n")
    return 64


if __name__ == "__main__":
    sys.exit(main())
