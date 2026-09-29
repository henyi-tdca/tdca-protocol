# -*- coding: utf-8 -*-
"""
TDCA-NS-RUNTIME-001 · M3 三轨性能基准（A-4）
============================================
度量: L2-R6 NS-Atlas 查询 / L2-R7 合约 precheck / L2-R8 NIA-MACM process
目标: avg <50ms / P95 <50ms（M3 沿用 M2 标准，DCD-NSFL-M3-001）

用法: python benchmark_m3.py [--count N]
锚定: DCD-NSFL-M3-001（A-4 <50ms）+ NSFL-M3-ICD-001
SPDX-License-Identifier: TDCA-Internal
"""
import statistics
import sys
import time

from ns_runtime import NSAtlas, NSFLContractAnchor, NIAMACMIntegrator


def bench_atlas(count: int) -> list:
    atlas = NSAtlas()
    atlas.register_source("SEA-ADMISSION-001", admin_signature="HUMAN-FOUNDER-001")
    for d in (0.9, 0.85, 0.8):
        atlas.ingest_point("BENCH-S", d, source_signature="SEA-ADMISSION-001")
    times = []
    for _ in range(count):
        t0 = time.perf_counter()
        atlas.query("BENCH-S")
        times.append((time.perf_counter() - t0) * 1000)
    return times


def bench_contract(count: int) -> list:
    c = NSFLContractAnchor()
    c.register_escrow("ESCROW-B", 200000.0, admin_signature="HUMAN-FOUNDER-001")
    c.register_audit_integrity("BENCH-S", 0.98, admin_signature="HUMAN-FOUNDER-001")
    times = []
    for _ in range(count):
        t0 = time.perf_counter()
        c.precheck("TRANSACTION", subject="BENCH-S", escrow_ref="ESCROW-B")
        times.append((time.perf_counter() - t0) * 1000)
    return times


def bench_nia(count: int) -> list:
    nia = NIAMACMIntegrator()
    times = []
    for _ in range(count):
        t0 = time.perf_counter()
        nia.process({"S_agent_cog": {"id": "BENCH-S"}},
                    {"type": "CODE_MODIFICATION", "delta_c": "refactor logging"})
        times.append((time.perf_counter() - t0) * 1000)
    return times


def report(name: str, times: list) -> bool:
    times.sort()
    avg = statistics.mean(times)
    p95 = times[int(len(times) * 0.95)]
    mx = max(times)
    ok = avg < 50 and p95 < 50
    print(f"{name:28s} avg {avg:8.3f} ms | P95 {p95:8.3f} ms | max {mx:8.3f} ms | {'PASS' if ok else 'FAIL'}")
    return ok


def main(count: int = 300) -> None:
    print("=" * 72)
    print("NSFL M3 三轨性能基准（A-4 <50ms，DCD-NSFL-M3-001）")
    print("=" * 72)
    ok = True
    ok &= report("L2-R6 NS-Atlas query", bench_atlas(count))
    ok &= report("L2-R7 contract precheck", bench_contract(count))
    ok &= report("L2-R8 NIA-MACM process", bench_nia(count))
    print("=" * 72)
    print(f"总判定: {'ALL PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    count = 300
    if len(sys.argv) > 1 and sys.argv[1].startswith("--count="):
        count = int(sys.argv[1].split("=")[1])
    raise SystemExit(main(count))
