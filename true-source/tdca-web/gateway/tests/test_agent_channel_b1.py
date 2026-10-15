# -*- coding: utf-8 -*-
"""智能体通道 批1 身份与登记测试（/api/v1/agent-channel/*——A-26，L1SI147-CHANNEL-B1-001）。

验收映射（开工令 §四 新增冒烟四例）：
  ① fail-closed 总闸一正例一负例：登记正常→闸放；吊销/冻结→403 全拒
  ② 登记一正例一负例：201＋落库＋NCA 存证；无会话→401／缺六要素→400
  ③ 锚无效不发令牌：默认锚（记名级·待补）→403 ANCHOR_INVALID 且库内零凭据；
     补锚至 notifier·固锚级·已补 → 201 且库内只存指纹（⛔ 值不入库）
  ④ 未登记公开查显幽灵态：HTTP 200＋ghost:true＋四字段 null（⛔ 不伪装存在）
另验：公开面四字段（权属/授权/授权状态/获取方式）；非主体本人签发→403（人类签名权不可绕）。
"""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import agent_channel_ops
from app import app
from db import get_session
from db import models as M

client = TestClient(app)

_PW = "B1chan-2026"
_SEQ = {"n": 0}


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    import api_v1
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth(anchor_kind: str | None = None, uname: str | None = None) -> dict:
    """注册＋登录；anchor_kind 选 notifier 时注册流程自动建「固锚级·待补」锚行。"""
    if uname is None:
        _SEQ["n"] += 1
        name = f"b1u{_SEQ['n']:03d}"
    else:
        name = uname
    body = {"username": name, "password": _PW, "agree_contract": True,
            "contract_version": "V1.0"}
    if anchor_kind:
        body["anchor_kind"] = anchor_kind
        body["anchor_evidence_ref"] = "test-anchor-ref"
    r = client.post("/api/v1/auth/register", json=body)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/auth/login", json={"username": name, "password": _PW})
    assert r.status_code == 200, r.text[:300]
    return {"Authorization": r.json()["data"]["token"]}


def _register(hdr: dict, ref: str = "six-elements://test/0001") -> str:
    r = client.post("/api/v1/agent-channel/register",
                    json={"six_elements_ref": ref}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    return r.json()["data"]["reg_no"]


def _set_anchor_verified(username: str) -> None:
    """测试态人工受理补锚：tier_state 待补→已补（等价受理核验落点）。"""
    with get_session() as s:
        a = s.get(M.UserAnchor, username)
        a.tier_state = "已补"
        a.verified_at = "2026-10-16T00:00:00Z"
        a.verifier = "test-fixture"
        s.commit()


# ---------------------------------------------------------------- ② 登记正/负例
def test_register_positive_creates_and_attests():
    hdr = _auth()
    r = client.post("/api/v1/agent-channel/register",
                    json={"six_elements_ref": "six-elements://demo/0001",
                          "anchor_ref": "anchor://notifier/x",
                          "tier": "standard"}, headers=hdr)
    assert r.status_code == 201
    d = r.json()["data"]
    assert d["registered"] is True and d["status"] == "正常"
    reg_no = d["reg_no"]
    assert reg_no.startswith("SAR-")
    # 落库实读：登记即创建
    with get_session() as s:
        row = s.get(M.SiteAgentRegistry, reg_no)
        assert row is not None and row.status == "正常"
        assert row.data_provenance == "real"
        assert row.six_elements_ref == "six-elements://demo/0001"
        assert row.nca_ref      # 登记存证回链
    # NCA 链实读
    with get_session() as s:
        nca = s.get(M.NcaChain, row.nca_ref)
        assert nca is not None and nca.action == "AGENT_CHANNEL_REGISTER"


def test_register_negative_no_session_and_missing_elements():
    # 负例 1：无会话 → 401（须人类会话，智能体不得自登）
    r = client.post("/api/v1/agent-channel/register",
                    json={"six_elements_ref": "six-elements://x"})
    assert r.status_code == 401
    # 负例 2：缺创世六要素引用 → 400
    hdr = _auth(uname="b1neg2")
    r = client.post("/api/v1/agent-channel/register", json={}, headers=hdr)
    assert r.status_code == 400


# ---------------------------------------------------------------- ① 总闸正/负例
def test_gate_fail_closed_positive_and_negative():
    hdr = _auth()
    reg_no = _register(hdr)
    with get_session() as s:
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    assert gate["admitted"] is True and gate["ghost"] is False
    assert gate["steps"]["nca-evidence"]["state"] == "satisfied"   # 登记已落链
    assert gate["steps"]["token"]["state"] == "pending"
    assert gate["steps"]["protocol-load"]["state"] == "pending_batch"  # 批 2 承接，如实不虚报
    # 负例：吊销（惩罚三态之一）→ 总闸 403 全拒
    with get_session() as s:
        s.get(M.SiteAgentRegistry, reg_no).status = "吊销"
        s.commit()
    with get_session() as s:
        row = s.get(M.SiteAgentRegistry, reg_no)
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    assert gate["admitted"] is False
    assert gate["denied_reason"] == "PUNISHMENT_STATE:吊销"
    with get_session() as s:
        with pytest.raises(HTTPException) as ei:
            agent_channel_ops.gate_assert(s, reg_no)
    assert ei.value.status_code == 403


# ---------------------------------------------------------------- ③ 锚无效不发令牌
def test_anchor_invalid_no_token_then_valid_issued():
    hdr = _auth(anchor_kind="notifier", uname="b1notif")
    reg_no = _register(hdr)
    # 锚未受理（固锚级·待补）→ 拒发，库内零凭据
    r = client.post(f"/api/v1/agent-channel/{reg_no}/credentials", json={}, headers=hdr)
    assert r.status_code == 403 and "ANCHOR_INVALID" in r.text
    with get_session() as s:
        assert s.query(M.SiteAgentCredential).filter_by(reg_no=reg_no).count() == 0
    # 受理补锚（notifier·固锚级·已补）→ 签发；库内只存指纹
    _set_anchor_verified("b1notif")
    r = client.post(f"/api/v1/agent-channel/{reg_no}/credentials", json={}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    d = r.json()["data"]
    assert d["credential"].startswith("TDCA-AGT-")
    fp = d["credential_fingerprint_sha256_16"]
    with get_session() as s:
        row = s.query(M.SiteAgentCredential).filter_by(reg_no=reg_no).one()
        assert row.status == "active"
        assert row.cred_fingerprint.startswith(fp)          # 指纹核对
        assert row.cred_fingerprint != d["credential"]      # ⛔ 值不入库
        assert "TDCA-AGT-" not in row.cred_fingerprint
        assert row.issuer_session                           # 签发会话指纹在册
        assert row.nca_ref
    # 总闸 ②步随凭据转 satisfied
    with get_session() as s:
        assert agent_channel_ops.evaluate_gate(s, reg_no)["steps"]["token"]["state"] == "satisfied"


def test_credential_non_owner_denied():
    hdr_owner = _auth(anchor_kind="notifier", uname="b1own")
    hdr_other = _auth(uname="b1oth")
    reg_no = _register(hdr_owner)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/credentials", json={}, headers=hdr_other)
    assert r.status_code == 403   # 人类签名权不可绕：非主体本人即拒


# ---------------------------------------------------------------- ④ 未登记公开查幽灵态
def test_public_query_ghost_and_registered():
    # 幽灵态：未登记如实显（HTTP 200＋ghost，⛔ 不伪装存在）
    r = client.get("/api/v1/agent-channel/SAR-NOT-EXIST-0001")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["ghost"] is True and d["registered"] is False
    for k in ("权属信息", "授权信息", "授权状态", "获取方式"):
        assert d[k] is None
    # 在册：公开面四字段齐备
    hdr = _auth(uname="b1pubq")
    reg_no = _register(hdr)
    r = client.get(f"/api/v1/agent-channel/{reg_no}")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["ghost"] is False and d["registered"] is True
    for k in ("权属信息", "授权信息", "授权状态", "获取方式"):
        assert d[k]
    assert d["授权状态"] == "正常"
    assert "register" in d["获取方式"]
    # ⛔ 公开面不含凭据值／指纹原文／内部编号
    assert "TDCA-AGT-" not in str(d)
    assert "SCD-" not in str(d)
