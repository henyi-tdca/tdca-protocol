# -*- coding: utf-8 -*-
"""P5 T-P5-001 工作流引擎测试（DSL 执行 / 签名门禁不可绕过 / 负空间阻断 / NCA / WORM 日志 / <10s）。"""
import pytest
from fastapi.testclient import TestClient

from workbuddy.api import app
from workbuddy.engine import (CrossSceneWorkflowEngine, WorkflowDSL,
                              WORKFLOW_TIME_LIMIT_S)

client = TestClient(app)

DSL = {
    "workflow_id": "cross-scene-001",
    "steps": [
        {"scene": "scene-A", "function": "f_A", "role": "L", "config_right": "S-Right",
         "output": "intermediate_1"},
        {"scene": "scene-B", "function": "translator_A2B", "role": "L",
         "config_right": "S-Right", "input": "intermediate_1", "output": "intermediate_2",
         "nsfl_check": True},   # 强制负空间检查（跨场景边界）
        {"scene": "scene-B", "function": "g_B", "role": "L", "config_right": "S-Right",
         "input": "intermediate_2", "output": "final_result"},
    ],
    "human_gates": [
        {"before": "step_2"},        # 跨场景切换前
        {"after": "workflow_complete"},
    ],
}


def _create():
    return client.post("/workflow/create", json={
        "cscp_handshake_id": "HS-TEST-001", "workflow_template": DSL})


# ---- 创建 + 执行（正常路径）----

def test_create_pending_human_gate():
    r = _create()
    assert r.status_code == 201
    assert r.json()["status"] == "PENDING_HUMAN_GATE"


def test_execute_full_cycle():
    wf = _create().json()["workflow_id"]
    r = client.post("/workflow/execute", json={"workflow_id": wf,
                                               "human_signature": "HUMAN-SIG-WF-001"})
    body = r.json()
    assert body["status"] == "COMPLETED"
    assert len(body["nca_refs"]) >= 5          # 全程 NCA 审计轨迹
    assert body["nsfl_status"] == "CHECKED"    # 跨场景负空间已检查


def test_execute_under_10s():
    """验收: 端到端执行 <10s。"""
    import time
    wf = _create().json()["workflow_id"]
    t0 = time.perf_counter()
    client.post("/workflow/execute", json={"workflow_id": wf,
                                           "human_signature": "HUMAN-SIG-WF-001"})
    assert (time.perf_counter() - t0) < WORKFLOW_TIME_LIMIT_S


# ---- 人类签名不可绕过（P5 绝对负空间 2）----

def test_execute_without_signature_blocked():
    wf = _create().json()["workflow_id"]
    r = client.post("/workflow/execute", json={"workflow_id": wf, "human_signature": ""})
    assert r.status_code == 403
    assert "HUMAN_SIGNATURE_REQUIRED" in r.json()["detail"]


# ---- 负空间阻断（跨场景边界 TRIGGERED）----

def test_nsfl_block_cross_scene():
    eng = CrossSceneWorkflowEngine(nsfl_check_fn=lambda step: False)   # 负空间拒绝
    wf = WorkflowDSL.from_dict(DSL)
    ex = eng.execute(wf, "HUMAN-SIG-WF-001")
    assert ex.status == "BLOCKED"
    assert ex.nsfl_status == "TRIGGERED"
    assert any("NSFL_BLOCK" in n for n in ex.nca_refs)


# ---- WORM 日志不可篡改（P5 绝对负空间 3）----

def test_worm_log_integrity():
    eng = CrossSceneWorkflowEngine()
    wf = WorkflowDSL.from_dict(DSL)
    eng.execute(wf, "HUMAN-SIG-WF-001")
    assert eng.verify_log_integrity() is True
    eng._log[0] = "TAMPERED :: deadbeef"   # 篡改 → 完整性校验失败
    assert eng.verify_log_integrity() is False


# ---- /signature 硬件签名门禁 ----

def test_signature_confirm_requires_hardware():
    r = client.post("/signature/request", json={"workflow_id": "WF-X",
                                                "gate_id": "GATE-before-1"})
    rid = r.json()["signature_request_id"]
    # 无硬件签名 → 403（自动化签名尝试 → 熔断）
    r = client.post("/signature/confirm", json={"request_id": rid, "hardware_signature": ""})
    assert r.status_code == 403
    # 有效硬件签名 → verified
    r = client.post("/signature/confirm", json={"request_id": rid,
                                                "hardware_signature": "HW-SIG-ABCDEF1234"})
    assert r.json()["verified"] is True


# ---- 依赖顺序错误（DSL 校验）----

def test_execute_dependency_error():
    bad = dict(DSL)
    bad["steps"][1]["input"] = "nonexistent_output"
    r = client.post("/workflow/create", json={"cscp_handshake_id": "HS-1",
                                              "workflow_template": bad})
    assert r.status_code == 201
    wf = r.json()["workflow_id"]
    r = client.post("/workflow/execute", json={"workflow_id": wf,
                                               "human_signature": "HUMAN-SIG-WF-001"})
    assert r.status_code == 400                       # DSL 依赖错误 → 400
    assert "依赖" in r.json()["detail"]
