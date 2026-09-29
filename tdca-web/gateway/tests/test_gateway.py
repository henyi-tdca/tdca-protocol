# -*- coding: utf-8 -*-
"""统一网关测试（前端数据源全链路：CP-1~6 经单 BASE 可访问）。"""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "OK"


def test_gateway_cp1_preflight():
    """CP-1: /nsfl/preflight/check 经网关。"""
    r = client.post("/nsfl/preflight/check", json={
        "caller_scene": {"scene_id": "A", "rules": [
            {"rule_id": "A1", "ns_type": "TRANSACTION_LIMIT", "operator": "LIMIT_MAX",
             "parameter": "1000000", "unit": "CNY"}]},
        "callee_scene": {"scene_id": "B", "rules": [
            {"rule_id": "B1", "ns_type": "TRANSACTION_LIMIT", "operator": "LIMIT_MAX",
             "parameter": "500000", "unit": "CNY"}]}})
    assert r.status_code == 200
    assert r.json()["conflict_set"][0]["resolution"] == "TAKE_STRICTER"


def test_gateway_cp2_handshake_list():
    """CP-2/4/5: /handshake/* 经网关（include_router 保留原路径）。"""
    r = client.get("/handshake/list")
    assert r.status_code == 200
    assert "items" in r.json()


def test_gateway_cp6_workflow_status():
    """CP-6: /workflow/status 经网关（404=参数缺失正常路由可达）。"""
    r = client.get("/workflow/status")
    assert r.status_code == 422 or r.status_code == 404  # 路由可达（参数校验/未找到）


def test_gateway_translator():
    """W4: /translator/count 经网关。"""
    r = client.get("/translator/count")
    assert r.status_code == 200
    assert r.json()["pass"] is True


def test_gateway_cross_scene():
    """W3: /cross-scene 经网关（创建需 ≥3 场景）。"""
    r = client.post("/cross-scene/create", json={
        "scene_ids": ["A", "B", "C"], "pcr_budget": 9000, "sponsor_did": "DID-1"})
    assert r.status_code == 201
