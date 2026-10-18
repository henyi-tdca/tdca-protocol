"""E-3 端到端联调测试：多边随机场景 + 五不变量全断言 + 异常分支"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "tdca-microtax"))

import numpy as np
import pytest

from tdca_cls.engine import CLSEngine
from tdca_cls.dpi import State
from tdca_cls.rtn import RTNNetting


def test_e2e_ring_case_full():
    """环案例全链路（DRAFTING→RECONCILED + 税收 + NCA + 五不变量）"""
    eng = CLSEngine()
    edges = [("A", "B", 10.0), ("B", "C", 10.0), ("C", "A", 5.0)]
    eng.add_debt_edges(edges)
    outcomes = eng.run_settlement()
    # 结算 1 笔（净额 5：A→C 或 A→B→C 路径）
    assert len(outcomes) == 1
    assert outcomes[0].state == State.RECONCILED
    assert outcomes[0].dpi.amount == pytest.approx(5.0)
    assert outcomes[0].tax > 0                       # 同刻计税
    assert outcomes[0].nca_id.startswith("NCA-CLS-")
    # 五不变量全真
    inv = eng.invariants()
    for k, v in inv.items():
        assert v, f"不变量 {k} 违例"


def test_e2e_random_multilateral():
    """多边随机场景（n=8，100 边）: 全链路 + 五不变量 + T_net 恒等"""
    rng = np.random.default_rng(5)
    for trial in range(30):
        eng = CLSEngine()
        n = 8
        edges = []
        for _ in range(100):
            u = int(rng.integers(0, n))
            v = int(rng.integers(0, n))
            if u == v:
                v = (v + 1) % n
            edges.append((f"N{u}", f"N{v}", float(rng.integers(1, 30))))
        eng.add_debt_edges(edges)
        # T_net 恒等（环销前后）
        t_net_full = eng.rtn.net([f"N{i}" for i in range(n)], dict(eng.network.debt)).t_net
        outcomes = eng.run_settlement()
        inv = eng.invariants(t_net_before=t_net_full)
        for k, v in inv.items():
            assert v, f"trial {trial}: 不变量 {k} 违例"
        # 至少 1 笔结算（稠密网络必有净额）
        assert any(o.state == State.RECONCILED for o in outcomes)


def test_e2e_exception_branch():
    """异常分支: MOU≤0 → HELD（I-5 快慢隔离——其他环结算不中断）"""
    eng = CLSEngine()
    # 双环: A 环（A 的 MOU=0 → HELD）+ D 环（正常 → RECONCILED）
    edges = [("A", "B", 10.0), ("B", "C", 10.0), ("C", "A", 5.0),
             ("D", "E", 8.0), ("E", "F", 8.0), ("F", "D", 3.0)]
    eng.add_debt_edges(edges)
    outcomes = eng.run_settlement(mou_map={"A": 0.0})
    states = [o.state for o in outcomes]
    assert State.HELD in states          # A 环净额 HELD（MOU≤0 熔断）
    assert State.RECONCILED in states    # D 环正常结算（I-5: 异常不中断常规）
    inv = eng.invariants()
    assert inv["I-5"] is True            # 快慢隔离成立


def test_e2e_multi_settlements():
    """多净额主体: 多笔 DPI 结算（I-1 定向性/I-2 流动性）"""
    eng = CLSEngine()
    # 两个独立环: A↔B↔C + D↔E↔F
    edges = [("A", "B", 10.0), ("B", "C", 10.0), ("C", "A", 5.0),
             ("D", "E", 8.0), ("E", "F", 8.0), ("F", "D", 3.0)]
    eng.add_debt_edges(edges)
    outcomes = eng.run_settlement()
    # 两环各 1 笔净额（A 5 + D 5）
    total_dpi = sum(o.dpi.amount for o in outcomes)
    assert total_dpi == pytest.approx(10.0)          # 5 + 5
    inv = eng.invariants()
    for k, v in inv.items():
        assert v


def test_e2e_qualification_revoked():
    """T-037 资格: REVOKED 主体不能产生新债务（R-CLS-1 待批判点 5 落实）"""
    eng = CLSEngine()
    eng.network.add_node("X")
    eng.network.qualification["X"] = __import__("tdca_cls.models", fromlist=["Qualification"]).Qualification.REVOKED
    with pytest.raises(AssertionError):
        eng.add_debt_edges([("X", "A", 10.0)])      # REVOKED 禁新债务
