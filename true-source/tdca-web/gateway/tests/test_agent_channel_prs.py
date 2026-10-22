# -*- coding: utf-8 -*-
"""T-037《惩罚三态统一状态机条例》工程接入测试（任务 A 判级档／B 恢复三端点／C 超期升档）。

验收映射（IMPL-002 §五 七项）：
  1  Q-3/Q-4/Q-6/Q-7/Q-11/Q-12 逐条直译测试（命名 test_prs_qNN_…）
  2  跳步反例三条：未重塑直调 restore→409；重塑未验证直调→409；reverify 无对应周期→409
  3  非 founder 调三端点 → 403
  4  法律级标记下调 remediate → 403
  5  吊销终态复验（继承批 4 既有测 test_agent_channel_b4_punish.py）
  6  任务 C 三条：满 30 天⟹ 置永久＋独立存证；未满期不动；只升不降
  7  引擎写口实证 ⛔ 不写 status（判级/裁决/扫掠三写口均不落态）
另验：完整恢复环（重塑→验证→返回）、failed 续周期（次数不限）、待裁队列。
"""
import pytest
from fastapi.testclient import TestClient

import agent_channel_ops
from agent_channel_ops import run_permanent_upgrade_sweep
from app import app
from auth import hash_password
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "PRS-t037-2026"
_SEQ = {"n": 0}


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    import api_v1
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth(tag: str = "u") -> tuple[str, dict]:
    _SEQ["n"] += 1
    name = f"prs{tag}{_SEQ['n']:03d}"
    r = client.post("/api/v1/auth/register", json={
        "username": name, "password": _PW, "agree_contract": True,
        "contract_version": "V1.0", "anchor_kind": "notifier",
        "anchor_evidence_ref": "test-anchor-ref"})
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/auth/login", json={"username": name, "password": _PW})
    assert r.status_code == 200, r.text[:300]
    return name, {"Authorization": r.json()["data"]["token"]}


def _founder() -> dict:
    from datetime import datetime, timezone
    name = "founder-prs-t037"
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


_REG_SEQ = {"n": 0}


def _register(hdr: dict, tag: str | None = None) -> str:
    if tag is None:
        _REG_SEQ["n"] += 1
        tag = f"prs-{_REG_SEQ['n']:03d}"
    r = client.post("/api/v1/agent-channel/register",
                    json={"channel_type": "ANCHOR",
                          "device": f"测试设备-{tag}", "compute": "测试算力-x",
                          "protocol": "测试协议-x", "role": "测试角色-x",
                          "knowledge": "测试知识-x", "permission_ttl": "测试权限时效-x",
                          "root_token_ref": "root-token://test/1"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    return r.json()["data"]["reg_no"]


def _punish(reg_no: str, hdr: dict, action: str, reason: str = "裁决测试理由"):
    return client.post(f"/api/v1/agent-channel/{reg_no}/punishments",
                       json={"action": action, "reason": reason}, headers=hdr)


def _classify(reg_no: str, source: str, ref: str = "signal://test/0001"):
    return client.post("/api/v1/agent-channel/classifications",
                       json={"reg_no": reg_no, "signal_source": source, "signal_ref": ref})


def _status(reg_no: str) -> str:
    with get_session() as s:
        return s.get(M.SiteAgentRegistry, reg_no).status


def _backdate_revoke_evidence(reg_no: str, days: int):
    """把最近一条吊销存证 ts 回拨（扫掠判期输入）。"""
    from datetime import datetime, timedelta, timezone
    past = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with get_sessionmaker().begin() as s:
        ev = (s.query(M.NcaChain)
              .filter(M.NcaChain.action == "AGENT_CHANNEL_PUNISH_REVOKE",
                      M.NcaChain.artifact_path.like(f"agent-channel:{reg_no}/punish:revoke:%"))
              .order_by(M.NcaChain.ts.desc()).first())
        assert ev is not None
        ev.ts = past


# ================================================================ 任务 A
def test_prs_classify_maps_band_and_never_writes_status():
    """§五.7/引擎写口实证：判级写口⛔ 不写 status；档位服务端依三空间分档导出。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    expect = {"sensor_warning": "轻度", "sensor_cryogenic": "中度",
              "sensor_blocked": "严重", "legal_matrix": "法律级"}
    for source, band in expect.items():
        r = _classify(reg_no, source)
        assert r.status_code == 201, r.text[:300]
        d = r.json()["data"]
        assert d["band"] == band and d["ruling_state"] == "pending" and d["nca_ref"]
    assert _status(reg_no) == "正常"   # 四档判级后状态一字未动
    # ⛔ 调用方不得自报档位（extra=forbid）
    r = client.post("/api/v1/agent-channel/classifications",
                    json={"reg_no": reg_no, "signal_source": "sensor_warning",
                          "signal_ref": "x", "band": "法律级"})
    assert r.status_code == 422
    # 闭集外信号源拒
    r = _classify(reg_no, "unknown_source")
    assert r.status_code == 400
    # 幽灵主体不受理
    r = _classify("SAR-NONEXIST0000", "sensor_warning")
    assert r.status_code == 403 and "GATE_FAIL_CLOSED" in r.text


def test_prs_q03_ruling_closure_adopt_and_dismiss():
    """Q-3（不得由 AI 单方施加）：判级→待裁→人类裁决；采纳须回绑既有惩罚端点存证。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    r = _classify(reg_no, "sensor_blocked")
    event_id = r.json()["data"]["event_id"]
    # 裁决前施加未发生：status 不动
    assert _status(reg_no) == "正常"
    rp = _punish(reg_no, fhdr, "revoke", reason="采纳裁决施加")
    assert rp.status_code == 200, rp.text[:300]
    punish_nca = rp.json()["data"]["nca_ref"]
    # adopt：回绑惩罚存证 → ruled
    r = client.post(f"/api/v1/agent-channel/classifications/{event_id}/rule",
                    json={"decision": "adopt", "punish_nca_ref": punish_nca,
                          "reason": "采纳：严重档"}, headers=fhdr)
    assert r.status_code == 200, r.text[:300]
    assert r.json()["data"]["ruling_state"] == "ruled"
    # 旁路存证不认（其它登记号/非惩罚存证）
    _, owner2 = _auth()
    reg2 = _register(owner2)
    r = _classify(reg2, "sensor_warning")
    ev2 = r.json()["data"]["event_id"]
    r = client.post(f"/api/v1/agent-channel/classifications/{ev2}/rule",
                    json={"decision": "adopt", "punish_nca_ref": punish_nca,
                          "reason": "x"}, headers=fhdr)
    assert r.status_code == 400
    # dismiss 径
    r = client.post(f"/api/v1/agent-channel/classifications/{ev2}/rule",
                    json={"decision": "dismiss", "reason": "证据不足驳回"}, headers=fhdr)
    assert r.status_code == 200 and r.json()["data"]["ruling_state"] == "dismissed"
    # 重复裁决 409
    r = client.post(f"/api/v1/agent-channel/classifications/{ev2}/rule",
                    json={"decision": "dismiss", "reason": "再裁"}, headers=fhdr)
    assert r.status_code == 409
    # 判级/裁决全程只有人类惩罚动作改了 status
    assert _status(reg_no) == "吊销" and _status(reg2) == "正常"


def test_prs_queue_founders_only():
    """待裁队列（裁决面只读）：founder 可见，余者 403。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    _classify(reg_no, "sensor_warning")
    fhdr = _founder()
    r = client.get("/api/v1/agent-channel/classifications/queue", headers=fhdr)
    assert r.status_code == 200, r.text[:300]
    assert any(i["reg_no"] == reg_no for i in r.json()["data"]["items"])
    r = client.get("/api/v1/agent-channel/classifications/queue", headers=owner_hdr)
    assert r.status_code == 403 and "PRS_FORBIDDEN" in r.text


# ================================================================ 任务 B
def test_prs_q06_skip_step_rejected_three_cases():
    """Q-6/§五.2 跳步反例三条：未重塑直调 restore→409；重塑未验证→409；reverify 无周期→409。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    assert _punish(reg_no, fhdr, "freeze").status_code == 200
    # ① 未重塑直调 restore
    r = client.post(f"/api/v1/agent-channel/{reg_no}/restore", headers=fhdr)
    assert r.status_code == 409 and "RESTORE_FACT_MISSING" in r.text
    # ③ reverify 无对应周期
    r = client.post(f"/api/v1/agent-channel/{reg_no}/reverify",
                    json={"result": "passed"}, headers=fhdr)
    assert r.status_code == 409 and "REVERIFY_NO_CYCLE" in r.text
    # 重塑后未验证直调 restore
    r = client.post(f"/api/v1/agent-channel/{reg_no}/remediate", headers=fhdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post(f"/api/v1/agent-channel/{reg_no}/restore", headers=fhdr)
    assert r.status_code == 409 and "RESTORE_FACT_MISSING" in r.text
    assert _status(reg_no) == "冻结"   # 跳步全程状态未动


def test_prs_q04_nonfounder_recovery_forbidden():
    """Q-4（不得由 AI 单方解除）：非 founder 调三端点 → 403；无会话 → 401。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    assert _punish(reg_no, fhdr, "demote").status_code == 200
    _, other_hdr = _auth(tag="v")
    for ep, body in (("remediate", None), ("reverify", {"result": "passed"}),
                     ("restore", None)):
        r = client.post(f"/api/v1/agent-channel/{reg_no}/{ep}",
                        json=body or {}, headers=other_hdr)
        assert r.status_code == 403 and "PRS_FORBIDDEN" in r.text, ep
        r = client.post(f"/api/v1/agent-channel/{reg_no}/{ep}", json=body or {})
        assert r.status_code == 401, ep
    assert _status(reg_no) == "降权"


def test_prs_q11_punished_no_positive_space():
    """Q-11（三态期间不得正空间执行）：惩罚态全链即时拒（总闸继承批 1）。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    assert _punish(reg_no, fhdr, "freeze").status_code == 200
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "issue"}, headers=owner_hdr)
    assert r.status_code == 403 and "GATE_FAIL_CLOSED" in r.text
    with get_session() as s:
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    assert gate["admitted"] is False and gate["registry_ok"] is False


def test_prs_full_recovery_cycle_and_evidence_chain():
    """完整恢复环：冻结→重塑→验证(passed)→返回；NCA 三证链实读。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    assert _punish(reg_no, fhdr, "freeze").status_code == 200
    r = client.post(f"/api/v1/agent-channel/{reg_no}/remediate", headers=fhdr)
    assert r.status_code == 200 and r.json()["data"]["new_cycle"] is True
    cycle_no = r.json()["data"]["cycle_no"]
    r = client.post(f"/api/v1/agent-channel/{reg_no}/reverify",
                    json={"result": "passed"}, headers=fhdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post(f"/api/v1/agent-channel/{reg_no}/restore", headers=fhdr)
    assert r.status_code == 200, r.text[:300]
    d = r.json()["data"]
    assert d["restored"] is True and d["from_status"] == "冻结" and d["status"] == "正常"
    assert _status(reg_no) == "正常"
    with get_session() as s:
        cyc = s.get(M.SiteAgentRemediation, cycle_no)
        assert cyc.remediated_at and cyc.reverify_at and cyc.reverify_result == "passed"
        for want in ("AGENT_CHANNEL_REMEDIATE", "AGENT_CHANNEL_REVERIFY",
                     "AGENT_CHANNEL_RESTORE"):
            assert s.query(M.NcaChain).filter_by(action=want).first() is not None, want
    # 重复验证幂等拒（不并步之证：周期已闭）
    r = client.post(f"/api/v1/agent-channel/{reg_no}/reverify",
                    json={"result": "passed"}, headers=fhdr)
    assert r.status_code == 409


def test_prs_reverify_failed_allows_new_cycle_unlimited():
    """第十五条：failed 可续（次数不限，⛔ 不倒计不悬置）：failed→新周期→passed→返回。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    assert _punish(reg_no, fhdr, "demote").status_code == 200
    assert client.post(f"/api/v1/agent-channel/{reg_no}/remediate", headers=fhdr).status_code == 200
    r = client.post(f"/api/v1/agent-channel/{reg_no}/reverify",
                    json={"result": "failed"}, headers=fhdr)
    assert r.status_code == 200, r.text[:300]
    # 验证未通过：返回必拒
    r = client.post(f"/api/v1/agent-channel/{reg_no}/restore", headers=fhdr)
    assert r.status_code == 409
    # 再开周期（seq=2）→ passed → 返回
    r = client.post(f"/api/v1/agent-channel/{reg_no}/remediate", headers=fhdr)
    assert r.status_code == 200 and r.json()["data"]["cycle_seq"] == 2
    assert client.post(f"/api/v1/agent-channel/{reg_no}/reverify",
                       json={"result": "passed"}, headers=fhdr).status_code == 200
    assert client.post(f"/api/v1/agent-channel/{reg_no}/restore", headers=fhdr).status_code == 200
    assert _status(reg_no) == "正常"


def test_prs_legal_level_recovery_forbidden():
    """§五.4/第十六条：法律级裁决在册 → remediate/reverify/restore 一律 403。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    event_id = _classify(reg_no, "legal_matrix").json()["data"]["event_id"]
    rp = _punish(reg_no, fhdr, "revoke", reason="法律级裁决施加")
    assert rp.status_code == 200, rp.text[:300]
    r = client.post(f"/api/v1/agent-channel/classifications/{event_id}/rule",
                    json={"decision": "adopt",
                          "punish_nca_ref": rp.json()["data"]["nca_ref"],
                          "reason": "采纳：法律级"}, headers=fhdr)
    assert r.status_code == 200
    for ep, body in (("remediate", None), ("reverify", {"result": "passed"}),
                     ("restore", None)):
        r = client.post(f"/api/v1/agent-channel/{reg_no}/{ep}",
                        json=body or {}, headers=fhdr)
        assert r.status_code == 403 and "LEGAL" in r.text, ep
    assert _status(reg_no) == "吊销"   # 无任何径解除此态（除恢复径，恢复径已闭）


def test_prs_direct_punish_without_classification_is_economic():
    """对照例：无判级之直罚（经济级口径）可入恢复径（法律级必出自判级档）。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    assert _punish(reg_no, fhdr, "revoke").status_code == 200
    r = client.post(f"/api/v1/agent-channel/{reg_no}/remediate", headers=fhdr)
    assert r.status_code == 200, r.text[:300]


# ================================================================ 任务 C
def test_prs_sweep_upgrades_after_30d_and_blocks_everything():
    """§五.6①：吊销满 30 天 ⟹ 置永久＋独立存证；status 不动（不改表结构闭集）；
    恢复径全闭。"""
    from datetime import datetime, timezone
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    assert _punish(reg_no, fhdr, "revoke").status_code == 200
    _backdate_revoke_evidence(reg_no, days=31)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = run_permanent_upgrade_sweep(now=now)
    assert out["upgraded"] == 1, out
    with get_session() as s:
        pm = s.get(M.SiteAgentPermanent, reg_no)
        assert pm is not None and pm.source == "sweep_upgrade"
        ev = s.get(M.NcaChain, pm.nca_ref)
        assert ev.action == "AGENT_CHANNEL_PUNISH_UPGRADE_PERMANENT"
        assert "吊销->永久" in ev.artifact_path
    assert _status(reg_no) == "吊销"   # status 闭集未动
    for ep, body in (("remediate", None), ("reverify", {"result": "passed"}),
                     ("restore", None)):
        r = client.post(f"/api/v1/agent-channel/{reg_no}/{ep}",
                        json=body or {}, headers=fhdr)
        assert r.status_code == 403 and "PRS_PERMANENT_FINAL" in r.text, ep
    # 重复扫掠：幂等不重复处置
    out = run_permanent_upgrade_sweep(now=now)
    assert out["upgraded"] == 0 and out["skipped"] >= 1


def test_prs_sweep_skips_before_30d():
    """§五.6②：未满期不动。"""
    from datetime import datetime, timezone
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    assert _punish(reg_no, fhdr, "revoke").status_code == 200
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = run_permanent_upgrade_sweep(now=now)
    assert out["upgraded"] == 0
    with get_session() as s:
        assert s.get(M.SiteAgentPermanent, reg_no) is None


def test_prs_sweep_only_upgrades_never_downgrades():
    """§五.6③：只升不降——冻结/降权不扫；不产生任何降档/复活。"""
    from datetime import datetime, timezone
    _, owner_hdr = _auth()
    reg_fz = _register(owner_hdr)
    fhdr = _founder()
    assert _punish(reg_fz, fhdr, "freeze").status_code == 200
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = run_permanent_upgrade_sweep(now=now)
    assert out["upgraded"] == 0
    with get_session() as s:
        assert s.get(M.SiteAgentPermanent, reg_fz) is None
    assert _status(reg_fz) == "冻结"   # 未误升/未降档/未复活
    # 恢复径可用性未被扫掠扰动（三态存续）
    r = client.post(f"/api/v1/agent-channel/{reg_fz}/remediate", headers=fhdr)
    assert r.status_code == 200, r.text[:300]


def test_prs_q07_revoked_no_self_revive_and_q12_no_auto_punish():
    """Q-7：吊销未经重塑不得自行复活；Q-12：判级可自动、⛔ 无自动施加之径。"""
    _, owner_hdr = _auth()
    reg_no = _register(owner_hdr)
    fhdr = _founder()
    # 法律级判级（最重组）自动落档：status 不动——无自动施加
    r = _classify(reg_no, "legal_matrix")
    assert r.status_code == 201
    assert _status(reg_no) == "正常"
    # 人类吊销后、未经重塑：无任何自行复活径（恢复径须逐步事实）
    assert _punish(reg_no, fhdr, "revoke").status_code == 200
    assert client.post(f"/api/v1/agent-channel/{reg_no}/restore", headers=fhdr).status_code == 409
    with get_session() as s:
        assert s.query(M.NcaChain).filter(
            M.NcaChain.action == "AGENT_CHANNEL_RESTORE",
            M.NcaChain.artifact_path.like(f"agent-channel:{reg_no}/restore:%")).first() is None
    assert _status(reg_no) == "吊销"
