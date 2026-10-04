"""CLS 端到端测试：环案例全链路（R-CLS-5 E-3 前置）"""
import pytest

from tdca_cls.gim import GIMOnCycle
from tdca_cls.rtn import RTNNetting
from tdca_cls.dpi import CLSStateMachine, DPI, State
from tdca_cls.dvp import DVPExecutor


def test_ring_case_end_to_end():
    """环案例（A欠B10/B欠C10/C欠A5）: DRAFTING→...→RECONCILED 全链路"""
    gim = GIMOnCycle()
    # ① 债务到达（DRAFTING）
    gim.add_edge("A", "B", 10)
    gim.add_edge("B", "C", 10)
    cycles = gim.add_edge("C", "A", 5)   # 环命中（MATCHED）
    assert len(cycles) == 1
    assert cycles[0].delta == pytest.approx(5.0)
    # ② RTN 净额（NETTED）
    rtn = RTNNetting()
    r = rtn.net(["A", "B", "C"], gim.residual_debt())
    assert r.t_net == pytest.approx(5.0)          # 最小流动性
    # ③ DPI 定向支付（SETTLED 条件）
    dpi = DPI(payer=r.payment_orders[0][0], payee=r.payment_orders[0][1],
              amount=r.payment_orders[0][2],
              conditions={"C_MOU": True, "C_delivery": True, "C_dpi": True},
              ref="NCA:RING-001")
    dvp = DVPExecutor()
    res = dvp.conditional_pay("RING-001", dpi, {"mou": 3.0, "delivery": True, "tax_rate": 0.02})
    assert res.state == State.SETTLED
    # ④ 状态机全链路
    sm = CLSStateMachine()
    sm.new_transaction("RING-001")
    for cond in [{"cycle": True}, {"netted": True}, {"settle": True}, {"reconciled": True}]:
        sm.transition("RING-001", cond)
    assert sm.state_of("RING-001") == State.RECONCILED
    # ⑤ 五不变量
    assert sm.invariant_directionality()
    assert sm.invariant_auditability()
    assert res.tax == pytest.approx(0.1)          # 5 × 2% 同刻计税


def test_ring_case_nominal_flow():
    """环案例名义流水: 环销 15 + 残余 10（G-4 语义）"""
    gim = GIMOnCycle()
    gim.add_edge("A", "B", 10)
    gim.add_edge("B", "C", 10)
    gim.add_edge("C", "A", 5)
    assert gim.residual_nominal() == pytest.approx(10.0)   # A→B5 + B→C5
    # 总名义 = 环销 15 + 残余 10 = 25 = T_full
    total = sum(c.nominal_net for c in gim.cycles) + gim.residual_nominal()
    assert total == pytest.approx(25.0)
