# -*- coding: utf-8 -*-
"""智能体通道 批3 交易接线测试（/api/v1/agent-channel/*——L1SI147-CHANNEL-B1-003）。

验收映射（批 3 令 §四 六例冒烟）：
  ① execute 一正一负：全链＋有效授权件 → executed＋计量落账；授权件场景不覆盖 → 拒
  ② 无授权件 → 拒（配置即侵权口径）
  ③ ④未过 → 拒（沙盒 failed 后 execute 403，⛔ 不得正空间执行）
  ④ 授权件四要件缺件 → 拒（逐要件：R1 场景/R2 五阶/R3 全构成/R4 签名）
  ⑤ 计量落账＋存证：窗口累计 units、闸步表 execute passed、nca 链落点
  ⑥ 吊销后即时拒执行：token revoke 后 execute 即时 403（②步即闭）
另验：总闸⑤execute 接真（passed→satisfied，admitted 全六步口径）；
     计量数值 SIMULATED 水印（响应 data_nature=mixed，units 标 simulated）。
"""
import pytest
from fastapi.testclient import TestClient

import agent_channel_ops
from agent_channel_ops import CONTRACT_VERSION, _REGISTERED_PACKAGE_HASHES_16
from app import app
from db import get_session
from db import models as M

client = TestClient(app)

_PW = "B3chan-2026"
_SEQ = {"n": 0}
_GOOD_HASH = _REGISTERED_PACKAGE_HASHES_16[0]

_SCENE = "scene://b3/demo"
_GOOD_GRANT = {"scene_constraint": _SCENE,
               "tiers_covered": "一阶,三阶",
               "full_composition": True,
               "legal_signer": "测试签署主体甲",
               "signature_ref": "nca://sig/b3-001"}


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    import api_v1
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth(anchor: bool = True) -> tuple[str, dict]:
    _SEQ["n"] += 1
    name = f"b3u{_SEQ['n']:03d}"
    body = {"username": name, "password": _PW,
            "agree_contract": True, "contract_version": "V1.0"}
    if anchor:
        body["anchor_kind"] = "notifier"
        body["anchor_evidence_ref"] = "test-anchor-ref"
    r = client.post("/api/v1/auth/register", json=body)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/auth/login", json={"username": name, "password": _PW})
    assert r.status_code == 200, r.text[:300]
    if anchor:   # 人工受理补锚（等价核验落点）
        with get_session() as s:
            a = s.get(M.UserAnchor, name)
            a.tier_state = "已补"
            a.verified_at = "2026-10-16T00:00:00Z"
            a.verifier = "test-fixture"
            s.commit()
    return name, {"Authorization": r.json()["data"]["token"]}


_REG_SEQ = {"n": 0}


def _register(hdr: dict, tag: str | None = None) -> str:
    if tag is None:
        _REG_SEQ["n"] += 1
        tag = f"b3-{_REG_SEQ['n']:03d}"
    r = client.post("/api/v1/agent-channel/register",
                    json={"channel_type": "ANCHOR",
                          "device": f"测试设备-{tag}", "compute": "测试算力-x",
                          "protocol": "测试协议-x", "role": "测试角色-x",
                          "knowledge": "测试知识-x", "permission_ttl": "测试权限时效-x",
                          "root_token_ref": "root-token://test/1"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    reg_no = r.json()["data"]["reg_no"]
    # 对外补齐 C（L1SI166-CHANNEL-GAP-001 项 C）：进沙盒须先押付有效保金——登记即
    # 代押测试保金，使后续沙盒步可达（阈值 1 MOU，见 conftest 配置）。
    r = client.post(f"/api/v1/agent-channel/{reg_no}/deposits",
                    json={"amount_mou": 5, "mou_ref": "mou://test/x"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    return reg_no


def _full_chain(hdr: dict | None = None) -> tuple[str, dict]:
    """①②③④ 全过链：登记→加载→签发→负空间→沙盒。返回 (reg_no, hdr)。"""
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
                    json={"reg_no": reg_no, "boundary_ref": "nsfl://boundary/b3-001",
                          "adversarial_set_ref": "nsfl://adv/b3-001",
                          "scene_scope": _SCENE}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/sandbox",
                    json={"reg_no": reg_no, "sea_elements_ref": "sea://b3/001",
                          "sandbox_run_ref": "run://b3/001", "result": "passed"},
                    headers=hdr)
    assert r.status_code == 200, r.text[:300]
    return reg_no, hdr


def _grant(reg_no: str, hdr: dict, **over) -> object:
    body = dict(_GOOD_GRANT)
    body.update(over)
    return client.post(f"/api/v1/agent-channel/{reg_no}/grants", json=body, headers=hdr)


def _exec(reg_no: str, hdr: dict, scene: str = _SCENE, **kw) -> object:
    body = {"reg_no": reg_no, "scene": scene, "action": "invoke://b3/demo", "units": 2}
    body.update(kw)
    return client.post("/api/v1/agent-channel/execute", json=body, headers=hdr)


# ---------------------------------------------------------------- ① execute 一正一负
def test_execute_positive_metered_and_admitted():
    reg_no, hdr = _full_chain()
    r = _grant(reg_no, hdr)
    assert r.status_code == 201, r.text[:300]
    grant_no = r.json()["data"]["grant_no"]
    r = _exec(reg_no, hdr)
    assert r.status_code == 200, r.text[:300]
    d = r.json()["data"]
    assert d["executed"] is True and d["grant_no"] == grant_no
    assert d["ledger"]["units"] == 2
    assert d["ledger"]["data_nature"] == "simulated"   # SIMULATED 水印
    assert r.json()["data_nature"] == "mixed"          # 事实真＋计量数值模拟
    assert d["nca_ref"]
    with get_session() as s:
        assert agent_channel_ops._step_state(s, reg_no, "execute") == "passed"
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    assert gate["steps"]["execute"]["state"] == "satisfied"
    assert gate["admitted"] is True   # 六步全 satisfied（B2-FIX-001 名实相符口径）


def test_execute_negative_scene_not_covered():
    reg_no, hdr = _full_chain()
    r = _grant(reg_no, hdr)   # 仅授权 _SCENE
    assert r.status_code == 201, r.text[:300]
    r = _exec(reg_no, hdr, scene="scene://b3/other")
    assert r.status_code == 403 and "GRANT_REQUIRED" in r.text
    with get_session() as s:
        assert agent_channel_ops._step_state(s, reg_no, "execute") is None


# ---------------------------------------------------------------- ② 无授权件 → 拒（配置即侵权）
def test_execute_rejected_without_grant():
    reg_no, hdr = _full_chain()
    r = _exec(reg_no, hdr)
    assert r.status_code == 403 and "GRANT_REQUIRED" in r.text
    assert "配置即侵权" in r.text
    with get_session() as s:
        assert agent_channel_ops._step_state(s, reg_no, "execute") is None
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    assert gate["steps"]["execute"]["state"] == "pending"   # 未达不虚报


# ---------------------------------------------------------------- ③ ④未过 → 拒
def test_execute_rejected_when_sandbox_failed():
    reg_no, hdr = _full_chain()
    r = _grant(reg_no, hdr)
    assert r.status_code == 201, r.text[:300]
    r = client.post("/api/v1/agent-channel/sandbox",
                    json={"reg_no": reg_no, "sea_elements_ref": "sea://b3/002",
                          "sandbox_run_ref": "run://b3/002", "result": "failed"},
                    headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = _exec(reg_no, hdr)
    assert r.status_code == 403 and "④" in r.text and "不得正空间执行" in r.text
    with get_session() as s:
        assert agent_channel_ops._step_state(s, reg_no, "execute") is None


# ---------------------------------------------------------------- ④ 四要件缺件 → 拒（逐要件）
def test_grant_rejected_missing_requirements_one_by_one():
    reg_no, hdr = _full_chain()
    cases = [
        ("R1", {"scene_constraint": ""}),
        ("R2 五阶清单缺失", {"tiers_covered": ""}),
        ("R2 五阶清单越闭集", {"tiers_covered": "一阶,九阶"}),
        ("R3", {"full_composition": False}),
        ("R4 法律主体签名者缺失", {"legal_signer": ""}),
        ("R4 签名事件引用缺失", {"signature_ref": ""}),
    ]
    for tag, over in cases:
        r = _grant(reg_no, hdr, **over)
        assert r.status_code == 400, f"{tag}: {r.status_code} {r.text[:200]}"
        assert "GRANT_REJECTED" in r.text and "缺一不成立" in r.text
    with get_session() as s:
        assert s.query(M.SiteAgentGrant).filter_by(reg_no=reg_no).count() == 0


# ---------------------------------------------------------------- ⑤ 计量落账＋存证
def test_metering_aggregation_window_and_ledger():
    reg_no, hdr = _full_chain()
    r = _grant(reg_no, hdr)
    assert r.status_code == 201, r.text[:300]
    r = _exec(reg_no, hdr, units=2)
    assert r.status_code == 200, r.text[:300]
    r = _exec(reg_no, hdr, units=3)
    assert r.status_code == 200, r.text[:300]
    with get_session() as s:
        rows = s.query(M.SiteAgentCallLedger).filter_by(reg_no=reg_no).all()
        assert len(rows) == 1            # 同窗口聚合一行（⛔ 不高频直写）
        assert rows[0].endpoint == "execute"
        assert rows[0].units == 5        # 窗口累计
        assert rows[0].data_provenance == "mixed"
        assert rows[0].nca_anchor
        detail = s.get(M.SiteAgentAdmission, (reg_no, "execute")).detail
    assert "申报来源" in detail and "机验层级" in detail


# ---------------------------------------------------------------- ⑥ 吊销后即时拒执行
def test_execute_rejected_immediately_after_revoke():
    reg_no, hdr = _full_chain()
    r = _grant(reg_no, hdr)
    assert r.status_code == 201, r.text[:300]
    r = _exec(reg_no, hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "revoke"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = _exec(reg_no, hdr)
    assert r.status_code == 403 and "STEP_ORDER" in r.text   # ②步即闭，全库即时拒
