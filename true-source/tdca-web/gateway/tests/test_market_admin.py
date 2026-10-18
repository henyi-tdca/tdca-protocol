# -*- coding: utf-8 -*-
"""配置权市场「管理」面测试（四操作·闸门·权限·留痕·不溯及）。"""
import os
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import app          # noqa: E402
from auth import hash_password   # noqa: E402
from db import get_session, get_sessionmaker   # noqa: E402
from db import models as M   # noqa: E402

client = TestClient(app)

_PW = "MA-test-pass-only"


@pytest.fixture(autouse=True)
def _auth_on():
    """仅本模块内启用网关鉴权（try/finally，对齐 test_auth_m3 风格，不污染他件）。"""
    os.environ["TDCA_GATEWAY_AUTH"] = "1"
    yield
    os.environ.pop("TDCA_GATEWAY_AUTH", None)


def _auth_headers(username: str) -> dict:
    """造用户（viewer 即可——本面权限只看权属登记人身份，不看角色）＋登录取头。"""
    ph, salt, iters = hash_password(_PW)
    with get_sessionmaker().begin() as s:
        if s.get(M.User, username) is None:
            s.add(M.User(username=username, password_hash=ph, salt=salt,
                         iterations=iters, role="viewer",
                         created_at=datetime.now(timezone.utc).isoformat()))
    r = client.post("/api/v1/auth/login", json={"username": username,
                                                "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"authorization": r.json()["data"]["token"]}


def _mk_ownership(owner: str, rid: str = "OR-test-1", status: str = "registered"):
    with get_sessionmaker().begin() as s:
        if s.get(M.OwnershipRecord, rid) is None:
            s.add(M.OwnershipRecord(
                record_id=rid, work_title="测试资产表达形式", owner_ref=owner,
                expression_form="文本", source_lineage="test",
                status=status, data_provenance="simulated",
                created_at="2026-10-08T00:00:00+08:00",
                updated_at="2026-10-08T00:00:00+08:00"))


def _mk_authz(rid: str, four: bool = True, status: str = "active"):
    with get_sessionmaker().begin() as s:
        if s.get(M.AuthorizationRecord, rid) is None:
            s.add(M.AuthorizationRecord(
                record_id=rid, asset_ref="asset-x", grantee_ref="co-x",
                scene="生产交付", req_scene=four, req_five_forms=four,
                req_full_grant=four, req_legal_signature=four,
                template_fields="{}", status=status, data_provenance="simulated",
                created_at="2026-10-08T00:00:00+08:00",
                updated_at="2026-10-08T00:00:00+08:00"))


def _publish_payload(**over):
    p = {"ownership_record_id": "OR-test-1",
         "authorization_record_id": "AR-test-1",
         "asset_summary": "五阶资产形态·测试件",
         "scene": "生产交付",
         "scope_note": "复制·部署·运行",
         "term_note": "2026-10-08~2027-10-07",
         "initial_conditions": "初始条件：照授权件载明，公开可查"}
    p.update(over)
    return p


def _pub_once():
    """造一套本人成件并挂出，返回 (headers, listing_id)。"""
    u = f"o{uuid.uuid4().hex[:8]}"
    h = _auth_headers(u)
    ow_id = f"OR-{uuid.uuid4().hex[:8]}"
    ar_id = f"AR-{uuid.uuid4().hex[:8]}"
    _mk_ownership(u, ow_id)
    _mk_authz(ar_id)
    r = client.post("/api/v1/market-admin/listings",
                    json=_publish_payload(ownership_record_id=ow_id,
                                          authorization_record_id=ar_id),
                    headers=h)
    assert r.status_code == 201, r.text
    return u, h, ow_id, ar_id, r.json()["data"]["listing"]["listing_id"]


# ---------------------------------------------------------------- A-1 挂出


def test_publish_ok_with_full_four():
    u, h, ow_id, ar_id, lid = _pub_once()
    r = client.get(f"/api/v1/market-admin/listings/{lid}", headers=h)
    d = r.json()["data"]["listing"]
    assert d["status"] == "active"
    assert d["data_provenance"] == "real"
    assert d["sandbox_flag"] is False
    assert d["owner_ref"] == u


def test_publish_fail_closed_no_authz_record():
    u = f"o{uuid.uuid4().hex[:8]}"
    h = _auth_headers(u)
    _mk_ownership(u, f"OR-{uuid.uuid4().hex[:8]}")
    r = client.post("/api/v1/market-admin/listings",
                    json=_publish_payload(
                        ownership_record_id="OR-test-x",
                        authorization_record_id="AR-none"),
                    headers=h)
    assert r.status_code == 403 and "fail-closed" in r.text


def test_publish_fail_closed_four_incomplete():
    u = f"o{uuid.uuid4().hex[:8]}"
    h = _auth_headers(u)
    ow_id = f"OR-{uuid.uuid4().hex[:8]}"
    _mk_ownership(u, ow_id)
    _mk_authz("AR-bad", four=False)
    try:
        r = client.post("/api/v1/market-admin/listings",
                        json=_publish_payload(ownership_record_id=ow_id,
                                              authorization_record_id="AR-bad"),
                        headers=h)
        assert r.status_code == 403 and "四要件" in r.text
    finally:
        # 共享测试库口径：授权查询为全局清单——四要件不齐之件须即测即清，免污染他件
        with get_sessionmaker().begin() as s:
            bad = s.get(M.AuthorizationRecord, "AR-bad")
            if bad is not None:
                s.delete(bad)


def test_publish_fail_closed_not_owner():
    u = f"o{uuid.uuid4().hex[:8]}"
    h = _auth_headers(u)
    _mk_ownership("someone-else")          # 权属成件非本人
    _mk_authz("AR-test-1")
    r = client.post("/api/v1/market-admin/listings",
                    json=_publish_payload(), headers=h)
    assert r.status_code == 403


def test_publish_fail_closed_cancelled_ownership():
    u = f"o{uuid.uuid4().hex[:8]}"
    h = _auth_headers(u)
    ow_id = f"OR-{uuid.uuid4().hex[:8]}"
    _mk_ownership(u, ow_id, status="cancelled")
    _mk_authz("AR-test-1")
    r = client.post("/api/v1/market-admin/listings",
                    json=_publish_payload(ownership_record_id=ow_id),
                    headers=h)
    assert r.status_code == 403


def test_publish_sandbox_exception_marked():
    u = f"o{uuid.uuid4().hex[:8]}"
    h = _auth_headers(u)
    ow_id = f"OR-{uuid.uuid4().hex[:8]}"
    _mk_ownership(u, ow_id)
    r = client.post("/api/v1/market-admin/listings",
                    json=_publish_payload(ownership_record_id=ow_id,
                                          authorization_record_id="",
                                          sandbox=True),
                    headers=h)
    assert r.status_code == 201, r.text
    d = r.json()["data"]["listing"]
    assert d["sandbox_flag"] is True
    assert d["data_provenance"] == "simulated"
    assert d["authorization_record_id"] == ""


def test_publish_fail_closed_missing_initial_conditions():
    u = f"o{uuid.uuid4().hex[:8]}"
    h = _auth_headers(u)
    ow_id = f"OR-{uuid.uuid4().hex[:8]}"
    _mk_ownership(u, ow_id)
    _mk_authz("AR-test-1")
    r = client.post("/api/v1/market-admin/listings",
                    json=_publish_payload(ownership_record_id=ow_id,
                                          initial_conditions="  "),
                    headers=h)
    assert r.status_code == 400


def test_publish_fail_closed_negative_space():
    u = f"o{uuid.uuid4().hex[:8]}"
    h = _auth_headers(u)
    ow_id = f"OR-{uuid.uuid4().hex[:8]}"
    _mk_ownership(u, ow_id)
    _mk_authz("AR-test-1")
    r = client.post("/api/v1/market-admin/listings",
                    json=_publish_payload(ownership_record_id=ow_id,
                                          initial_conditions="token: abcdefgh"),
                    headers=h)
    assert r.status_code == 400 and "负空间" in r.text


def test_publish_requires_login():
    r = client.post("/api/v1/market-admin/listings", json=_publish_payload())
    assert r.status_code == 401


# ---------------------------------------------------------------- A-2 查询


def test_public_list_four_fields_no_session():
    _, _, _, _, lid = _pub_once()
    r = client.get("/api/v1/market-admin/public/listings")
    assert r.status_code == 200
    rows = r.json()["data"]["listings"]
    row = [x for x in rows if x["listing_id"] == lid][0]
    assert {"权属信息", "授权信息", "授权状态", "获取方式"}.issubset(row.keys())
    assert row["授权状态"]["listing_status"] == "active"


def test_public_list_excludes_delisted():
    _, h, _, _, lid = _pub_once()
    client.post(f"/api/v1/market-admin/listings/{lid}/delist", headers=h)
    rows = client.get("/api/v1/market-admin/public/listings").json()["data"]["listings"]
    assert all(x["listing_id"] != lid for x in rows)


def test_owner_sees_delisted_in_mine():
    _, h, _, _, lid = _pub_once()
    client.post(f"/api/v1/market-admin/listings/{lid}/delist", headers=h)
    r = client.get("/api/v1/market-admin/listings", headers=h)
    assert any(x["listing_id"] == lid and x["status"] == "delisted"
               for x in r.json()["data"]["listings"])


def test_mine_hidden_from_other_and_detail_403():
    _, h, _, _, lid = _pub_once()
    h2 = _auth_headers(f"u{uuid.uuid4().hex[:8]}")
    r = client.get("/api/v1/market-admin/listings", headers=h2)
    assert all(x["listing_id"] != lid for x in r.json()["data"]["listings"])
    r2 = client.get(f"/api/v1/market-admin/listings/{lid}", headers=h2)
    assert r2.status_code == 403


def test_public_one_delisted_404():
    _, h, _, _, lid = _pub_once()
    client.post(f"/api/v1/market-admin/listings/{lid}/delist", headers=h)
    r = client.get(f"/api/v1/market-admin/public/listings/{lid}")
    assert r.status_code == 404


# ------------------------------------------------------- A-3 状态变更 / A-4 下架


def test_pause_resume_double_trail():
    _, h, _, _, lid = _pub_once()
    r1 = client.post(f"/api/v1/market-admin/listings/{lid}/status",
                     json={"action": "pause"}, headers=h)
    assert r1.status_code == 200
    assert r1.json()["data"]["from"] == "active"
    assert r1.json()["data"]["to"] == "paused"
    assert r1.json()["data"]["nca_ref"]
    r2 = client.post(f"/api/v1/market-admin/listings/{lid}/status",
                     json={"action": "resume"}, headers=h)
    assert r2.json()["data"]["from"] == "paused"
    assert r2.json()["data"]["to"] == "active"
    r3 = client.get(f"/api/v1/market-admin/listings/{lid}", headers=h)
    evs = r3.json()["data"]["events"]
    pairs = [(e["from_status"], e["to_status"]) for e in evs]
    assert ("", "active") in pairs            # publish 留痕
    assert ("active", "paused") in pairs      # 原态新态双留痕
    assert ("paused", "active") in pairs
    assert all(e["nca_ref"] for e in evs)


def test_status_wrong_transition_409():
    _, h, _, _, lid = _pub_once()
    r = client.post(f"/api/v1/market-admin/listings/{lid}/status",
                    json={"action": "resume"}, headers=h)
    assert r.status_code == 409


def test_status_other_user_403():
    _, h, _, _, lid = _pub_once()
    h2 = _auth_headers(f"u{uuid.uuid4().hex[:8]}")
    r = client.post(f"/api/v1/market-admin/listings/{lid}/status",
                    json={"action": "pause"}, headers=h2)
    assert r.status_code == 403


def test_delist_does_not_touch_authz_record():
    _, h, _, ar_id, lid = _pub_once()
    with get_session() as s:
        before = s.get(M.AuthorizationRecord, ar_id).status
    r = client.post(f"/api/v1/market-admin/listings/{lid}/delist", headers=h)
    assert r.status_code == 200
    assert r.json()["data"]["to"] == "delisted"
    with get_session() as s:
        after = s.get(M.AuthorizationRecord, ar_id).status
    assert before == after == "active"        # 不溯及：授权件一字不动


def test_delist_twice_409():
    _, h, _, _, lid = _pub_once()
    client.post(f"/api/v1/market-admin/listings/{lid}/delist", headers=h)
    r = client.post(f"/api/v1/market-admin/listings/{lid}/delist", headers=h)
    assert r.status_code == 409


def test_rules_endpoint():
    h = _auth_headers(f"u{uuid.uuid4().hex[:8]}")
    r = client.get("/api/v1/market-admin/rules", headers=h)
    assert r.status_code == 200
    d = r.json()["data"]
    assert len(d["four_operations"]) == 4
    assert "不溯及" in d["four_operations"][3]["rule"]
    assert d["permission"].startswith("挂出")
