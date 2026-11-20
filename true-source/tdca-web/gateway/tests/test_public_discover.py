# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# FC-ID: TDCA-FC-WEB-PUBDISC-001 | 目标函数: PUBLIC-DISCOVER-001 验收测试
# 约束矩阵: TDCA-HANDOFF-EXEC-L1SI223-PUBLIC-DISCOVER-001 §四
#   ① /api/v1/health 匿名 200，JSON 含 status/time/version
#   ② 最小可观察面：⛔ 内网地址/容器名/凭据/内部编号/自然人信息/堆栈细节
#   ③ 只读：写方法 405
# SPDX-License-Identifier: TDCA-Internal
# =============================================================================
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

_FORBIDDEN_PATTERNS = [
    "127.0.0.1", "0.0.0.0", "localhost", "172.", "192.168.", "10.0.",
    "TDCA-CRT", "TDCA-SES", "password", "token", "secret",
    "GSEQ-", "L1SI", "FC-ID", "Traceback", "File \"",
]


def test_health_anonymous_200_minimal_face():
    r = client.get("/api/v1/health")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert "time" in body and ("+" in body["time"] or "Z" in body["time"] or "T" in body["time"])
    assert "version" in body and isinstance(body["version"], str) and body["version"]
    assert body["deps"]["db"] in ("ok", "degraded")


def test_health_no_internal_leak():
    r = client.get("/api/v1/health")
    text = r.text
    for pat in _FORBIDDEN_PATTERNS:
        assert pat not in text, f"健康端点泄漏内部面: {pat}"


def test_health_top_level_keys_exact():
    r = client.get("/api/v1/health")
    assert set(r.json().keys()) == {"status", "time", "version", "deps"}


def test_health_read_only():
    for m in ("post", "put", "delete", "patch"):
        r = client.request(m, "/api/v1/health")
        assert r.status_code == 405, (m, r.status_code)
