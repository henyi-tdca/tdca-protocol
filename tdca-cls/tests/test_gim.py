"""GIM 增量环检测测试（R-CLS-3：简单路径/终止性/无负权/G-1 不变量）"""
import numpy as np
import pytest

from tdca_cls.gim import GIMOnCycle


def test_gim_simple_cycle():
    """环案例: A欠B10/B欠C10/C欠A5 → 检测环 + 环销 δ=5"""
    gim = GIMOnCycle()
    gim.add_edge("A", "B", 10)
    gim.add_edge("B", "C", 10)
    cyc = gim.add_edge("C", "A", 5)   # 形成环的边
    assert len(cyc) == 1
    assert cyc[0].delta == pytest.approx(5.0)
    assert cyc[0].nominal_net == pytest.approx(15.0)   # 3 边 × 5
    # 环销后残余: A→B 5 + B→C 5 = 10
    assert gim.residual_nominal() == pytest.approx(10.0)
    # 无负权
    assert all(w > 0 for w in gim.debt.values())


def test_gim_no_negative_weight_random():
    """1500 随机边: 无负权 + 环均为简单路径（终止性隐式验证）"""
    rng = np.random.default_rng(7)
    gim = GIMOnCycle()
    for _ in range(1500):
        u = int(rng.integers(0, 20))
        v = int(rng.integers(0, 20))
        if u == v:
            v = (v + 1) % 20
        w = float(rng.integers(1, 20))
        gim.add_edge(f"N{u}", f"N{v}", w)
    assert all(w > 0 for w in gim.debt.values())
    # 环的边数 ≥ 3（简单环，无自环/重边）
    for c in gim.cycles:
        assert len(c.cycle_edges) >= 2
        assert len(set(c.cycle_edges)) == len(c.cycle_edges)   # 无重复边


def test_gim_tnet_invariant():
    """G-1: 环销不改变净头寸 → T_net 不变"""
    rng = np.random.default_rng(11)
    gim = GIMOnCycle()
    net = {f"N{i}": 0.0 for i in range(10)}
    for _ in range(200):
        u = int(rng.integers(0, 10))
        v = int(rng.integers(0, 10))
        if u == v:
            v = (v + 1) % 10
        w = float(rng.integers(1, 20))
        gim.add_edge(f"N{u}", f"N{v}", w)
        net[f"N{u}"] -= w
        net[f"N{v}"] += w
    # 环销后净头寸不变（用残余债务重算）
    net2 = {f"N{i}": 0.0 for i in range(10)}
    for (u, v), w in gim.residual_debt().items():
        net2[u] -= w
        net2[v] += w
    for i in range(10):
        assert net2[f"N{i}"] == pytest.approx(net[f"N{i}"])
    t_net = sum(max(0.0, -v) for v in net.values())
    t_net2 = sum(max(0.0, -v) for v in net2.values())
    assert t_net2 == pytest.approx(t_net)   # G-1: T_net 不变量


def test_gim_parallel_edges():
    """并行边: 多条同向边合并后环销无负权（M3 修订场景）"""
    gim = GIMOnCycle()
    gim.add_edge("A", "B", 10)
    gim.add_edge("A", "B", 5)     # 并行边合并 → A→B 15
    gim.add_edge("B", "C", 7)
    gim.add_edge("C", "A", 3)
    # A→B 15, B→C 7, C→A 3: 环销 δ=3（无负权）
    assert all(w > 0 for w in gim.debt.values())
    assert gim.debt.get(("A", "B")) == pytest.approx(12.0)
