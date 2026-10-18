"""CLS 状态机 + DPI 测试（R-CLS-1：状态转移/DISPUTED 可达/五不变量）"""
import numpy as np
import pytest

from tdca_cls.dpi import CLSStateMachine, DPI, State
from tdca_cls.dvp import DVPExecutor


def test_state_machine_normal_path():
    """常规路径: DRAFTING→MATCHED→NETTED→SETTLED→RECONCILED"""
    sm = CLSStateMachine()
    sm.new_transaction("T1")
    assert sm.state_of("T1") == State.DRAFTING
    sm.transition("T1", {"cycle": True})
    assert sm.state_of("T1") == State.MATCHED
    sm.transition("T1", {"netted": True})
    assert sm.state_of("T1") == State.NETTED
    sm.transition("T1", {"settle": True})
    assert sm.state_of("T1") == State.SETTLED
    sm.transition("T1", {"reconciled": True})
    assert sm.state_of("T1") == State.RECONCILED


def test_disputed_reachable():
    """M3 修订: HELD/ESCALATED → DISPUTED（争议提起）可达"""
    sm = CLSStateMachine()
    sm.new_transaction("T2")
    sm.transition("T2", {"cycle": True})       # → MATCHED
    sm.transition("T2", {"netted": True})      # → NETTED
    sm.transition("T2", {"held": True})        # → HELD
    assert sm.state_of("T2") == State.HELD
    sm.transition("T2", {"dispute": True})
    assert sm.state_of("T2") == State.DISPUTED
    sm.transition("T2", {"fault": True})
    assert sm.state_of("T2") == State.PENALIZED      # 过错方 → T-037
    # 另一争议: 非过错 → INSURED
    sm2 = CLSStateMachine()
    sm2.new_transaction("T3")
    sm2.transition("T3", {"cycle": True})
    sm2.transition("T3", {"netted": True})
    sm2.transition("T3", {"held": True})
    sm2.transition("T3", {"dispute": True})
    sm2.transition("T3", {"no_fault": True})
    assert sm2.state_of("T3") == State.INSURED


def test_dpi_conditions():
    """DPI 定向支付指令: 条件求值（C_MOU∧C_delivery∧C_dpi）"""
    dpi = DPI(payer="A", payee="C", amount=5.0,
              conditions={"C_MOU": True, "C_delivery": True, "C_dpi": True})
    assert dpi.check()
    dpi_bad = DPI(payer="A", payee="C", amount=5.0,
                  conditions={"C_MOU": False, "C_delivery": True, "C_dpi": True})
    assert not dpi_bad.check()


def test_dvp_conditional_pay():
    """DVP 条件支付: 全真→SETTLED（同刻计税）；MOU≤0→HELD"""
    dvp = DVPExecutor()
    dpi = DPI(payer="A", payee="C", amount=5.0,
              conditions={"C_MOU": True, "C_delivery": True, "C_dpi": True})
    r = dvp.conditional_pay("T1", dpi, {"mou": 3.0, "delivery": True, "tax_rate": 0.02})
    assert r.state == State.SETTLED
    assert r.tax == pytest.approx(0.1)    # 5 × 2% 同刻计税
    # MOU ≤ 0 → HELD（L1 硬约束）
    r2 = dvp.conditional_pay("T2", dpi, {"mou": 0.0, "delivery": True})
    assert r2.state == State.HELD
    assert "C_MOU" in r2.message


def test_invariants():
    """五不变量抽查: I-1 定向性 + I-4 可审计"""
    sm = CLSStateMachine()
    sm.new_transaction("T1")
    for cond in [{"cycle": True}, {"netted": True}, {"settle": True}, {"reconciled": True}]:
        sm.transition("T1", cond)
    dpi = DPI(payer="A", payee="C", amount=5.0,
              conditions={"C_MOU": True, "C_delivery": True, "C_dpi": True})
    sm.dpis.append(dpi)
    assert sm.invariant_directionality()          # I-1
    assert sm.invariant_auditability()            # I-4
    assert len(sm.nca_log) >= 5                    # 每步存证


def test_random_state_machine_no_violation():
    """100 随机交易: 状态机无非法转移（终态覆盖 + 五不变量违例 0）"""
    rng = np.random.default_rng(3)
    for _ in range(100):
        sm = CLSStateMachine()
        sm.new_transaction("T")
        # 随机条件序列（合法顺序）
        seq = [{"cycle": True}]
        if rng.random() < 0.9:
            seq.append({"netted": True})
        if rng.random() < 0.9:
            seq.append({"settle": True} if rng.random() < 0.9 else {"held": True})
        for c in seq:
            sm.transition("T", c)
        s = sm.state_of("T")
        assert s in (State.DRAFTING, State.MATCHED, State.NETTED, State.SETTLED,
                     State.RECONCILED, State.HELD)   # 终态覆盖
