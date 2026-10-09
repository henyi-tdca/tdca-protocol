# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     API E2E 测试——REST 全生命周期 + 错误语义 + NCA 校验端点
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 接口熵=0
# 先验分布:     NS-OPS test_api.py 模式
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""API E2E 测试（FastAPI TestClient）。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_SIX = {
    "目标函数": "API 测试沙盒",
    "约束矩阵": "FC-SBX-OPS-001 SV-1~7",
    "先验分布": "任务书 FROZEN",
    "配置权边界": "L2 层",
    "预期分配": "测试",
    "审计轨迹": "TDCA-NCA-{YYYYMMDD}-{SEQ}",
}

_SIG = [
    {"role": "innovator", "did": "did:tdca:INNOVATOR-001", "signature": "s1"},
    {"role": "investor", "did": "did:tdca:INVESTOR-001", "signature": "s2"},
    {"role": "government", "did": "did:tdca:GOV-001", "signature": "s3"},
]


class TestHealth:
    def test_health(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["service"] == "tdca-sbx-ops"


class TestCreate:
    def test_create_201(self):
        r = client.post("/api/v1/sandboxes", json={"name": "E2E", "initiator_did": "did:tdca:INNOVATOR-001", "initiator_role": "innovator", "six_elements": _SIX})
        assert r.status_code == 201
        body = r.json()
        assert body["phase"] == "Phase0"
        assert len(body["nca_ids"]) == 1

    def test_create_incomplete_six_422(self):
        r = client.post("/api/v1/sandboxes", json={"name": "E2E", "initiator_did": "did:tdca:INNOVATOR-001", "initiator_role": "innovator", "six_elements": {"目标函数": "x"}})
        assert r.status_code == 422

    def test_list_includes_seed(self):
        r = client.get("/api/v1/sandboxes")
        assert r.status_code == 200
        assert len(r.json()) >= 1  # 种子沙盒

    def test_get_404(self):
        # 合法格式（32 hex）但未创建 → 404
        r = client.get(f"/api/v1/sandboxes/did:tdca:sandbox:{'0' * 32}")
        assert r.status_code == 404

    def test_get_rejects_invalid_id_format(self):
        """非法格式（非 did 白名单）→ 422（路径穿越防护）。"""
        r = client.get("/api/v1/sandboxes/hacker-id")
        assert r.status_code == 422

    def test_get_200(self):
        """V-11 修复：get() 公开路径 200 单测。"""
        r = client.post("/api/v1/sandboxes", json={"name": "GET", "initiator_did": "did:tdca:INNOVATOR-001", "initiator_role": "innovator", "six_elements": _SIX})
        sid = r.json()["sandbox_id"]
        r = client.get(f"/api/v1/sandboxes/{sid}")
        assert r.status_code == 200
        assert r.json()["name"] == "GET"


class TestLifecycleE2E:
    def _full_flow(self):
        r = client.post("/api/v1/sandboxes", json={"name": "E2E-流程", "initiator_did": "did:tdca:INNOVATOR-001", "initiator_role": "innovator", "six_elements": _SIX})
        sid = r.json()["sandbox_id"]
        client.post(f"/api/v1/sandboxes/{sid}/configure", json={"pucr": {"amount": 10000}})
        client.post(f"/api/v1/sandboxes/{sid}/start", json={})
        client.post(f"/api/v1/sandboxes/{sid}/run", json={"iteration": {"m": 1}})
        return sid

    def test_e2e_exit_flow(self):
        sid = self._full_flow()
        r = client.post(f"/api/v1/sandboxes/{sid}/evaluate", json={"pcr_input": 100.0, "tax_revenue": 150.0, "employment_ss": 20.0})
        assert r.status_code == 200
        assert r.json()["phase"] == "P1"
        assert r.json()["activation_logs"][-1]["coefficient"] == 1.7

        r = client.post(f"/api/v1/sandboxes/{sid}/exit", json={"signatures": _SIG, "human_signatory": "did:tdca:HUMAN-FOUNDER-001"})
        assert r.status_code == 200
        assert r.json()["phase"] == "Exit"

    def test_evaluate_invalid_input_422(self):
        sid = self._full_flow()
        r = client.post(f"/api/v1/sandboxes/{sid}/evaluate", json={"pcr_input": 0.0, "tax_revenue": 1.0, "employment_ss": 0.0})
        assert r.status_code == 422

    def test_exit_with_low_alpha_422(self):
        """SV-1: α ≤1.2 出盒被 API 拒绝。"""
        sid = self._full_flow()
        client.post(f"/api/v1/sandboxes/{sid}/evaluate", json={"pcr_input": 100.0, "tax_revenue": 100.0, "employment_ss": 0.0})  # α=1.0
        r = client.post(f"/api/v1/sandboxes/{sid}/exit", json={"signatures": _SIG, "human_signatory": "did:tdca:HUMAN-FOUNDER-001"})
        assert r.status_code == 422
        assert "SV-1" in r.json()["detail"]

    def test_close_flow(self):
        sid = self._full_flow()
        r = client.post(f"/api/v1/sandboxes/{sid}/close", json={"trigger_role": "government", "reason": "负空间熔断", "human_signatory": "did:tdca:HUMAN-FOUNDER-001"})
        assert r.status_code == 200
        assert r.json()["phase"] == "Closed"


class TestNcaApi:
    def test_nca_list_and_verify(self):
        client.post("/api/v1/sandboxes", json={"name": "NCA", "initiator_did": "did:tdca:INNOVATOR-001", "initiator_role": "innovator", "six_elements": _SIX})
        r = client.get("/api/v1/nca")
        assert r.status_code == 200
        assert len(r.json()) >= 2  # 种子 + 新建

        r = client.get("/api/v1/nca/verify")
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_nca_detail_404(self):
        r = client.get("/api/v1/nca/NCA-99999999-999")
        assert r.status_code == 404
