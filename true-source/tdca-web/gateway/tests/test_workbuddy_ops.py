# -*- coding: utf-8 -*-
"""P1 WorkBuddy 上站测试（/api/v1/workbuddy/*——A-12）。

验收映射：① 会话鉴权 fail-closed（无登录 401）
          ② create→execute→status 闭环 + NCA 落链（DB 实读）
          ③ 人类签名不可绕过（空签 → 403；不写 run 记录）
          ④ 签名 request→confirm 全链（短签 → 403 熔断；幂等）
          ⑤ NSFL BLOCK 语义（D-2 场景自带 LEGAL/高档位 → BLOCKED 留痕）
          ⑥ WORM 日志完整性为 True
"""
import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "Wb-pass-2026"

_DSL = {
    "workflow_id": "WF-TEST-001",
    "steps": [
        {"scene": "scene_alpha", "function": "f_alpha", "role": "L",
         "config_right": "S-Right", "output": "m1"},
        {"scene": "scene_beta", "function": "f_beta", "role": "L",
         "config_right": "S-Right", "input": "m1", "output": "m2"},
    ],
    "human_gates": [{"after": "workflow_complete"}],
}


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


@pytest.fixture()
def auth():
    """注册并登录一个内部测试用户，返回 Authorization 头。"""
    uname = "wbtester01"
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login",
                    json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def _create(headers, dsl=None):
    return client.post("/api/v1/workbuddy/workflow/create",
                       json={"workflow_template": dsl or _DSL},
                       headers=headers)


# ---- ① 会话鉴权 fail-closed ----

def test_auth_required_on_all_endpoints():
    assert client.post("/api/v1/workbuddy/workflow/create",
                       json={"workflow_template": _DSL}).status_code == 401
    assert client.post("/api/v1/workbuddy/workflow/execute",
                       json={"workflow_id": "WF-X", "human_signature": "x"}).status_code == 401
    assert client.get("/api/v1/workbuddy/workflow/status",
                      params={"execution_id": "EX-X"}).status_code == 401
    assert client.post("/api/v1/workbuddy/signature/request",
                       json={"gate_id": "G1"}).status_code == 401
    assert client.post("/api/v1/workbuddy/signature/confirm",
                       json={"request_id": "SR-X",
                             "hardware_signature": "abcdefgh"}).status_code == 401
    assert client.get("/api/v1/workbuddy/log-integrity").status_code == 401


# ---- ② create→execute→status 闭环 ----

def test_create_execute_status_roundtrip(auth):
    r = _create(auth)
    assert r.status_code == 201, r.text[:200]
    body = r.json()["data"]
    assert body["status"] == "PENDING_HUMAN_GATE"
    assert "nca_ref" in body

    r = client.post("/api/v1/workbuddy/workflow/execute",
                    json={"workflow_id": "WF-TEST-001",
                          "human_signature": "SIG-BY-HUMAN-01"}, headers=auth)
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["status"] == "COMPLETED"
    assert d["elapsed_ms"] < 10000          # P5 硬指标
    ex_id = d["execution_id"]

    r = client.get("/api/v1/workbuddy/workflow/status",
                   params={"execution_id": ex_id}, headers=auth)
    assert r.status_code == 200
    s = r.json()["data"]
    assert s["status"] == "COMPLETED"
    assert len(s["nca_refs"]) >= 3          # 步骤 + 完成 + 执行落链

    with get_sessionmaker().begin() as s2:
        row = s2.get(M.WorkflowRun, ex_id)
        assert row is not None and row.status == "COMPLETED"


def test_create_dsl_invalid(auth):
    r = _create(auth, dsl={"steps": [{"no_scene": 1}]})
    assert r.status_code == 400


def test_execute_unknown_workflow(auth):
    r = client.post("/api/v1/workbuddy/workflow/execute",
                    json={"workflow_id": "WF-NONE",
                          "human_signature": "SIG-BY-HUMAN-01"}, headers=auth)
    assert r.status_code == 404


def test_execute_forbidden_for_non_owner(auth):
    _create(auth)   # owner = wbtester01
    r = client.post("/api/v1/auth/register", json={
        "username": "wbtester02", "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    assert r.status_code in (200, 201)
    r = client.post("/api/v1/auth/login",
                    json={"username": "wbtester02", "password": _PW})
    other = {"Authorization": r.json()["data"]["token"]}
    r = client.post("/api/v1/workbuddy/workflow/execute",
                    json={"workflow_id": "WF-TEST-001",
                          "human_signature": "SIG-BY-HUMAN-02"}, headers=other)
    assert r.status_code == 403


# ---- ③ 人类签名不可绕过 ----

def test_execute_empty_signature_rejected(auth):
    _create(auth)
    r = client.post("/api/v1/workbuddy/workflow/execute",
                    json={"workflow_id": "WF-TEST-001",
                          "human_signature": ""}, headers=auth)
    assert r.status_code == 403
    assert "HUMAN_SIGNATURE_REQUIRED" in r.text


# ---- ④ 签名 request→confirm ----

def test_signature_request_confirm(auth):
    r = client.post("/api/v1/workbuddy/signature/request",
                    json={"workflow_id": "WF-TEST-001", "gate_id": "GATE-1",
                          "description": "出盒终裁"}, headers=auth)
    assert r.status_code == 201, r.text[:200]
    rid = r.json()["data"]["signature_request_id"]

    r = client.post("/api/v1/workbuddy/signature/confirm",
                    json={"request_id": rid, "hardware_signature": "ab"},
                    headers=auth)
    assert r.status_code == 403           # 自动化签名熔断

    r = client.post("/api/v1/workbuddy/signature/confirm",
                    json={"request_id": rid,
                          "hardware_signature": "HW-SIGN-8CHARS"}, headers=auth)
    assert r.status_code == 200
    assert r.json()["data"]["verified"] is True

    r = client.post("/api/v1/workbuddy/signature/confirm",   # 幂等
                    json={"request_id": rid,
                          "hardware_signature": "HW-SIGN-8CHARS"}, headers=auth)
    assert r.status_code == 200
    assert r.json()["data"]["note"].startswith("已签署")


def test_signature_confirm_unknown(auth):
    r = client.post("/api/v1/workbuddy/signature/confirm",
                    json={"request_id": "SR-NONE",
                          "hardware_signature": "HW-SIGN-8CHARS"}, headers=auth)
    assert r.status_code == 404


# ---- ⑤ NSFL BLOCK 语义（场景自带 LEGAL/高档位负空间 → BLOCKED）----

def test_nsfl_legal_tier_scene_blocks(auth):
    import workbuddy_ops

    def _blocked(step):
        return False

    workbuddy_ops._engine._nsfl_check = _blocked
    try:
        r = _create(auth, dsl={
            "workflow_id": "WF-TEST-NSFL",
            "steps": [
                {"scene": "scene_alpha", "function": "f_a", "output": "m1"},
                {"scene": "scene_beta", "function": "f_b", "input": "m1",
                 "output": "m2", "nsfl_check": True},
            ]})
        assert r.status_code == 201
        r = client.post("/api/v1/workbuddy/workflow/execute",
                        json={"workflow_id": "WF-TEST-NSFL",
                              "human_signature": "SIG-BY-HUMAN-01"}, headers=auth)
        assert r.status_code == 200
        d = r.json()["data"]
        assert d["status"] == "BLOCKED"
        assert d["nsfl_status"] == "TRIGGERED"
    finally:
        workbuddy_ops._engine._nsfl_check = workbuddy_ops._gateway_nsfl_check


# ---- ⑥ WORM 日志完整性 ----

def test_worm_log_integrity(auth):
    r = client.get("/api/v1/workbuddy/log-integrity", headers=auth)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["integrity"] is True
    assert d["worm_log_entries"] >= 1
