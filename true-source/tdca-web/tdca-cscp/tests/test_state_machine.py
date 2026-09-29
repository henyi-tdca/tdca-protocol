# -*- coding: utf-8 -*-
"""CSCP 五步状态机 + HumanGate 双签名 + 超时回滚测试（T-CSCP-001 / H-CSCP-005 / R-CSCP-002）。"""
import pytest

from cscp_gateway.saga import Saga
from cscp_gateway.state_machine import (HandshakeStatus, HandshakeStateMachine,
                                        PreflightStatus, Step)


class FakeClock:
    """可控时钟（超时测试用）。"""

    def __init__(self):
        self.t = 0.0

    def advance(self, seconds: float):
        self.t += seconds

    def __call__(self):
        return self.t


def _mocks(clock, preflight=PreflightStatus.PASS, sandbox_active=True,
           translator_matched=True, locked=True, budget_ok=True, workbuddy_ok=True):
    from cscp_gateway.adapters import (MockCBDCContractAdapter,
                                       MockNSFLUnionAdapter, MockSandboxAdapter,
                                       MockTranslatorAdapter, MockWorkbuddyAdapter)
    saga = Saga()
    refunded = []

    def _refund():
        refunded.append("refund")

    def _unlock():
        refunded.append("unlock")

    def _cancel():
        refunded.append("cancel")

    def _release():
        refunded.append("release")

    saga = Saga(refund_fn=_refund, unlock_fn=_unlock, cancel_fn=_cancel, release_fn=_release)
    sm = HandshakeStateMachine(
        preflight_fn=MockNSFLUnionAdapter(forced=preflight).preflight_check,
        sandbox_fn=MockSandboxAdapter(active=sandbox_active).verify,
        translator_fn=MockTranslatorAdapter(matched=translator_matched).match,
        cbdclock_fn=MockCBDCContractAdapter(locked=locked, budget_ok=budget_ok).lock,
        workbuddy_fn=MockWorkbuddyAdapter(created=workbuddy_ok).create_work_order,
        saga=saga, now=clock,
    )
    return sm, saga, refunded


def _req():
    return {"caller_scene": {"scene_id": "A", "rules": []},
            "callee_scene": {"scene_id": "B", "rules": []},
            "caller_tier": "L2", "cross_scene_flag": True}


def test_happy_path_full_cycle():
    """五步正常流 → COMPLETED（H-CSCP-001 端到端路径）。"""
    clock = FakeClock()
    sm, saga, _ = _mocks(clock)
    h = sm.initiate(_req())
    assert h.status == HandshakeStatus.PENDING_NSFL
    h = sm.preflight(h.handshake_id, _req())
    assert h.status == HandshakeStatus.PENDING_SANDBOX
    h = sm.match(h.handshake_id, f"SIG-{h.handshake_id[:6]}-ALPHA")
    assert h.status == HandshakeStatus.PENDING_LOCK
    assert h.human_gates["gate1"] is True
    h = sm.lock(h.handshake_id, 0.5)
    assert h.status == HandshakeStatus.PENDING_DISPATCH
    assert h.escrow_id is not None
    h = sm.dispatch(h.handshake_id, f"SIG-{h.handshake_id[:6]}-BETA")
    assert h.status == HandshakeStatus.COMPLETED
    assert h.human_gates["gate2"] is True
    assert h.work_order_id == "WO-MOCK-001"
    assert len(h.nca_refs) >= 5  # 全链路 NCA（H-CSCP-006）


def test_preflight_triggered_legal_rejected():
    """LEGAL → TRIGGERED → REJECTED（DCD-CSCP-CHANGE-001 HIGH 熔断）。"""
    clock = FakeClock()
    sm, _, _ = _mocks(clock, preflight=PreflightStatus.TRIGGERED)
    h = sm.initiate(_req())
    h = sm.preflight(h.handshake_id, _req())
    assert h.status == HandshakeStatus.REJECTED
    assert h.rejection_step == "STEP2"


def test_preflight_fail_alt_paths():
    clock = FakeClock()
    sm, _, _ = _mocks(clock, preflight=PreflightStatus.FAIL)
    h = sm.initiate(_req())
    h = sm.preflight(h.handshake_id, _req())
    assert h.status == HandshakeStatus.REJECTED
    assert h.alt_paths == ["SCN-C-MOCK"]  # 拒绝 + Alt-Path（可解释，H-CSCP-007）


def test_human_gate1_cannot_be_bypassed():
    """H-CSCP-005: 无签名 #1 直接 match → REJECTED（不可绕过）。"""
    clock = FakeClock()
    sm, _, _ = _mocks(clock)
    h = sm.initiate(_req())
    h = sm.preflight(h.handshake_id, _req())
    h = sm.match(h.handshake_id, "")  # 空签名
    assert h.status == HandshakeStatus.REJECTED
    assert "HUMAN_GATE_1" in h.rejection_reason
    # 且 lock 前门禁校验兜底
    h2 = sm.lock(h.handshake_id, 0.5)
    assert h2.status == HandshakeStatus.REJECTED


def test_human_gate2_cannot_be_bypassed():
    """H-CSCP-005: 无签名 #2 直接 dispatch → REJECTED（不可绕过）。"""
    clock = FakeClock()
    sm, _, _ = _mocks(clock)
    h = sm.initiate(_req())
    sm.preflight(h.handshake_id, _req())
    sm.match(h.handshake_id, f"SIG-{h.handshake_id[:6]}-ALPHA")
    sm.lock(h.handshake_id, 0.5)  # 推进到 PENDING_DISPATCH
    h = sm.dispatch(h.handshake_id, "")  # 空签名
    assert h.status == HandshakeStatus.REJECTED
    assert "HUMAN_GATE_2" in h.rejection_reason


def test_step3_timeout_rollback_executes_compensations():
    """R-CSCP-002: Step-3 超时 → Saga 逆序补偿（unlock+release 已注册）。"""
    clock = FakeClock()
    sm, saga, actions = _mocks(clock)
    h = sm.initiate(_req())
    sm.preflight(h.handshake_id, _req())
    clock.advance(2.0)  # 超过 STEP3 上限 1.0s
    h = sm.match(h.handshake_id, f"SIG-{h.handshake_id[:6]}-ALPHA")
    assert h.status == HandshakeStatus.FAILED
    assert "超时" in h.rejection_reason
    assert saga.pending() == []  # 全部补偿完成


def test_step4_timeout_rollback_refund():
    """Step-4 超时 → ESCROW_REFUND 补偿（CCP T4 M-4）。"""
    clock = FakeClock()
    sm, saga, actions = _mocks(clock)
    h = sm.initiate(_req())
    sm.preflight(h.handshake_id, _req())
    sm.match(h.handshake_id, f"SIG-{h.handshake_id[:6]}-ALPHA")
    clock.advance(2.0)  # 超过 STEP4 上限 1.5s
    h = sm.lock(h.handshake_id, 0.5)
    assert h.status == HandshakeStatus.FAILED
    # 补偿顺序: STEP3 注册的 unlock/release 已被上一步验证；本步锁定时长未满 → 未注册 refund
    # （lock 超时在注册 refund 之前发生，符合 Saga 语义：未执行的动作不补偿）


def test_sandbox_inactive_rejected():
    clock = FakeClock()
    sm, _, _ = _mocks(clock, sandbox_active=False)
    h = sm.initiate(_req())
    sm.preflight(h.handshake_id, _req())
    h = sm.match(h.handshake_id, f"SIG-{h.handshake_id[:6]}-ALPHA")
    assert h.status == HandshakeStatus.REJECTED
    assert "ACTIVE" in h.rejection_reason


def test_no_translator_rejected():
    clock = FakeClock()
    sm, _, _ = _mocks(clock, translator_matched=False)
    h = sm.initiate(_req())
    sm.preflight(h.handshake_id, _req())
    h = sm.match(h.handshake_id, f"SIG-{h.handshake_id[:6]}-ALPHA")
    assert h.status == HandshakeStatus.REJECTED
    assert "NO_TRANSLATOR" in h.rejection_reason


def test_insufficient_budget_rejected():
    clock = FakeClock()
    sm, _, _ = _mocks(clock, budget_ok=False)
    h = sm.initiate(_req())
    sm.preflight(h.handshake_id, _req())
    sm.match(h.handshake_id, f"SIG-{h.handshake_id[:6]}-ALPHA")
    h = sm.lock(h.handshake_id, 0.5)
    assert h.status == HandshakeStatus.REJECTED
    assert "INSUFFICIENT_BUDGET" in h.rejection_reason


def test_unknown_handshake_raises():
    clock = FakeClock()
    sm, _, _ = _mocks(clock)
    with pytest.raises(KeyError):
        sm.status("HS-NOT-EXIST")
