# -*- coding: utf-8 -*-
"""W7 前端契约端点测试（/handshake/list + /handshake/detail + /nca/chain，CP-4/CP-5）。"""
from fastapi.testclient import TestClient

from cscp_gateway.gateway import app
from cscp_gateway.human_gate import HumanGate

client = TestClient(app)


def _complete_handshake():
    req = {"caller_scene": {"scene_id": "SCN-TOUR",
                            "rules": [{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}]},
           "callee_scene": {"scene_id": "SCN-AGRI",
                            "rules": [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}]},
           "caller_tier": "L2", "cross_scene_flag": True}
    r = client.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    client.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    r = client.post(f"/handshake/challenge/{hs}", json={"action": "MATCH"})
    client.post("/handshake/match", params={"handshake_id": hs},
                json={"human_signature_1": HumanGate().compute_signature(hs, "MATCH", r.json()["nonce"])})
    client.post("/handshake/lock", params={"handshake_id": hs}, json={"mou_split_ratio": 0.5})
    r = client.post(f"/handshake/challenge/{hs}", json={"action": "DISPATCH"})
    client.post("/handshake/dispatch", params={"handshake_id": hs},
                json={"human_signature_2": HumanGate().compute_signature(hs, "DISPATCH", r.json()["nonce"])})
    return hs


def test_handshake_list():
    _complete_handshake()
    r = client.get("/handshake/list")
    body = r.json()
    assert body["total"] >= 1
    assert body["items"][0]["handshake_id"]
    assert "human_gates" in body["items"][0]


def test_handshake_list_status_filter():
    _complete_handshake()
    r = client.get("/handshake/list", params={"status_filter": "COMPLETED"})
    assert r.json()["total"] >= 1
    assert all(i["status"] == "COMPLETED" for i in r.json()["items"])


def test_handshake_detail():
    hs = _complete_handshake()
    r = client.get("/handshake/detail", params={"handshake_id": hs})
    body = r.json()
    assert body["handshake_id"] == hs
    assert body["status"] == "COMPLETED"
    assert body["human_gates"] == {"gate1": True, "gate2": True}
    assert body["escrow_id"] and body["work_order_id"]
    assert body["caller_tier"] == "L2"


def test_nca_chain():
    hs = _complete_handshake()
    r = client.get("/nca/chain", params={"handshake_id": hs})
    body = r.json()
    assert body["total"] >= 5                       # 全链路 NCA ≥5（H-CSCP-006）
    assert all("nca://tdca/" in item["link"] for item in body["chain"])
    assert all(item["nca_ref"] for item in body["chain"])   # 无断裂（CP-5）


def test_handshake_detail_404():
    r = client.get("/handshake/detail", params={"handshake_id": "HS-NOPE"})
    assert r.status_code == 404
