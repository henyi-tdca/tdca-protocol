# -*- coding: utf-8 -*-
"""D-2 并集引擎性能基准（A-2）: 1000 对随机场景组合，平均 <100ms（P95 <150ms）。

用法: python benchmark.py
输出: JSON 基准报告（交付物之一）
"""
import json
import random
import statistics
import time
from decimal import Decimal

from nsfl_union import (NS_Operator, NS_Rule, NS_Type, NSFLUnionEngine,
                        SceneNSFL, Severity)

random.seed(20260810)

_NUM_PAIRS = 1000

_NS_TYPES = [NS_Type.TRANSACTION_LIMIT, NS_Type.DATA_CROSS_BORDER,
             NS_Type.SENSITIVE_CONTENT, NS_Type.TECH_CONSTRAINT,
             NS_Type.ETHICAL, NS_Type.EMOTIONAL, NS_Type.BELIEF]


def random_scene(sid: str, n_rules: int = 3) -> SceneNSFL:
    rules = []
    for i in range(n_rules):
        ns = random.choice(_NS_TYPES)
        op = random.choice([NS_Operator.ALLOW, NS_Operator.FORBID,
                            NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN])
        kw = {}
        if op in (NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN):
            kw = {"parameter": Decimal(random.randint(1, 10**7)), "unit": "CNY"}
        rules.append(NS_Rule(f"{sid}-R{i}", ns, op, **kw))
    return SceneNSFL(scene_id=sid, rules=rules)


def main() -> None:
    scenes = [random_scene(f"S{i}") for i in range(100)]
    eng = NSFLUnionEngine()

    latencies = []
    for i in range(_NUM_PAIRS):
        a = scenes[random.randrange(len(scenes))]
        b = scenes[random.randrange(len(scenes))]
        t0 = time.perf_counter()
        eng.compute(a, b, compute_alt_path=False)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    latencies.sort()
    avg = statistics.mean(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    report = {
        "benchmark": "D2-NSFL-UNION-BENCH-001",
        "schema_version": "D2-NSFL-UNION-SCHEMA-001-V0.1-REV2-FINAL",
        "pairs": _NUM_PAIRS,
        "avg_ms": round(avg, 3),
        "p95_ms": round(p95, 3),
        "p99_ms": round(p99, 3),
        "max_ms": round(latencies[-1], 3),
        "pass": avg < 100.0 and p95 < 150.0,
        "hard_target": "avg<100ms / P95<150ms (A-2)",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert report["pass"], f"FAIL: avg={avg:.2f}ms p95={p95:.2f}ms"


if __name__ == "__main__":
    main()
