# -*- coding: utf-8 -*-
"""A-11 确权 API 测试（F5 前置缺口补建——meta/dynamic/history/queue 四端点）。

AMEND-1（2026-11-06）：history/queue 只收登录面——匿名 401＋结构化错误体；
登录态读数沿用 _mkuser 会话（范式同 test_dashboard_m5）。"""
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import app
from auth import hash_password
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_NOW = datetime.now(timezone.utc).isoformat()


def _mkuser(username: str, role: str = "viewer") -> str:
    """建用户 + 登录拿会话 token（沿用 test_auth_m3 / test_dashboard_m5 范式）。"""
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


def _get(path, headers=None):
    r = client.get(path, headers=headers)
    assert r.status_code == 200, f"{path} → {r.status_code}: {r.text[:200]}"
    body = r.json()
    assert "nca_watermark" in body
    assert body["data_nature"] == "simulated"
    return body["data"]


def _post(path, payload):
    r = client.post(path, json=payload)
    assert r.status_code == 200, f"{path} → {r.status_code}: {r.text[:200]}"
    body = r.json()
    assert "nca_watermark" in body       # 全链路 NCA 水印（ID91）
    assert body["data_nature"] == "simulated"
    return body["data"]


# ---- A-11 元函数初始确权（出盒终裁）----
def test_a11_meta_approved():
    d = _post("/api/v1/attestation/meta", {
        "agent_id": "AGENT-007", "activation": 1.35,
        "sandbox_report": "SEA 4/5 GREEN", "six_elements": {"objective_function": "f(x)", "audit_trail": "NCA"},
    })
    assert d["status"] == "SIGNED"
    assert d["verified"] is True
    assert d["huf_irreducible"] is True
    assert d["attestation_id"].startswith("META-ATT-")


def test_a11_meta_rejected_below_threshold():
    d = _post("/api/v1/attestation/meta", {"agent_id": "AGENT-009", "activation": 1.1})
    assert d["status"] == "REJECTED"      # 激活系数 ≤1.2 → 拒绝（继续孵化或 HUF 特批）


# ---- A-11 动态确权审批（四操作）----
def test_a11_dynamic_approve():
    d = _post("/api/v1/attestation/dynamic", {
        "request_id": "DAR-001", "agent_id": "AGENT-007",
        "request_type": "scene_extension", "urgency": "urgent", "decision": "approve",
    })
    assert d["status"] == "APPROVED"
    assert d["nca_ref"].startswith("Approval-NCA-")


def test_a11_dynamic_reject_and_defer():
    d1 = _post("/api/v1/attestation/dynamic", {"request_id": "DAR-002", "decision": "reject"})
    assert d1["status"] == "REJECTED"
    d2 = _post("/api/v1/attestation/dynamic", {"request_id": "DAR-003", "decision": "defer"})
    assert d2["status"] == "DEFERRED"


# ---- A-11 确权历史查询（ATTEST-SCRUB-001 公开视图）----
# M2 起本端点为 DB 实读且有状态：上文 4 个 POST 产生 4 条已决记录
# （meta approved / meta rejected / DAR-001 approved / DAR-002 rejected），
# DAR-003 defer 后仍为 pending 不计入。断言改为集合语义（同秒 ts 不定序）。
def test_a11_history_chain():
    d = _get("/api/v1/attestation/history", _h(_mkuser("viewer-a11-hist")))  # AMEND-1：登录面读数不变
    assert d["total"] == 4
    assert {c["status"] for c in d["events"]} == {"APPROVED", "REJECTED"}
    assert any(c["event_type"] == "确权体系初始化" for c in d["events"])   # 元函数确权在链（对外语义名）
    assert sum(c["status"] == "REJECTED" for c in d["events"]) == 2  # 拒绝事件保留
    # ATTEST-SCRUB-001：白名单字段，内部编号/智能体名/内部枚举值一律不出
    for c in d["events"]:
        assert set(c.keys()) == {"time", "event_type", "status", "summary"}
        assert "NCA" not in str(c.values()) and "AGENT" not in str(c.values())


def test_a11_history_filter_by_agent():
    d = _get("/api/v1/attestation/history?agent_id=AGENT-007", _h(_mkuser("viewer-a11-hist")))
    assert d["total"] == 3


# ---- A-11 待审队列（紧急度排序）----
# M2 有状态：DAR-001/002 已决，仅 DAR-003（defer）仍在 pending 队列。
def test_a11_queue():
    d = _get("/api/v1/attestation/queue", _h(_mkuser("viewer-a11-queue")))  # AMEND-1：登录面读数不变
    assert d["total"] == 1
    assert d["queue"][0]["request_id"] == "DAR-003"
    assert d["queue"][0]["urgency"] == "normal"


# ---- RULING-ENTRY-CONTENT-DEPLOY-001 裁示3（2026-11-10，较 AMEND-1 新）：恢复匿名可见 ----
def test_ruling_history_anonymous_public_view():
    """匿名 200：白名单公开视图（时间/公开类型/公开状态/公开摘要），逐字段同登录态。"""
    r = client.get("/api/v1/attestation/history")
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert "events" in d and "total" in d
    for ev in d["events"]:
        assert set(ev.keys()) == {"time", "event_type", "status", "summary"}


def test_ruling_queue_anonymous_scrubbed():
    """匿名 200 脱敏视图：⛔ request_id／agent_id／reason 不出；登录态全字段不变（上）。"""
    r = client.get("/api/v1/attestation/queue")
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    for item in d["queue"]:
        assert set(item.keys()) == {"request_type", "urgency"}


def test_amend1_ledger_public_untouched():
    # ⛔不动面照核：公共账本匿名仍 200
    r = client.get("/api/v1/audit/ledger-public")
    assert r.status_code == 200
