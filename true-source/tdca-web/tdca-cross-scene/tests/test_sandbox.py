# -*- coding: utf-8 -*-
"""W3 T-P3-001 跨场景沙盒测试（≥3 场景交互/激活系数可解释/注入负空间拒绝/晋升签名不可绕过/算法哈希/数据隔离）。"""
import pytest
from fastapi.testclient import TestClient

from cross_scene.p3_api import app
from cross_scene.sandbox import CrossSceneSandbox, SandboxStatus

client = TestClient(app)


def _create(scene_ids=None, pcr=9000.0):
    return client.post("/cross-scene/create", json={
        "scene_ids": scene_ids or ["SCN-TOUR", "SCN-AGRI", "SCN-EDU"],
        "pcr_budget": pcr, "sponsor_did": "DID-SPONSOR-001"})


# ---- T-P3-001 核心：≥3 场景 + 激活系数可解释 ----

def test_create_requires_3_scenes():
    assert _create(scene_ids=["A", "B"]).status_code in (400, 422)   # <3 拒绝（pydantic 422 / 应用层 400）
    r = _create()
    assert r.status_code == 201
    assert r.json()["status"] == "HIBERNATING"


def test_activation_coefficient_explainable():
    r = _create()
    sid = r.json()["sandbox_id"]
    r = client.post("/cross-scene/evaluate", json={"sandbox_id": sid, "duration_days": 30})
    detail = r.json()
    # 明细可解释（MOU/PCR/衰减/网络效应——验收：输出明细至 NCA）
    assert set(detail) >= {"activation_coefficient", "total_mou", "total_pcr",
                           "externality_decay", "externality_benefit"}
    assert detail["total_pcr"] == 9000.0
    assert detail["externality_benefit"] > 0   # 3 场景网络效应


def test_interaction_increases_decay():
    sb = CrossSceneSandbox.create(["A", "B", "C"], 9000.0, "DID-1")
    a0 = sb.activation_coefficient()["activation_coefficient"]
    sb.interactions.append({"conflicts": 10, "mapping_cost": 5})
    a1 = sb.activation_coefficient()["activation_coefficient"]
    assert a1 < a0   # 冲突增多 → 衰减增大 → 系数下降


# ---- 数据隔离（安全约束 1：脱敏 + 负空间审查）----

def test_data_isolation_sanitized_view():
    sb = CrossSceneSandbox.create(["A", "B", "C"], 9000.0, "DID-1")
    r = sb.inject_data("A", {"id": "USER-1", "did": "DID-X", "revenue": 100}, nsfl_verdict="PASS")
    assert r["injection_status"] == "SUCCESS"
    view = sb.get_shared_view("A", caller="B")
    assert "revenue" in view and "id" not in view and "did" not in view   # 脱敏
    with pytest.raises(PermissionError):
        sb.get_shared_view("A", caller="A")   # 原始数据隔离（自身仅经脱敏视图）


def test_inject_rejected_on_nsfl_conflict():
    """D-2 联调：负空间边界冲突 → REJECTED。"""
    r = _create()
    sid = r.json()["sandbox_id"]
    boundary = {"scene_id": "SCN-TOUR",
                "rules": [{"rule_id": "L1", "ns_type": "LEGAL", "operator": "FORBID"}]}
    r = client.post("/cross-scene/inject-data", json={
        "sandbox_id": sid, "scene_id": "SCN-TOUR",
        "data": {"x": 1}, "nsfl_boundary": boundary})
    assert r.json()["injection_status"] == "REJECTED"
    assert "负空间" in r.json()["reason"] or "REQUIRES_REVIEW" in r.json()["reason"]


def test_inject_success_clean_boundary():
    r = _create()
    sid = r.json()["sandbox_id"]
    r = client.post("/cross-scene/inject-data", json={
        "sandbox_id": sid, "scene_id": "SCN-TOUR",
        "data": {"revenue": 200}, "nsfl_boundary": {"rules": []}})
    assert r.json()["injection_status"] == "SUCCESS"


# ---- 晋升人类签名不可绕过（安全约束 3）----

def test_promote_requires_human_signature():
    # 极小 PCR 抬高激活系数（MOU/PCR 比值驱动，模拟态数值）
    r = _create(pcr=1.0)
    sid = r.json()["sandbox_id"]
    # 注入正和交互（少量，避免 mapping_cost 过度抬升衰减）
    for i in range(5):
        client.post("/cross-scene/inject-data", json={
            "sandbox_id": sid, "scene_id": f"SCN-{['TOUR','AGRI','EDU'][i % 3]}",
            "data": {"revenue": 100 + i}, "nsfl_boundary": {"rules": []}})
    r = client.post("/promote/propose", json={"sandbox_id": sid, "duration_days": 72})
    assert r.status_code == 200
    pid = r.json()["proposal_id"]
    assert r.json()["requires_human_signature"] is True
    # 无签名 confirm → 403（负空间熔断）
    r = client.post("/promote/confirm", json={"proposal_id": pid,
                                              "human_signature": "", "human_did": "DID-H"})
    assert r.status_code == 403
    # 签名过短 → 403
    r = client.post("/promote/confirm", json={"proposal_id": pid,
                                              "human_signature": "short", "human_did": "DID-H"})
    assert r.status_code == 403
    # 有效签名 → ACTIVE + market_entry_id
    r = client.post("/promote/confirm", json={"proposal_id": pid,
                                              "human_signature": "HUMAN-SIG-CONFIRM-001",
                                              "human_did": "DID-H"})
    assert r.json()["new_status"] == "ACTIVE"
    assert r.json()["market_entry_id"].startswith("ME-")


def test_promote_below_threshold_rejected():
    r = _create()
    sid = r.json()["sandbox_id"]
    r = client.post("/promote/propose", json={"sandbox_id": sid, "duration_days": 72})
    assert r.status_code == 409   # 激活系数 ≤1.2


# ---- 算法哈希上链（安全约束 2）----

def test_algorithm_hash_verifies():
    sb = CrossSceneSandbox.create(["A", "B", "C"], 9000.0, "DID-1")
    assert sb.verify_algorithm_hash() is True
    # 篡改检测：算法行为变更 → 哈希不匹配
    sb.algorithm_hash = "tampered"
    assert sb.verify_algorithm_hash() is False
