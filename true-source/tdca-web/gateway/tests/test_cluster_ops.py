# -*- coding: utf-8 -*-
"""P2 集群编排 + 准入闸门测试（/api/v1/cluster/*——A-13）。

验收映射：① 会话鉴权 fail-closed（无登录 401）
          ② 授权件四要件逐条机验（缺一即 400；形态越界 400；代签短签 403 熔断）
          ③ 首授登记 → 落库 + 谱系落账（DB 实读）
          ④ 多层转授链（subgrant 挂 parent；revoked 上级 → 转授 403 fail-closed）
          ⑤ 准入闸门：config 无授权件 403（仅握手不成立）；有授权件 ADMITTED + 链可追溯
          ⑥ general 调用只给 HANDSHAKE_ONLY（可信联通 ≠ 可信协作）
          ⑦ 注销幂等 + 谱系 revoke 留痕
"""
import pytest
from fastapi.testclient import TestClient

import api_v1

from app import app
from db import get_sessionmaker
from db import models as M


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()

client = TestClient(app)

_PW = "Cl-pass-2026"
_SIGN = "HW-SIGN-8CHARS"


def _auth():
    uname = "cltester01"
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def _grant_payload(**over):
    p = {"subject_agent": "agent-cl-001", "scene_constraint": "场景：内部编排测试",
         "asset_order": 2, "full_composition": True,
         "legal_signer": "法律主体-测试", "signature": _SIGN}
    p.update(over)
    return p


def test_no_session_401():
    r = client.post("/api/v1/cluster/grant/register", json=_grant_payload())
    assert r.status_code == 401


def test_requirement_missing_400():
    r = client.post("/api/v1/cluster/grant/register",
                    json=_grant_payload(scene_constraint=""), headers=_auth())
    assert r.status_code == 400 and "场景约束" in r.text


def test_asset_order_out_of_range_400():
    r = client.post("/api/v1/cluster/grant/register",
                    json=_grant_payload(asset_order=9), headers=_auth())
    assert r.status_code == 400 and "五阶" in r.text


def test_full_composition_required_400():
    r = client.post("/api/v1/cluster/grant/register",
                    json=_grant_payload(full_composition=False), headers=_auth())
    assert r.status_code == 400 and "全构成" in r.text


def test_agent_signature_short_403():
    r = client.post("/api/v1/cluster/grant/register",
                    json=_grant_payload(signature="short"), headers=_auth())
    assert r.status_code == 403 and "代签" in r.text


def test_register_persisted_201():
    h = _auth()
    r = client.post("/api/v1/cluster/grant/register", json=_grant_payload(), headers=h)
    assert r.status_code == 201, r.text
    gid = r.json()["data"]["grant_id"]
    with get_sessionmaker().begin() as s:
        g = s.get(M.AuthGrant, gid)
        assert g is not None and g.status == "active" and g.parent_grant_id is None
        le = s.query(M.LineageEntry).filter_by(grant_id=gid).one()
        assert le.kind == "grant" and le.nca_ref is not None


def test_subgrant_chain_and_revoked_parent_403():
    h = _auth()
    gid = client.post("/api/v1/cluster/grant/register",
                      json=_grant_payload(), headers=h).json()["data"]["grant_id"]
    sub = {"parent_grant_id": gid, "subject_agent": "agent-cl-002",
           "scene_constraint": "场景：转授测试", "asset_order": 3,
           "full_composition": True, "legal_signer": "法律主体-测试",
           "signature": _SIGN}
    r = client.post("/api/v1/cluster/grant/subgrant", json=sub, headers=h)
    assert r.status_code == 201, r.text
    sub_id = r.json()["data"]["grant_id"]
    with get_sessionmaker().begin() as s:
        g = s.get(M.AuthGrant, sub_id)
        assert g.parent_grant_id == gid
        le = s.query(M.LineageEntry).filter_by(grant_id=sub_id).one()
        assert le.kind == "subgrant" and le.parent_grant_id == gid
    # 注销上级 → 转授 403
    client.post("/api/v1/cluster/grant/revoke", json={"grant_id": gid}, headers=h)
    r2 = client.post("/api/v1/cluster/grant/subgrant", json=sub, headers=h)
    assert r2.status_code == 403 and "revoked" in r2.text


def test_admission_config_denied_then_admitted():
    h = _auth()
    r = client.post("/api/v1/cluster/admission/check",
                    json={"agent_id": "agent-cl-003", "call_type": "config"}, headers=h)
    assert r.status_code == 403 and "仅握手不成立" in r.text
    client.post("/api/v1/cluster/grant/register",
                json=_grant_payload(subject_agent="agent-cl-003"), headers=h)
    r2 = client.post("/api/v1/cluster/admission/check",
                     json={"agent_id": "agent-cl-003", "call_type": "config"}, headers=h)
    assert r2.status_code == 200 and r2.json()["data"]["verdict"] == "ADMITTED"


def test_admission_general_handshake_only():
    r = client.post("/api/v1/cluster/admission/check",
                    json={"agent_id": "agent-cl-004", "call_type": "general"},
                    headers=_auth())
    assert r.status_code == 200
    assert r.json()["data"]["verdict"] == "HANDSHAKE_ONLY"


def test_lineage_trace_and_revoke_idempotent():
    h = _auth()
    gid = client.post("/api/v1/cluster/grant/register",
                      json=_grant_payload(), headers=h).json()["data"]["grant_id"]
    sub = {"parent_grant_id": gid, "subject_agent": "agent-cl-001",
           "scene_constraint": "场景：链追溯", "asset_order": 2,
           "full_composition": True, "legal_signer": "法律主体-测试",
           "signature": _SIGN}
    sub_id = client.post("/api/v1/cluster/grant/subgrant", json=sub, headers=h)\
                   .json()["data"]["grant_id"]
    r = client.get("/api/v1/cluster/lineage/agent-cl-001", headers=h)
    assert r.status_code == 200
    data = r.json()["data"]
    kinds = [e["kind"] for e in data["lineage"]]
    assert "grant" in kinds and "subgrant" in kinds
    # 链上溯：sub 的 parent = gid
    sub_entry = [e for e in data["lineage"] if e["grant_id"] == sub_id][0]
    assert sub_entry["parent_grant_id"] == gid
    # 注销幂等
    client.post("/api/v1/cluster/grant/revoke", json={"grant_id": gid}, headers=h)
    r2 = client.post("/api/v1/cluster/grant/revoke", json={"grant_id": gid}, headers=h)
    assert r2.status_code == 200 and r2.json()["data"]["status"] == "revoked"
    with get_sessionmaker().begin() as s:
        revokes = s.query(M.LineageEntry).filter_by(kind="revoke", grant_id=gid).all()
        assert len(revokes) == 1  # 幂等：第二次不重复落账
