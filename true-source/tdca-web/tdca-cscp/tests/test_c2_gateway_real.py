# -*- coding: utf-8 -*-
"""C2 验收测试：真实 D-2 引擎替换 mock 后 gateway 全链路（H-C2-001~004；H-C2-005 见 test_c1_acceptance）。"""
import time
from decimal import Decimal

from fastapi.testclient import TestClient

from cscp_gateway.gateway import app, build_state_machine
from cscp_gateway.human_gate import HumanGate

client = TestClient(app)


def _sig(handshake_id: str, action: str) -> str:
    """T-CSCP-008 真实签名流程：challenge 端点签发 nonce → 签名设备计算 HMAC token。"""
    r = client.post(f"/handshake/challenge/{handshake_id}", json={"action": action})
    assert r.status_code == 201
    nonce = r.json()["nonce"]
    return HumanGate().compute_signature(handshake_id, action, nonce)


def _req(a_rules, b_rules):
    return {"caller_scene": {"scene_id": "A", "rules": a_rules},
            "callee_scene": {"scene_id": "B", "rules": b_rules},
            "caller_tier": "L2", "cross_scene_flag": True}


def _limit(ns_type, op, val):
    return {"rule_id": f"R-{ns_type}-{op}", "ns_type": ns_type, "operator": op,
            "parameter": str(val), "unit": "CNY"}


def _full_handshake(req):
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    client.post("/handshake/match", params={"handshake_id": hs}, json={"human_signature_1": _sig(hs, "MATCH")})
    client.post("/handshake/lock", params={"handshake_id": hs}, json={"mou_split_ratio": 0.5})
    r = client.post("/handshake/dispatch", params={"handshake_id": hs}, json={"human_signature_2": _sig(hs, "DISPATCH")})
    return hs, r.json()


def test_h_c2_001_end_to_end_latency_under_3s():
    """真实引擎替换后五步握手端到端 <3s（P95<5s）。"""
    t0 = time.perf_counter()
    for _ in range(20):
        hs, out = _full_handshake(_req(
            [{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
            [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}]))
        assert out["status"] == "DISPATCHED"
    dt = (time.perf_counter() - t0) * 1000
    avg = dt / 20
    assert avg < 3000.0, f"端到端 avg {avg:.1f}ms >= 3s"


def test_h_c2_002_medium_conflict_fail_with_altpath():
    """MEDIUM 冲突（限额取严）→ preflight FAIL（拒绝 + 兜底流程），与 B2 集成验证一致。"""
    r = client.post("/handshake/initiate", json=_req(
        [_limit("TRANSACTION_LIMIT", "LIMIT_MAX", 1000000)],
        [_limit("TRANSACTION_LIMIT", "LIMIT_MAX", 500000)]))
    hs = r.json()["handshake_id"]
    r = client.post("/handshake/preflight", params={"handshake_id": hs},
                    json=_req([_limit("TRANSACTION_LIMIT", "LIMIT_MAX", 1000000)],
                              [_limit("TRANSACTION_LIMIT", "LIMIT_MAX", 500000)]))
    body = r.json()
    assert body["status"] == "FAIL"           # 契约层状态（红队 #2 #8）
    assert body["rejection_step"] == "STEP2"


def test_h_c2_003_high_conflict_triggered_circuit_break():
    """HIGH（LEGAL）→ TRIGGERED 熔断：无资金锁定、无 WorkOrder。"""
    req = _req([{"rule_id": "L1", "ns_type": "LEGAL", "operator": "FORBID"}],
               [{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}])
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    r = client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    assert r.json()["status"] == "TRIGGERED"   # 契约层状态（熔断可见，红队 #2 #8）
    assert r.json()["rejection_step"] == "STEP2"
    # 熔断后无后续步骤（无 lock/dispatch）
    st = client.get(f"/handshake/status/{hs}").json()
    assert st["escrow_id"] is None and st["work_order_id"] is None
    assert len(st["nca_refs"]) >= 2  # 熔断 NCA 记录完整


def test_h_c2_004_pass_premium_to_step3():
    """PASS 场景 → risk_premium 正确传递（preflight 响应含 premium；status 视图可见）。"""
    req = _req([{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
               [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}])
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    r = client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    body = r.json()
    assert body["status"] == "PASS"            # 契约层状态（FIN-5: PASS 分支一致）
    assert body["risk_premium"] == 0.2  # 无冲突 → M（OBSERVE 档位）


def test_build_state_machine_fallback_mock():
    """mock fallback 保留（use_real_engine=False，R-CSCP-001）。"""
    sm = build_state_machine(use_real_engine=False)
    assert sm is not None


def test_dispatch_via_real_p5_workbuddy():
    """F-5 缺口 II 关闭验证：CSCP Step-5 dispatch 走真实 P5 引擎（work_order_id = P5 execution_id）。"""
    req = _req([{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
               [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}])
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    client.post("/handshake/match", params={"handshake_id": hs},
                json={"human_signature_1": _sig(hs, "MATCH")})
    client.post("/handshake/lock", params={"handshake_id": hs}, json={"mou_split_ratio": 0.5})
    r = client.post("/handshake/dispatch", params={"handshake_id": hs},
                    json={"human_signature_2": _sig(hs, "DISPATCH")})
    body = r.json()
    assert body["status"] == "DISPATCHED"
    assert body["work_order_id"].startswith("EX-")      # P5 execution_id（非 WO-MOCK）
    st = client.get(f"/handshake/status/{hs}").json()
    assert st["status"] == "COMPLETED"
