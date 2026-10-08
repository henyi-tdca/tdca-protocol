# -*- coding: utf-8 -*-
"""批 1 用户控制台 P1 测试：dashboard 权属栏本人过滤（含负例）/ GET /me/nca 分页与过滤。

验收映射（TDCA-PLAN-20261009-MY-HUMAN-CHANNEL 批 1 ④）：
  my_ownership 本人隔离 → test_p1_my_ownership_owner_filter / test_p1_my_ownership_negative
  /me/nca 未登录 401 → test_p1_me_nca_unauth_401
  /me/nca 分页与总数 → test_p1_me_nca_pagination
  /me/nca action 过滤 → test_p1_me_nca_action_filter
  /me/nca 参数校验 fail-closed → test_p1_me_nca_param_guard
"""
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import app
from auth import hash_password
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)
_NOW = datetime.now(timezone.utc).isoformat()


def _mkuser(username: str, role: str = "viewer") -> str:
    ph, salt, iters = hash_password(f"pw-{username}")
    with get_sessionmaker().begin() as s:
        if s.get(M.User, username) is None:
            s.add(M.User(username=username, password_hash=ph, salt=salt,
                         iterations=iters, role=role, created_at=_NOW))
    r = client.post("/api/v1/auth/login", json={"username": username, "password": f"pw-{username}"})
    assert r.status_code == 200, r.text[:200]
    return r.json()["data"]["token"]


def _h(token: str) -> dict:
    return {"Authorization": token}


def _mk_ownership(record_id: str, owner: str) -> None:
    with get_sessionmaker().begin() as s:
        if s.get(M.OwnershipRecord, record_id) is None:
            s.add(M.OwnershipRecord(
                record_id=record_id, work_title=f"作品-{record_id}", owner_ref=owner,
                source_lineage="test-lineage", data_provenance="simulated",
                created_at=_NOW, updated_at=_NOW))


def _mk_nca(nca_id: str, actor: str, action: str, ts: str) -> None:
    with get_sessionmaker().begin() as s:
        if s.get(M.NcaChain, nca_id) is None:
            s.add(M.NcaChain(nca_id=nca_id, prev_nca="GENESIS", action=action,
                             actor=actor, data_provenance="simulated", ts=ts))


def test_p1_my_ownership_owner_filter():
    _mkuser("p1-own-a"); _mkuser("p1-own-b")
    _mk_ownership("OR-P1-A1", "p1-own-a")
    _mk_ownership("OR-P1-B1", "p1-own-b")
    tok = _mkuser("p1-own-a")
    r = client.get("/api/v1/me/dashboard", headers=_h(tok))
    assert r.status_code == 200
    own = r.json()["data"]["my_ownership"]
    ids = [o["record_id"] for o in own]
    assert "OR-P1-A1" in ids and "OR-P1-B1" not in ids  # 负例：他人件不可见


def test_p1_my_ownership_negative():
    """隔离负例：B 登录只见自己；且权属字段集不含内部敏感列。"""
    tok_b = _mkuser("p1-own-b")
    r = client.get("/api/v1/me/dashboard", headers=_h(tok_b))
    own = r.json()["data"]["my_ownership"]
    ids = [o["record_id"] for o in own]
    assert ids == ["OR-P1-B1"]
    assert set(own[0].keys()) == {"record_id", "work_title", "jurisdiction_branch",
                                  "status", "nca_ref", "data_provenance", "created_at"}


def test_p1_me_nca_unauth_401():
    assert client.get("/api/v1/me/nca").status_code == 401


def test_p1_me_nca_pagination():
    actor = "p1-nca-page"
    tok = _mkuser(actor)
    for i in range(25):
        _mk_nca(f"NCA-P1-{i:03d}", actor, "P1_PROBE", f"2026-10-09T00:{i // 60:02d}:{i % 60:02d}Z")
    r1 = client.get("/api/v1/me/nca?page=1&limit=10", headers=_h(tok))
    d1 = r1.json()["data"]
    assert d1["total"] == 25 and len(d1["items"]) == 10 and d1["page"] == 1
    r3 = client.get("/api/v1/me/nca?page=3&limit=10", headers=_h(tok))
    assert len(r3.json()["data"]["items"]) == 5
    # 倒序：首页首条 ts 应晚于末页末条
    assert d1["items"][0]["ts"] >= r3.json()["data"]["items"][-1]["ts"]


def test_p1_me_nca_action_filter():
    actor = "p1-nca-act"
    tok = _mkuser(actor)
    _mk_nca("NCA-P1-ACT1", actor, "P1_ALPHA", "2026-10-09T01:00:00Z")
    _mk_nca("NCA-P1-ACT2", actor, "P1_BETA", "2026-10-09T01:01:00Z")
    r = client.get("/api/v1/me/nca?action=P1_ALPHA&limit=50", headers=_h(tok))
    d = r.json()["data"]
    assert d["total"] == 1 and d["items"][0]["action"] == "P1_ALPHA"


def test_p1_me_nca_param_guard():
    tok = _mkuser("p1-nca-page")
    assert client.get("/api/v1/me/nca?page=0", headers=_h(tok)).status_code == 400
    assert client.get("/api/v1/me/nca?limit=101", headers=_h(tok)).status_code == 400
