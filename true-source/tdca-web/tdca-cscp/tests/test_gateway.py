# -*- coding: utf-8 -*-
"""CSCP 网关 API 端到端测试（FastAPI TestClient，T-CSCP-001）。"""
import pytest

from fastapi.testclient import TestClient

from cscp_gateway.gateway import app
from cscp_gateway.human_gate import HumanGate

client = TestClient(app)


def _sig(handshake_id: str, action: str) -> str:
    """T-CSCP-008 真实签名流程：challenge 端点签发 nonce → 签名设备计算 HMAC token。"""
    r = client.post(f"/handshake/challenge/{handshake_id}", json={"action": action})
    assert r.status_code == 201
    nonce = r.json()["nonce"]
    return HumanGate().compute_signature(handshake_id, action, nonce)

_REQ = {
    "caller_scene": {"scene_id": "A", "rules": []},
    "callee_scene": {"scene_id": "B", "rules": []},
    "caller_tier": "L2",
    "cross_scene_flag": True,
}


def test_full_handshake_via_api():
    """端到端: initiate→preflight→match→lock→dispatch→status（H-CSCP-001）。"""
    r = client.post("/handshake/initiate", json=_REQ)
    assert r.status_code == 201
    hs_id = r.json()["handshake_id"]

    r = client.post("/handshake/preflight", params={"handshake_id": hs_id}, json=_REQ)
    assert r.json()["status"] == "PASS"   # 契约层状态（FIN-5）

    r = client.post("/handshake/match", params={"handshake_id": hs_id},
                    json={"human_signature_1": _sig(hs_id, "MATCH")})
    assert r.json()["status"] == "MATCHED"

    r = client.post("/handshake/lock", params={"handshake_id": hs_id},
                    json={"mou_split_ratio": 0.5})
    assert r.json()["status"] == "LOCKED"
    assert r.json()["escrow_id"]

    r = client.post("/handshake/dispatch", params={"handshake_id": hs_id},
                    json={"human_signature_2": _sig(hs_id, "DISPATCH")})
    assert r.json()["status"] == "DISPATCHED"
    assert r.json()["work_order_id"]

    r = client.get(f"/handshake/status/{hs_id}")
    body = r.json()
    assert body["status"] == "COMPLETED"
    assert body["human_gates"] == {"gate1": True, "gate2": True}
    assert len(body["nca_refs"]) >= 5  # H-CSCP-006 全链路 NCA


def test_gate1_missing_via_api():
    r = client.post("/handshake/initiate", json=_REQ)
    hs_id = r.json()["handshake_id"]
    client.post("/handshake/preflight", params={"handshake_id": hs_id}, json=_REQ)
    r = client.post("/handshake/match", params={"handshake_id": hs_id},
                    json={"human_signature_1": ""})
    assert r.json()["status"] == "REJECTED"
    assert "HUMAN_GATE_1" in r.json()["reason"]


def test_forged_signature_rejected_via_api():
    """E2E-007 形态：伪造签名（无密钥）→ REJECTED（T-CSCP-008 真实级验证）。"""
    r = client.post("/handshake/initiate", json=_REQ)
    hs_id = r.json()["handshake_id"]
    client.post("/handshake/preflight", params={"handshake_id": hs_id}, json=_REQ)
    # 攻击者：自造 nonce + 伪 HMAC（无 secret）
    forged = f"{'ab' * 16}.{'cd' * 32}"
    r = client.post("/handshake/match", params={"handshake_id": hs_id},
                    json={"human_signature_1": forged})
    assert r.json()["status"] == "REJECTED"
    assert "HUMAN_GATE_1" in r.json()["reason"]


def test_status_404():
    r = client.get("/handshake/status/HS-NOPE")
    assert r.status_code == 404


def test_legal_scene_triggered_via_api():
    req = {
        "caller_scene": {"scene_id": "A", "rules": [{"ns_type": "LEGAL", "operator": "FORBID"}]},
        "callee_scene": {"scene_id": "B", "rules": []},
        "caller_tier": "L2", "cross_scene_flag": True,
    }
    r = client.post("/handshake/initiate", json=req)
    hs_id = r.json()["handshake_id"]
    r = client.post("/handshake/preflight", params={"handshake_id": hs_id}, json=req)
    assert r.json()["status"] == "REJECTED"
    assert r.json()["rejection_step"] == "STEP2"
