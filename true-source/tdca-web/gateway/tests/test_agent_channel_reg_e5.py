# -*- coding: utf-8 -*-
"""块 E（L1SI167-AGENT-REG-UI-001 ＋ AMEND-001）智能体自助登记入口测试。

覆盖回报面：
  E-1  GET …/register → 405（⛔ 不再回 reg_no:"register" 幽灵态）
  E-2  六要素逐项缺项点名／锚定项缺项点名／派生登记缺来源谱系
  E-3  ANCHOR 正例（201＋登记号＋NCA）、幂等复用原号、频控 429
  E-5  GUEST 路：合规前置校验逐项（缺 agent_card／声明／联系方式 → 400 点名）、
       通过 ⟹ 发号（channel_type=GUEST）＋校验存证时间戳早于发号时间戳、
       GUEST 幂等（同一外部声明＋同一表达形式复用原号）、GUEST 频控严于 ANCHOR、
       显著标识三层（gate 调用面 channel_type＋「创建者未在本网注册」／
       公开面 channel_type＋外部创建者标签／审计 NCA precheck 行）。
"""
import pytest
from fastapi.testclient import TestClient

import agent_channel_ops
from app import app
from db import get_session
from db import models as M

client = TestClient(app)

_PW = "E5chan-2026"
_SEQ = {"n": 0}


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    agent_channel_ops._chreg_hits.clear()
    import api_v1
    api_v1._register_hits.clear()   # 开关新测增 _auth 调用：auth 注册频控逐测同清
    yield
    agent_channel_ops._chreg_hits.clear()
    api_v1._register_hits.clear()


def _auth(uname: str | None = None) -> dict:
    if uname is None:
        _SEQ["n"] += 1
        uname = f"e5u{_SEQ['n']:03d}"
    r = client.post("/api/v1/auth/register",
                    json={"username": uname, "password": _PW,
                          "agree_contract": True, "contract_version": "V1.0"})
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:300]
    return {"Authorization": r.json()["data"]["token"]}


def _six(tag: str) -> dict:
    return {"device": f"设备-{tag}", "compute": f"算力-{tag}",
            "protocol": f"协议-{tag}", "role": f"角色-{tag}",
            "knowledge": f"知识-{tag}", "permission_ttl": f"权限时效-{tag}"}


def _anchor_body(tag: str, **kw) -> dict:
    body = {"channel_type": "ANCHOR", **_six(tag),
            "root_token_ref": "root-token://e5/1"}
    body.update(kw)
    return body


def _guest_body(tag: str, **kw) -> dict:
    body = {"channel_type": "GUEST", **_six(tag),
            "agent_card": {"name": f"guest-agent-{tag}", "version": "1.0"},
            "ext_declaration": f"外部创建者主体声明-{tag}",
            "ext_contact": f"guest-{tag}@example.org"}
    body.update(kw)
    return body


# ---------------------------------------------------------------- E-1 405
def test_get_register_is_405_not_ghost():
    r = client.get("/api/v1/agent-channel/register")
    assert r.status_code == 405
    d = r.json()
    assert d["detail"] == "Method Not Allowed"
    assert d["code"] == "TDCA-E-SYS-SYS-001"
    # 原幽灵态不再现：响应不再是 200＋ghost 形态
    assert "ghost" not in d


# ---------------------------------------------------------------- E-2 缺项点名
def test_missing_fields_itemized():
    hdr = _auth()
    body = _anchor_body("miss")
    del body["device"]
    del body["role"]
    r = client.post("/api/v1/agent-channel/register", json=body, headers=hdr)
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert "设备" in detail and "角色" in detail
    assert "算力" not in detail   # 已填项不点名


# ---------------------------------------------------------------- E-3 ANCHOR 正例＋幂等
def test_anchor_positive_and_idempotent_reuse():
    hdr = _auth()
    body = _anchor_body("idem")
    r = client.post("/api/v1/agent-channel/register", json=body, headers=hdr)
    assert r.status_code == 201
    d1 = r.json()["data"]
    assert d1["channel_type"] == "ANCHOR" and d1["reused"] is False
    assert d1["reg_no"].startswith("SAR-")
    assert d1["nca_ref"] and d1["idem_key"]
    # 幂等：同一锚定账户＋同一表达形式再提交 ⟹ 复用原登记号（⛔ 重复建档）
    r = client.post("/api/v1/agent-channel/register", json=body, headers=hdr)
    assert r.status_code == 201
    d2 = r.json()["data"]
    assert d2["reused"] is True and d2["reg_no"] == d1["reg_no"]
    with get_session() as s:
        n = s.query(M.SiteAgentRegistry).filter_by(idem_key=d1["idem_key"]).count()
    assert n == 1
    # 表达形式不同（设备字段变）⟹ 新号
    r = client.post("/api/v1/agent-channel/register",
                    json=_anchor_body("idem2"), headers=hdr)
    assert r.json()["data"]["reg_no"] != d1["reg_no"]


# ---------------------------------------------------------------- E-5 GUEST 正例＋时序
def test_guest_positive_precheck_before_issue():
    body = _guest_body("g1")
    r = client.post("/api/v1/agent-channel/register", json=body)
    assert r.status_code == 201, r.text[:300]
    d = r.json()["data"]
    assert d["channel_type"] == "GUEST" and d["reused"] is False
    assert d["owner"] is None
    gp = d["guest_precheck"]
    assert gp["precheck_nca_ref"] and gp["precheck_at"]
    assert gp["precheck_at"] <= gp["registered_at"]   # 校验在前、发号在后
    # NCA 链实读：校验行存在且时间戳不晚于登记行
    with get_session() as s:
        pre = s.get(M.NcaChain, gp["precheck_nca_ref"])
        reg = s.get(M.NcaChain, d["nca_ref"])
        row = s.get(M.SiteAgentRegistry, d["reg_no"])
    assert pre is not None and pre.action == "AGENT_CHANNEL_GUEST_PRECHECK"
    assert reg is not None and reg.action == "AGENT_CHANNEL_REGISTER"
    assert pre.ts <= reg.ts
    assert row.channel_type == "GUEST"
    assert row.ext_declaration and row.ext_contact   # 入库（⛔ 不上公开面）
    # 响应不泄露声明／联系方式明文
    assert "ext_declaration" not in d and "ext_contact" not in d


# ---------------------------------------------------------------- E-5 校验逐项
def test_guest_precheck_itemized_rejections():
    base = _guest_body("c0")
    cases = [
        ("无 agent_card", {k: v for k, v in base.items() if k != "agent_card"}, "agent_card"),
        ("agent_card 非对象", {**base, "agent_card": "not-a-dict"}, "agent_card"),
        ("缺主体声明", {k: v for k, v in base.items() if k != "ext_declaration"}, "主体声明"),
        ("缺联系方式", {k: v for k, v in base.items() if k != "ext_contact"}, "联系方式"),
    ]
    # 校验不过 ⟹ 不落号、不落幽灵态（前后行数不变）
    with get_session() as s:
        before = s.query(M.SiteAgentRegistry).count()
    for name, body, kw in cases:
        r = client.post("/api/v1/agent-channel/register", json=body)
        assert r.status_code == 400, f"{name}: {r.text[:200]}"
        assert kw in r.json()["detail"], f"{name}: {r.json()}"
    with get_session() as s:
        assert s.query(M.SiteAgentRegistry).count() == before


# ---------------------------------------------------------------- E-5 GUEST 幂等
def test_guest_idempotent_by_declaration_and_expression():
    body = _guest_body("g2")
    r1 = client.post("/api/v1/agent-channel/register", json=body)
    r2 = client.post("/api/v1/agent-channel/register", json=body)
    assert r1.status_code == 201 and r2.status_code == 201
    assert r2.json()["data"]["reused"] is True
    assert r2.json()["data"]["reg_no"] == r1.json()["data"]["reg_no"]
    # 声明不同 ⟹ 新号
    r3 = client.post("/api/v1/agent-channel/register", json=_guest_body("g3"))
    assert r3.json()["data"]["reg_no"] != r1.json()["data"]["reg_no"]


# ---------------------------------------------------------------- 频控（GUEST 严于 ANCHOR）
def test_rate_limit_guest_stricter_than_anchor():
    hdr = _auth()
    # ANCHOR 阈 30/h：第 31 次触限
    for i in range(30):
        r = client.post("/api/v1/agent-channel/register",
                        json=_anchor_body(f"rl-a{i}"), headers=hdr)
        assert r.status_code == 201
    r = client.post("/api/v1/agent-channel/register",
                    json=_anchor_body("rl-a31"), headers=hdr)
    assert r.status_code == 429
    # GUEST 阈 5/h：第 6 次触限（匿名路，计数独立于 ANCHOR）
    for i in range(5):
        r = client.post("/api/v1/agent-channel/register", json=_guest_body(f"rl-g{i}"))
        assert r.status_code == 201
    r = client.post("/api/v1/agent-channel/register", json=_guest_body("rl-g6"))
    assert r.status_code == 429
    assert r.json()["code"] == "TDCA-E-RES-RES-001"


# ---------------------------------------------------------------- E-5-3 显著标识三层
def test_guest_signage_three_layers():
    hdr = _auth()
    d = client.post("/api/v1/agent-channel/register",
                    json=_guest_body("sig")).json()["data"]
    reg_no = d["reg_no"]
    # ① 命名／公开面：channel_type＋外部创建者标签；⛔ 无明文声明与联系方式
    r = client.get(f"/api/v1/agent-channel/{reg_no}")
    assert r.status_code == 200
    pd = r.json()["data"]
    assert pd["channel_type"] == "GUEST"
    assert "未在本网注册" in pd["权属信息"]
    assert "guest-sig@example.org" not in str(pd)
    assert "外部创建者主体声明" not in str(pd)
    # ② 审计轨迹：NCA 校验行（action 记 GUEST 前置校验）
    with get_session() as s:
        pre = s.get(M.NcaChain, d["guest_precheck"]["precheck_nca_ref"])
    assert pre is not None and "GUEST" in pre.action
    # ③ 调用面：gate 必带 channel_type 与「创建者未在本网注册」（登录用户可查 GUEST 实况）
    r = client.get(f"/api/v1/agent-channel/gate/{reg_no}", headers=hdr)
    assert r.status_code == 200, r.text[:300]
    gd = r.json()["data"]
    assert gd["channel_type"] == "GUEST"
    assert gd["creator_marker"] == "创建者未在本网注册"
    # ANCHOR 行 gate 不带 GUEST 标识且仍 owner-only
    hdr2 = _auth()
    d2 = client.post("/api/v1/agent-channel/register",
                     json=_anchor_body("sig2"), headers=hdr2).json()["data"]
    r = client.get(f"/api/v1/agent-channel/gate/{d2['reg_no']}", headers=hdr2)
    assert r.json()["data"]["channel_type"] == "ANCHOR"
    assert "creator_marker" not in r.json()["data"]
    r = client.get(f"/api/v1/agent-channel/gate/{d2['reg_no']}", headers=hdr)
    assert r.status_code == 403   # 非登记主体本人（人类签名权不可绕）
    # 匿名 gate 仍 401（fail-closed 口径未变）
    r = client.get(f"/api/v1/agent-channel/gate/{reg_no}")
    assert r.status_code == 401


# ------------------------------------------- E-6 中间件豁免（GUEST 小门过闸证明）
# 线上 TDCA_GATEWAY_AUTH=1 时写操作 fail-closed；块 E 小门 = /agent-channel/register
# 豁免中间件（auth.py _AUTH_EXEMPT）。以下两例在启用鉴权下跑，证明豁免后行为正确：
# GUEST 匿名递件到达端点（端点内校验点名），ANCHOR 匿名被端点层 401 拦（⛔ 非中间件层）。

import os  # noqa: E402

def test_e6_middleware_exempt_guest_reaches_endpoint():
    """鉴权启用＋匿名 GUEST：非中间件 401，而是端点层 400 点名（缺六要素）。"""
    os.environ["TDCA_GATEWAY_AUTH"] = "1"
    try:
        r = client.post("/api/v1/agent-channel/register",
                        json={"channel_type": "GUEST",
                              "agent_card": {"name": "x"}, "ext_declaration": "d",
                              "ext_contact": "c@example.org"})
        assert r.status_code == 400, r.text[:300]
        assert "创世六要素不齐" in r.json()["detail"]
    finally:
        os.environ.pop("TDCA_GATEWAY_AUTH", None)


def test_e6_middleware_exempt_anchor_still_endpoint_401():
    """鉴权启用＋匿名 ANCHOR（六要素齐）：端点层 401「未登录」（端点内会话守卫，非中间件体）。"""
    os.environ["TDCA_GATEWAY_AUTH"] = "1"
    try:
        r = client.post("/api/v1/agent-channel/register",
                        json=_anchor_body("e6mw"))
        assert r.status_code == 401, r.text[:300]
        body = r.json()
        assert body.get("detail") == "未登录"          # 端点层 HTTPException 形态
        assert "error" not in body                      # ⛔ 非中间件 401 形态
    finally:
        os.environ.pop("TDCA_GATEWAY_AUTH", None)


# ------------------------------------------- GO-LIVE-001 步6b · 注册开关（默认关）
def test_reg_switch_closed_blocks_anon_but_not_session(monkeypatch):
    """开关 0（缺省）：匿名 GUEST → 403 TDCA-E-GOV-PERM-003；会话 ANCHOR 照常 201。"""
    monkeypatch.delenv("TDCA_AGENT_REG_OPEN", raising=False)   # 缺省=0（关）
    r = client.post("/api/v1/agent-channel/register", json=_guest_body("sw-closed"))
    assert r.status_code == 403, r.text[:300]
    assert "TDCA-E-GOV-PERM-003" in r.text and "通道尚未开放登记" in r.text
    # 内部账号走会话路不受开关影响
    hdr = _auth()
    r = client.post("/api/v1/agent-channel/register",
                    json=_anchor_body("sw-closed-anchor"), headers=hdr)
    assert r.status_code == 201, r.text[:300]


def test_reg_switch_open_restores_guest_then_close_again(monkeypatch):
    """开关 1：匿名 GUEST 照现有逻辑 201；改回 0 再拒（验完即改回之测试内等价）。"""
    monkeypatch.setenv("TDCA_AGENT_REG_OPEN", "1")
    r = client.post("/api/v1/agent-channel/register", json=_guest_body("sw-open"))
    assert r.status_code == 201, r.text[:300]
    assert r.json()["data"]["channel_type"] == "GUEST"
    monkeypatch.setenv("TDCA_AGENT_REG_OPEN", "0")
    r = client.post("/api/v1/agent-channel/register", json=_guest_body("sw-reclosed"))
    assert r.status_code == 403 and "TDCA-E-GOV-PERM-003" in r.text
    # 会话路两态皆通（开态已验 201 于上测试；此处验关态）
    hdr = _auth()
    r = client.post("/api/v1/agent-channel/register",
                    json=_anchor_body("sw-reclosed-anchor"), headers=hdr)
    assert r.status_code == 201, r.text[:300]
