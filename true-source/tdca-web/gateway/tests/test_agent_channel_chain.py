# -*- coding: utf-8 -*-
"""CHANNEL-CHAIN-001 通道域转授链改域测试（site_agent_grant／agent_channel_ops.py）。

改域来源：集群域（auth_grants／cluster_ops.py）CHAIN-ASSERT-SUP-001 已修六缺口——
  ① issue_grant 父件校验只验直接上级 → 全链上溯（任一级祖先非 active ⟹ 404）
  ② _active_grant（execute 准入）本级 active 即放行 → 须至少一件全链有效
  ③ 无撤销端点 → 新建 POST /{reg_no}/grants/{grant_no}/revoke＋BFS 级联 revoked
  ④ 已注销上级之转授 403 GRANT_PARENT_INVALID → 404 同码同文案（GSEQ-8225）
  ⑤ 无链深上限 → 64 层防御上限（本域层级＝tiers_covered 五阶清单＋链深，⛔ 非 int）
  ⑥ 无越权校验 → 转授不超出原授权（R1 场景／R2 五阶 ⊆ 上级，越项点名 400）

12 断言：A-1 三层链可建／A-2 逐层须件／A-3 逐层须签／A-4 任一环失效下游全失效
（新端点实证）／A-5 已注销上级转授 404 同码／A-6 超 64 层明确报错／A-7 转授不超
原授权／A-8 谱系可上溯；N-1 上游已撤持下游旧会话必拒（要害——存量旧语义行以
DB 直改模拟，等价 -367 集群域形态）／N-2 只给中间层件调末层拒／N-3 层级留空拒
（本域＝五阶清单缺失）／N-4 对已撤件再转授 404 同码。

修复前实录（等价 -367「修复前 4 败 6 过」形态）：A-4／A-5／A-6／A-7／N-1 五测
在旧码上必败（无撤销端点／403 非 404／无上限／无越权校验／准入不上溯）；
A-1／A-2／A-3／N-2／N-3 本域在役本已成立（照令照实核，⛔ 编造修复前失败）。
"""
import pytest
from fastapi.testclient import TestClient

import agent_channel_ops
from agent_channel_ops import CONTRACT_VERSION, _REGISTERED_PACKAGE_HASHES_16
from app import app
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "ChainCh-2026"
_SEQ = {"n": 0}
_GOOD_HASH = _REGISTERED_PACKAGE_HASHES_16[0]

_SCENE = "scene://chain/demo"
_GOOD_GRANT = {"scene_constraint": _SCENE,
               "tiers_covered": "一阶,三阶",
               "full_composition": True,
               "legal_signer": "测试签署主体-链",
               "signature_ref": "nca://sig/chain-001"}


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    import api_v1
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth() -> tuple[str, dict]:
    _SEQ["n"] += 1
    name = f"chch{_SEQ['n']:03d}"
    r = client.post("/api/v1/auth/register", json={
        "username": name, "password": _PW, "agree_contract": True,
        "contract_version": "V1.0", "anchor_kind": "notifier",
        "anchor_evidence_ref": "test-anchor-ref"})
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/auth/login", json={"username": name, "password": _PW})
    assert r.status_code == 200, r.text[:300]
    with get_session() as s:
        a = s.get(M.UserAnchor, name)
        a.tier_state = "已补"
        a.verified_at = "2026-11-16T00:00:00Z"
        a.verifier = "test-fixture"
        s.commit()
    return name, {"Authorization": r.json()["data"]["token"]}


_REG_SEQ = {"n": 0}


def _register(hdr: dict) -> str:
    _REG_SEQ["n"] += 1
    tag = f"chch-{_REG_SEQ['n']:03d}"
    r = client.post("/api/v1/agent-channel/register",
                    json={"channel_type": "ANCHOR",
                          "device": f"测试设备-{tag}", "compute": "测试算力-x",
                          "protocol": "测试协议-x", "role": "测试角色-x",
                          "knowledge": "测试知识-x", "permission_ttl": "测试权限时效-x",
                          "root_token_ref": "root-token://test/1"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    reg_no = r.json()["data"]["reg_no"]
    r = client.post(f"/api/v1/agent-channel/{reg_no}/deposits",
                    json={"amount_mou": 5, "mou_ref": "mou://test/x"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    return reg_no


def _full_chain(hdr: dict | None = None) -> tuple[str, dict]:
    """①②③④ 全过链（照 test_agent_channel_b3 同口径）。"""
    if hdr is None:
        _, hdr = _auth()
    reg_no = _register(hdr)
    r = client.post("/api/v1/agent-channel/protocol-load",
                    json={"reg_no": reg_no, "contract_version": CONTRACT_VERSION,
                          "package_sha256_16": _GOOD_HASH}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/ns-review",
                    json={"reg_no": reg_no, "boundary_ref": "nsfl://boundary/c-001",
                          "adversarial_set_ref": "nsfl://adv/c-001",
                          "scene_scope": _SCENE}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/sandbox",
                    json={"reg_no": reg_no, "sea_elements_ref": "sea://c/001",
                          "sandbox_run_ref": "run://c/001", "result": "passed"},
                    headers=hdr)
    assert r.status_code == 200, r.text[:300]
    return reg_no, hdr


def _issue(reg_no: str, hdr: dict, **over) -> object:
    body = dict(_GOOD_GRANT)
    body.update(over)
    return client.post(f"/api/v1/agent-channel/{reg_no}/grants", json=body, headers=hdr)


def _sub(reg_no: str, hdr: dict, parent: str, **over) -> object:
    body = dict(_GOOD_GRANT)
    body.update(over)
    body["parent_grant_no"] = parent
    return client.post(f"/api/v1/agent-channel/{reg_no}/grants", json=body, headers=hdr)


def _revoke(reg_no: str, grant_no: str, hdr: dict) -> object:
    return client.post(f"/api/v1/agent-channel/{reg_no}/grants/{grant_no}/revoke",
                       headers=hdr)


def _exec(reg_no: str, hdr: dict, scene: str = _SCENE) -> object:
    return client.post("/api/v1/agent-channel/execute",
                       json={"reg_no": reg_no, "scene": scene,
                             "action": "invoke://chain/demo", "units": 1}, headers=hdr)


def _chain_walk(grant_no: str) -> list:
    """谱系上溯（A-8）：DB 直读 parent_grant_no 至首授。"""
    out = []
    gid = grant_no
    for _ in range(64):
        with get_session() as s:
            row = s.get(M.SiteAgentGrant, gid) if gid else None
        if row is None:
            break
        out.append(row.grant_no)
        gid = row.parent_grant_no
        if gid is None:
            break
    return out


# ---------------------------------------------------------------- A-1/A-8
def test_a1_three_layer_chain_and_lineage():
    """A-1 三层链可建（parent_grant_no 逐层挂接）＋ A-8 谱系可上溯。"""
    _, hdr = _auth()
    reg_no = _register(hdr)
    r1 = _issue(reg_no, hdr)
    assert r1.status_code == 201, r1.text[:300]
    g1 = r1.json()["data"]["grant_no"]
    r2 = _sub(reg_no, hdr, g1)
    assert r2.status_code == 201, r2.text[:300]
    g2 = r2.json()["data"]["grant_no"]
    r3 = _sub(reg_no, hdr, g2)
    assert r3.status_code == 201, r3.text[:300]
    g3 = r3.json()["data"]["grant_no"]
    chain = _chain_walk(g3)
    assert chain == [g3, g2, g1], chain


# ---------------------------------------------------------------- A-2
def test_a2_requirement_missing_at_any_layer_blocks():
    """A-2 逐层须件：转授层缺任一要件即拒（本域在役本已成立，照实核）。"""
    _, hdr = _auth()
    reg_no = _register(hdr)
    g1 = _issue(reg_no, hdr).json()["data"]["grant_no"]
    cases = [
        ("scene_constraint", "", "R1"),
        ("tiers_covered", "", "R2"),
        ("tiers_covered", "九阶", "R2"),
        ("full_composition", False, "R3"),
        ("legal_signer", "", "R4"),
        ("signature_ref", "", "R4"),
    ]
    for k, v, kw in cases:
        r = _sub(reg_no, hdr, g1, **{k: v})
        assert r.status_code == 400 and kw in r.text, (k, r.status_code, r.text[:200])


# ---------------------------------------------------------------- A-3
def test_a3_unsigned_layer_rejected():
    """A-3 逐层须签：签名事件引用缺失即拒（本域在役本已成立，照实核）。"""
    _, hdr = _auth()
    reg_no = _register(hdr)
    g1 = _issue(reg_no, hdr).json()["data"]["grant_no"]
    r = _sub(reg_no, hdr, g1, signature_ref="")
    assert r.status_code == 400 and "R4" in r.text


# ---------------------------------------------------------------- A-4（新端点实证）
def test_a4_revoke_cascades_and_downstream_dead():
    """A-4 任一环失效 ⟹ 下游全失效：撤首授级联全下游，execute 必拒。"""
    reg_no, hdr = _full_chain()
    g1 = _issue(reg_no, hdr).json()["data"]["grant_no"]
    g2 = _sub(reg_no, hdr, g1).json()["data"]["grant_no"]
    g3 = _sub(reg_no, hdr, g2).json()["data"]["grant_no"]
    r = _exec(reg_no, hdr)   # 正向对照：修复后全链有效
    assert r.status_code == 200, r.text[:300]
    r = _revoke(reg_no, g1, hdr)
    assert r.status_code == 200, r.text[:300]
    assert set(r.json()["data"]["cascade_revoked"]) == {g2, g3}
    with get_session() as s:
        for g in (g1, g2, g3):
            assert s.get(M.SiteAgentGrant, g).status == "revoked"
    r = _exec(reg_no, hdr)   # 下游全失效：旧会话再调必拒
    assert r.status_code == 403, r.text[:300]
    # 幂等：重复撤不报错
    r = _revoke(reg_no, g1, hdr)
    assert r.status_code == 200 and r.json()["data"]["cascade_revoked"] == []


# ---------------------------------------------------------------- A-5/N-4
def test_a5_revoked_or_missing_parent_subgrant_404_same_code():
    """A-5 已注销上级之转授 404 同码同文案；不存在上级同码（N-4 对已撤件再转授）。"""
    _, hdr = _auth()
    reg_no = _register(hdr)
    g1 = _issue(reg_no, hdr).json()["data"]["grant_no"]
    g2 = _sub(reg_no, hdr, g1).json()["data"]["grant_no"]
    _revoke(reg_no, g1, hdr)
    r1 = _sub(reg_no, hdr, g2)                       # 对已撤层再转授
    r2 = _sub(reg_no, hdr, "SGR-NOT-EXIST-000000")   # 不存在上级
    assert r1.status_code == 404 and "parent_grant_no 不存在" in r1.text
    assert r2.status_code == 404 and "parent_grant_no 不存在" in r2.text


# ---------------------------------------------------------------- A-6
def test_a6_chain_depth_64_limit():
    """A-6 链深 64 层防御上限：第 65 层转授明确报错（文案含上限值）。"""
    _, hdr = _auth()
    reg_no = _register(hdr)
    gid = _issue(reg_no, hdr).json()["data"]["grant_no"]
    for _ in range(63):   # 建至 64 层
        r = _sub(reg_no, hdr, gid)
        assert r.status_code == 201, r.text[:300]
        gid = r.json()["data"]["grant_no"]
    r = _sub(reg_no, hdr, gid)   # 第 65 层
    assert r.status_code == 400 and "CHAIN_DEPTH_LIMIT" in r.text and "64" in r.text


# ---------------------------------------------------------------- A-7
def test_a7_subgrant_scope_subset_of_parent():
    """A-7 转授不超出原授权：R1 场景／R2 五阶越上级者拒，并指明超出哪一项。"""
    _, hdr = _auth()
    reg_no = _register(hdr)
    g1 = _issue(reg_no, hdr,
                scene_constraint="场景甲,场景乙", tiers_covered="一阶,三阶"
                ).json()["data"]["grant_no"]
    r = _sub(reg_no, hdr, g1, scene_constraint="场景丙")
    assert r.status_code == 400 and "SUPERSEDE_SCOPE" in r.text and "场景越界：场景丙" in r.text
    r = _sub(reg_no, hdr, g1, tiers_covered="一阶,三阶,五阶")
    assert r.status_code == 400 and "五阶越界：五阶" in r.text
    r = _sub(reg_no, hdr, g1, scene_constraint="场景乙",
             tiers_covered="三阶")   # 正向：⊆ 上级
    assert r.status_code == 201, r.text[:300]


# ---------------------------------------------------------------- N-1（要害）
def test_n1_legacy_upstream_revoked_old_session_denied():
    """N-1 要害：存量旧语义链（上级已撤而下级仍 active）持下游旧会话执行必拒。

    存量行以 DB 直改模拟（等价 -367 集群域形态：修复前无级联语义年代之在册行）。
    """
    reg_no, hdr = _full_chain()
    g1 = _issue(reg_no, hdr).json()["data"]["grant_no"]
    g2 = _sub(reg_no, hdr, g1).json()["data"]["grant_no"]
    g3 = _sub(reg_no, hdr, g2).json()["data"]["grant_no"]
    r = _exec(reg_no, hdr)
    assert r.status_code == 200, r.text[:300]
    with get_sessionmaker().begin() as s:   # 模拟存量旧语义行：仅撤上级，下游仍 active
        s.get(M.SiteAgentGrant, g1).status = "revoked"
    r = _exec(reg_no, hdr)   # 同一旧会话再调：⛔ 因本级 active 放行
    assert r.status_code == 403
    assert "GRANT_CHAIN_BROKEN" in r.text or "上游已撤" in r.text


# ---------------------------------------------------------------- N-2/N-3（在役本已成立）
def test_n2_middle_layer_only_last_layer_denied():
    """N-2 只给中间层件、末层无己件 ⟹ 拒（本域 execute 仅验本级件，在役本已成立）。"""
    reg_no, hdr = _full_chain()
    g1 = _issue(reg_no, hdr).json()["data"]["grant_no"]
    _sub(reg_no, hdr, g1)   # 仅链上有件；本级（reg_no 直持件）无
    with get_sessionmaker().begin() as s:
        s.query(M.SiteAgentGrant).filter_by(reg_no=reg_no).delete()
    r = _exec(reg_no, hdr)
    assert r.status_code == 403 and "GRANT_REQUIRED" in r.text


def test_n3_level_empty_rejected():
    """N-3 层级留空拒（本域层级＝tiers_covered 五阶清单，缺失即 400）。"""
    _, hdr = _auth()
    reg_no = _register(hdr)
    g1 = _issue(reg_no, hdr).json()["data"]["grant_no"]
    r = _sub(reg_no, hdr, g1, tiers_covered="")
    assert r.status_code == 400 and "R2" in r.text
