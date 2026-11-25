# -*- coding: utf-8 -*-
"""CHAIN-ASSERT-SUP-001 六条断言实测（多层转授链）。

载体内在役集群授权件链 auth_grants.parent_grant_id（与 -366 同面）：
  A-2 逐层须件：登记面逐层缺一即拒（链上无缝可钻）；准入面就持件全链核验，
      存量要件缺损层（DB 直改模拟——API 登记面无缝）下游必拒。
  A-3 逐层须签：任一层未签（短签/空签=代签熔断）该层不成立；存量未签层下游必拒。
  N-1 上游已撤冒充必拒（要害）：级联撤 A ⟹ B、C 全 revoked 下游拒；
      存量旧语义链（-366 披露：GSEQ-8225 前旧码不级联致「上级已撤而下级仍
      active」在册）以 DB 直改模拟 ⟹ 同一旧会话再调必拒（实现无准入缓存，逐判定实查库）。
  N-2 只给中间层件调末层必拒：末层主体无己件即 403（不因中间层在册件放行）。
  N-3 层级留空或填 0 必拒：机面层级由链位机推（chain_depth），调用方无层级注入面；
      等价机验——五阶形态 asset_order 填 0 → 400、留空 → 422（登记/转授同判）。
  N-4 一件一层：grant_no 服务端生成、主键唯一、单一链位；对已撤件再转授/重签
      404 同码（同号不同层之「重签」机面无入口，结构性不可发生）。
"""
import pytest
from fastapi.testclient import TestClient

import api_v1

from app import app
from db import get_sessionmaker
from db import models as M


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


client = TestClient(app)

_PW = "Chain-sup-2026"
_SIGN = "HW-SIGN-8CHARS"
_seq = [0]


def _auth():
    _seq[0] += 1
    uname = f"chsup{_seq[0]:03d}"
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return uname, {"Authorization": r.json()["data"]["token"]}


def _gates(uname, h):
    """备齐 G-2~G-5 成件，返回 (ownership_record_id, authorization_record_id)。"""
    ow = client.post("/api/v1/ownership/register",
                     json={"work_title": "链路断言测试资产", "owner_ref": uname,
                           "source_lineage": "chain-assert-sup 测试"}, headers=h)
    assert ow.status_code == 201, ow.text
    ar = client.post("/api/v1/authorization/register",
                     json={"asset_ref": "五族资产·测试", "grantee_ref": "被授权方·测试",
                           "scene": "生产交付", "req_scene": True,
                           "req_five_forms": True, "req_full_grant": True,
                           "req_legal_signature": True}, headers=h)
    assert ar.status_code == 201, ar.text
    return ow.json()["data"]["record_id"], ar.json()["data"]["record_id"]


def _register(agent, uname, h, **over):
    p = {"subject_agent": agent, "scene_constraint": "场景：链路断言",
         "asset_order": 2, "full_composition": True,
         "legal_signer": uname,  # K1FIX-R1裁定一：原"法律主体-测试"属待封之代签名，对齐本人语义
         "signature": _SIGN}
    p.update(over)
    r = client.post("/api/v1/cluster/grant/register", json=p, headers=h)
    assert r.status_code == 201, r.text
    return r.json()["data"]["grant_id"]


def _subgrant(parent, agent, uname, h, **over):
    p = {"parent_grant_id": parent, "subject_agent": agent,
         "scene_constraint": "场景：链路断言转授", "asset_order": 2,
         "full_composition": True,
         "legal_signer": uname,  # K1FIX-R1裁定一：原"法律主体-测试"属待封之代签名，对齐本人语义
         "signature": _SIGN}
    p.update(over)
    return client.post("/api/v1/cluster/grant/subgrant", json=p, headers=h)


def _admit(agent, h, ow, ar):
    return client.post("/api/v1/cluster/admission/check",
                       json={"agent_id": agent, "call_type": "config",
                             "ownership_record_id": ow,
                             "authorization_record_id": ar}, headers=h)


def _no_active_grant(agent):
    with get_sessionmaker().begin() as s:
        return s.query(M.AuthGrant).filter_by(
            subject_agent=agent, status="active").count() == 0


# ---------------------------------------------------------------- A-2

def test_a2_requirement_missing_at_any_layer_blocks_chain():
    """A-2 登记面：转授层缺任一要件 ⟹ 该层即拒，链上无缝可钻。"""
    uname, h = _auth()
    a = _register("agent-a2-a", uname, h)
    cases = [  # (覆盖字段, 值, 期望码, 期望关键字)
        ("scene_constraint", "", 400, "场景约束"),
        ("asset_order", 0, 400, "五阶"),
        ("full_composition", False, 400, "全构成"),
        ("legal_signer", "", 400, "法律主体签名"),
        ("signature", "short", 403, "SIGNATURE_INVALID"),
    ]
    for i, (k, v, code, kw) in enumerate(cases):
        agent = f"agent-a2-b{i}"
        r = _subgrant(a, agent, uname, h, **{k: v})
        assert r.status_code == code, (k, r.status_code, r.text[:200])
        assert kw in r.text
        assert _no_active_grant(agent), f"{agent} 不应有成件"


def test_a2_three_layer_chain_admitted_positive():
    """A-2 正向：三层链逐层须件齐备 ⟹ 最下游获配置权（链深 3 可追溯）。"""
    uname, h = _auth()
    ow, ar = _gates(uname, h)
    a = _register("agent-a2p-a", uname, h)
    rb = _subgrant(a, "agent-a2p-b", uname, h)
    assert rb.status_code == 201
    rc = _subgrant(rb.json()["data"]["grant_id"], "agent-a2p-c", uname, h)
    assert rc.status_code == 201
    r = _admit("agent-a2p-c", h, ow, ar)
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["verdict"] == "ADMITTED" and d["chain_depth"] == 3


def test_a2_legacy_deficient_middle_layer_downstream_denied():
    """A-2 准入面：链上某层要件缺损（存量异常，DB 直改模拟）⟹ 最下游无配置权。"""
    uname, h = _auth()
    ow, ar = _gates(uname, h)
    a = _register("agent-a2l-a", uname, h)
    b = _subgrant(a, "agent-a2l-b", uname, h).json()["data"]["grant_id"]
    _subgrant(b, "agent-a2l-c", uname, h)
    with get_sessionmaker().begin() as s:  # 模拟存量要件③缺损层
        s.get(M.AuthGrant, b).full_composition = 0
    r = _admit("agent-a2l-c", h, ow, ar)
    assert r.status_code == 403 and "要件缺损" in r.text


# ---------------------------------------------------------------- A-3

def test_a3_unsigned_layer_and_proxy_sign_rejected():
    """A-3：登记面未签/短签（代签熔断）即拒；存量未签层下游必拒。"""
    uname, h = _auth()
    ow, ar = _gates(uname, h)
    a = _register("agent-a3-a", uname, h)
    r0 = _subgrant(a, "agent-a3-b0", uname, h, signature="")
    assert r0.status_code == 403 and "SIGNATURE_INVALID" in r0.text
    assert _no_active_grant("agent-a3-b0")
    b = _subgrant(a, "agent-a3-b", uname, h).json()["data"]["grant_id"]
    _subgrant(b, "agent-a3-c", uname, h)
    with get_sessionmaker().begin() as s:  # 模拟存量未签层
        s.get(M.AuthGrant, b).signature = ""
    r = _admit("agent-a3-c", h, ow, ar)
    assert r.status_code == 403 and "要件缺损" in r.text


# ---------------------------------------------------------------- N-1

def test_n1_revoked_upstream_downstream_old_session_denied():
    """N-1（要害）：上游已撤后持下游旧会话直调 ⟹ 必拒（⛔ 因本级 active 放行）。"""
    uname, h = _auth()
    ow, ar = _gates(uname, h)
    a = _register("agent-n1-a", uname, h)
    b = _subgrant(a, "agent-n1-b", uname, h).json()["data"]["grant_id"]
    c = _subgrant(b, "agent-n1-c", uname, h).json()["data"]["grant_id"]
    r = client.post("/api/v1/cluster/grant/revoke", json={"grant_id": a}, headers=h)
    assert r.status_code == 200 and set(r.json()["data"]["cascade_revoked"]) == {b, c}
    r1 = _admit("agent-n1-c", h, ow, ar)  # 级联后：B、C 已 revoked
    assert r1.status_code == 403
    # 存量旧语义链（-366 披露）：旧码不级联年代「B、C 仍 active」在册行
    with get_sessionmaker().begin() as s:
        s.get(M.AuthGrant, b).status = "active"
        s.get(M.AuthGrant, c).status = "active"
    r2 = _admit("agent-n1-c", h, ow, ar)  # 同一旧会话再调：逐判定实查库（无准入缓存）
    assert r2.status_code == 403 and "上游已撤" in r2.text


def test_n1_other_valid_grant_of_same_agent_still_admitted():
    """修复不扩大杀伤：同主体另持全链有效首授件 ⟹ 仍准入（逐件独立核验）。"""
    uname, h = _auth()
    ow, ar = _gates(uname, h)
    a = _register("agent-n1v-a", uname, h)
    _subgrant(a, "agent-n1v-x", uname, h)
    client.post("/api/v1/cluster/grant/revoke", json={"grant_id": a}, headers=h)
    _register("agent-n1v-x", uname, h)  # 级联只及 A 之后代；同主体新首授件不受影响
    r = _admit("agent-n1v-x", h, ow, ar)
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["verdict"] == "ADMITTED" and d["chain_depth"] == 1


# ---------------------------------------------------------------- N-2

def test_n2_middle_layer_only_last_layer_denied():
    """N-2：只给中间层件、未给末层件 ⟹ 末层直调必拒（403）。"""
    uname, h = _auth()
    ow, ar = _gates(uname, h)
    a = _register("agent-n2-a", uname, h)
    _subgrant(a, "agent-n2-mid", uname, h)
    r = _admit("agent-n2-last", h, ow, ar)  # 末层主体无任何己件
    assert r.status_code == 403 and "无有效授权件" in r.text


# ---------------------------------------------------------------- N-3

def test_n3_level_empty_or_zero_rejected():
    """N-3：层级留空或填 0 ⟹ 必拒。机面层级由链位机推，调用方无注入面；
    等价机验——五阶形态 asset_order 填 0（400）/留空（422）皆拒。"""
    uname, h = _auth()
    a = _register("agent-n3-a", uname, h)
    r0 = _subgrant(a, "agent-n3-b0", uname, h, asset_order=0)
    assert r0.status_code == 400 and "五阶" in r0.text
    assert _no_active_grant("agent-n3-b0")
    p = {"parent_grant_id": a, "subject_agent": "agent-n3-b1",
         "scene_constraint": "场景：转授", "full_composition": True,
         "legal_signer": uname,  # K1FIX-R1裁定一：原"法律主体-测试"属待封之代签名，对齐本人语义
         "signature": _SIGN}  # 无 asset_order
    r1 = client.post("/api/v1/cluster/grant/subgrant", json=p, headers=h)
    assert r1.status_code == 422
    r2 = client.post("/api/v1/cluster/grant/register", json={
        "subject_agent": "agent-n3-c", "scene_constraint": "场景：首授",
        "asset_order": 0, "full_composition": True,
        "legal_signer": uname,  # K1FIX-R1裁定一：原"法律主体-测试"属待封之代签名，对齐本人语义
        "signature": _SIGN}, headers=h)
    assert r2.status_code == 400 and "五阶" in r2.text


# ---------------------------------------------------------------- N-4

def test_n4_one_instrument_one_level():
    """N-4：同一件号不可重签于不同层级——件号服务端生成、主键唯一、单一链位；
    对已撤件再转授/重签 404 同码（同号换层之机面入口不存在）。"""
    uname, h = _auth()
    a = _register("agent-n4-a", uname, h)
    b1 = _subgrant(a, "agent-n4-b1", uname, h).json()["data"]
    b2 = _subgrant(a, "agent-n4-b2", uname, h).json()["data"]
    assert b1["grant_id"] != b2["grant_id"]  # 每次签发皆新件号
    assert b1["chain_depth"] == 2 and b2["chain_depth"] == 2  # 一件一层
    with get_sessionmaker().begin() as s:
        assert s.query(M.AuthGrant).filter_by(grant_id=b1["grant_id"]).count() == 1
        assert s.get(M.AuthGrant, b1["grant_id"]).parent_grant_id == a
    client.post("/api/v1/cluster/grant/revoke",
                json={"grant_id": b1["grant_id"]}, headers=h)
    r = _subgrant(b1["grant_id"], "agent-n4-c", uname, h)  # 对已撤件「重签续用」⟹ 404 同码
    assert r.status_code == 404 and "parent_grant_id 不存在" in r.text


# -------------------------------------------------- 转授登记面全链上溯

def test_subgrant_grandfather_revoked_blocked_404():
    """转授登记面全链上溯：祖父层已撤（存量旧语义链）⟹ 新转授 404 同码。"""
    uname, h = _auth()
    a = _register("agent-sg-a", uname, h)
    b = _subgrant(a, "agent-sg-b", uname, h).json()["data"]["grant_id"]
    client.post("/api/v1/cluster/grant/revoke", json={"grant_id": a}, headers=h)
    with get_sessionmaker().begin() as s:  # 模拟存量「B 仍 active」行
        s.get(M.AuthGrant, b).status = "active"
    r = _subgrant(b, "agent-sg-c", uname, h)
    assert r.status_code == 404 and "parent_grant_id 不存在" in r.text
