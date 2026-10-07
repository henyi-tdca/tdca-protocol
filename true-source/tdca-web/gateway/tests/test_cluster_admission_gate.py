# -*- coding: utf-8 -*-
"""准入闸门 G-1~G-5 测试（2026-10-08 开工令：五条合取·fail-closed·沙盒例外·每判落 NCA）。

验收映射：G-1 缔约存证缺一即拦（直造用户绕过注册 → 无缔约 NCA → 403）
          G-2 权属成件（不存在／非本人／已注销 → 403）
          G-3 授权成件不存在 → 403；G-4 四要件不齐 → 403；G-5 已注销 → 403
          沙盒例外（G-1 仍验、G-2~G-5 跳过、显式 simulated 标记）
          全过 → ADMITTED（real）；拒绝落 CLUSTER_ADMIT_DENY 留痕
"""
import pytest
from fastapi.testclient import TestClient

import api_v1

from app import app
from auth import hash_password
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "Cg-pass-2026"
_SIGN = "HW-SIGN-8CHARS"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _register(u):
    r = client.post("/api/v1/auth/register", json={
        "username": u, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    assert r.status_code in (200, 201, 409), r.text[:200]
    r2 = client.post("/api/v1/auth/login", json={"username": u, "password": _PW})
    assert r2.status_code == 200, r2.text[:200]
    return {"Authorization": r2.json()["data"]["token"]}


def _seed_contracted(u="cg-owner"):
    """缔约用户（走注册端点）＋权属成件＋授权成件（四要件齐）。"""
    h = _register(u)
    ow = client.post("/api/v1/ownership/register",
                     json={"work_title": "闸门测试资产", "owner_ref": u,
                           "source_lineage": "admission-gate 测试"}, headers=h)
    assert ow.status_code == 201, ow.text
    ar = client.post("/api/v1/authorization/register",
                     json={"asset_ref": "五族资产·测试", "grantee_ref": "被授权方·测试",
                           "scene": "生产交付",
                           "req_scene": True, "req_five_forms": True,
                           "req_full_grant": True, "req_legal_signature": True},
                     headers=h)
    assert ar.status_code == 201, ar.text
    return h, ow.json()["data"]["record_id"], ar.json()["data"]["record_id"]


def _payload(agent, ow="", ar="", sandbox=False):
    return {"agent_id": agent, "call_type": "config",
            "ownership_record_id": ow, "authorization_record_id": ar,
            "sandbox": sandbox}


def test_g1_not_contracted_403():
    """G-1：直造用户（绕过注册）→ 无缔约存证 → 403 G-1。"""
    u = "cg-nopact-01"
    ph, salt, iters = hash_password(_PW)
    with get_sessionmaker().begin() as s:
        s.add(M.User(username=u, password_hash=ph, salt=salt, iterations=iters,
                     role="viewer", data_provenance="simulated",
                     created_at="2026-10-08T00:00:00+00:00"))
    r2 = client.post("/api/v1/auth/login", json={"username": u, "password": _PW})
    h = {"Authorization": r2.json()["data"]["token"]}
    r = client.post("/api/v1/cluster/admission/check",
                    json=_payload("agent-cg-g1"), headers=h)
    assert r.status_code == 403 and "G-1" in r.text


def test_g2_ownership_gates_403():
    h, ow, ar = _seed_contracted()
    # 空 ID
    r = client.post("/api/v1/cluster/admission/check",
                    json=_payload("agent-cg-g2", ow="", ar=ar), headers=h)
    assert r.status_code == 403 and "G-2" in r.text
    # 他人权属
    other = _register("cg-other")
    ow_other = client.post("/api/v1/ownership/register",
                           json={"work_title": "他人资产", "owner_ref": "cg-other",
                                 "source_lineage": "admission-gate 测试"},
                           headers=other)
    assert ow_other.status_code == 201
    r2 = client.post("/api/v1/cluster/admission/check",
                     json=_payload("agent-cg-g2", ow=ow_other.json()["data"]["record_id"],
                                   ar=ar), headers=h)
    assert r2.status_code == 403 and "G-2" in r.text
    # 已注销权属
    ow_c = client.post("/api/v1/ownership/register",
                       json={"work_title": "将注销资产", "owner_ref": "cg-owner",
                             "source_lineage": "admission-gate 测试"}, headers=h)
    client.post("/api/v1/ownership/cancel",
                json={"record_id": ow_c.json()["data"]["record_id"], "note": "测试注销"},
                headers=h)
    r3 = client.post("/api/v1/cluster/admission/check",
                     json=_payload("agent-cg-g2",
                                   ow=ow_c.json()["data"]["record_id"], ar=ar), headers=h)
    assert r3.status_code == 403 and "G-2" in r.text


def test_g3_g4_g5_authorization_gates_403():
    h, ow, ar = _seed_contracted()
    # G-3 授权成件不存在
    r = client.post("/api/v1/cluster/admission/check",
                    json=_payload("agent-cg-g3", ow=ow, ar="AR-none-zz"), headers=h)
    assert r.status_code == 403 and "G-3" in r.text
    # G-4 四要件不齐（直造库件；登记端点本身 400 拒）——测后即删
    with get_sessionmaker().begin() as s:
        s.add(M.AuthorizationRecord(
            record_id="AR-badfour-cg01", asset_ref="a", grantee_ref="g",
            scene="生产交付", req_scene=False, req_five_forms=False,
            req_full_grant=False, req_legal_signature=False,
            template_fields="{}", status="active", data_provenance="simulated",
            created_at="2026-10-08T00:00:00+00:00",
            updated_at="2026-10-08T00:00:00+00:00"))
    r2 = client.post("/api/v1/cluster/admission/check",
                     json=_payload("agent-cg-g4", ow=ow, ar="AR-badfour-cg01"),
                     headers=h)
    assert r2.status_code == 403 and "G-4" in r2.text
    with get_sessionmaker().begin() as s:
        s.query(M.AuthorizationRecord).filter_by(record_id="AR-badfour-cg01").delete()
    # G-5 已注销授权（登记→注销→再判）
    ar_c = client.post("/api/v1/authorization/register",
                       json={"asset_ref": "五族资产·测试", "grantee_ref": "被授权方·测试",
                             "scene": "生产交付",
                             "req_scene": True, "req_five_forms": True,
                             "req_full_grant": True, "req_legal_signature": True},
                       headers=h)
    rid = ar_c.json()["data"]["record_id"]
    client.post("/api/v1/authorization/cancel",
                json={"record_id": rid, "note": "测试注销"}, headers=h)
    r3 = client.post("/api/v1/cluster/admission/check",
                     json=_payload("agent-cg-g5", ow=ow, ar=rid), headers=h)
    assert r3.status_code == 403 and "G-5" in r3.text


def test_sandbox_exception_admitted_simulated():
    h, _, _ = _seed_contracted()
    r = client.post("/api/v1/cluster/admission/check",
                    json=_payload("agent-cg-sb", sandbox=True), headers=h)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["verdict"] == "ADMITTED_SANDBOX" and d["sandbox"] is True


def test_sandbox_still_requires_contract():
    """沙盒不豁免 G-1：未缔约用户即使 sandbox 也拦。"""
    u = "cg-nopact-02"
    ph, salt, iters = hash_password(_PW)
    with get_sessionmaker().begin() as s:
        s.add(M.User(username=u, password_hash=ph, salt=salt, iterations=iters,
                     role="viewer", data_provenance="simulated",
                     created_at="2026-10-08T00:00:00+00:00"))
    h = {"Authorization": client.post(
        "/api/v1/auth/login", json={"username": u, "password": _PW}
    ).json()["data"]["token"]}
    r = client.post("/api/v1/cluster/admission/check",
                    json=_payload("agent-cg-sb2", sandbox=True), headers=h)
    assert r.status_code == 403 and "G-1" in r.text


def test_full_pass_admitted_and_deny_nca_trail():
    h, ow, ar = _seed_contracted("cg-full")
    agent = "agent-cg-full"
    # 先制造一次拒绝（无授权件）→ 链上应留 CLUSTER_ADMIT_DENY
    client.post("/api/v1/cluster/admission/check",
                json=_payload(agent, ow=ow, ar=ar), headers=h)  # 无谱系授权件 → G-GRANT 拒
    client.post("/api/v1/cluster/grant/register",
                json={"subject_agent": agent, "scene_constraint": "场景：闸门全过测试",
                      "asset_order": 2, "full_composition": True,
                      "legal_signer": "法律主体-测试", "signature": _SIGN}, headers=h)
    r = client.post("/api/v1/cluster/admission/check",
                    json=_payload(agent, ow=ow, ar=ar), headers=h)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["verdict"] == "ADMITTED" and len(d["gates"]) == 6
    with get_sessionmaker().begin() as s:
        acts = [x.action for x in s.query(M.NcaChain).filter(
            M.NcaChain.action.like("CLUSTER_ADMIT%")).all()]
    assert "CLUSTER_ADMIT_DENY" in acts and "CLUSTER_ADMIT" in acts
