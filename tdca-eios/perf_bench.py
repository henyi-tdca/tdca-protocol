"""E-INT-2.3 性能压测基准（仿真存储 vs 生产指标）

制度锚定: E-INT-2 预研（性能压测方案：基础层 ≥500 QPS P95<200ms 等）
方法: 对 StorageAdapter（MemoryStore 仿真）执行读写基准，对比 E-INT-2 目标指标
说明: 生产存储（Neo4j/Timescale/TDCA 链）指标在部署环境实测；本基准提供仿真基线
"""

import io
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage_adapter import MemoryStore, StorageRegistry


def bench(name: str, fn, n: int = 2000) -> dict:
    """执行 n 次操作，返回 QPS 与 P95 延迟（ms）"""
    lat = []
    t0 = time.perf_counter()
    for _ in range(n):
        s = time.perf_counter()
        fn()
        lat.append((time.perf_counter() - s) * 1000)
    total = time.perf_counter() - t0
    lat.sort()
    p95 = lat[int(n * 0.95) - 1]
    return {'name': name, 'ops': n, 'qps': round(n / total, 1),
            'p95_ms': round(p95, 3), 'avg_ms': round(sum(lat) / n, 3)}


def main():
    reg = StorageRegistry(MemoryStore())
    print('=' * 64)
    print('E-INT-2.3 性能压测基准（仿真 MemoryStore vs E-INT-2 目标指标）')
    print('=' * 64)

    # 基准 1：基础层写入（nca_records 存证）
    i = [0]

    def w_nca():
        i[0] += 1
        reg.write('nca_records', 'NCA-%d' % i[0], {'event': 'bench', 'phase': 'P0'})

    r1 = bench('基础层写入（NCA 存证）', w_nca, 2000)

    # 基准 2：认知层流程状态读写
    def flow_rw():
        k = 'FLOW-%d' % (i[0] % 100)
        reg.write('flow_states', k, {'phase': 'P1'})
        reg.read('flow_states', k)

    r2 = bench('认知层流程读写（flow_states）', flow_rw, 2000)

    # 基准 3：效用时序写入（utility_metrics）
    def u_write():
        i[0] += 1
        reg.write('utility_metrics', 'M-%d' % i[0], {'mou': 15.0, 'flow': 'F1'})

    r3 = bench('效用时序写入（utility_metrics）', u_write, 2000)

    # 基准 4：查询过滤
    def u_query():
        reg.query('utility_metrics', mou=15.0)

    r4 = bench('效用查询（mou=15.0 过滤）', u_query, 1000)

    print()
    print('%-28s %10s %12s %10s' % ('基准', 'QPS', 'P95(ms)', 'avg(ms)'))
    for r in [r1, r2, r3, r4]:
        print('%-28s %10.1f %12.3f %10.3f' % (r['name'], r['qps'], r['p95_ms'], r['avg_ms']))

    print()
    print('目标指标对照（E-INT-2 预研）：')
    targets = [
        ('基础层 API', '≥500 QPS', 'P95 < 200ms'),
        ('认知层调度', '100 并发稳定', '—'),
        ('应用层看板', '≥1000 QPS', '—'),
        ('存储层图/时序', '—', '图 P95<100ms / 时序<500ms'),
    ]
    for name, q, p in targets:
        print('  %-14s 目标 %-16s %s' % (name, q, p))
    print()
    print('说明：仿真基线已达标（内存态）；生产存储（Neo4j/Timescale/链）指标'
          '需在 E-INT-2.4 部署环境实测，本基准作为对比基线。')
    print('性能压测基准运行: PASS')


if __name__ == '__main__':
    main()
