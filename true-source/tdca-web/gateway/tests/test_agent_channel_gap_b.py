# -*- coding: utf-8 -*-
"""通道对外补齐 B 测试（转正令牌；L1SI166-CHANNEL-GAP-001 项 B ＋ 收窄附页照办）。

覆盖：
  B-1  签发正例：四要件齐＋③④过＋物绑定在册沙盒签批记录 → 201；值一次性回显；
       库内只存指纹（无值列）；NCA 落链
  B-2  匿名 401／非本人 403（人类签名权不可绕）
  B-3  四要件逐项缺 → 400 点名；人≠会话主体 → 400
  B-4  ④未过（无沙盒签批记录）→ 403；物≠在册 result_ref → 400
  B-5  ③未过（有④无③，直接写闸步表模拟异常态）→ 403 出盒判据未达
  B-6  签发即轮换：再签 → 旧 active revoked
  B-7  验伪：active → valid；乱值 → invalid（fail-closed）；revoked → invalid
  B-8  吊销即时：revoke → 验伪 invalid；重复吊销 → 409；非本人吊销 → 403
"""
import hashlib

import pytest
from fastapi.testclient import TestClient

import agent_channel_promo_ops
from agent_channel_ops import CONTRACT_VERSION, _REGISTERED_PACKAGE_HASHES_16
from app import app
from db import get_session
from db import models as M

client = TestClient(app)

_PW = "GapB-2026"
_SEQ = {"n": 0}
_GOOD_HASH = _REGISTERED_PACKAGE_HASHES_16[0]


@pytest.fixture(autouse=True)
def _fresh():
    import api_v1
    api_v1._register_hits.clear()
    api_v1._login_hits.clear()
    agent_channel_promo_ops._verify_hits.clear()
    yield
    agent_channel_promo_ops._verify_hits.clear()


def _auth() -> tuple[str, dict]:
    _SEQ["n"] += 1
    name = f"gb{_SEQ['n']:03d}"
    r = client.post("/api/v1/auth/register",
                    json={"username": name, "password": _PW,
                          "agree_contract": True, "contract_version": "V1.0",
                          "anchor_kind": "notifier", "anchor_evidence_ref": "t"})
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/auth/login", json={"username": name, "password": _PW})
    assert r.status_code == 200, r.text[:300]
    with get_session() as s:   # 补锚（等价核验落点，同 b3 惯例）
        a = s.get(M.UserAnchor, name)
        a.tier_state = "已补"
        a.verified_at = "2026-10-20T00:00:00Z"
        a.verifier = "test-fixture"
        s.commit()
    return name, {"Authorization": r.json()["data"]["token"]}


def _register(hdr: dict) -> str:
    r = client.post("/api/v1/agent-channel/register",
                    json={"channel_type": "ANCHOR",
                          "device": "B路设备-x", "compute": "B路算力-x",
                          "protocol": "B路协议-x", "role": "B路角色-x",
                          "knowledge": "B路知识-x", "permission_ttl": "B路权限时效-x",
                          "root_token_ref": "root-token://gapb/1"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    reg_no = r.json()["data"]["reg_no"]
    # 对外补齐 C（L1SI166-CHANNEL-GAP-001 项 C）：进沙盒须先押付有效保金——登记即
    # 代押测试保金，使后续沙盒步可达（阈值 1 MOU，见 conftest 配置）。
    r = client.post(f"/api/v1/agent-channel/{reg_no}/deposits",
                    json={"amount_mou": 5, "mou_ref": "mou://test/x"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    return reg_no


def _chain_to_sandbox(hdr: dict, reg_no: str) -> str:
    """①②③④ 走通，返回在册沙盒签批记录引用（闸步表 sandbox 行 result_ref）。"""
    r = client.post("/api/v1/agent-channel/protocol-load",
                    json={"reg_no": reg_no, "contract_version": CONTRACT_VERSION,
                          "package_sha256_16": _GOOD_HASH}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/ns-review",
                    json={"reg_no": reg_no, "boundary_ref": "nsfl://gapb/1",
                          "adversarial_set_ref": "nsfl://gapb/adv1",
                          "scene_scope": "scene://gapb/demo"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    run_ref = "run://gapb/0001"
    r = client.post("/api/v1/agent-channel/sandbox",
                    json={"reg_no": reg_no, "sea_elements_ref": "sea://gapb/1",
                          "sandbox_run_ref": run_ref, "result": "passed"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    return run_ref


def _four(run_ref: str, who: str, **kw) -> dict:
    body = {"approver": who, "approved_at": "2026-10-23T00:00:00Z",
            "sandbox_approval_ref": run_ref,
            "approval_intent": "签批意旨：出盒转正（测试）"}
    body.update(kw)
    return body


# ---------------------------------------------------------------- B-1 正例
def test_issue_positive_once_echo_fingerprint_only():
    who, hdr = _auth()
    reg_no = _register(hdr)
    run_ref = _chain_to_sandbox(hdr, reg_no)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                    json=_four(run_ref, who), headers=hdr)
    assert r.status_code == 201, r.text[:400]
    d = r.json()["data"]
    assert d["issued"] is True and d["status"] == "active"
    assert d["token_no"].startswith("SPT-")
    assert d["token_value"].startswith("TDCA-PRT-")
    assert d["nca_ref"]
    with get_session() as s:
        row = s.get(M.SiteAgentPromoToken, d["token_no"])
        assert row is not None
        assert row.token_fingerprint == hashlib.sha256(
            d["token_value"].encode()).hexdigest()
        assert "token_value" not in row.__table__.columns          # 值不入库
        assert row.approver == who and row.sandbox_approval_ref == run_ref
        nca = s.get(M.NcaChain, d["nca_ref"])
        assert nca is not None and nca.action == "AGENT_CHANNEL_PROMO_TOKEN_ISSUE"


# ---------------------------------------------------------------- B-2 权限
def test_issue_anon_401_and_non_owner_403():
    who, hdr = _auth()
    reg_no = _register(hdr)
    run_ref = _chain_to_sandbox(hdr, reg_no)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                    json=_four(run_ref, who))
    assert r.status_code == 401
    _, hdr2 = _auth()
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                    json=_four(run_ref, who), headers=hdr2)
    assert r.status_code == 403 and "人类签名权" in r.text


# ---------------------------------------------------------------- B-3 四要件
def test_issue_four_elements_itemized():
    who, hdr = _auth()
    reg_no = _register(hdr)
    run_ref = _chain_to_sandbox(hdr, reg_no)
    for field in ("approver", "approved_at", "sandbox_approval_ref", "approval_intent"):
        body = _four(run_ref, who)
        body[field] = ""
        r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                        json=body, headers=hdr)
        assert r.status_code == 400, (field, r.text[:300])
        assert "四要件不齐" in r.text
    # 人≠会话主体
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                    json=_four(run_ref, "别人"), headers=hdr)
    assert r.status_code == 400 and "单一责任锚点" in r.text


# ---------------------------------------------------------------- B-4 物与④
def test_issue_requires_registered_sandbox_approval():
    who, hdr = _auth()
    reg_no = _register(hdr)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                    json=_four("run://gapb/none", who), headers=hdr)
    assert r.status_code == 403 and "沙盒签批记录" in r.text
    run_ref = _chain_to_sandbox(hdr, reg_no)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                    json=_four("run://gapb/WRONG", who), headers=hdr)
    assert r.status_code == 400 and "result_ref" in r.text


# ---------------------------------------------------------------- B-5 出盒判据
def test_issue_exit_criteria_ns_review_required():
    who, hdr = _auth()
    reg_no = _register(hdr)
    # 直接落④ passed 而无③（异常态模拟：闸步表白写）
    from agent_channel_ops import _admission_set
    _admission_set(reg_no, "sandbox", "passed", result_ref="run://gapb/manual")
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                    json=_four("run://gapb/manual", who), headers=hdr)
    assert r.status_code == 403 and "出盒判据未达" in r.text


# ---------------------------------------------------------------- B-6 轮换
def test_issue_rotates_old_active():
    who, hdr = _auth()
    reg_no = _register(hdr)
    run_ref = _chain_to_sandbox(hdr, reg_no)
    r1 = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                     json=_four(run_ref, who), headers=hdr)
    t1 = r1.json()["data"]["token_no"]
    r2 = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                     json=_four(run_ref, who), headers=hdr)
    assert r2.status_code == 201, r2.text[:300]
    assert r2.json()["data"]["rotated"] == [t1]
    with get_session() as s:
        assert s.get(M.SiteAgentPromoToken, t1).status == "revoked"


# ---------------------------------------------------------------- B-7 验伪
def test_verify_active_invalid_revoked():
    who, hdr = _auth()
    reg_no = _register(hdr)
    run_ref = _chain_to_sandbox(hdr, reg_no)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                    json=_four(run_ref, who), headers=hdr)
    tok = r.json()["data"]["token_value"]
    v = client.post("/api/v1/agent-channel/promotion-token/verify",
                    json={"token_value": tok}, headers=hdr)
    assert v.status_code == 200 and v.json()["data"]["valid"] is True
    v = client.post("/api/v1/agent-channel/promotion-token/verify",
                    json={"token_value": "TDCA-PRT-garbage"}, headers=hdr)
    assert v.json()["data"]["valid"] is False
    # 吊销后 invalid
    token_no = r.json()["data"]["token_no"]
    client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token/{token_no}/revoke",
                headers=hdr)
    v = client.post("/api/v1/agent-channel/promotion-token/verify",
                    json={"token_value": tok}, headers=hdr)
    assert v.json()["data"]["valid"] is False
    assert v.json()["data"]["status"] == "revoked"


# ---------------------------------------------------------------- B-8 吊销
def test_revoke_immediate_and_race():
    who, hdr = _auth()
    reg_no = _register(hdr)
    run_ref = _chain_to_sandbox(hdr, reg_no)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                    json=_four(run_ref, who), headers=hdr)
    token_no = r.json()["data"]["token_no"]
    _, hdr2 = _auth()
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token/{token_no}/revoke",
                    headers=hdr2)
    assert r.status_code == 403
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token/{token_no}/revoke",
                    headers=hdr)
    assert r.status_code == 200 and r.json()["data"]["revoked"] is True
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token/{token_no}/revoke",
                    headers=hdr)
    assert r.status_code == 409
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token/SPT-NO0000000000/revoke",
                    headers=hdr)
    assert r.status_code == 404
