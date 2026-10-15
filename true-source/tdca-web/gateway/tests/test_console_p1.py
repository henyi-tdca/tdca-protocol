# -*- coding: utf-8 -*-
"""批 1 用户控制台 P1 测试：dashboard 权属栏本人过滤（含负例）/ GET /me/nca 分页与过滤。

验收映射（TDCA-PLAN-20261009-MY-HUMAN-CHANNEL 批 1 ④）：
  my_ownership 本人隔离 → test_p1_my_ownership_owner_filter / test_p1_my_ownership_negative
  /me/nca 未登录 401 → test_p1_me_nca_unauth_401
  /me/nca 分页与总数 → test_p1_me_nca_pagination
  /me/nca action 过滤 → test_p1_me_nca_action_filter
  /me/nca 参数校验 fail-closed → test_p1_me_nca_param_guard
"""
from datetime import datetime, timedelta, timezone
import json

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


# =====================================================================
# 用量统计 v1（可增项第 2 件）：GET /me/usage 本人 NCA 按日计数聚合
# 口径：actor==本人；+08 日界；窗口默认 30 天上限 90；纯 SELECT 零写
# =====================================================================

_USAGE_ACTOR = "p1-usage-a"


def test_p1_me_usage_unauth_401():
    assert client.get("/api/v1/me/usage").status_code == 401


def test_p1_me_usage_daily_tz_and_actor_exclusion():
    tok = _mkuser(_USAGE_ACTOR)
    now_utc = datetime.now(timezone.utc)
    # +08 日界实证：同一 +08 日的 00:30 与 23:30（分属两个不同 UTC 日）须归并到同一 date
    d08 = (now_utc + timedelta(hours=8)).date()
    tz8 = timezone(timedelta(hours=8))
    ts_a = datetime(d08.year, d08.month, d08.day, 0, 30, tzinfo=tz8).astimezone(timezone.utc)
    ts_b = datetime(d08.year, d08.month, d08.day, 23, 30, tzinfo=tz8).astimezone(timezone.utc)
    assert ts_a.date() != ts_b.date()          # 前提自检：确属两个 UTC 日
    _mk_nca("NCA-U-A1", _USAGE_ACTOR, "user_action_x", ts_a.strftime("%Y-%m-%dT%H:%M:%SZ"))
    _mk_nca("NCA-U-A2", _USAGE_ACTOR, "user_action_x", ts_b.strftime("%Y-%m-%dT%H:%M:%SZ"))
    _mk_nca("NCA-U-A3", _USAGE_ACTOR, "user_action_y", ts_b.strftime("%Y-%m-%dT%H:%M:%SZ"))
    # 排除规则：非用户形态 actor 与他人 actor 不计入「本人」
    _mk_nca("NCA-U-G1", "gateway:internal", "sys_op", ts_b.strftime("%Y-%m-%dT%H:%M:%SZ"))
    _mk_nca("NCA-U-B1", "p1-usage-b", "user_action_x", ts_b.strftime("%Y-%m-%dT%H:%M:%SZ"))
    r = client.get("/api/v1/me/usage", headers=_h(tok))
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    row = next(x for x in d["daily"] if x["date"] == d08.isoformat())
    assert row["count"] == 3                   # +08 日界归并实证（两 UTC 日 → 同一 +08 日）
    assert row["by_action"] == {"user_action_x": 2, "user_action_y": 1}
    assert d["total"] == 3
    assert d["timezone"] == "+08"
    acts = {a for x in d["daily"] for a in x["by_action"]}
    assert "sys_op" not in acts                # gateway: 形态排除
    assert all(x["count"] == sum(x["by_action"].values()) for x in d["daily"])
    assert d["data_provenance"] == "simulated"  # _mk_nca 行全 simulated（ID92 明示口径）


def test_p1_me_usage_window_and_param_guard():
    tok = _mkuser(_USAGE_ACTOR)
    old = (datetime.now(timezone.utc) - timedelta(days=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _mk_nca("NCA-U-OLD1", _USAGE_ACTOR, "old_action", old)
    d = client.get("/api/v1/me/usage", headers=_h(tok)).json()["data"]
    assert "old_action" not in {a for x in d["daily"] for a in x["by_action"]}  # 默认 30 天窗口外
    d60 = client.get("/api/v1/me/usage?days=60", headers=_h(tok)).json()["data"]
    assert "old_action" in {a for x in d60["daily"] for a in x["by_action"]}    # days=60 收入
    assert client.get("/api/v1/me/usage?days=0", headers=_h(tok)).status_code == 400
    assert client.get("/api/v1/me/usage?days=91", headers=_h(tok)).status_code == 400


def test_p1_me_usage_readonly_and_shape():
    tok = _mkuser(_USAGE_ACTOR)
    with get_session() as s:
        n_before = s.query(M.NcaChain).count()
        cols_before = [c.name for c in M.NcaChain.__table__.columns]
    r = client.get("/api/v1/me/usage", headers=_h(tok))
    assert r.status_code == 200
    with get_session() as s:
        n_after = s.query(M.NcaChain).count()
        cols_after = [c.name for c in M.NcaChain.__table__.columns]
    assert n_before == n_after                 # 零写证明：调用前后链行数相等
    assert cols_before == cols_after           # 未新增表列
    d = r.json()["data"]
    assert set(d.keys()) == {"days", "timezone", "actor_filter", "total",
                             "daily", "data_provenance", "note"}
    assert all(set(x.keys()) == {"date", "count", "by_action"} for x in d["daily"])
    body_keys = set(d.keys()) | {k for x in d["daily"] for k in x.keys()}
    assert not ({"token", "token_hash", "password", "salt"} & body_keys)   # 不含凭据字段


# =====================================================================
# 账户信息栏升级版（可增项第 3 件）：/me/dashboard session 段新增 created_at 系字段
# 口径：users.created_at 现值如实带出；+08 展示；缺失/不可解析如实降级不猜测；
#       只增不改、零写、未新增写端点；⛔ password_hash/salt/token 不落响应
# =====================================================================

def _mkuser_at(username: str, created_at: str, role: str = "viewer") -> str:
    ph, salt, iters = hash_password(f"pw-{username}")
    with get_sessionmaker().begin() as s:
        if s.get(M.User, username) is None:
            s.add(M.User(username=username, password_hash=ph, salt=salt,
                         iterations=iters, role=role, created_at=created_at))
    r = client.post("/api/v1/auth/login", json={"username": username, "password": f"pw-{username}"})
    assert r.status_code == 200, r.text[:200]
    return r.json()["data"]["token"]


def test_p1_me_accountinfo_created_at_plus8():
    """+08 口径实证：UTC 16:00 → 次日 +08 00:00:00；原值如实带出；无凭据字段。"""
    tok = _mkuser_at("p1-acct-a", "2026-10-09T16:00:00+00:00")
    r = client.get("/api/v1/me/dashboard", headers=_h(tok))
    assert r.status_code == 200
    sess = r.json()["data"]["session"]
    assert sess["created_at"] == "2026-10-09T16:00:00+00:00"   # 原值如实
    assert sess["created_at_display"] == "2026-10-10 00:00:00"  # +08 跨日
    assert sess["created_at_parse_ok"] is True
    body = json.dumps(r.json())
    assert "password_hash" not in body and "salt" not in body
    assert "token" not in sess and "token_hash" not in sess


def test_p1_me_accountinfo_created_at_degrade():
    """不可解析 ⟹ display=null、parse_ok=false、原值如实（不猜测不伪造）。"""
    tok = _mkuser_at("p1-acct-bad", "not-a-date")
    r = client.get("/api/v1/me/dashboard", headers=_h(tok))
    sess = r.json()["data"]["session"]
    assert sess["created_at"] == "not-a-date"
    assert sess["created_at_display"] is None
    assert sess["created_at_parse_ok"] is False


def test_p1_me_accountinfo_readonly_and_no_write_endpoint():
    tok = _mkuser_at("p1-acct-ro", "2026-10-09T00:00:00Z")
    with get_session() as s:
        n_before = s.query(M.User).count()
        cols_before = [c.name for c in M.User.__table__.columns]
    r = client.get("/api/v1/me/dashboard", headers=_h(tok))
    assert r.status_code == 200
    with get_session() as s:
        n_after = s.query(M.User).count()
        cols_after = [c.name for c in M.User.__table__.columns]
    assert n_before == n_after               # 零写证明：行数相等
    assert cols_before == cols_after         # 未加列
    # 未新增写端点：/api/v1/me 系 POST 路径集合与上批一致——
    # L1SI145-ANCHOR-B2-001 起＋一件：/me/anchor/verify（人工核验受理，founder/operator 闸）
    spec = app.openapi()
    me_posts = sorted(p for p, ops in spec["paths"].items() if "post" in ops and "/me/" in p)
    assert me_posts == ["/api/v1/me/anchor/verify", "/api/v1/me/password",
                        "/api/v1/me/sessions/revoke", "/api/v1/me/sessions/revoke-all"]
