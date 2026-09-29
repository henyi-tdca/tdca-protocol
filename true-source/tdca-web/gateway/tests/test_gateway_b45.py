# -*- coding: utf-8 -*-
"""网关 B-4/B-5 测试：鉴权中间件 + WebSocket 实时端点（默认宽松模式）。"""
import os
import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


# ---- B-4 鉴权（默认关闭 → 向后兼容）----

def test_b4_auth_default_off_write_allowed():
    """默认（TDCA_GATEWAY_AUTH 未设）写操作放行——向后兼容既有测试。"""
    r = client.post("/nsfl/preflight/check", json={
        "caller_scene": {"scene_id": "A", "rules": []},
        "callee_scene": {"scene_id": "B", "rules": []}})
    assert r.status_code == 200


def test_b4_auth_enabled_blocks_write_without_token():
    """启用鉴权后，写操作无 token → 401。"""
    os.environ["TDCA_GATEWAY_AUTH"] = "1"
    try:
        r = client.post("/nsfl/preflight/check", json={
            "caller_scene": {"scene_id": "A", "rules": []},
            "callee_scene": {"scene_id": "B", "rules": []}})
        assert r.status_code == 401
        assert r.json()["error"] == "UNAUTHORIZED"
    finally:
        os.environ.pop("TDCA_GATEWAY_AUTH", None)


def test_b4_auth_enabled_allows_write_with_token():
    """启用鉴权后，携带有效 token 的写操作放行。"""
    os.environ["TDCA_GATEWAY_AUTH"] = "1"
    os.environ["TDCA_GATEWAY_TOKEN"] = "TDCA-CRT-test-token"
    try:
        r = client.post("/nsfl/preflight/check",
                        headers={"Authorization": "TDCA-CRT-TDCA-CRT-test-token"},
                        json={"caller_scene": {"scene_id": "A", "rules": []},
                              "callee_scene": {"scene_id": "B", "rules": []}})
        assert r.status_code == 200
    finally:
        os.environ.pop("TDCA_GATEWAY_AUTH", None)
        os.environ.pop("TDCA_GATEWAY_TOKEN", None)


def test_b4_auth_read_allowed_default():
    """读操作（GET）无需 token——制度即公开。"""
    os.environ["TDCA_GATEWAY_AUTH"] = "1"
    try:
        r = client.get("/handshake/list")
        assert r.status_code == 200
    finally:
        os.environ.pop("TDCA_GATEWAY_AUTH", None)


def test_b4_token_bare_env_value_accepted():
    """M5 热修：面板填裸串（不带 TDCA-CRT- 前缀）+ 调用方头带单前缀 → 放行。"""
    os.environ["TDCA_GATEWAY_AUTH"] = "1"
    os.environ["TDCA_GATEWAY_TOKEN"] = "bare-prod-token"
    try:
        r = client.post("/nsfl/preflight/check",
                        headers={"Authorization": "TDCA-CRT-bare-prod-token"},
                        json={"caller_scene": {"scene_id": "A", "rules": []},
                              "callee_scene": {"scene_id": "B", "rules": []}})
        assert r.status_code == 200
    finally:
        os.environ.pop("TDCA_GATEWAY_AUTH", None)
        os.environ.pop("TDCA_GATEWAY_TOKEN", None)


def test_b4_token_unset_env_fail_closed():
    """M5 热修②（防缺省）：未设 TDCA_GATEWAY_TOKEN 时，连 demo 头也必须 403——
    宁可降级通道关闭，不可忘设变量=公开默认钥匙。"""
    os.environ["TDCA_GATEWAY_AUTH"] = "1"
    os.environ.pop("TDCA_GATEWAY_TOKEN", None)   # 未设
    try:
        r = client.post("/nsfl/preflight/check",
                        headers={"Authorization": "TDCA-CRT-demo-2026"},
                        json={"caller_scene": {"scene_id": "A", "rules": []},
                              "callee_scene": {"scene_id": "B", "rules": []}})
        assert r.status_code == 403
    finally:
        os.environ.pop("TDCA_GATEWAY_AUTH", None)


def test_b5_ws_token_consistent_with_http():
    """M5 热修③：WS 握手与 HTTP 同一 env 口径（双侧归一）——
    env 带前缀 + query 带前缀 → 放行；错 token → 4401。"""
    from starlette.websockets import WebSocketDisconnect
    os.environ["TDCA_GATEWAY_AUTH"] = "1"
    os.environ["TDCA_GATEWAY_TOKEN"] = "TDCA-CRT-ws-tok"
    try:
        with client.websocket_connect("/ws/events?channel=handshake&token=TDCA-CRT-ws-tok") as ws:
            ws.send_text("hi")
            assert ws.receive_json()["type"] == "echo"
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws/events?channel=handshake&token=TDCA-CRT-wrong"):
                pass
        assert exc.value.code == 4401
    finally:
        os.environ.pop("TDCA_GATEWAY_AUTH", None)
        os.environ.pop("TDCA_GATEWAY_TOKEN", None)


def test_b4_auth_governance_requires_token():
    """治理路径（/governance/*）无论读写均须 token。"""
    os.environ["TDCA_GATEWAY_AUTH"] = "1"
    try:
        r = client.get("/governance/status")
        assert r.status_code == 401
    finally:
        os.environ.pop("TDCA_GATEWAY_AUTH", None)


# ---- B-5 WebSocket ----

def test_b5_ws_unknown_channel_rejected():
    """未知 channel → 4404 拒绝（TestClient 抛 WebSocketDisconnect）。"""
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/events?channel=unknown"):
            pass
    assert exc.value.code == 4404


def test_b5_ws_handshake_echo():
    """合法 channel 连接 + echo。"""
    with client.websocket_connect("/ws/events?channel=handshake") as ws:
        ws.send_text("hello")
        msg = ws.receive_json()
        assert msg["type"] == "echo"
        assert msg["channel"] == "handshake"
        assert msg["data"] == "hello"


def test_b5_broadcast():
    """broadcast() 入队（不阻塞，订阅者收到事件）。"""
    from ws_events import broadcast
    m = broadcast("audit", "nca_created", {"nca_ref": "NCA-TEST-001"})
    assert m["type"] == "nca_created"
    assert m["channel"] == "audit"
    assert m["seq"] >= 1
