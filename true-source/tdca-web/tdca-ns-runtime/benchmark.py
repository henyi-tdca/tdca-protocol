# -*- coding: utf-8 -*-
"""
TDCA-NS-RUNTIME-001 · M1 Layer 1 性能基准（A-4）
================================================
度量: Layer 1 全链路预检时延（热路径）
目标: avg <10ms / P95 <10ms

用法: python benchmark.py [--count N]
锚定: DCD-NS-RUNTIME-001（A-4 <10ms 热路径）+ TDCA-NS-RUNTIME-001 §五
SPDX-License-Identifier: TDCA-Internal
"""
import statistics
import sys

from ns_runtime import Layer1Runtime, Layer1Verdict

SAMPLES = [
    dict(operation="data.aggregate", api="data.api", signature="anonymized",
         behavior_domain="transaction", rule_id="BENCH-OK"),
    dict(operation="collab.task_assign", api="collab.api", signature="signed",
         behavior_domain="collaboration", rule_id="BENCH-OK2"),
    dict(operation="cross_border.report", api="cb.api", signature="perm",
         behavior_domain="cross_border", rule_id="BENCH-OK3"),
]


def main(count: int = 300) -> None:
    rt = Layer1Runtime()
    times = []
    for i in range(count):
        kw = SAMPLES[i % len(SAMPLES)]
        res = rt.preflight(**kw)
        if res.verdict != Layer1Verdict.PASS:
            raise SystemExit(f"预检失败: {kw} -> {res.reason}")
        times.append(res.duration_ms)

    times.sort()
    p50 = times[int(len(times) * 0.50)]
    p95 = times[int(len(times) * 0.95)]
    avg = statistics.mean(times)
    mx = max(times)

    ok = avg < 10 and p95 < 10
    print("=" * 52)
    print("Runtime M1 Layer 1 性能基准（A-4 热路径）")
    print("=" * 52)
    print(f"样本数      : {len(times)}")
    print(f"avg         : {avg:.3f} ms  (目标 <10ms)")
    print(f"P50         : {p50:.3f} ms")
    print(f"P95         : {p95:.3f} ms  (目标 <10ms)")
    print(f"max         : {mx:.3f} ms")
    print(f"通过 A-4    : {'PASS' if ok else 'FAIL'}")
    print("=" * 52)
    return 0 if ok else 1


if __name__ == "__main__":
    count = 300
    if len(sys.argv) > 1 and sys.argv[1].startswith("--count="):
        count = int(sys.argv[1].split("=")[1])
    raise SystemExit(main(count))
