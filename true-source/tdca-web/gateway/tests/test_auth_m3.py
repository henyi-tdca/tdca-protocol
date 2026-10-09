# -*- coding: utf-8 -*-
"""M3 鉴权测试（F-2 关闭）：登录/会话/页面级权限 + 安全用例。

验收映射：① 未登录写被拒 fail-closed → test_m3_write_without_login_401
          ② 会话过期自动登出 → test_m3_expired_session_401（session_expired 标记）
          ③ 密码哈希存储 → test_m3_password_not_plaintext
安全用例：错口令 / 登出吊销 / 重登录挤下线（防会话固定）/ 读公开回归
"""
import json
import os
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app import app
from auth import SESSION_PREFIX, hash_password
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "M3-test-pass-only"          # 测试口令（仅测试库，非真实凭据）
_USER = "founder"


class _auth_on:
    """临时启用网关鉴权（try/finally 语义，对齐 test_gateway_b45 风格）。"""
    def __enter__(self):
        os.environ["TDCA_GATEWAY_AUTH"] = "1"
    def __exit__(self, *a):
        os.environ.pop("TDCA_GATEWAY_AUTH", None)


def _ensure_user():
    ph, salt, iters = hash_password(_PW)
    with get_sessionmaker().begin() as s:
        if s.get(M.User, _USER) is None:
            s.add(M.User(username=_USER, password_hash=ph, salt=salt,
                         iterations=iters, role="founder",
                         created_at=datetime.now(timezone.utc).isoformat()))


def _login() -> str:
    r = client.post("/api/v1/auth/login", json={"username": _USER, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return r.json()["data"]["token"]


_ensure_user()


# ---- 验收③：密码哈希存储 ----
def test_m3_password_not_plaintext():
    with get_session() as s:
        u = s.get(M.User, _USER)
    assert u is not None
    assert u.password_hash != _PW and u.salt != _PW
    assert _PW not in (u.password_hash + u.salt)
    assert len(u.password_hash) == 64 and len(u.salt) == 32   # hex 长度
    assert u.iterations >= 100_000


# ---- 登录 ----
def test_m3_login_success():
    r = client.post("/api/v1/auth/login", json={"username": _USER, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["token"].startswith(SESSION_PREFIX)
    assert d["role"] == "founder" and "expires_at" in d


def test_m3_login_wrong_password_401():
    r = client.post("/api/v1/auth/login", json={"username": _USER, "password": "wrong"})
    assert r.status_code == 401


# ---- 验收①：未登录写被拒（fail-closed）----
def test_m3_write_without_login_401():
    with _auth_on():
        r = client.post("/api/v1/sandbox/apply", json={})
        assert r.status_code == 401
        assert r.json()["error"] == "UNAUTHORIZED"


# ---- 持会话写放行 ----
def test_m3_write_with_session_200():
    token = _login()
    with _auth_on():
        r = client.post("/api/v1/sandbox/apply", json={},
                        headers={"Authorization": token})
        assert r.status_code == 200, r.text[:200]


# ---- 验收②：会话过期自动登出（过期 → 401 + session_expired 标记）----
def test_m3_expired_session_401():
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    with get_sessionmaker().begin() as s:
        s.add(M.AuthSession(token_hash=__import__("hashlib").sha256(
            b"TDCA-SES-expired-stub").hexdigest(),
            username=_USER, expires_at=past, revoked=0, created_at=now))
    with _auth_on():
        r = client.post("/api/v1/sandbox/apply", json={},
                        headers={"Authorization": "TDCA-SES-expired-stub"})
        assert r.status_code == 401
        assert r.json().get("session_expired") is True


# ---- 登出吊销 ----
def test_m3_logout_revokes():
    token = _login()
    r = client.post("/api/v1/auth/logout", headers={"Authorization": token})
    assert r.status_code == 200 and r.json()["data"]["revoked"] is True
    with _auth_on():
        r = client.post("/api/v1/sandbox/apply", json={},
                        headers={"Authorization": token})
        assert r.status_code == 403          # 已吊销 → FORBIDDEN


# ---- 安全用例：重登录挤下线（防会话固定，单会话制）----
def test_m3_relogin_revokes_old():
    t1 = _login()
    t2 = _login()
    assert t1 != t2
    with _auth_on():
        assert client.post("/api/v1/sandbox/apply", json={},
                           headers={"Authorization": t1}).status_code == 403
        assert client.post("/api/v1/sandbox/apply", json={},
                           headers={"Authorization": t2}).status_code == 200


# ---- 会话状态查询（前端接缝依赖）----
def test_m3_me_valid_and_invalid():
    token = _login()
    r = client.get("/api/v1/auth/me", headers={"Authorization": token})
    assert r.status_code == 200
    assert r.json()["data"]["username"] == _USER
    assert r.json()["data"]["expires_in_s"] > 0
    assert client.get("/api/v1/auth/me").status_code == 401


# ---- 读公开回归（制度即公开 BV-3：未登录 GET 放行）----
def test_m3_read_public_with_auth_on():
    with _auth_on():
        assert client.get("/api/v1/system/overview").status_code == 200


# =====================================================================
# 会话管理（看＋踢本人会话 · 2026-10-09 可增项第 1 件）
# 三件端点：GET /me/sessions · POST /me/sessions/revoke · POST /me/sessions/revoke-all
# 硬约束：本人过滤；⛔ 响应不含 token/token_hash；⛔ 不删行；写动作落 NCA
# =====================================================================

_USER2 = "viewer_b"


def _ensure_user2():
    ph, salt, iters = hash_password(_PW)
    with get_sessionmaker().begin() as s:
        if s.get(M.User, _USER2) is None:
            s.add(M.User(username=_USER2, password_hash=ph, salt=salt,
                         iterations=iters, role="viewer",
                         created_at=datetime.now(timezone.utc).isoformat()))


def _login2() -> str:
    _ensure_user2()
    r = client.post("/api/v1/auth/login", json={"username": _USER2, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return r.json()["data"]["token"]


def _sid_of_token(token: str) -> str:
    """与 api_v1._session_sid 同式：sha256(sha256(token))[:12]（指纹口径自核）。"""
    import hashlib
    th = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return hashlib.sha256(th.encode("utf-8")).hexdigest()[:12]


def _count_sessions(username: str) -> int:
    with get_session() as s:
        return s.query(M.AuthSession).filter(M.AuthSession.username == username).count()


# ---- 负例：未登录三项全 401（fail-closed）----
def test_me_sessions_unauthenticated_401():
    assert client.get("/api/v1/me/sessions").status_code == 401
    assert client.post("/api/v1/me/sessions/revoke", json={"sid": "x" * 12}).status_code == 401
    assert client.post("/api/v1/me/sessions/revoke-all").status_code == 401


# ---- 正例①看：字段齐＋当前标记＋S-1 不含 token/token_hash 值 ----
def test_me_sessions_list_current_fields_and_no_secret():
    token = _login()
    r = client.get("/api/v1/me/sessions", headers={"Authorization": token})
    assert r.status_code == 200, r.text[:200]
    items = r.json()["data"]["sessions"]
    assert len(items) >= 1
    cur = [i for i in items if i["is_current"]]
    assert len(cur) == 1                     # 单活制：恰一条当前
    row = cur[0]
    for k in ("sid", "created_at", "expires_at", "is_current", "is_revoked", "is_expired"):
        assert k in row, f"缺字段 {k}"
    assert row["is_revoked"] is False and row["is_expired"] is False
    assert row["sid"] == _sid_of_token(token)   # 指纹口径自核
    body = json.dumps(r.json(), ensure_ascii=False)
    assert token not in body                 # S-1：token 值不落响应
    import hashlib
    assert hashlib.sha256(token.encode("utf-8")).hexdigest() not in body  # token_hash 亦不落响应


# ---- 负例：乱造 sid / 他人会话 sid → 404（不可见处理，不泄漏存在性）----
def test_me_sessions_revoke_unknown_or_other_user_404():
    token = _login()
    r = client.post("/api/v1/me/sessions/revoke", json={"sid": "f0f0f0f0f0f0"},
                    headers={"Authorization": token})
    assert r.status_code == 404
    t_a = _login()                       # 用户 A 当前会话 sid
    r = client.get("/api/v1/me/sessions", headers={"Authorization": t_a})
    sid_a = [i for i in r.json()["data"]["sessions"] if i["is_current"]][0]["sid"]
    t_b = _login2()                      # 用户 B 越权吊销 A 的会话
    r = client.post("/api/v1/me/sessions/revoke", json={"sid": sid_a},
                    headers={"Authorization": t_b})
    assert r.status_code == 404          # 他人会话标识按不可见处理
    r = client.get("/api/v1/me/sessions", headers={"Authorization": t_a})
    assert r.status_code == 200          # A 会话不受影响（存在性未泄漏、无副作用）


# ---- 正例②踢指定（含当前）：revoked=1 且行保留，当前会话随即失效 ----
def test_me_sessions_revoke_current_then_dead_and_row_kept():
    token = _login()
    n_before = _count_sessions(_USER)
    r = client.get("/api/v1/me/sessions", headers={"Authorization": token})
    sid = [i for i in r.json()["data"]["sessions"] if i["is_current"]][0]["sid"]
    r = client.post("/api/v1/me/sessions/revoke", json={"sid": sid},
                    headers={"Authorization": token})
    assert r.status_code == 200 and r.json()["data"]["revoked"] is True
    assert r.json()["data"]["nca_ref"]      # 写动作落 NCA
    assert _count_sessions(_USER) == n_before   # ⛔ 不删行
    assert client.get("/api/v1/me/sessions",
                      headers={"Authorization": token}).status_code == 401


# ---- 正例③踢全部（S-3）：含当前；吊销后当前会话确已失效；行全保留 ----
def test_me_sessions_revoke_all_kills_current_s3():
    token = _login()
    n_before = _count_sessions(_USER)
    r = client.post("/api/v1/me/sessions/revoke-all", headers={"Authorization": token})
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["revoked"] >= 1 and d["nca_ref"]
    assert _count_sessions(_USER) == n_before   # ⛔ 不删行
    assert client.get("/api/v1/me/sessions",
                      headers={"Authorization": token}).status_code == 401   # S-3 当前会话确已失效
    r = client.post("/api/v1/auth/login", json={"username": _USER, "password": _PW})
    assert r.status_code == 200                 # 重新登录不受阻（新会话正常签发）
