# -*- coding: utf-8 -*-
"""AUTHTEST-001+AMEND-1：require_write_privilege 四档鉴权专测（五断言＋founder 档负例）。

令：TDCA-HANDOFF-EXEC-L1SI222-AUTHTEST-001 / -AMEND-1（2026-11-20，创始人「死命令」：
不写测试不许合入）。依据：TDCA-ASSESS-L1SI222-EXTWATCH-001 附条 1（48 处挂载零专项覆盖）。

约束（硬四条）：只新增本测试文件——⛔改依赖实现（ops_auth_gate.py）⛔改 48 处挂载
⛔另立目录⛔新开 workflow；离线可跑（sqlite 测试库，conftest 既有惰性工厂）。

做法：独立最小 FastAPI 面（tapp）挂四档写端点直测依赖语义；会话 token 经真实
app 登录面签发（_mkuser 范式同 test_api_v1）；既有 pytest 工作流自动命中本文件。

五断言（AMEND-1 §一）：
  1 无 Session → 401（⛔403，401 语义由 _require_session_user 提供）
  2 viewer 调 operator 档 → 403（文案含原 action 字串）
  3 operator 调 operator 档 → 2xx
  4 owner 匹配调 owner_or_operator 档 → 2xx
  5 owner 不匹配调 owner_or_operator 档 → 403
负例旁证：founder 档验非 founder（含 operator）→ 403（文案含原 action 字串）。
"""
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from app import app as _real_app          # noqa: F401  仅用于登录面签发会话
from auth import hash_password
from db import get_sessionmaker
from db import models as M
from ops_auth_gate import require_write_privilege

_client = TestClient(_real_app)

# ---- 最小四档写面（独立 app，⛔不向生产 app 注册任何路由） ----
_ACTION_OP = "登记测试客体"
_ACTION_FOUNDER = "发布测试公告"
_ACTION_OWNER = "验收判定"


def _verdict_owner(payload: dict, user: dict):
    """属主判定（范式同 acceptance_ops._verdict_owner）：入参为已解析 JSON 体。"""
    return payload.get("verdict_owner")


tapp = FastAPI()


@tapp.post("/t/login-tier")
def _t_login(request: Request,
             user: dict = Depends(require_write_privilege("login", action="登录档动作"))):
    return {"ok": True, "user": user["username"]}


@tapp.post("/t/operator-tier")
def _t_operator(request: Request,
                user: dict = Depends(require_write_privilege("operator", action=_ACTION_OP))):
    return {"ok": True, "user": user["username"]}


@tapp.post("/t/founder-tier")
def _t_founder(request: Request,
               user: dict = Depends(require_write_privilege("founder", action=_ACTION_FOUNDER))):
    return {"ok": True, "user": user["username"]}


@tapp.post("/t/owner-or-operator-tier")
def _t_owner(request: Request,
             user: dict = Depends(require_write_privilege(
                 "owner_or_operator", action=_ACTION_OWNER, owner_getter=_verdict_owner))):
    return {"ok": True, "user": user["username"]}


tclient = TestClient(tapp)

_NOW = datetime.now(timezone.utc).isoformat()


def _mkuser(username: str, role: str = "viewer") -> str:
    """建用户＋登录拿会话 token（沿用 test_api_v1._mkuser 范式）。"""
    ph, salt, iters = hash_password(f"pw-{username}")
    with get_sessionmaker().begin() as s:
        if s.get(M.User, username) is None:
            s.add(M.User(username=username, password_hash=ph, salt=salt,
                         iterations=iters, role=role, created_at=_NOW))
    r = _client.post("/api/v1/auth/login",
                     json={"username": username, "password": f"pw-{username}"})
    assert r.status_code == 200, r.text[:200]
    return r.json()["data"]["token"]


def _h(token: str) -> dict:
    return {"Authorization": token}


# ---- 断言 1：无 Session（未登录）→ 401（⛔403）----
def test_aw1_anonymous_login_tier_401():
    r = tclient.post("/t/login-tier", json={})
    assert r.status_code == 401
    assert r.status_code != 403


def test_aw1b_anonymous_operator_tier_401():
    r = tclient.post("/t/operator-tier", json={})
    assert r.status_code == 401
    assert r.status_code != 403


# ---- 断言 2：viewer（普通用户）调 operator 档 → 403，文案含原 action ----
def test_aw2_viewer_operator_tier_403_action_text():
    tok = _mkuser("aw-viewer-op", "viewer")
    r = tclient.post("/t/operator-tier", json={}, headers=_h(tok))
    assert r.status_code == 403
    assert _ACTION_OP in r.json()["detail"]


# ---- 断言 3：operator 调 operator 档 → 成功（2xx）----
def test_aw3_operator_operator_tier_ok():
    tok = _mkuser("aw-operator", "operator")
    r = tclient.post("/t/operator-tier", json={}, headers=_h(tok))
    assert r.status_code == 200


# ---- 断言 4：owner 匹配调 owner_or_operator 档 → 成功（2xx）----
def test_aw4_owner_match_ok():
    u = "aw-owner-a"
    tok = _mkuser(u, "viewer")
    r = tclient.post("/t/owner-or-operator-tier",
                     json={"verdict_owner": u}, headers=_h(tok))
    assert r.status_code == 200


# ---- 断言 5：owner 不匹配调 owner_or_operator 档 → 403 ----
def test_aw5_owner_mismatch_403():
    tok = _mkuser("aw-owner-b", "viewer")
    r = tclient.post("/t/owner-or-operator-tier",
                     json={"verdict_owner": "aw-owner-a"}, headers=_h(tok))
    assert r.status_code == 403


# ---- 负例旁证：founder 档——非 founder（含 operator）→ 403，文案含原 action ----
def test_aw6_founder_tier_operator_negative_403_action_text():
    tok = _mkuser("aw-operator-not-founder", "operator")   # 非 founder
    r = tclient.post("/t/founder-tier", json={}, headers=_h(tok))
    assert r.status_code == 403
    assert _ACTION_FOUNDER in r.json()["detail"]


def test_aw6b_founder_tier_viewer_negative_403():
    tok = _mkuser("aw-viewer-not-founder", "viewer")
    r = tclient.post("/t/founder-tier", json={}, headers=_h(tok))
    assert r.status_code == 403
    assert _ACTION_FOUNDER in r.json()["detail"]


# ---- 正例旁证（低成本一并）：founder 调 founder 档 / login 档放行 ----
def test_aw6c_founder_tier_founder_ok():
    tok = _mkuser("aw-founder", "founder")
    r = tclient.post("/t/founder-tier", json={}, headers=_h(tok))
    assert r.status_code == 200


def test_aw0_login_tier_logged_in_ok():
    tok = _mkuser("aw-viewer-login", "viewer")
    r = tclient.post("/t/login-tier", json={}, headers=_h(tok))
    assert r.status_code == 200
