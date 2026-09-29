# -*- coding: utf-8 -*-
"""D-2 preflight HTTP 端点测试（CP-1 数据源，可用性修复）。"""
from fastapi.testclient import TestClient

from nsfl_union.api import app

client = TestClient(app)

_REQ = {
    "caller_scene": {"scene_id": "SCN-TOUR", "rules": [
        {"rule_id": "A1", "ns_type": "TRANSACTION_LIMIT", "operator": "LIMIT_MAX",
         "parameter": "1000000", "unit": "CNY"}]},
    "callee_scene": {"scene_id": "SCN-AGRI", "rules": [
        {"rule_id": "B1", "ns_type": "TRANSACTION_LIMIT", "operator": "LIMIT_MAX",
         "parameter": "500000", "unit": "CNY"}]},
    "caller_tier": "L2",
}


def test_preflight_medium_conflict():
    r = client.post("/nsfl/preflight/check", json=_REQ)
    assert r.status_code == 200
    body = r.json()
    assert body["conflict_set"][0]["resolution"] == "TAKE_STRICTER"
    assert body["conflict_set"][0]["severity"] == "MEDIUM"
    assert body["risk_premium"] > 0
    assert body["nca_ref"]


def test_preflight_legal_triggered():
    req = {
        "caller_scene": {"scene_id": "A", "rules": [
            {"rule_id": "L1", "ns_type": "LEGAL", "operator": "FORBID"}]},
        "callee_scene": {"scene_id": "B", "rules": [
            {"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}]},
    }
    r = client.post("/nsfl/preflight/check", json=req)
    assert r.status_code == 200
    assert r.json()["conflict_set"][0]["severity"] == "HIGH"


def test_preflight_clean_pass():
    req = {
        "caller_scene": {"scene_id": "A", "rules": [
            {"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}]},
        "callee_scene": {"scene_id": "B", "rules": [
            {"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}]},
    }
    r = client.post("/nsfl/preflight/check", json=req)
    assert r.json()["conflict_set"] == []
    assert r.json()["risk_premium"] == 0.2
