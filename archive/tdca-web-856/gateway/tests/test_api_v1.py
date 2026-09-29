# -*- coding: utf-8 -*-
"""A 类 API 面包装层测试（/api/v1/*，10 项端点冒烟 + 核心断言）。"""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _get(path):
    r = client.get(path)
    assert r.status_code == 200, f"{path} → {r.status_code}: {r.text[:200]}"
    body = r.json()
    assert "nca_watermark" in body       # 全链路 NCA 水印
    assert body["data_nature"] == "simulated"
    return body["data"]


# ---- A-1 首页 KPI ----
def test_a1_system_overview():
    d = _get("/api/v1/system/overview")
    assert d["system"].startswith("ECOCOG")
    assert d["tax_rates"]["dispatch_tax"] == 0.02


# ---- A-2 税收仪表盘 ----
def test_a2_tax_mou():
    d = _get("/api/v1/tax/mou/AGENT-A")
    assert d["mou_irreducible"] is True     # ID79


def test_a2_tax_nca_history():
    d = _get("/api/v1/tax/nca-history")
    assert "events" in d


def test_a2_tax_shapley():
    d = _get("/api/v1/tax/shapley/CALL-1")
    assert d["call_id"] == "CALL-1"


# ---- A-3 配置权市场调用 ----
def test_a3_config_right_call():
    r = client.post("/api/v1/config-right/call", json={
        "delivery_id": "DEL-T1", "caller": "AGENT-A", "callee": "AGENT-B",
        "call_value": 1000.0, "tax_receipt": 100.0})
    assert r.status_code == 200, r.text[:200]
    body = r.json()["data"]
    assert "full_cognition" in body


# ---- A-4 五阶资产池 ----
def test_a4_assets():
    d = _get("/api/v1/assets/five-orders")
    assert len(d["assets"]) == 5


# ---- A-5 沙盒准入 ----
def test_a5_sea_status():
    d = _get("/api/v1/sandbox/sea-status")
    assert len(d["sea"]) == 5
    assert d["all_green"] is False        # AMBER 项不阻塞预研


def test_a5_sandbox_apply():
    r = client.post("/api/v1/sandbox/apply", json={})
    assert r.status_code == 200, r.text[:200]
    assert r.json()["data"]["sandbox_id"].startswith("SBX-")


# ---- A-6 术语 ----
def test_a6_knowledge_terms():
    d = _get("/api/v1/knowledge/terms")
    assert len(d["terms"]) >= 5
    d2 = _get("/api/v1/knowledge/terms?q=mou")
    assert all("mou" in t["term"].lower() or "mou" in t["def"].lower() for t in d2["terms"])


# ---- A-7 审计 ----
def test_a7_ledger_public():
    d = _get("/api/v1/audit/ledger-public")
    assert "events" in d


def test_a7_nca_verify():
    r = client.post("/api/v1/audit/nca-verify", json={"nca_hash": "abc", "payload": "data"})
    assert r.status_code == 200
    assert "verified" in r.json()["data"]


# ---- A-8 治理 ----
def test_a8_huf_sign():
    r = client.post("/api/v1/governance/huf-sign", json={"action": "ota_upgrade"})
    assert r.status_code == 200
    assert r.json()["data"]["huf_irreducible"] is True


def test_a8_emergency_fuse():
    r = client.post("/api/v1/governance/emergency-fuse", json={})
    assert r.status_code == 200
    assert "fused" in r.json()["data"]


# ---- A-9 通知机 ----
def test_a9_notifier_mrcr():
    d = _get("/api/v1/notifier/mrcr-status")
    assert len(d["roles"]) == 4           # NM-Operator/Gov/Fin/Med
    assert d["roles"][0]["role"] == "NM-Operator"


# ---- A-10 智能体集群 ----
def test_a10_eios_cluster():
    d = _get("/api/v1/eios/cluster-status")
    assert len(d["cluster"]) == 10        # ID25 九大能力 + 派生
