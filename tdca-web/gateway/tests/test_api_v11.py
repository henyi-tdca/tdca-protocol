# -*- coding: utf-8 -*-
"""A-11 确权 API 测试（F5 前置缺口补建——meta/dynamic/history/queue 四端点）。"""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _post(path, payload):
    r = client.post(path, json=payload)
    assert r.status_code == 200, f"{path} → {r.status_code}: {r.text[:200]}"
    body = r.json()
    assert "nca_watermark" in body       # 全链路 NCA 水印（ID91）
    assert body["data_nature"] == "simulated"
    return body["data"]


def _get(path):
    r = client.get(path)
    assert r.status_code == 200, f"{path} → {r.status_code}: {r.text[:200]}"
    body = r.json()
    assert "nca_watermark" in body
    assert body["data_nature"] == "simulated"
    return body["data"]


# ---- A-11 元函数初始确权（出盒终裁）----
def test_a11_meta_approved():
    d = _post("/api/v1/attestation/meta", {
        "agent_id": "AGENT-007", "activation": 1.35,
        "sandbox_report": "SEA 4/5 GREEN", "six_elements": {"objective_function": "f(x)", "audit_trail": "NCA"},
    })
    assert d["status"] == "SIGNED"
    assert d["verified"] is True
    assert d["huf_irreducible"] is True
    assert d["attestation_id"].startswith("META-ATT-")


def test_a11_meta_rejected_below_threshold():
    d = _post("/api/v1/attestation/meta", {"agent_id": "AGENT-009", "activation": 1.1})
    assert d["status"] == "REJECTED"      # 激活系数 ≤1.2 → 拒绝（继续孵化或 HUF 特批）


# ---- A-11 动态确权审批（四操作）----
def test_a11_dynamic_approve():
    d = _post("/api/v1/attestation/dynamic", {
        "request_id": "DAR-001", "agent_id": "AGENT-007",
        "request_type": "scene_extension", "urgency": "urgent", "decision": "approve",
    })
    assert d["status"] == "APPROVED"
    assert d["nca_ref"].startswith("Approval-NCA-")


def test_a11_dynamic_reject_and_defer():
    d1 = _post("/api/v1/attestation/dynamic", {"request_id": "DAR-002", "decision": "reject"})
    assert d1["status"] == "REJECTED"
    d2 = _post("/api/v1/attestation/dynamic", {"request_id": "DAR-003", "decision": "defer"})
    assert d2["status"] == "DEFERRED"


# ---- A-11 确权历史查询（NCA 链跨代）----
# M2 起本端点为 DB 实读且有状态：上文 4 个 POST 产生 4 条已决记录
# （meta approved / meta rejected / DAR-001 approved / DAR-002 rejected），
# DAR-003 defer 后仍为 pending 不计入。断言改为集合语义（同秒 ts 不定序）。
def test_a11_history_chain():
    d = _get("/api/v1/attestation/history")
    assert d["total"] == 4
    assert all(c["nca_ref"] for c in d["chain"])            # 每条均有 NCA 存证
    assert {c["status"] for c in d["chain"]} == {"APPROVED", "REJECTED"}
    assert any(c["type"] == "META" for c in d["chain"])     # 元函数确权在链
    assert sum(c["status"] == "REJECTED" for c in d["chain"]) == 2  # 拒绝事件保留


def test_a11_history_filter_by_agent():
    d = _get("/api/v1/attestation/history?agent_id=AGENT-007")
    assert d["total"] == 3


# ---- A-11 待审队列（紧急度排序）----
# M2 有状态：DAR-001/002 已决，仅 DAR-003（defer）仍在 pending 队列。
def test_a11_queue():
    d = _get("/api/v1/attestation/queue")
    assert d["total"] == 1
    assert d["queue"][0]["request_id"] == "DAR-003"
    assert d["queue"][0]["urgency"] == "normal"
