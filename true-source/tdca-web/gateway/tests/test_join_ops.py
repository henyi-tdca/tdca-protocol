# -*- coding: utf-8 -*-
"""批3 A-1 缔约评审只读队列测试（/api/site/join/list——L1SI176-B3-GATE-001 §二 A-1）。

覆盖判据四条：未登录 401；非审核身份 403；空队列 200 items:[]；正常 200 数组。
审核身份双通道：会话 founder/operator；CRT 令牌＋x-tdca-reviewer。
"""
import pytest
from fastapi.testclient import TestClient

from app import app
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)
_PW = "Joinlist-2026"
_SEQ = {"n": 0}


@pytest.fixture(autouse=True)
def _clean():
    import api_v1
    api_v1._register_hits.clear()          # 注册限流清零（照 test_ops_logs 范式）
    with get_sessionmaker().begin() as s:
        s.query(M.JoinRequest).delete()
    yield
    api_v1._register_hits.clear()
    with get_sessionmaker().begin() as s:
        s.query(M.JoinRequest).delete()


def _auth(role=None):
    _SEQ["n"] += 1
    uname = f"join{_SEQ['n']:03d}"
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    if role:
        with get_sessionmaker().begin() as s:
            s.get(M.User, uname).role = role
    return {"Authorization": r.json()["data"]["token"]}


def _seed_join(status="pending", name="演示申请方甲"):
    with get_sessionmaker().begin() as s:
        s.add(M.JoinRequest(
            display_name=name, applicant_kind="human", channel="web",
            status=status, nsfl_result="", created_at="2026-10-27T00:00:00+08:00",
            updated_at="2026-10-27T00:00:00+08:00", data_provenance="simulated"))


def test_no_token_401():
    r = client.get("/api/site/join/list")
    assert r.status_code == 401


def test_viewer_session_403():
    h = _auth(role="viewer")
    r = client.get("/api/site/join/list", headers=h)
    assert r.status_code == 403


def test_empty_queue_200():
    h = _auth(role="operator")
    r = client.get("/api/site/join/list", headers=h)
    assert r.status_code == 200
    assert r.json() == {"items": []}


def test_founder_session_200_fields():
    _seed_join()
    h = _auth(role="founder")
    r = client.get("/api/site/join/list", headers=h)
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    it = items[0]
    # 键集恰为契约八字段（⛔ 多返即可能带出凭据/敏感面）
    assert set(it.keys()) == {"id", "display_name", "applicant_kind", "channel",
                              "created_at", "status", "nsfl_result", "reviewer_note"}
    assert it["status"] == "pending"


def test_crt_token_plus_reviewer_header(monkeypatch):
    monkeypatch.setenv("TDCA_GATEWAY_TOKEN", "JOINLIST-CRT-TEST")
    _seed_join()
    r = client.get("/api/site/join/list",
                   headers={"Authorization": "TDCA-CRT-JOINLIST-CRT-TEST",
                            "x-tdca-reviewer": "ops-01"})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1
    # 无 reviewer 头 → 403
    r2 = client.get("/api/site/join/list",
                    headers={"Authorization": "TDCA-CRT-JOINLIST-CRT-TEST"})
    assert r2.status_code == 403
    # agent 形态 reviewer → 403（⛔ 代签）
    r3 = client.get("/api/site/join/list",
                    headers={"Authorization": "TDCA-CRT-JOINLIST-CRT-TEST",
                             "x-tdca-reviewer": "agent:wb-1"})
    assert r3.status_code == 403


def test_bad_token_403():
    r = client.get("/api/site/join/list", headers={"Authorization": "TDCA-CRT-nope"})
    assert r.status_code == 403


# ── A-2 审核写 ─────────────────────────────────────────────────────────────
def _seed_ret_id(status="pending", name="演示申请方甲"):
    with get_sessionmaker().begin() as s:
        s.add(M.JoinRequest(
            display_name=name, applicant_kind="human", channel="web",
            status=status, nsfl_result="", created_at="2026-10-27T00:00:00+08:00",
            updated_at="2026-10-27T00:00:00+08:00", data_provenance="simulated"))
    with get_session() as s:
        return s.query(M.JoinRequest).order_by(M.JoinRequest.id.desc()).first().id


def _row(jid):
    with get_session() as s:
        r = s.get(M.JoinRequest, jid)
        return {"status": r.status, "note": r.reviewer_note, "nca_ref": r.nca_ref}


def _nca(nca_id):
    with get_session() as s:
        return s.get(M.NcaChain, nca_id)


def test_review_requires_auth():
    jid = _seed_ret_id()
    r = client.post("/api/site/join/review", json={"join_request_id": jid, "action": "approve"})
    assert r.status_code == 401


def test_review_viewer_403():
    jid = _seed_ret_id()
    h = _auth(role="viewer")
    r = client.post("/api/site/join/review", json={"join_request_id": jid, "action": "approve"}, headers=h)
    assert r.status_code == 403


def test_approve_two_stage_pending_to_sandbox_to_active():
    h = _auth(role="operator")
    jid = _seed_ret_id()
    r1 = client.post("/api/site/join/review",
                     json={"join_request_id": jid, "action": "approve", "note": "一审过"}, headers=h)
    assert r1.status_code == 200 and r1.json()["status"] == "sandbox"
    row = _row(jid)
    assert row["nca_ref"]
    n = _nca(row["nca_ref"])
    assert n is not None and n.action == "join-review-approve"   # NCA 存证落点
    r2 = client.post("/api/site/join/review",
                     json={"join_request_id": jid, "action": "approve"}, headers=h)
    assert r2.status_code == 200 and r2.json()["status"] == "active"


def test_reject_pending_to_rejected():
    h = _auth(role="founder")
    jid = _seed_ret_id()
    r = client.post("/api/site/join/review",
                    json={"join_request_id": jid, "action": "reject", "note": "材料不足"}, headers=h)
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    assert _row(jid)["note"] == "材料不足"


def test_nsfl_block_409_status_unchanged_and_trail():
    h = _auth(role="operator")
    jid = _seed_ret_id(name="演示申请方（涉嫌诈骗）")
    r = client.post("/api/site/join/review",
                    json={"join_request_id": jid, "action": "approve"}, headers=h)
    assert r.status_code == 409
    row = _row(jid)
    assert row["status"] == "pending"          # 状态未变
    n = _nca(row["nca_ref"])
    assert n is not None and n.action == "join-review-nsfl-blocked"   # 触负留痕


def test_nsfl_block_via_note_409():
    h = _auth(role="operator")
    jid = _seed_ret_id()
    r = client.post("/api/site/join/review",
                    json={"join_request_id": jid, "action": "approve", "note": "备注含赌博字样"},
                    headers=h)
    assert r.status_code == 409
    assert _row(jid)["status"] == "pending"


def test_duplicate_review_409():
    h = _auth(role="operator")
    jid = _seed_ret_id()
    client.post("/api/site/join/review", json={"join_request_id": jid, "action": "reject"}, headers=h)
    r = client.post("/api/site/join/review", json={"join_request_id": jid, "action": "approve"}, headers=h)
    assert r.status_code == 409                 # 已终态再操作 → 409（本侧取 409 不取幂等）


def test_review_bad_action_400_and_missing_404():
    h = _auth(role="operator")
    jid = _seed_ret_id()
    r = client.post("/api/site/join/review", json={"join_request_id": jid, "action": "hack"}, headers=h)
    assert r.status_code == 400
    r2 = client.post("/api/site/join/review", json={"join_request_id": 999999, "action": "approve"}, headers=h)
    assert r2.status_code == 404


def test_review_no_token_value_persisted():
    """⛔ 令牌值不落库：审核后库内任何行不得含测试口令/令牌串。"""
    h = _auth(role="operator")
    jid = _seed_ret_id()
    client.post("/api/site/join/review",
                json={"join_request_id": jid, "action": "approve", "note": "合规"}, headers=h)
    with get_session() as s:
        rows = s.query(M.JoinRequest).all()
    blob = " ".join(str(vars(r)) for r in rows)
    assert _PW not in blob
    for tok in ("TDCA-SES-", "TDCA-CRT-"):
        assert tok not in blob
