# -*- coding: utf-8 -*-
"""智能体通道 批4块二 惩罚三态执行器测试（/api/v1/agent-channel/{reg_no}/punishments）。

验收映射（复工令 §五 四例冒烟）：
  ① 三态各一例：施加后总闸即时拒（gate_assert 403）＋ evaluate_gate admitted=False
  ② 留痕 NCA 实读：施加后 nca_chain 最新存证（action/裁决者/前后态）
  ③ 无人类会话 → 拒（负例：⛔ 无自动触发之径）
  ④ 非有权者 → 拒（viewer 会话施加 403 PUNISH_FORBIDDEN）
另验：吊销为终态（再施加 403 PUNISH_FINAL）；同态重复施加 409；
     恢复径未实施（本批无 restore 端点）。
"""
import pytest
from fastapi.testclient import TestClient

import agent_channel_ops
from agent_channel_ops import CONTRACT_VERSION, _REGISTERED_PACKAGE_HASHES_16
from app import app
from auth import hash_password
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "B4pun-2026"
_SEQ = {"n": 0}
_GOOD_HASH = _REGISTERED_PACKAGE_HASHES_16[0]


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    import api_v1
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth(anchor: bool = True, tag: str = "u") -> tuple[str, dict]:
    _SEQ["n"] += 1
    name = f"b4{tag}{_SEQ['n']:03d}"
    body = {"username": name, "password": _PW,
            "agree_contract": True, "contract_version": "V1.0"}
    if anchor:
        body["anchor_kind"] = "notifier"
        body["anchor_evidence_ref"] = "test-anchor-ref"
    r = client.post("/api/v1/auth/register", json=body)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/auth/login", json={"username": name, "password": _PW})
    assert r.status_code == 200, r.text[:300]
    if anchor:
        with get_session() as s:
            a = s.get(M.UserAnchor, name)
            a.tier_state = "已补"
            a.verified_at = "2026-10-16T00:00:00Z"
            a.verifier = "test-fixture"
            s.commit()
    return name, {"Authorization": r.json()["data"]["token"]}


def _founder() -> dict:
    """人类裁决（founder 会话）——照 NS-OPS §4.1 权限矩阵的状态转换权落点。"""
    from datetime import datetime, timezone
    name = "founder-b4-punish"
    now = datetime.now(timezone.utc).isoformat()
    ph, salt, iters = hash_password(f"pw-{name}")
    with get_sessionmaker().begin() as s:
        u = s.get(M.User, name)
        if u is None:
            s.add(M.User(username=name, password_hash=ph, salt=salt,
                         iterations=iters, role="founder", created_at=now))
        else:
            u.role = "founder"
    r = client.post("/api/v1/auth/login", json={"username": name, "password": f"pw-{name}"})
    assert r.status_code == 200, r.text[:300]
    return {"Authorization": r.json()["data"]["token"]}


def _register(hdr: dict) -> str:
    r = client.post("/api/v1/agent-channel/register",
                    json={"six_elements_ref": "six-elements://b4/0001"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    return r.json()["data"]["reg_no"]


def _punish(reg_no: str, hdr: dict, action: str, reason: str = "裁决测试理由") -> object:
    return client.post(f"/api/v1/agent-channel/{reg_no}/punishments",
                       json={"action": action, "reason": reason}, headers=hdr)


# ---------------------------------------------------------------- ① 三态各一例（即时拒）
@pytest.mark.parametrize("action,target", [("freeze", "冻结"), ("demote", "降权"), ("revoke", "吊销")])
def test_punish_three_states_immediate_deny(action, target):
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    r = _punish(reg_no, fhdr, action)
    assert r.status_code == 200, r.text[:300]
    d = r.json()["data"]
    assert d["punished"] is True and d["status"] == target
    assert d["effective"] == "immediate" and d["nca_ref"]
    # 即时生效实证：主体本人走全链端点 → 总闸即时拒
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "issue"}, headers=owner_hdr)
    assert r.status_code == 403 and "GATE_FAIL_CLOSED" in r.text
    with get_session() as s:
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    assert gate["admitted"] is False and gate["registry_ok"] is False
    assert gate["denied_reason"] == f"PUNISHMENT_STATE:{target}"


# ---------------------------------------------------------------- ② 留痕 NCA 实读
def test_punish_nca_evidence_readable():
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    r = _punish(reg_no, fhdr, "freeze", reason="深度审查留痕实测")
    assert r.status_code == 200, r.text[:300]
    nca_ref = r.json()["data"]["nca_ref"]
    with get_session() as s:
        row = s.get(M.NcaChain, nca_ref)
        assert row is not None                     # 存证实读：链上可查
        assert row.action == "AGENT_CHANNEL_PUNISH_FREEZE"
        assert row.artifact_path and "正常->冻结" in row.artifact_path
        assert row.actor == "founder-b4-punish"
        assert row.data_provenance == "real"


# ---------------------------------------------------------------- ③ 无人类会话 → 拒
def test_punish_rejected_without_session():
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/punishments",
                    json={"action": "freeze", "reason": "无会话负例"})
    assert r.status_code == 401   # ⛔ 无自动触发之径：非人类会话即拒


# ---------------------------------------------------------------- ④ 非有权者 → 拒
def test_punish_rejected_for_non_authorized_role():
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    _, viewer_hdr = _auth(tag="v")          # 普通账户（viewer）
    r = _punish(reg_no, viewer_hdr, "freeze")
    assert r.status_code == 403 and "PUNISH_FORBIDDEN" in r.text
    assert "不得自罚" in r.text
    # 登记主体本人亦无权自罚（NS-OPS §4.1：主体自身仅查询/申请）
    r = _punish(reg_no, owner_hdr, "freeze")
    assert r.status_code == 403 and "PUNISH_FORBIDDEN" in r.text
    with get_session() as s:
        assert s.get(M.SiteAgentRegistry, reg_no).status == "正常"


# ---------------------------------------------------------------- 吊销终态 / 幂等 / 幽灵拒
def test_revoke_final_state_and_idempotence():
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    r = _punish(reg_no, fhdr, "revoke")
    assert r.status_code == 200, r.text[:300]
    # 已吊销为终态：⛔ 不得再变更（不得复活）
    r = _punish(reg_no, fhdr, "demote")
    assert r.status_code == 403 and "PUNISH_FINAL" in r.text
    # 同态重复施加 → 409 幂等拒
    _, owner2 = _auth()
    reg2 = _register(owner2)
    fhdr2 = _founder()
    assert _punish(reg2, fhdr2, "freeze").status_code == 200
    r = _punish(reg2, fhdr2, "freeze")
    assert r.status_code == 409
    # 幽灵态拒（用新会话：单会话制，旧会话已被 fhdr2 顶吊销）
    r = _punish("SAR-NONEXIST0000", fhdr2, "freeze")
    assert r.status_code == 403 and "GATE_FAIL_CLOSED" in r.text
