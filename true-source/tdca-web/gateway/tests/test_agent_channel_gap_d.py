# -*- coding: utf-8 -*-
"""通道对外补齐 D 测试（履约保证保险；L1SI166-CHANNEL-GAP-001 项 D ＋ 裁定项三／五条）。

覆盖：
  D-1  保单登记正例：201；policy_no SIP- 前缀；NCA 落链
       （AGENT_CHANNEL_INSURANCE_POLICY_REGISTER）；行落库
  D-2  权限：匿名 401；非本人 403（人类签名权不可绕）
  D-3  fail-closed 入参：缺承保方/保障期 → 400；零/负保额 → 400；
       保障期止≤起 → 400
  D-4  转正双重前置 fail-closed：无令牌 → 403；有保单无令牌 → 403；
       有令牌无保单 → 403（无有效保单——拒转正）；双有 → 201 事件落 NCA
       （AGENT_CHANNEL_PROMOTED）且 ⛔ 不改 channel_type
  D-5  有效保单口径：保障期未覆盖当前时点（已期满）→ 拒转正；
       status=revoked → 拒转正（fail-closed）
  D-6  漏洞损失申报：正例 201；状态 INSURED；NCA 落链
       （AGENT_CHANNEL_INSURANCE_CLAIM）；loss_type 闭集校验 400；
       情述缺/零负额 → 400
  D-7  申报权限：匿名 401；非本人 403
"""
import pytest
from fastapi.testclient import TestClient

from agent_channel_ops import CONTRACT_VERSION, _REGISTERED_PACKAGE_HASHES_16
from app import app
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "GapD-2026"
_SEQ = {"n": 0}
_GOOD_HASH = _REGISTERED_PACKAGE_HASHES_16[0]
_PERIOD_START = "2026-01-01T00:00:00Z"
_PERIOD_END = "2027-12-31T00:00:00Z"


@pytest.fixture(autouse=True)
def _fresh():
    import api_v1
    api_v1._register_hits.clear()
    api_v1._login_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth() -> tuple[str, dict]:
    _SEQ["n"] += 1
    name = f"gd{_SEQ['n']:03d}"
    r = client.post("/api/v1/auth/register",
                    json={"username": name, "password": _PW,
                          "agree_contract": True, "contract_version": "V1.0",
                          "anchor_kind": "notifier", "anchor_evidence_ref": "t"})
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/auth/login", json={"username": name, "password": _PW})
    assert r.status_code == 200, r.text[:300]
    with get_session() as s:   # 补锚（等价核验落点，同 gap_b 惯例）
        a = s.get(M.UserAnchor, name)
        a.tier_state = "已补"
        a.verified_at = "2026-10-23T00:00:00Z"
        a.verifier = "test-fixture"
        s.commit()
    return name, {"Authorization": r.json()["data"]["token"]}


_REG_SEQ = {"n": 0}


def _register(hdr: dict) -> str:
    _REG_SEQ["n"] += 1
    tag = f"gd-{_REG_SEQ['n']:03d}"
    r = client.post("/api/v1/agent-channel/register",
                    json={"channel_type": "ANCHOR",
                          "device": f"D路设备-{tag}", "compute": "D路算力-x",
                          "protocol": "D路协议-x", "role": "D路角色-x",
                          "knowledge": "D路知识-x", "permission_ttl": "D路权限时效-x",
                          "root_token_ref": "root-token://gapd/1"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    reg_no = r.json()["data"]["reg_no"]
    # 对外补齐 C：进沙盒须先押付有效保金（阈值 1 MOU，见 conftest 配置）
    r = client.post(f"/api/v1/agent-channel/{reg_no}/deposits",
                    json={"amount_mou": 5, "mou_ref": "mou://test/x"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    return reg_no


def _policy(hdr: dict, reg_no: str, **over) -> object:
    body = {"insurer": "在册保险共同体", "coverage_mou": 100,
            "period_start": _PERIOD_START, "period_end": _PERIOD_END}
    body.update(over)
    return client.post(f"/api/v1/agent-channel/{reg_no}/insurance-policies",
                       json=body, headers=hdr)


def _issue_token(hdr: dict, reg_no: str) -> str:
    """①②③④ 走通＋签转正令牌（对外补齐 B 正例链），返回令牌号。"""
    r = client.post("/api/v1/agent-channel/protocol-load",
                    json={"reg_no": reg_no, "contract_version": CONTRACT_VERSION,
                          "package_sha256_16": _GOOD_HASH}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/ns-review",
                    json={"reg_no": reg_no, "boundary_ref": "nsfl://gapd/1",
                          "adversarial_set_ref": "nsfl://gapd/adv1",
                          "scene_scope": "scene://gapd/demo"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/sandbox",
                    json={"reg_no": reg_no, "sea_elements_ref": "sea://gapd/1",
                          "sandbox_run_ref": "run://gapd/0001", "result": "passed"},
                    headers=hdr)
    assert r.status_code == 200, r.text[:300]
    with get_session() as s:
        who = s.get(M.SiteAgentRegistry, reg_no).owner_username
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion-token",
                    json={"approver": who, "approved_at": "2026-10-23T00:00:01Z",
                          "sandbox_approval_ref": "run://gapd/0001",
                          "approval_intent": "签批意旨：出盒转正（测试）"},
                    headers=hdr)
    assert r.status_code == 201, r.text[:400]
    return r.json()["data"]["token_no"]


# ---------------------------------------------------------------- D-1 保单登记正例
def test_policy_register_positive():
    who, hdr = _auth()
    reg_no = _register(hdr)
    r = _policy(hdr, reg_no)
    assert r.status_code == 201, r.text[:400]
    d = r.json()["data"]
    assert d["registered"] is True and d["status"] == "active"
    assert d["policy_no"].startswith("SIP-") and d["nca_ref"]
    with get_session() as s:
        row = s.get(M.SiteAgentInsurancePolicy, d["policy_no"])
        assert row is not None and row.reg_no == reg_no
        assert row.coverage_mou == 100 and row.insurer == "在册保险共同体"
        nca = s.get(M.NcaChain, d["nca_ref"])
        assert nca is not None and nca.action == "AGENT_CHANNEL_INSURANCE_POLICY_REGISTER"


# ---------------------------------------------------------------- D-2 权限
def test_policy_anon_401_and_non_owner_403():
    _, hdr = _auth()
    reg_no = _register(hdr)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/insurance-policies",
                    json={"insurer": "x", "coverage_mou": 1,
                          "period_start": _PERIOD_START, "period_end": _PERIOD_END})
    assert r.status_code == 401
    _, hdr2 = _auth()
    r = _policy(hdr2, reg_no)
    assert r.status_code == 403 and "人类签名权" in r.text


# ---------------------------------------------------------------- D-3 fail-closed 入参
def test_policy_fail_closed_fields():
    _, hdr = _auth()
    reg_no = _register(hdr)
    bad = [{"insurer": "", "coverage_mou": 1,
            "period_start": _PERIOD_START, "period_end": _PERIOD_END},
           {"insurer": "x", "coverage_mou": 0,
            "period_start": _PERIOD_START, "period_end": _PERIOD_END},
           {"insurer": "x", "coverage_mou": -5,
            "period_start": _PERIOD_START, "period_end": _PERIOD_END},
           {"insurer": "x", "coverage_mou": 1,
            "period_start": "", "period_end": _PERIOD_END},
           {"insurer": "x", "coverage_mou": 1,
            "period_start": _PERIOD_START, "period_end": ""},
           {"insurer": "x", "coverage_mou": 1,
            "period_start": "2027-01-01T00:00:00Z",   # 止≤起
            "period_end": "2026-01-01T00:00:00Z"}]
    for body in bad:
        r = client.post(f"/api/v1/agent-channel/{reg_no}/insurance-policies",
                        json=body, headers=hdr)
        assert r.status_code == 400, (body, r.text[:300])
    r = _policy(hdr, reg_no, surprise=1)               # extra=forbid
    assert r.status_code == 422


# ---------------------------------------------------------------- D-4 转正双重前置
def test_promotion_dual_prerequisite_fail_closed():
    _, hdr = _auth()
    # ① 无令牌无保单 → 拒
    reg_no = _register(hdr)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion", headers=hdr)
    assert r.status_code == 403 and "转正令牌" in r.text
    # ② 有保单无令牌 → 拒
    reg_no2 = _register(hdr)
    assert _policy(hdr, reg_no2).status_code == 201
    r = client.post(f"/api/v1/agent-channel/{reg_no2}/promotion", headers=hdr)
    assert r.status_code == 403 and "转正令牌" in r.text
    # ③ 有令牌无保单 → 拒（无有效保单——拒转正）
    reg_no3 = _register(hdr)
    tok3 = _issue_token(hdr, reg_no3)
    r = client.post(f"/api/v1/agent-channel/{reg_no3}/promotion", headers=hdr)
    assert r.status_code == 403 and "无有效保单" in r.text
    # ④ 双有 → 201：事件落 NCA，⛔ 不改 channel_type
    assert _policy(hdr, reg_no3).status_code == 201
    r = client.post(f"/api/v1/agent-channel/{reg_no3}/promotion", headers=hdr)
    assert r.status_code == 201, r.text[:400]
    d = r.json()["data"]
    assert d["promoted"] is True and d["event_only"] is True
    assert d["token_no"] == tok3 and d["policy_no"].startswith("SIP-")
    assert d["channel_type_unchanged"] == "ANCHOR"     # ⛔ 不改通道定性
    with get_session() as s:
        row = s.get(M.SiteAgentRegistry, reg_no3)
        assert row.channel_type == "ANCHOR"            # 库内同样未动
        nca = s.get(M.NcaChain, d["nca_ref"])
        assert nca is not None and nca.action == "AGENT_CHANNEL_PROMOTED"
    # ⑤ 非本人申报 → 403
    _, hdr2 = _auth()
    r = client.post(f"/api/v1/agent-channel/{reg_no3}/promotion", headers=hdr2)
    assert r.status_code == 403
    # ⑥ 匿名 → 401
    r = client.post(f"/api/v1/agent-channel/{reg_no3}/promotion")
    assert r.status_code == 401


# ---------------------------------------------------------------- D-5 有效保单口径
def test_promotion_policy_period_and_revoke_fail_closed():
    _, hdr = _auth()
    reg_no = _register(hdr)
    _issue_token(hdr, reg_no)
    # 保障期已期满（2020~2021）：可登记，判效拒转正（fail-closed）
    r = _policy(hdr, reg_no, period_start="2020-01-01T00:00:00Z",
                period_end="2021-01-01T00:00:00Z")
    assert r.status_code == 201
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion", headers=hdr)
    assert r.status_code == 403 and "无有效保单" in r.text
    # 覆盖期保单登记后吊销（status=revoked）→ 拒转正
    d = _policy(hdr, reg_no).json()["data"]
    with get_sessionmaker().begin() as s:
        s.get(M.SiteAgentInsurancePolicy, d["policy_no"]).status = "revoked"
    r = client.post(f"/api/v1/agent-channel/{reg_no}/promotion", headers=hdr)
    assert r.status_code == 403 and "无有效保单" in r.text


# ---------------------------------------------------------------- D-6 申报正例与校验
def test_claim_file_positive_and_validation():
    _, hdr = _auth()
    reg_no = _register(hdr)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/claims",
                    json={"loss_type": "技术漏洞",
                          "description": "越界调用致损失（测试申报）",
                          "amount_mou": 12}, headers=hdr)
    assert r.status_code == 201, r.text[:400]
    d = r.json()["data"]
    assert d["filed"] is True and d["status"] == "INSURED"
    assert d["claim_no"].startswith("SIC-") and d["amount_mou"] == 12
    with get_session() as s:
        row = s.get(M.SiteAgentInsuranceClaim, d["claim_no"])
        assert row is not None and row.loss_type == "技术漏洞"
        assert row.status == "INSURED"                 # 触发态口径
        nca = s.get(M.NcaChain, d["nca_ref"])
        assert nca is not None and nca.action == "AGENT_CHANNEL_INSURANCE_CLAIM"
    # 闭集/必填/正额校验（fail-closed）
    bad = [{"loss_type": "流程漏洞", "description": "x", "amount_mou": 1},
           {"loss_type": "制度漏洞", "description": "", "amount_mou": 1},
           {"loss_type": "制度漏洞", "description": "x", "amount_mou": 0},
           {"loss_type": "制度漏洞", "description": "x", "amount_mou": -3}]
    for body in bad:
        r = client.post(f"/api/v1/agent-channel/{reg_no}/claims",
                        json=body, headers=hdr)
        assert r.status_code == 400, (body, r.text[:300])
    r = client.post(f"/api/v1/agent-channel/{reg_no}/claims",
                    json={"loss_type": "技术漏洞", "description": "x",
                          "amount_mou": 1, "surprise": 1}, headers=hdr)
    assert r.status_code == 422


# ---------------------------------------------------------------- D-7 申报权限
def test_claim_anon_401_and_non_owner_403():
    _, hdr = _auth()
    reg_no = _register(hdr)
    body = {"loss_type": "制度漏洞", "description": "x", "amount_mou": 1}
    r = client.post(f"/api/v1/agent-channel/{reg_no}/claims", json=body)
    assert r.status_code == 401
    _, hdr2 = _auth()
    r = client.post(f"/api/v1/agent-channel/{reg_no}/claims", json=body, headers=hdr2)
    assert r.status_code == 403 and "人类签名权" in r.text
