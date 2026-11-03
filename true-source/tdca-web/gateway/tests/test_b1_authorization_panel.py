# -*- coding: utf-8 -*-
"""L1SI193-B1-001：C1 授权配置面板测试（/api/v1/authorization/draft|sign|revoke＋GET /{auth_id}）。

验收映射（令面自测五条）：
  ① 四要件缺一即拒，且提示缺哪一项
  ② 智能体代签被拒（on_behalf 非空 400；非本人签 403）
  ③ auth_id＋nca_seq 生成且可查（业务行、事件流水、NCA 链三处）
  ④ 撤回路径可用（POST /revoke；事件另记一笔、既往不抹）
  ⑤ 匿名凭 auth_id 查到范围与期限与状态；查不到凭据值
可靠性九项（三栏回报读数源）：半条记录（NCA 失败清行）、对拍、恢复字段齐、
  熔断三条（resign/hash/standard）、fail-closed、operator 解冻、默认拒、无存证拒、⛔降级。
"""
import hashlib

import pytest
from fastapi.testclient import TestClient

import api_v1
import authorization_panel_ops
from app import app
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "B1Panel-pass-2026"


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    api_v1._register_hits.clear()
    api_v1._login_hits.clear()
    yield
    api_v1._register_hits.clear()
    api_v1._login_hits.clear()


def _auth(uname):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


_FULL = {
    "operation": "activate",
    "grantor": "甲主体（测试）", "grantee": "乙主体（测试）",
    "subject": "配置权·算法件一", "scope": "场景：联调；地域：站内；次数：100 次",
    "term": "2026-11-04 至 2026-12-31",
    "conditions": {"may_sub_grant": "否", "may_commercialize": "是",
                   "attribution_required": "是"},
    "submit": True,
}


def _draft(headers, **kw):
    body = dict(_FULL)
    body.update(kw)
    return client.post("/api/v1/authorization/draft", json=body, headers=headers)


# ─────────────────────────── 令面自测五条 ───────────────────────────

def test_1_requirement_missing_rejected_with_hint():
    h = _auth("b1p_req01")
    r = _draft(h, grantor="", scope="")
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert "授权方" in detail and "标的与范围" in detail   # 缺哪一项逐一点名


def test_1b_condition_yesno_and_etc_guard():
    h = _auth("b1p_req02")
    # 条件缺一（may_commercialize 未填）
    r = _draft(h, conditions={"may_sub_grant": "否", "attribution_required": "是"})
    assert r.status_code == 400 and "可否商用" in r.json()["detail"]
    # 「等」字兜底
    r = _draft(h, scope="场景联调等")
    assert r.status_code == 400 and "等" in r.json()["detail"]


def test_2_agent_sign_rejected_and_non_owner_403():
    h = _auth("b1p_drafter1")
    r = _draft(h)
    assert r.status_code == 201
    aid = r.json()["data"]["auth_id"]
    # 智能体代签（on_behalf 非空）
    r = client.post("/api/v1/authorization/sign",
                    json={"auth_id": aid, "on_behalf": "assistant-x"}, headers=h)
    assert r.status_code == 400 and "代签" in r.json()["detail"]
    # 非本人签
    h2 = _auth("b1p_other1")
    r = client.post("/api/v1/authorization/sign", json={"auth_id": aid}, headers=h2)
    assert r.status_code == 403


def test_3_id_and_nca_seq_queryable():
    h = _auth("b1p_drafter2")
    r = _draft(h)
    assert r.status_code == 201
    d = r.json()["data"]
    aid, nca = d["auth_id"], d["nca_seq"]
    assert aid.startswith("AP-") and nca.startswith("NCA-WEB-")
    # 业务行＋事件＋NCA 链三处可查
    with get_session() as s:
        doc = s.get(M.AuthorizationPanelDoc, aid)
        assert doc is not None and doc.nca_seq == nca
        evs = s.query(M.AuthorizationPanelEvent).filter_by(auth_id=aid).all()
        assert len(evs) == 1 and evs[0].nca_ref == nca
        nca_row = s.get(M.NcaChain, nca)
        assert nca_row is not None
        assert nca_row.artifact_path == f"authorization-panel:{aid}"
    # 对拍字段齐（可靠性·存证/恢复）：业务表 rec_hash 与 NCA 行一致
    assert doc.rec_hash == nca_row.rec_hash


def test_4_revoke_path_and_append_only_events():
    h = _auth("b1p_drafter3")
    aid = _draft(h).json()["data"]["auth_id"]
    assert client.post("/api/v1/authorization/sign",
                       json={"auth_id": aid}, headers=h).status_code == 200
    r = client.post("/api/v1/authorization/revoke",
                    json={"auth_id": aid, "note": "测试撤回"}, headers=h)
    assert r.status_code == 200 and r.json()["data"]["status"] == "revoked"
    with get_session() as s:
        evs = (s.query(M.AuthorizationPanelEvent).filter_by(auth_id=aid)
               .order_by(M.AuthorizationPanelEvent.created_at).all())
        kinds = [e.event_type for e in evs]
        assert kinds == ["submit", "sign", "revoke"]   # 另记一笔、既往不抹
    # 重复撤回 409
    r = client.post("/api/v1/authorization/revoke",
                    json={"auth_id": aid}, headers=h)
    assert r.status_code == 409


def test_5_public_get_scope_term_status_no_credential():
    h = _auth("b1p_drafter4")
    aid = _draft(h, credential_ref="PTR-TEST-001").json()["data"]["auth_id"]
    r = client.get(f"/api/v1/authorization/{aid}")      # 匿名
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["status"] == "pending_sign"
    assert d["scope"] and d["term"]                      # 范围与期限可查
    blob = r.text
    assert "PTR-TEST-001" not in blob                    # 凭据号（指针）也不出公开面
    assert "credential" not in d or not d.get("credential_ref")
    assert "signer" not in d and "drafter" not in d      # 账号信息不出
    # 既有字面路由不被 /{auth_id} 抢（回归护栏）
    assert client.get("/api/v1/authorization/rules", headers=h).status_code == 200
    assert client.get("/api/v1/authorization/query", headers=h).status_code == 200
    assert client.get("/api/v1/authorization/public/AR-x").status_code == 404


# ─────────────────────────── 可靠性九项 ───────────────────────────

def test_r1_no_half_record_on_nca_failure():
    h = _auth("b1p_half01")
    import authorization_panel_ops as ops
    orig = ops._nca_append
    monkey = pytest.MonkeyPatch()
    monkey.setattr(ops, "_nca_append", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    r = _draft(h, grantor="甲主体（半条记录专用）")
    monkey.undo()
    assert r.status_code == 500
    with get_session() as s:
        assert s.query(M.AuthorizationPanelDoc).filter_by(
            grantor="甲主体（半条记录专用）").first() is None
        # NCA 链不留「新增悬挂引用」（此前测试的存量存证不究）
        dangling = [n for n in s.query(M.NcaChain).all()
                    if n.artifact_path and n.artifact_path.startswith("authorization-panel:")
                    and s.get(M.AuthorizationPanelDoc,
                              n.artifact_path.split(":", 1)[1]) is None]
        assert dangling == []


def test_r2_r3_dual_hash_and_recovery_fields():
    h = _auth("b1p_hash01")
    aid = _draft(h).json()["data"]["auth_id"]
    with get_session() as s:
        doc = s.get(M.AuthorizationPanelDoc, aid)
        row = s.get(M.NcaChain, doc.nca_seq)
    # 对拍：按公开口径重算
    expect = api_v1.rec_hash_of(row.nca_id, row.prev_nca, row.action, row.actor,
                                row.artifact_path, row.sha256_8, row.handshake_id,
                                row.data_provenance, row.ts)
    assert expect == doc.rec_hash
    # 恢复字段齐：编号/字段/存证指针可从 NCA 反查复建
    assert row.artifact_path == f"authorization-panel:{aid}"
    for f in ("grantor", "grantee", "subject", "scope", "term", "conditions"):
        assert getattr(doc, f)


def test_r4_r5_r6_breaker_resign_and_operator_resume():
    h = _auth("b1p_break1")
    aid = _draft(h).json()["data"]["auth_id"]
    assert client.post("/api/v1/authorization/sign",
                       json={"auth_id": aid}, headers=h).status_code == 200
    # 短时重复签署 → 熔断①
    r = client.post("/api/v1/authorization/sign",
                    json={"auth_id": aid}, headers=h)
    assert r.status_code == 423
    with get_session() as s:
        doc = s.get(M.AuthorizationPanelDoc, aid)
        fz = s.query(M.AuthorizationPanelFreeze).filter_by(auth_id=aid).first()
    assert doc.status == "suspended" and fz is not None and fz.reason == "resign"
    # fail-closed：冻结后全拒
    assert client.post("/api/v1/authorization/revoke",
                       json={"auth_id": aid}, headers=h).status_code == 423
    # 非 operator 解冻被拒
    h2 = _auth("b1p_break2")
    r = client.post("/api/v1/authorization/sign",
                    json={"auth_id": aid, "resume": True}, headers=h2)
    assert r.status_code == 403
    # operator 复核解冻（回摆 active）
    op = _auth("b1p_op01")
    with get_sessionmaker().begin() as s:
        u = s.get(M.User, "b1p_op01")
        u.role = "operator"
    r = client.post("/api/v1/authorization/sign",
                    json={"auth_id": aid, "resume": True, "note": "复核通过"}, headers=op)
    assert r.status_code == 200 and r.json()["data"]["status"] == "active"
    with get_session() as s:
        fz = s.query(M.AuthorizationPanelFreeze).filter_by(auth_id=aid).first()
        assert fz.unfrozen_at is not None and fz.unfrozen_by == "b1p_op01"


def test_r4_hash_streak_trip():
    h = _auth("b1p_hash02")
    aid = _draft(h).json()["data"]["auth_id"]
    # 篡改业务表 rec_hash → 对拍不符
    with get_sessionmaker().begin() as s:
        d = s.get(M.AuthorizationPanelDoc, aid)
        d.rec_hash = "DEADBEEF00000000"
    for i in range(1, 3):
        r = client.post("/api/v1/authorization/revoke",
                        json={"auth_id": aid}, headers=h)
        assert r.status_code == 409 and f"连续 {i} 次" in r.json()["detail"]
    # 第三次 → 熔断②
    r = client.post("/api/v1/authorization/revoke",
                    json={"auth_id": aid}, headers=h)
    assert r.status_code == 423
    with get_session() as s:
        fz = s.query(M.AuthorizationPanelFreeze).filter_by(auth_id=aid).first()
    assert fz is not None and fz.reason == "hash"


def test_r4_standard_unmapped_rejected():
    h = _auth("b1p_std01")
    r = _draft(h, operation="hijack")
    assert r.status_code == 400 and "标准无法对应" in r.json()["detail"]


def test_r7_r8_r9_default_deny_and_no_degrade():
    # 未登录 ⛔ 起草（默认拒）
    r = client.post("/api/v1/authorization/draft", json=_FULL)
    assert r.status_code == 401
    # 未登录签署/撤回同拒
    r = client.post("/api/v1/authorization/sign",
                    json={"auth_id": "AP-deadbeef00"})
    assert r.status_code == 401
    # 不存在 auth_id：匿名 404（无存证视为未发生；⛔ 降级放行）
    r = client.get("/api/v1/authorization/AP-deadbeef00")
    assert r.status_code == 404
    # 未知 operation 值在 drafts 表无从落（草稿已经过标准对应）
    h = _auth("b1p_deny01")
    aid = _draft(h).json()["data"]["auth_id"]
    with get_session() as s:
        doc = s.get(M.AuthorizationPanelDoc, aid)
        assert doc.operation == "activate"   # 无无法对应的存量


def test_five_states_all_reachable():
    # draft 态（submit=false）
    h = _auth("b1p_states1")
    r = _draft(h, submit=False)
    assert r.json()["data"]["status"] == "draft"
    aid = r.json()["data"]["auth_id"]
    assert client.get(f"/api/v1/authorization/{aid}").json()["data"]["status"] == "draft"
    # pending_sign → active → suspended（熔断）→ revoked 各态见 test_r4/test_4
    # 状态机不可自 active 回 draft：无此路径即为回摆只限 suspended→active
    assert client.post("/api/v1/authorization/sign",
                       json={"auth_id": aid}, headers=h).status_code == 200
    assert client.get(f"/api/v1/authorization/{aid}").json()["data"]["status"] == "active"


def test_p8b_untouched():
    """S-1 护栏：P8b 合约备案面照旧（本件零改其逻辑）。"""
    h = _auth("b1p_p8b01")
    r = client.post("/api/v1/authorization/register", json={
        "asset_ref": "OR-TEST-1", "grantee_ref": "乙主体", "scene": "测试场景",
        "req_scene": True, "req_five_forms": True, "req_full_grant": True,
        "req_legal_signature": True}, headers=h)
    assert r.status_code == 201 and r.json()["data"]["record_id"].startswith("AR-")
