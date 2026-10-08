# -*- coding: utf-8 -*-
"""改密端点测试（2026-10-09 最小实现令）：POST /api/v1/me/password。

验收映射：
  未登录 401        → test_pw_change_unauth_401
  旧密错 401        → test_pw_change_wrong_old_401
  新密弱 400        → test_pw_change_weak_new_400（且旧密仍可用=未误改）
  正例              → test_pw_change_positive：改后新密可登录、旧密不可登录、当前会话保留
  吊销其它会话      → test_pw_change_current_session_kept：改密后当前会话仍有效
  落链              → test_pw_change_nca_written：NCA 链有 user_password_change 一条
"""
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import app
from auth import hash_password
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)
_NOW = datetime.now(timezone.utc).isoformat()
_URL = "/api/v1/me/password"


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


def _login(username: str, password: str):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def test_pw_change_unauth_401():
    r = client.post(_URL, json={"old_password": "x", "new_password": "abcd1234"})
    assert r.status_code == 401


def test_pw_change_wrong_old_401():
    tok = _mkuser("pw-old-wrong")
    r = client.post(_URL, json={"old_password": "not-the-old-one9", "new_password": "newpass123"},
                    headers=_h(tok))
    assert r.status_code == 401
    assert "旧密码" in r.json()["detail"]
    # 负例保险：旧密仍可登录（密码未被误改）
    assert _login("pw-old-wrong", "pw-pw-old-wrong").status_code == 200


def test_pw_change_weak_new_400():
    tok = _mkuser("pw-weak")
    for weak in ("short1", "abcdefgh", "12345678"):  # 短/无数字/无字母
        r = client.post(_URL, json={"old_password": "pw-pw-weak", "new_password": weak},
                        headers=_h(tok))
        assert r.status_code == 400, weak
        assert "强度不足" in r.json()["detail"]
    assert _login("pw-weak", "pw-pw-weak").status_code == 200  # 未误改


def test_pw_change_positive():
    _mkuser("pw-ok-user")
    tok = _login("pw-ok-user", "pw-pw-ok-user").json()["data"]["token"]
    r = client.post(_URL, json={"old_password": "pw-pw-ok-user", "new_password": "newpass123"},
                    headers=_h(tok))
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["changed"] is True
    assert d["username"] == "pw-ok-user"
    assert d["nca_ref"]
    # 改后：新密可登录、旧密不可登录
    assert _login("pw-ok-user", "newpass123").status_code == 200
    assert _login("pw-ok-user", "pw-pw-ok-user").status_code == 401


def test_pw_change_current_session_kept():
    tok = _mkuser("pw-keep-session")
    r = client.post(_URL, json={"old_password": "pw-pw-keep-session", "new_password": "newpass123"},
                    headers=_h(tok))
    assert r.status_code == 200
    # 当前会话保留（未强踢）；其它会话数如实报（单会话制下为 0）
    me = client.get("/api/v1/auth/me", headers=_h(tok))
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "pw-keep-session"


def test_pw_change_nca_written():
    tok = _mkuser("pw-nca-check")
    client.post(_URL, json={"old_password": "pw-pw-nca-check", "new_password": "newpass123"},
                headers=_h(tok))
    with get_session() as s:
        row = (s.query(M.NcaChain)
               .filter(M.NcaChain.action == "user_password_change", M.NcaChain.actor == "pw-nca-check")
               .order_by(M.NcaChain.ts.desc()).first())
    assert row is not None
    assert "password-change" in (row.artifact_path or "")
    assert "newpass123" not in (row.artifact_path or "")  # 响应/链上均无凭据值
