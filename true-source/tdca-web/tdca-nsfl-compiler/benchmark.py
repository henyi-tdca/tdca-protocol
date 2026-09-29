# -*- coding: utf-8 -*-
"""
TDCA-NSFL-COMPILER-001 · M1 编译性能基准（A-2）
==============================================
度量: 单条 NSFL 声明编译时延（发布期一次性编译，非运行热路径）
目标: avg <100ms / P95 <200ms

用法: python benchmark.py [--count N]
锚定: DCD-NSFL-COMPILER-001（A-2）+ TDCA-NSFL-COMPILER-001 §五
SPDX-License-Identifier: TDCA-Internal
"""
import statistics
import time

from nsfl_compiler import NSFLCompiler

SAMPLES = [
    "NSFL: ⊗ LEGAL.data.leak(third_party) — 绝对禁止泄露第三方隐私数据",
    "NSFL: ⊗ ETHICAL.contribution.forge — 禁止伪造协作贡献记录",
    "NSFL: ⊘ TRANSACTION_LIMIT.transfer | max:100000 @L2 — 单笔转账上限 10 万",
    "NSFL: ⊙ DATA_CROSS_BORDER.export | cn:teardown — 跨境数据导出需场景化熔断",
    "NSFL: ⊗ SENSITIVE_CONTENT.scene.meaning_erode — 禁止削弱场景意义",
    "NSFL: ⊘ TECH_CONSTRAINT.rate_limit | eq:60 — 调用频率定值 60/s",
    "NSFL: ⊗ BELIEF.identity_impersonate — 禁止冒用身份",
]


def main(count: int = 200) -> None:
    compiler = NSFLCompiler()
    times = []
    for i in range(count):
        src = SAMPLES[i % len(SAMPLES)]
        t0 = time.perf_counter()
        result = compiler.compile(src)
        dt = (time.perf_counter() - t0) * 1000
        if not result.ok:
            raise SystemExit(f"编译失败: {src} -> {result.errors}")
        times.append(dt)

    times.sort()
    p50 = times[int(len(times) * 0.50)]
    p95 = times[int(len(times) * 0.95)]
    avg = statistics.mean(times)
    mx = max(times)

    ok = avg < 100 and p95 < 200
    print("=" * 52)
    print("NSFL 编译器 M1 性能基准（A-2）")
    print("=" * 52)
    print(f"样本数      : {len(times)}")
    print(f"avg         : {avg:.3f} ms  (目标 <100ms)")
    print(f"P50         : {p50:.3f} ms")
    print(f"P95         : {p95:.3f} ms  (目标 <200ms)")
    print(f"max         : {mx:.3f} ms")
    print(f"通过 A-2    : {'PASS' if ok else 'FAIL'}")
    print("=" * 52)
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    count = 200
    if len(sys.argv) > 1 and sys.argv[1].startswith("--count="):
        count = int(sys.argv[1].split("=")[1])
    raise SystemExit(main(count))
