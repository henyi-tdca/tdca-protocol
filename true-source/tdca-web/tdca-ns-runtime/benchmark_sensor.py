# -*- coding: utf-8 -*-
"""
TDCA-NS-RUNTIME-001 · M2 L2-R5 Sensor 性能基准（A-4）
=====================================================
度量: NS-Boundary Sensor 单次 Δ 分析时延
目标: avg <50ms / P95 <50ms（M2 预设，DCD-NSFL-M2-001）

用法: python benchmark_sensor.py [--count N]
锚定: DCD-NSFL-M2-001（Runtime M2 A-4）+ NSFL-M2-ICD-001 §3.1
SPDX-License-Identifier: TDCA-Internal
"""
import statistics
import sys
import time

from ns_runtime import NSBoundarySensor

SAMPLES = [
    {"type": "CODE_MODIFICATION", "delta_c": "refactor logging module", "subject": "S_agent_cog-001"},
    {"type": "CODE_MODIFICATION", "delta_c": "optimize inference path", "subject": "S_agent_cog-002"},
    {"type": "WEIGHT_MODIFICATION", "delta_w": [0.01, -0.02], "labels": ["planning"], "subject": "S_agent_cog-001"},
]


def main(count: int = 300) -> None:
    sensor = NSBoundarySensor()
    times = []
    for i in range(count):
        delta = SAMPLES[i % len(SAMPLES)]
        state = {"S_agent_cog": {"id": delta.get("subject", "S_agent_cog"), "A": 0.8}}
        t0 = time.perf_counter()
        res = sensor.analyze(state, delta)
        dt = (time.perf_counter() - t0) * 1000
        assert res.verdict in ("SAFE", "WARNING", "BLOCKED", "CRYOGENIC")
        times.append(dt)

    times.sort()
    p50 = times[int(len(times) * 0.50)]
    p95 = times[int(len(times) * 0.95)]
    avg = statistics.mean(times)
    mx = max(times)

    ok = avg < 50 and p95 < 50
    print("=" * 52)
    print("L2-R5 NS-Boundary Sensor 性能基准（A-4）")
    print("=" * 52)
    print(f"样本数      : {len(times)}")
    print(f"avg         : {avg:.3f} ms  (目标 <50ms)")
    print(f"P50         : {p50:.3f} ms")
    print(f"P95         : {p95:.3f} ms  (目标 <50ms)")
    print(f"max         : {mx:.3f} ms")
    print(f"通过 A-4    : {'PASS' if ok else 'FAIL'}")
    print("=" * 52)
    return 0 if ok else 1


if __name__ == "__main__":
    count = 300
    if len(sys.argv) > 1 and sys.argv[1].startswith("--count="):
        count = int(sys.argv[1].split("=")[1])
    raise SystemExit(main(count))
