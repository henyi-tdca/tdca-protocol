# -*- coding: utf-8 -*-
"""集成骨架验证：真实 D-2 NSFLUnionEngine 替换 R-CSCP-001 mock，跑 CSCP 五步握手（C1 联调前置证明）。"""
from decimal import Decimal

import pytest

from cscp_gateway.saga import Saga
from cscp_gateway.state_machine import HandshakeStateMachine, HandshakeStatus


class RealNSFLAdapter:
    """CSCPNSFLAdapter 雏形（CSCP 任务书 §八 + DCD-CSCP-CHANGE-001 映射，D-2 W2 输出后冻结）。"""

    def __init__(self):
        from nsfl_union import (NS_Operator, NS_Rule, NS_Type, NSFLUnionEngine,
                                SceneNSFL)
        self._eng = NSFLUnionEngine()
        self._NS_Operator = NS_Operator
        self._NS_Rule = NS_Rule
        self._NS_Type = NS_Type
        self._SceneNSFL = SceneNSFL

    def preflight_check(self, request):
        ns_a = request.get("caller_scene", {})
        ns_b = request.get("callee_scene", {})
        scene_a = self._SceneNSFL(scene_id=ns_a.get("scene_id", "A"),
                                  rules=self._rules(ns_a.get("rules", [])))
        scene_b = self._SceneNSFL(scene_id=ns_b.get("scene_id", "B"),
                                  rules=self._rules(ns_b.get("rules", [])))
        u = self._eng.compute(scene_a, scene_b)
        max_sev = max((c.severity.value for c in u.conflict_set), default=None)
        if max_sev == "HIGH":
            return {"status": "TRIGGERED", "risk_premium": 1.0,
                    "ns_union": {"conflict_set": [{"severity": "HIGH"}]},
                    "next_step": "rejected"}
        if max_sev == "MEDIUM":
            return {"status": "FAIL", "risk_premium": u.risk_premium,
                    "ns_union": u.__dict__, "alt_paths": u.recommended_alt_path,
                    "next_step": "rejected"}
        if max_sev == "LOW":
            return {"status": "PASS", "risk_premium": u.risk_premium,
                    "ns_union": u.__dict__, "next_step": "sandbox_verify"}
        if u.review_queue:  # 兜底 REJECTED（DCD-CSCP-CHANGE-001）
            return {"status": "REJECTED", "reason": "REQUIRES_REVIEW",
                    "ns_union": u.__dict__, "next_step": "rejected"}
        return {"status": "PASS", "risk_premium": u.risk_premium,
                "ns_union": u.__dict__, "next_step": "sandbox_verify"}

    def _rules(self, raw_rules):
        out = []
        for rr in raw_rules:
            ns = self._NS_Type(rr["ns_type"])
            op = self._NS_Operator(rr["operator"])
            kw = {}
            if op in (self._NS_Operator.LIMIT_MAX, self._NS_Operator.LIMIT_MIN):
                kw = {"parameter": Decimal(str(rr["parameter"])), "unit": rr.get("unit", "CNY")}
            out.append(self._NS_Rule(rr.get("rule_id", f"R{len(out)}"), ns, op, **kw))
        return out


def test_integration_real_engine_transaction_limit():
    """真实引擎: 交易限额取严冲突（MEDIUM）→ preflight FAIL。"""
    adapter = RealNSFLAdapter()
    clock = lambda: 0.0
    sm = HandshakeStateMachine(
        preflight_fn=adapter.preflight_check,
        sandbox_fn=lambda request: {"status": "ACTIVE"},
        translator_fn=lambda request: {"matched": True, "translator_id": "T1", "translation_cost": 0.4},
        cbdclock_fn=lambda request: {"locked": True, "lock_tx_hash": "0x", "escrow_id": "E1"},
        workbuddy_fn=lambda request: {"created": True, "work_order_id": "W1"},
        saga=Saga(), now=clock,
    )
    req = {
        "caller_scene": {"scene_id": "A", "rules": [
            {"rule_id": "A1", "ns_type": "TRANSACTION_LIMIT", "operator": "LIMIT_MAX",
             "parameter": "1000000", "unit": "CNY"}]},
        "callee_scene": {"scene_id": "B", "rules": [
            {"rule_id": "B1", "ns_type": "TRANSACTION_LIMIT", "operator": "LIMIT_MAX",
             "parameter": "500000", "unit": "CNY"}]},
        "caller_tier": "L2", "cross_scene_flag": True,
    }
    h = sm.initiate(req)
    h = sm.preflight(h.handshake_id, req)
    assert h.status == HandshakeStatus.REJECTED  # MEDIUM → FAIL → REJECTED
    assert h.rejection_step == "STEP2"


def test_integration_real_engine_clean_pass():
    """真实引擎: 无冲突场景 → PASS → 全链路 COMPLETED。"""
    adapter = RealNSFLAdapter()
    sm = HandshakeStateMachine(
        preflight_fn=adapter.preflight_check,
        sandbox_fn=lambda request: {"status": "ACTIVE"},
        translator_fn=lambda request: {"matched": True, "translator_id": "T1", "translation_cost": 0.4},
        cbdclock_fn=lambda request: {"locked": True, "lock_tx_hash": "0x", "escrow_id": "E1"},
        workbuddy_fn=lambda request: {"created": True, "work_order_id": "W1"},
        saga=Saga(), now=lambda: 0.0,
    )
    req = {
        "caller_scene": {"scene_id": "A", "rules": [
            {"rule_id": "A1", "ns_type": "ETHICAL", "operator": "ALLOW"}]},
        "callee_scene": {"scene_id": "B", "rules": [
            {"rule_id": "B1", "ns_type": "ETHICAL", "operator": "ALLOW"}]},
        "caller_tier": "L2", "cross_scene_flag": True,
    }
    h = sm.initiate(req)
    h = sm.preflight(h.handshake_id, req)
    assert h.status == HandshakeStatus.PENDING_SANDBOX
    h = sm.match(h.handshake_id, f"SIG-{h.handshake_id[:6]}-ALPHA")
    assert h.status == HandshakeStatus.PENDING_LOCK
    h = sm.lock(h.handshake_id, 0.5)
    assert h.status == HandshakeStatus.PENDING_DISPATCH
    h = sm.dispatch(h.handshake_id, f"SIG-{h.handshake_id[:6]}-BETA")
    assert h.status == HandshakeStatus.COMPLETED
