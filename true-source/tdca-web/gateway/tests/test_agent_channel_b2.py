# -*- coding: utf-8 -*-
"""智能体通道 批2 通道本体测试（/api/v1/agent-channel/*——L1SI147-CHANNEL-B1-002）。

验收映射（批 2 令 §四 新增冒烟五例）：
  ① protocol-load 一正一负：在册版本+哈希 → passed＋可机验回执；哈希不符/版本不符 → 403 且步未达
  ② token 一正一负：锚无效 → 拒；签发即轮换——再签后旧 active 即时 revoked
  ③ ns-review 一正一负：要件齐 → passed；要件缺 → 400 且闸步记 failed（拒绝入网）
  ④ sandbox 一正一负：passed → executable；failed → 步记 failed（⛔ 不得正空间执行）
  ⑤ 吊销即时性：revoke 后②步即 pending，后续步（ns-review）403 全拒
另验：六步硬序不可跳（未加载发 token → 403；③未过进沙盒 → 403）；总闸 pending_batch 复核
（①③④ 批 2 接真不再报 pending_batch；⑤execute 批 3 接真——未达报 pending）；锚挂接（签发回执载锚口径）。
"""
import pytest
from fastapi.testclient import TestClient

import agent_channel_ops
from agent_channel_ops import CONTRACT_VERSION, _REGISTERED_PACKAGE_HASHES_16
from app import app
from db import get_session
from db import models as M

client = TestClient(app)

_PW = "B2chan-2026"
_SEQ = {"n": 0}
_GOOD_HASH = _REGISTERED_PACKAGE_HASHES_16[0]


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    import api_v1
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth(anchor: bool = True) -> tuple[str, dict]:
    _SEQ["n"] += 1
    name = f"b2u{_SEQ['n']:03d}"
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
        tag = f"b2-{_REG_SEQ['n']:03d}"
    r = client.post("/api/v1/agent-channel/register",
                    json={"channel_type": "ANCHOR",
                          "device": f"测试设备-{tag}", "compute": "测试算力-x",
                          "protocol": "测试协议-x", "role": "测试角色-x",
                          "knowledge": "测试知识-x", "permission_ttl": "测试权限时效-x",
                          "root_token_ref": "root-token://test/1"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    return r.json()["data"]["reg_no"]


def _load(reg_no: str, hdr: dict, sha: str = _GOOD_HASH) -> object:
    return client.post("/api/v1/agent-channel/protocol-load",
                       json={"reg_no": reg_no, "contract_version": CONTRACT_VERSION,
                             "package_sha256_16": sha}, headers=hdr)


def _full_chain() -> tuple[str, dict]:
    """①②③④ 全过链：登记→加载→签发→负空间→沙盒。返回 (reg_no, hdr)。"""
    _, hdr = _auth()
    reg_no = _register(hdr)
    r = _load(reg_no, hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/ns-review",
                    json={"reg_no": reg_no, "boundary_ref": "nsfl://boundary/b2-001",
                          "adversarial_set_ref": "nsfl://adv/b2-001",
                          "scene_scope": "scene://b2/demo"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/sandbox",
                    json={"reg_no": reg_no, "sea_elements_ref": "sea://b2/001",
                          "sandbox_run_ref": "run://b2/001", "result": "passed"},
                    headers=hdr)
    assert r.status_code == 200, r.text[:300]
    return reg_no, hdr


# ---------------------------------------------------------------- ① protocol-load
def test_protocol_load_positive_receipt_verifiable():
    _, hdr = _auth()
    reg_no = _register(hdr)
    r = _load(reg_no, hdr)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["loaded"] is True and d["contract_version"] == CONTRACT_VERSION
    assert d["receipt_sha256_32"].startswith("sha256:")
    assert d["nca_ref"]
    with get_session() as s:
        assert agent_channel_ops._step_state(s, reg_no, "protocol-load") == "passed"
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    assert gate["steps"]["protocol-load"]["state"] == "satisfied"


def test_protocol_load_negative_hash_and_version():
    _, hdr = _auth()
    reg_no = _register(hdr)
    # 哈希不符 → 403，步未达
    r = _load(reg_no, hdr, sha="deadbeefcafe0001")
    assert r.status_code == 403 and "HASH_MISMATCH" in r.text
    # 版本不符 → 403
    r = client.post("/api/v1/agent-channel/protocol-load",
                    json={"reg_no": reg_no, "contract_version": "V0.0-FAKE",
                          "package_sha256_16": _GOOD_HASH}, headers=hdr)
    assert r.status_code == 403 and "VERSION_UNKNOWN" in r.text
    with get_session() as s:
        assert agent_channel_ops._step_state(s, reg_no, "protocol-load") is None


# ---------------------------------------------------------------- ② token 签发/轮换
def test_token_issue_and_rotate_immediate():
    _, hdr = _auth()
    reg_no = _register(hdr)
    assert _load(reg_no, hdr).status_code == 200
    # 首签
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    d1 = r.json()["data"]
    assert d1["credential"].startswith("TDCA-AGT-")
    assert d1["anchor"]["kind"] == "notifier" and d1["anchor"]["state"] == "已补"  # 锚挂接回执
    fp1 = d1["credential_fingerprint_sha256_16"]
    # 再签（签发即轮换）：旧 active 即时 revoked
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "rotate"}, headers=hdr)
    assert r.status_code == 200
    d2 = r.json()["data"]
    assert d2["rotated"] == 1
    assert d2["credential_fingerprint_sha256_16"] != fp1
    with get_session() as s:
        rows = s.query(M.SiteAgentCredential).filter_by(reg_no=reg_no).all()
        assert len(rows) == 2
        assert sum(1 for c in rows if c.status == "active") == 1
        revoked = [c for c in rows if c.status == "revoked"][0]
        assert revoked.cred_fingerprint.startswith(fp1)
        assert revoked.rotated_at is not None      # 轮换时点落库
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    assert gate["steps"]["token"]["state"] == "satisfied"


def test_token_negative_anchor_invalid_and_step_order():
    # 负例 A：锚无效 → 拒发（同批 1 口径复用）
    _, hdr_bad = _auth(anchor=False)
    reg_bad = _register(hdr_bad)
    assert _load(reg_bad, hdr_bad).status_code == 200
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_bad, "action": "issue"}, headers=hdr_bad)
    assert r.status_code == 403 and "ANCHOR_INVALID" in r.text
    # 负例 B：未加载协议即发 token → 403（未加载一切后续不可）
    _, hdr = _auth()
    reg_no = _register(hdr)
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    assert r.status_code == 403 and "STEP_ORDER" in r.text


# ---------------------------------------------------------------- ③ ns-review
def test_ns_review_positive_and_negative():
    _, hdr = _auth()
    reg_no = _register(hdr)
    assert _load(reg_no, hdr).status_code == 200
    client.post("/api/v1/agent-channel/token",
                json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    # 负例：要件缺失 → 400 且闸步记 failed（拒绝入网）
    r = client.post("/api/v1/agent-channel/ns-review",
                    json={"reg_no": reg_no, "boundary_ref": ""}, headers=hdr)
    assert r.status_code == 400 and "NS_REVIEW_REJECTED" in r.text
    with get_session() as s:
        assert agent_channel_ops._step_state(s, reg_no, "ns-review") == "failed"
    # 正例：要件齐 → passed
    r = client.post("/api/v1/agent-channel/ns-review",
                    json={"reg_no": reg_no, "boundary_ref": "nsfl://boundary/b2-002",
                          "adversarial_set_ref": "nsfl://adv/b2-002",
                          "scene_scope": "scene://b2/demo"}, headers=hdr)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["verdict"] == "passed" and d["admitted_to_sandbox"] is True
    with get_session() as s:
        assert agent_channel_ops._step_state(s, reg_no, "ns-review") == "passed"


def test_ns_review_step_order_before_token():
    _, hdr = _auth()
    reg_no = _register(hdr)
    assert _load(reg_no, hdr).status_code == 200
    # ②未达（无凭据）→ ③即拒（六步不可跳）
    r = client.post("/api/v1/agent-channel/ns-review",
                    json={"reg_no": reg_no, "boundary_ref": "nsfl://b/x",
                          "adversarial_set_ref": "nsfl://a/x",
                          "scene_scope": "scene://b2/x"}, headers=hdr)
    assert r.status_code == 403 and "STEP_ORDER" in r.text


# ---------------------------------------------------------------- ④ sandbox
def test_sandbox_positive_and_failed_blocks_execute():
    _, hdr = _auth()
    reg_no = _register(hdr)
    assert _load(reg_no, hdr).status_code == 200
    client.post("/api/v1/agent-channel/token",
                json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    client.post("/api/v1/agent-channel/ns-review",
                json={"reg_no": reg_no, "boundary_ref": "nsfl://b/f",
                      "adversarial_set_ref": "nsfl://a/f",
                      "scene_scope": "scene://b2/f"}, headers=hdr)
    # 负例：failed → 步记 failed，⛔ 不得正空间执行
    r = client.post("/api/v1/agent-channel/sandbox",
                    json={"reg_no": reg_no, "sea_elements_ref": "sea://b2/f",
                          "sandbox_run_ref": "run://b2/f", "result": "failed"},
                    headers=hdr)
    assert r.status_code == 200 and r.json()["data"]["executable"] is False
    with get_session() as s:
        assert agent_channel_ops._step_state(s, reg_no, "sandbox") == "failed"
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    assert gate["steps"]["sandbox"]["state"] == "failed"
    # 正例：passed → executable
    r = client.post("/api/v1/agent-channel/sandbox",
                    json={"reg_no": reg_no, "sea_elements_ref": "sea://b2/p",
                          "sandbox_run_ref": "run://b2/p", "result": "passed"},
                    headers=hdr)
    assert r.status_code == 200 and r.json()["data"]["executable"] is True
    with get_session() as s:
        assert agent_channel_ops._step_state(s, reg_no, "sandbox") == "passed"


def test_sandbox_step_order_ns_review_failed():
    _, hdr = _auth()
    reg_no = _register(hdr)
    assert _load(reg_no, hdr).status_code == 200
    client.post("/api/v1/agent-channel/token",
                json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    client.post("/api/v1/agent-channel/ns-review",
                json={"reg_no": reg_no, "boundary_ref": ""}, headers=hdr)  # → failed
    # ③未过 → ④即拒（⛔ 不得进沙盒）
    r = client.post("/api/v1/agent-channel/sandbox",
                    json={"reg_no": reg_no, "sea_elements_ref": "sea://b2/o",
                          "sandbox_run_ref": "run://b2/o", "result": "passed"},
                    headers=hdr)
    assert r.status_code == 403 and "STEP_ORDER" in r.text


# ---------------------------------------------------------------- ⑤ 吊销即时性
def test_revoke_immediate_subsequent_denied():
    reg_no, hdr = _full_chain()
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "revoke"}, headers=hdr)
    assert r.status_code == 200 and r.json()["data"]["immediate"] is True
    with get_session() as s:
        assert agent_channel_ops.evaluate_gate(s, reg_no)["steps"]["token"]["state"] == "pending"
    # 吊销后后续步即时全拒（ns-review 重申报亦拒——②未达）
    r = client.post("/api/v1/agent-channel/ns-review",
                    json={"reg_no": reg_no, "boundary_ref": "nsfl://b/r",
                          "adversarial_set_ref": "nsfl://a/r",
                          "scene_scope": "scene://b2/r"}, headers=hdr)
    assert r.status_code == 403 and "STEP_ORDER" in r.text


# ---------------------------------------------------------------- 总闸 pending_batch 复核（批 3 收口）
def test_gate_pending_batch_review_after_b2():
    _, hdr = _auth()
    reg_no = _register(hdr)
    with get_session() as s:
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    # 批 3 复核（令 -B3 §二）：⑤execute 已接真——未达报 pending（⛔ 不再报 pending_batch）
    for k in ("protocol-load", "ns-review", "sandbox"):
        assert gate["steps"][k]["state"] == "pending"
    assert gate["steps"]["execute"]["state"] == "pending"


def test_full_chain_all_four_steps_satisfied():
    reg_no, _ = _full_chain()
    with get_session() as s:
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    for k in ("protocol-load", "token", "ns-review", "sandbox", "nca-evidence"):
        assert gate["steps"][k]["state"] == "satisfied", k
    assert gate["steps"]["execute"]["state"] == "pending"   # 批 3 已接真：未跑 execute 报 pending


# ---------------------------------------------------------------- B2-FIX-001 补正加验
def test_gate_admitted_semantics_name_matches_fact():
    """补正①：admitted＝登记正常且六步全 satisfied——全链④步过、⑤execute 未达 ⟹ admitted False。"""
    reg_no, _ = _full_chain()
    with get_session() as s:
        gate = agent_channel_ops.evaluate_gate(s, reg_no)
    assert gate["registry_ok"] is True
    assert gate["admitted"] is False          # 名实相符：execute（批 3）未达
    assert gate["unsatisfied_steps"] == ["execute"]
    for k in ("protocol-load", "token", "ns-review", "sandbox", "nca-evidence"):
        assert gate["steps"][k]["state"] == "satisfied"


def test_credentials_endpoint_reuses_rotation():
    """补正③（取甲·复用轮换）：批 1 /credentials 新签自动置旧 active 为 revoked。"""
    _, hdr = _auth()
    reg_no = _register(hdr)
    r = client.post(f"/api/v1/agent-channel/{reg_no}/credentials", json={}, headers=hdr)
    assert r.status_code == 201
    fp1 = r.json()["data"]["credential_fingerprint_sha256_16"]
    r = client.post(f"/api/v1/agent-channel/{reg_no}/credentials", json={}, headers=hdr)
    assert r.status_code == 201 and r.json()["data"]["rotated"] == 1
    with get_session() as s:
        rows = s.query(M.SiteAgentCredential).filter_by(reg_no=reg_no).all()
        assert len(rows) == 2
        assert sum(1 for c in rows if c.status == "active") == 1
        old = [c for c in rows if c.cred_fingerprint.startswith(fp1)][0]
        assert old.status == "revoked" and old.rotated_at is not None


def test_protocol_load_full_64_hash_and_component():
    """建议④：完整 64 位哈希＋分量标识核验；分量声明不符即拒。"""
    from api_v1 import CONTRACT_JSON_SHA256
    _, hdr = _auth()
    reg_no = _register(hdr)
    r = client.post("/api/v1/agent-channel/protocol-load",
                    json={"reg_no": reg_no, "contract_version": CONTRACT_VERSION,
                          "package_sha256_16": CONTRACT_JSON_SHA256,
                          "package_component": "json"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    d = r.json()["data"]
    assert d["verified_component"] == "json"
    assert d["verified_sha256"] == CONTRACT_JSON_SHA256
    assert d["verified_sha256_16"] == CONTRACT_JSON_SHA256[:16]
    # 分量声明与哈希实际分量不符 → 403
    r = client.post("/api/v1/agent-channel/protocol-load",
                    json={"reg_no": reg_no, "contract_version": CONTRACT_VERSION,
                          "package_sha256_16": CONTRACT_JSON_SHA256,
                          "package_component": "zh"}, headers=hdr)
    assert r.status_code == 403 and "HASH_MISMATCH" in r.text


def test_ns_review_and_sandbox_provenance_annotations():
    """补正②：③④返回值与落库 detail 增列「申报来源」「机验层级」，passed ⛔ 不冒充已跑。"""
    _, hdr = _auth()
    reg_no = _register(hdr)
    assert _load(reg_no, hdr).status_code == 200
    client.post("/api/v1/agent-channel/token",
                json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    r = client.post("/api/v1/agent-channel/ns-review",
                    json={"reg_no": reg_no, "boundary_ref": "nsfl://b/pv",
                          "adversarial_set_ref": "nsfl://a/pv",
                          "scene_scope": "scene://b2/pv"}, headers=hdr)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["申报来源"] and "结构要件层" in d["机验层级"] and "引擎层未跑" in d["机验层级"]
    r = client.post("/api/v1/agent-channel/sandbox",
                    json={"reg_no": reg_no, "sea_elements_ref": "sea://b2/pv",
                          "sandbox_run_ref": "run://b2/pv", "result": "passed"},
                    headers=hdr)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["申报来源"] and "结果系申报" in d["机验层级"] and "非站内实跑" in d["机验层级"]
    # 落库 detail 同步载明（闸步表实读）
    with get_session() as s:
        ns = s.get(M.SiteAgentAdmission, (reg_no, "ns-review"))
        sb = s.get(M.SiteAgentAdmission, (reg_no, "sandbox"))
    import json as _json
    assert _json.loads(ns.detail)["申报来源"] and "机验层级" in _json.loads(ns.detail)
    assert _json.loads(sb.detail)["申报来源"] and "机验层级" in _json.loads(sb.detail)
