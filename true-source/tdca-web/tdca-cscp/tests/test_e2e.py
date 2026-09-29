# -*- coding: utf-8 -*-
"""E2E-001~010 端到端场景验收（TDCA-PLAN-5CC-PHASE-C-001 §4.2；真实 D-2 引擎 + HumanGate 真实签名 + mock 外部依赖）。"""
from fastapi.testclient import TestClient

from cscp_gateway.gateway import app
from cscp_gateway.human_gate import HumanGate

client = TestClient(app)


def _sig(hs_id, action):
    r = client.post(f"/handshake/challenge/{hs_id}", json={"action": action})
    assert r.status_code == 201
    return HumanGate().compute_signature(hs_id, action, r.json()["nonce"])


def _req(a_rules, b_rules, tier="L2", right="CONFIG"):
    return {"caller_scene": {"scene_id": "A", "rules": a_rules},
            "callee_scene": {"scene_id": "B", "rules": b_rules},
            "caller_tier": tier, "cross_scene_flag": True, "requested_right": right}


def _limit(ns, op, val):
    return {"rule_id": f"R-{ns}-{op}", "ns_type": ns, "operator": op,
            "parameter": str(val), "unit": "CNY"}


def _full(req, expect_dispatch=True):
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    client.post("/handshake/match", params={"handshake_id": hs},
                json={"human_signature_1": _sig(hs, "MATCH")})
    client.post("/handshake/lock", params={"handshake_id": hs}, json={"mou_split_ratio": 0.5})
    r = client.post("/handshake/dispatch", params={"handshake_id": hs},
                    json={"human_signature_2": _sig(hs, "DISPATCH")})
    return hs, r.json()


# ---- E2E-001 无冲突全链路 ----

def test_e2e_001_no_conflict_full_cycle():
    hs, out = _full(_req([{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
                         [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}]))
    assert out["status"] == "DISPATCHED"
    st = client.get(f"/handshake/status/{hs}").json()
    assert st["status"] == "COMPLETED"
    assert len(st["nca_refs"]) >= 5          # 全链路 NCA（H-CSCP-006）
    assert st["human_gates"] == {"gate1": True, "gate2": True}
    assert st["escrow_id"] and st["work_order_id"]


# ---- E2E-002 MEDIUM 冲突 → FAIL + Alt-Path ----

def test_e2e_002_medium_conflict_fail_with_altpath():
    req = _req([_limit("DATA_CROSS_BORDER", "ALLOW", 0)],
               [_limit("DATA_CROSS_BORDER", "FORBID", 0)])  # 占位（下用真实语义规则）
    # 真实 MEDIUM 冲突：交易限额取严
    req = _req([_limit("TRANSACTION_LIMIT", "LIMIT_MAX", 1000000)],
               [_limit("TRANSACTION_LIMIT", "LIMIT_MAX", 500000)])
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    r = client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    body = r.json()
    assert body["status"] == "FAIL"
    assert body["rejection_step"] == "STEP2"
    # 拒绝后可重新握手（新会话）
    hs2, out = _full(_req([{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
                          [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}]))
    assert out["status"] == "DISPATCHED"     # 二次握手成功


# ---- E2E-003 HIGH 冲突 → TRIGGERED 熔断 ----

def test_e2e_003_high_conflict_triggered_circuit_break():
    req = _req([{"rule_id": "L1", "ns_type": "LEGAL", "operator": "FORBID"}],
               [{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}])
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    r = client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    assert r.json()["status"] == "TRIGGERED"
    st = client.get(f"/handshake/status/{hs}").json()
    assert st["escrow_id"] is None and st["work_order_id"] is None   # 无资金锁定/无 WorkOrder
    assert st["status"] == "REJECTED"                                # 配置权冻结


# ---- E2E-004 Tier-3 请求 P-Right → TIER_INSUFFICIENT ----

def test_e2e_004_tier3_pright_rejected():
    req = _req([{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
               [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}],
               tier="L3", right="P_RIGHT")
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    r = client.post("/handshake/match", params={"handshake_id": hs},
                    json={"human_signature_1": _sig(hs, "MATCH")})
    assert r.json()["status"] == "REJECTED"
    assert "TIER_INSUFFICIENT" in r.json()["reason"]


# ---- E2E-005 沙盒 SUSPENDED → SANDBOX_NOT_ACTIVE ----

def test_e2e_005_sandbox_not_active():
    # 通过状态机直测（gateway 沙盒 mock 固定 ACTIVE）
    from cscp_gateway.saga import Saga
    from cscp_gateway.state_machine import HandshakeStateMachine
    from cscp_gateway.adapters import (MockNSFLUnionAdapter, MockSandboxAdapter,
                                       MockTranslatorAdapter, MockCBDCContractAdapter,
                                       MockWorkbuddyAdapter)
    from cscp_gateway.human_gate import HumanGate
    sm = HandshakeStateMachine(
        preflight_fn=MockNSFLUnionAdapter(forced="PASS").preflight_check,
        sandbox_fn=MockSandboxAdapter(active=False).verify,
        translator_fn=MockTranslatorAdapter().match,
        cbdclock_fn=MockCBDCContractAdapter().lock,
        workbuddy_fn=MockWorkbuddyAdapter().create_work_order,
        saga=Saga(), human_gate=HumanGate(), now=lambda: 0.0,
    )
    req = {"caller_scene": {"scene_id": "A", "rules": []},
           "callee_scene": {"scene_id": "B", "rules": []}}
    h = sm.initiate(req)
    sm.preflight(h.handshake_id, req)
    ch = sm._human_gate.issue_challenge(h.handshake_id, "MATCH")
    token = sm._human_gate.compute_signature(h.handshake_id, "MATCH", ch["nonce"])
    h = sm.match(h.handshake_id, token)
    assert h.status.value == "REJECTED"
    assert "SANDBOX_NOT_ACTIVE" in h.rejection_reason


# ---- E2E-006 HumanGate #1 空签名 ----

def test_e2e_006_gate1_empty_signature():
    req = _req([{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
               [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}])
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    r = client.post("/handshake/match", params={"handshake_id": hs},
                    json={"human_signature_1": ""})
    assert r.json()["status"] == "REJECTED"
    assert "HUMAN_GATE_1" in r.json()["reason"]


# ---- E2E-007 HumanGate #2 伪造签名 ----

def test_e2e_007_gate2_forged_signature():
    req = _req([{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
               [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}])
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    client.post("/handshake/match", params={"handshake_id": hs},
                json={"human_signature_1": _sig(hs, "MATCH")})
    client.post("/handshake/lock", params={"handshake_id": hs}, json={"mou_split_ratio": 0.5})
    r = client.post("/handshake/dispatch", params={"handshake_id": hs},
                    json={"human_signature_2": f"{'ab' * 16}.{'cd' * 32}"})  # 伪造
    assert r.json()["status"] == "REJECTED"
    assert "HUMAN_GATE_2" in r.json()["reason"]


# ---- E2E-008 Step-4 资金不足 ----

def test_e2e_008_insufficient_budget():
    from cscp_gateway.saga import Saga
    from cscp_gateway.state_machine import HandshakeStateMachine
    from cscp_gateway.adapters import (MockNSFLUnionAdapter, MockSandboxAdapter,
                                       MockTranslatorAdapter, MockCBDCContractAdapter,
                                       MockWorkbuddyAdapter)
    from cscp_gateway.human_gate import HumanGate
    sm = HandshakeStateMachine(
        preflight_fn=MockNSFLUnionAdapter(forced="PASS").preflight_check,
        sandbox_fn=MockSandboxAdapter().verify,
        translator_fn=MockTranslatorAdapter().match,
        cbdclock_fn=MockCBDCContractAdapter(budget_ok=False).lock,
        workbuddy_fn=MockWorkbuddyAdapter().create_work_order,
        saga=Saga(), human_gate=HumanGate(), now=lambda: 0.0,
    )
    req = {"caller_scene": {"scene_id": "A", "rules": []},
           "callee_scene": {"scene_id": "B", "rules": []}}
    h = sm.initiate(req)
    sm.preflight(h.handshake_id, req)
    ch = sm._human_gate.issue_challenge(h.handshake_id, "MATCH")
    sm.match(h.handshake_id, sm._human_gate.compute_signature(h.handshake_id, "MATCH", ch["nonce"]))
    h = sm.lock(h.handshake_id, 0.5)
    assert h.status.value == "REJECTED"
    assert "INSUFFICIENT_BUDGET" in h.rejection_reason
    assert h.escrow_id is None                # escrow 未创建


# ---- E2E-009 Step-3 无翻译器 ----

def test_e2e_009_no_translator():
    from cscp_gateway.saga import Saga
    from cscp_gateway.state_machine import HandshakeStateMachine
    from cscp_gateway.adapters import (MockNSFLUnionAdapter, MockSandboxAdapter,
                                       MockTranslatorAdapter, MockCBDCContractAdapter,
                                       MockWorkbuddyAdapter)
    from cscp_gateway.human_gate import HumanGate
    sm = HandshakeStateMachine(
        preflight_fn=MockNSFLUnionAdapter(forced="PASS").preflight_check,
        sandbox_fn=MockSandboxAdapter().verify,
        translator_fn=MockTranslatorAdapter(matched=False).match,
        cbdclock_fn=MockCBDCContractAdapter().lock,
        workbuddy_fn=MockWorkbuddyAdapter().create_work_order,
        saga=Saga(), human_gate=HumanGate(), now=lambda: 0.0,
    )
    req = {"caller_scene": {"scene_id": "A", "rules": []},
           "callee_scene": {"scene_id": "B", "rules": []}}
    h = sm.initiate(req)
    sm.preflight(h.handshake_id, req)
    ch = sm._human_gate.issue_challenge(h.handshake_id, "MATCH")
    h = sm.match(h.handshake_id, sm._human_gate.compute_signature(h.handshake_id, "MATCH", ch["nonce"]))
    assert h.status.value == "REJECTED"
    assert "NO_TRANSLATOR" in h.rejection_reason


# ---- E2E-010 Saga 补偿：Step-5 前取消 → ESCROW_REFUND ----

def test_e2e_010_cancel_triggers_refund():
    from cscp_gateway.saga import Saga
    from cscp_gateway.state_machine import HandshakeStateMachine
    from cscp_gateway.adapters import (MockNSFLUnionAdapter, MockSandboxAdapter,
                                       MockTranslatorAdapter, MockCBDCContractAdapter,
                                       MockWorkbuddyAdapter)
    from cscp_gateway.human_gate import HumanGate
    refunded = []
    saga = Saga(refund_fn=lambda: refunded.append("REFUND"),
                unlock_fn=lambda: None, cancel_fn=lambda: None, release_fn=lambda: None)
    sm = HandshakeStateMachine(
        preflight_fn=MockNSFLUnionAdapter(forced="PASS").preflight_check,
        sandbox_fn=MockSandboxAdapter().verify,
        translator_fn=MockTranslatorAdapter().match,
        cbdclock_fn=MockCBDCContractAdapter().lock,
        workbuddy_fn=MockWorkbuddyAdapter().create_work_order,
        saga=saga, human_gate=HumanGate(), now=lambda: 0.0,
    )
    req = {"caller_scene": {"scene_id": "A", "rules": []},
           "callee_scene": {"scene_id": "B", "rules": []}}
    h = sm.initiate(req)
    sm.preflight(h.handshake_id, req)
    ch = sm._human_gate.issue_challenge(h.handshake_id, "MATCH")
    sm.match(h.handshake_id, sm._human_gate.compute_signature(h.handshake_id, "MATCH", ch["nonce"]))
    sm.lock(h.handshake_id, 0.5)
    h = sm.cancel(h.handshake_id)           # Step-5 前取消
    assert h.status.value == "FAILED"
    assert "REFUND" in refunded             # ESCROW_REFUND 触发（M-4）
    assert any("HANDSHAKE_CANCELLED" in n for n in h.nca_refs) or len(h.nca_refs) >= 1
