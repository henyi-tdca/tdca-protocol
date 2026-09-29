# -*- coding: utf-8 -*-
"""GSEQ-0700 agent_card 持久化测试（TDCA-HANDOFF-KIMI-AGENTCARD-PERSIST-001）。

验收映射：① identity_type=external + owner_auth 可机读 → test_external_register_persists_identity
          ② 不静默丢弃（extra=forbid + external 缺卡/缺授权 fail-closed）→ test_extra_field_rejected_422
             / test_external_missing_card_400 / test_native_with_card_400
          ③ B1 补录身份标注（founder 专用端点）→ test_identity_annotation_*
          ④ 回归不回退 → 全量套件绿 + native 注册默认身份行
"""
import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from auth import hash_password
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "Reg-pass-2026"
_CARD = {"profile": "tdca-lite", "capabilities": ["training"],
         "runtime": "workbuddy", "version": "1.0"}
_AUTH = "TDCA-OWNER-CONTRACT-AUTH-001"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _reg(username: str, **kw):
    body = {"username": username, "password": _PW,
            "agree_contract": True, "contract_version": "V1.0"}
    body.update(kw)
    return client.post("/api/v1/auth/register", json=body)


def _drop_user(username: str):
    with get_sessionmaker().begin() as s:
        u = s.get(M.User, username)
        if u is not None:
            s.delete(u)
        i = s.get(M.UserIdentity, username)
        if i is not None:
            s.delete(i)


def _mkfounder_session(username: str = "founder-gseq0700") -> str:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    ph, salt, iters = hash_password(f"pw-{username}")
    with get_sessionmaker().begin() as s:
        u = s.get(M.User, username)
        if u is None:
            s.add(M.User(username=username, password_hash=ph, salt=salt,
                         iterations=iters, role="founder", created_at=now))
        else:
            u.role = "founder"
    r = client.post("/api/v1/auth/login", json={"username": username, "password": f"pw-{username}"})
    assert r.status_code == 200, r.text[:200]
    return r.json()["data"]["token"]


# ---- ① external 注册持久化身份三要素（可机读）----
def test_external_register_persists_identity():
    _drop_user("reg-ext-1")
    r = _reg("reg-ext-1", identity_type="external", agent_card=_CARD, owner_auth=_AUTH)
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["identity"]["identity_type"] == "external"
    assert d["identity"]["agent_card_persisted"] is True
    assert d["identity"]["owner_auth"] == _AUTH
    # 落库核验
    with get_session() as s:
        row = s.get(M.UserIdentity, "reg-ext-1")
        assert row is not None and row.identity_type == "external"
        assert row.owner_auth == _AUTH and row.nca_ref == d["nca_id"]
        import json
        assert json.loads(row.agent_card_json)["runtime"] == "workbuddy"
    # 链上可机验：artifact_path 含身份段
    with get_session() as s:
        nca = s.get(M.NcaChain, d["nca_id"])
        assert "identity:external" in nca.artifact_path
        assert f"owner_auth:{_AUTH}" in nca.artifact_path
    # /me 机读
    me = client.get("/api/v1/me/dashboard", headers={"Authorization": d["token"]})
    sess = me.json()["data"]["session"]
    assert sess["identity_type"] == "external" and sess["owner_auth"] == _AUTH
    assert sess["agent_card_persisted"] is True
    _drop_user("reg-ext-1")


# ---- ② 不静默丢弃 ----
def test_extra_field_rejected_422():
    """未知字段 fail-closed（extra=forbid）——不再静默丢弃。"""
    r = _reg("reg-extra-1", bogus_field="x")
    assert r.status_code == 422
    with get_session() as s:
        assert s.get(M.User, "reg-extra-1") is None


def test_external_missing_card_400():
    r = _reg("reg-ext-2", identity_type="external", owner_auth=_AUTH)
    assert r.status_code == 400 and "agent_card" in r.json()["detail"]
    r = _reg("reg-ext-2", identity_type="external", agent_card=_CARD)
    assert r.status_code == 400 and "owner_auth" in r.json()["detail"]
    with get_session() as s:
        assert s.get(M.User, "reg-ext-2") is None


def test_native_with_card_400():
    r = _reg("reg-nat-1", identity_type="native", agent_card=_CARD)
    assert r.status_code == 400


# ---- native 默认身份行（全账号身份可机读）----
def test_native_register_identity_row():
    _drop_user("reg-nat-2")
    r = _reg("reg-nat-2")
    assert r.status_code == 200
    assert r.json()["data"]["identity"]["identity_type"] == "native"
    with get_session() as s:
        row = s.get(M.UserIdentity, "reg-nat-2")
        assert row is not None and row.identity_type == "native" and row.agent_card_json is None
    _drop_user("reg-nat-2")


# ---- ③ B1 补录端点 ----
def test_identity_annotation_forbidden_for_viewer():
    _drop_user("reg-ann-v")
    tok = _reg("reg-ann-v").json()["data"]["token"]
    r = client.post("/api/v1/auth/identity-annotation",
                    json={"username": "reg-ann-v", "identity_type": "external",
                          "agent_card": _CARD, "owner_auth": _AUTH},
                    headers={"Authorization": tok})
    assert r.status_code == 403
    _drop_user("reg-ann-v")


def test_identity_annotation_founder_ok():
    """founder 补录：为存量账号（模拟 B1）补登记 external 身份 + 存证落链。"""
    _drop_user("reg-ann-b1")
    assert _reg("reg-ann-b1").status_code == 200   # native 注册（模拟修复前缔约）
    ftok = _mkfounder_session()
    r = client.post("/api/v1/auth/identity-annotation",
                    json={"username": "reg-ann-b1", "identity_type": "external",
                          "agent_card": _CARD, "owner_auth": _AUTH},
                    headers={"Authorization": ftok})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["identity_type"] == "external" and d["nca_id"].startswith("NCA-WEB-")
    with get_session() as s:
        row = s.get(M.UserIdentity, "reg-ann-b1")
        assert row.identity_type == "external" and row.owner_auth == _AUTH
        assert row.nca_ref == d["nca_id"]
        nca = s.get(M.NcaChain, d["nca_id"])
        assert nca.action == "user_identity_annotation"
        assert "identity://reg-ann-b1/external" in nca.artifact_path
    _drop_user("reg-ann-b1")


def test_identity_annotation_unknown_user_404():
    ftok = _mkfounder_session()
    r = client.post("/api/v1/auth/identity-annotation",
                    json={"username": "no-such-user-gseq0700", "identity_type": "external",
                          "agent_card": _CARD, "owner_auth": _AUTH},
                    headers={"Authorization": ftok})
    assert r.status_code == 404
