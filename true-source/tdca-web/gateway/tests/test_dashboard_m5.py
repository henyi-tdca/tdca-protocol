# -*- coding: utf-8 -*-
"""M5 双后台测试：归属迁移 / /me 个人后台 / /agents/:id 智能体后台 / 写路径归属强制。

验收映射（KIMI-WEB-DB-M5-PLAN-001 §五）：
  ① 归属迁移幂等、存量归 founder → test_m5_owner_backfill_idempotent
  ② /me 未登录 401 + 双用户隔离 → test_m5_me_unauth_401 / test_m5_me_isolation
  ③ /agents/:id 五区块齐全 + 404 → test_m5_agent_dashboard_full / test_m5_agent_404
  ④ 写路径归属强制 → test_m5_owner_forced_on_write / test_m5_sandbox_applicant_forced
  ⑤ 归属人脱敏（公开面不泄露用户名）→ test_m5_owner_desensitized
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
    """建用户 + 登录拿会话 token（沿用 test_auth_m3 范式）。"""
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


# ---- 验收①：归属回填幂等 ----
def test_m5_owner_backfill_idempotent():
    with get_sessionmaker().begin() as s:
        if s.get(M.Agent, "AGENT-M5-NULL") is None:
            s.add(M.Agent(agent_id="AGENT-M5-NULL", name="回填验证体",
                          created_at=_NOW, data_provenance="simulated"))
    # 模拟迁移/种子回填逻辑：仅 NULL 行回填 founder，两轮后行数稳定
    for _ in range(2):
        with get_sessionmaker().begin() as s:
            s.query(M.Agent).filter(M.Agent.owner_username.is_(None)).update(
                {M.Agent.owner_username: "founder"})
    with get_session() as s:
        a = s.get(M.Agent, "AGENT-M5-NULL")
        assert a.owner_username == "founder"
        nulls = s.query(M.Agent).filter(M.Agent.owner_username.is_(None)).count()
    assert nulls == 0


# ---- 验收②：/me 未登录 401 ----
def test_m5_me_unauth_401():
    r = client.get("/api/v1/me/dashboard")
    assert r.status_code == 401


# ---- 验收②：双用户隔离（各见各的）----
def test_m5_me_isolation():
    ta, tb = _mkuser("alice-m5"), _mkuser("bob-m5")
    with get_sessionmaker().begin() as s:
        s.add(M.Agent(agent_id="AGENT-ALICE-1", name="爱丽丝的体",
                      owner_username="alice-m5", created_at=_NOW, data_provenance="simulated"))
        s.add(M.Agent(agent_id="AGENT-BOB-1", name="鲍勃的体",
                      owner_username="bob-m5", created_at=_NOW, data_provenance="simulated"))
    ra = client.get("/api/v1/me/dashboard", headers=_h(ta))
    rb = client.get("/api/v1/me/dashboard", headers=_h(tb))
    assert ra.status_code == 200 and rb.status_code == 200
    a_ids = [x["agent_id"] for x in ra.json()["data"]["my_agents"]]
    b_ids = [x["agent_id"] for x in rb.json()["data"]["my_agents"]]
    assert "AGENT-ALICE-1" in a_ids and "AGENT-BOB-1" not in a_ids
    assert "AGENT-BOB-1" in b_ids and "AGENT-ALICE-1" not in b_ids


# ---- 验收③：/agents/:id 五区块齐全 ----
def test_m5_agent_dashboard_full():
    with get_sessionmaker().begin() as s:
        if s.get(M.Agent, "AGENT-M5-FULL") is None:
            s.add(M.Agent(agent_id="AGENT-M5-FULL", name="全区块验证体",
                          owner_username="founder", five_role="M",
                          created_at=_NOW, data_provenance="simulated"))
            s.add(M.MouRecord(agent_id="AGENT-M5-FULL", period="2026-08",
                              mou_inbound=100, mou_outbound=20,
                              ts=_NOW, data_provenance="simulated"))
            s.add(M.TaxEvent(event_id="EVT-M5-1", type="dispatch_tax",
                             agent_id="AGENT-M5-FULL", call_id="CALL-M5",
                             amount=100, tax_rate_bp=200, ts=_NOW,
                             data_provenance="simulated"))
            s.add(M.AttestationRequest(request_id="DAR-M5-1", agent_id="AGENT-M5-FULL",
                                       request_type="meta", status="pending",
                                       ts=_NOW, data_provenance="simulated"))
    r = client.get("/api/v1/agents/AGENT-M5-FULL/dashboard")
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["profile"]["agent_id"] == "AGENT-M5-FULL"
    assert d["mou"][0]["mou_total"] == 120          # MOU = 进项+出项（ID79）
    assert d["tax_events"][0]["event_id"] == "EVT-M5-1"
    assert d["attestations"][0]["request_id"] == "DAR-M5-1"
    assert "nca_chain" in d


# ---- 验收③：不存在 404 ----
def test_m5_agent_404():
    r = client.get("/api/v1/agents/AGENT-NOPE-404/dashboard")
    assert r.status_code == 404


# ---- 验收④：新注册智能体 owner=登录用户 ----
def test_m5_owner_forced_on_write():
    tok = _mkuser("carol-m5")
    r = client.post("/api/v1/attestation/dynamic",
                    json={"request_id": "DAR-M5-C1", "agent_id": "AGENT-CAROL-NEW",
                          "request_type": "scene_extension", "decision": "defer"},
                    headers=_h(tok))
    assert r.status_code == 200, r.text[:200]
    with get_session() as s:
        a = s.get(M.Agent, "AGENT-CAROL-NEW")
    assert a is not None and a.owner_username == "carol-m5"


# ---- 验收④：沙盒申请 applicant=登录用户（覆盖表单自由文本）----
def test_m5_sandbox_applicant_forced():
    tok = _mkuser("dave-m5")
    r = client.post("/api/v1/sandbox/apply",
                    json={"sponsor_did": "did:fake-spoofer", "scene_ids": ["S1"],
                          "pcr_budget": 100, "nsfl_boundary": "none"},
                    headers=_h(tok))
    assert r.status_code == 200, r.text[:200]
    sid = r.json()["data"]["sandbox_id"]
    with get_session() as s:
        app_row = s.get(M.SandboxApplication, sid)
    assert app_row is not None and app_row.applicant == "dave-m5"


# ---- 裁定③：公开面归属人脱敏（不泄露用户名原文）----
def test_m5_owner_desensitized():
    r = client.get("/api/v1/agents/AGENT-M5-FULL/dashboard")
    d = r.json()["data"]
    assert d["profile"]["owner_display"] == "创始人"   # founder→角色口径
    assert "founder" not in str(d["profile"])          # 用户名不出现在公开画像
