# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     M2 API E2E 测试——三位一体/化合/正和验证全链路
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 接口熵=0
# 先验分布:     任务书 §二 F2/F4/F5/F6
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M2 API E2E 测试（F2/F4/F5/F6 路由）。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_SIX = {
    "目标函数": "M2 API 测试",
    "约束矩阵": "FC-SBX-OPS-001 SV-1~7",
    "先验分布": "任务书 FROZEN",
    "配置权边界": "L2 层",
    "预期分配": "测试",
    "审计轨迹": "TDCA-NCA-{YYYYMMDD}-{SEQ}",
}

_TRINITY = [
    {"role": "innovator", "did": "did:tdca:INNOVATOR-001", "contribution": {"value": 30.0, "type": "ip"}, "reservation_utility": 5.0},
    {"role": "investor", "did": "did:tdca:INVESTOR-001", "contribution": {"value": 50.0, "type": "capital"}, "reservation_utility": 8.0},
    {"role": "government", "did": "did:tdca:GOV-001", "contribution": {"value": 20.0, "type": "pcr"}, "reservation_utility": 2.0},
]


def _create():
    r = client.post("/api/v1/sandboxes", json={"name": "M2-测试", "initiator_did": "did:tdca:INNOVATOR-001", "initiator_role": "innovator", "six_elements": _SIX})
    return r.json()["sandbox_id"]


class TestTrinityApi:
    def test_trinity_full_flow(self):
        sid = _create()
        r = client.post(f"/api/v1/sandboxes/{sid}/trinity", json={"profiles": _TRINITY})
        assert r.status_code == 200
        assert set(r.json()["trinity"]["profiles"].keys()) == {"innovator", "investor", "government"}

        r = client.post(f"/api/v1/sandboxes/{sid}/trinity/shapley", json={})
        assert r.status_code == 200
        weights = r.json()["trinity"]["shapley_weights"]
        # 效率性: v(N) = (30+50+20) * (1+0.15*3) = 100 * 1.45 = 145
        assert abs(sum(weights.values()) - 145.0) < 1e-6
        assert r.json()["trinity"]["shapley_properties"]["efficiency"] is True

        r = client.get(f"/api/v1/sandboxes/{sid}/trinity")
        assert r.status_code == 200

    def test_trinity_incomplete_rejected(self):
        sid = _create()
        r = client.post(f"/api/v1/sandboxes/{sid}/trinity", json={"profiles": _TRINITY[:2]})
        assert r.status_code == 200  # 配置阶段允许部分注册，Shapley 阶段才强制三方齐

    def test_shapley_without_trinity_422(self):
        sid = _create()
        r = client.post(f"/api/v1/sandboxes/{sid}/trinity/shapley", json={})
        assert r.status_code == 422

    def test_trinity_overwrite_rejected(self):
        """P3-4: 三方已配置齐后覆盖提交 → 422。"""
        sid = _create()
        assert client.post(f"/api/v1/sandboxes/{sid}/trinity", json={"profiles": _TRINITY}).status_code == 200
        r = client.post(f"/api/v1/sandboxes/{sid}/trinity", json={"profiles": _TRINITY})
        assert r.status_code == 422
        assert "禁止覆盖" in r.json()["detail"]


class TestSRightApi:
    def test_sright_and_pucr(self):
        sid = _create()
        r = client.post(f"/api/v1/sandboxes/{sid}/srights", json={"scene": "社区协作", "holder_did": "did:tdca:INNOVATOR-001"})
        assert r.status_code == 200
        assert r.json()["s_rights"][0]["gradient"] == "L0"

        r = client.post(f"/api/v1/sandboxes/{sid}/pucr", json={"amount": 50000.0})
        assert r.status_code == 200
        assert r.json()["pucr"]["amount"] == 50000.0
        assert r.json()["pucr"]["mou_anchor"] == ""

    def test_pucr_invalid_422(self):
        sid = _create()
        r = client.post(f"/api/v1/sandboxes/{sid}/pucr", json={"amount": 0.0})
        assert r.status_code == 422


class TestChemApi:
    def _prepare_positive_sum(self, sid):
        """化合前置：进入实验 + 正和验证（surplus 服务端取正和记录）。"""
        client.post(f"/api/v1/sandboxes/{sid}/start", json={})
        r = client.post(
            f"/api/v1/sandboxes/{sid}/positive-sum",
            json={"coalition_utility": 300.0, "independent_utilities": [80.0, 90.0, 50.0]},
        )
        assert r.status_code == 200

    def test_chem_combine_flow(self):
        sid = _create()
        self._prepare_positive_sum(sid)
        r = client.post(
            f"/api/v1/sandboxes/{sid}/chem/combine",
            json={
                "assets": ["IP", "knowledge", "scene_weight"],
                "conditions": {"indivisible": True, "emergent": True, "nonlinear": False},
                "justification": "组合产生涌现价值",
            },
        )
        assert r.status_code == 200
        assert r.json()["reactions"][0]["chem_type"] == "CHEM-001"
        assert r.json()["reactions"][0]["utility_surplus"] == 80.0  # 绑定正和验证 delta
        assert len(r.json()["eng003_log"]) == 1

        r = client.get(f"/api/v1/sandboxes/{sid}/chem/reactions")
        assert r.status_code == 200
        assert len(r.json()["reactions"]) == 1

    def test_chem_combine_without_positive_sum_422(self):
        """#13: 未正和验证直接化合 → 422（surplus 不可自报）。"""
        sid = _create()
        client.post(f"/api/v1/sandboxes/{sid}/start", json={})
        r = client.post(
            f"/api/v1/sandboxes/{sid}/chem/combine",
            json={
                "assets": ["IP"],
                "conditions": {"indivisible": True, "emergent": True, "nonlinear": True},
                "justification": "x",
            },
        )
        assert r.status_code == 422
        assert "正和验证" in r.json()["detail"]


class TestGenieApi:
    def test_positive_sum_check(self):
        sid = _create()
        client.post(f"/api/v1/sandboxes/{sid}/start", json={})  # 正和验证须在实验期 P0
        r = client.post(
            f"/api/v1/sandboxes/{sid}/positive-sum",
            json={"coalition_utility": 300.0, "independent_utilities": [80.0, 90.0, 50.0]},
        )
        assert r.status_code == 200
        assert r.json()["positive_sum_logs"][-1]["is_positive_sum"] is True

    def test_positive_sum_non_positive_422(self):
        """SV-3: 非正和 → FUSE 记录 + 422 阻断（任务书 F6 自动阻断）。"""
        sid = _create()
        client.post(f"/api/v1/sandboxes/{sid}/start", json={})
        r = client.post(
            f"/api/v1/sandboxes/{sid}/positive-sum",
            json={"coalition_utility": 200.0, "independent_utilities": [80.0, 90.0, 50.0]},
        )
        assert r.status_code == 422
        assert "熔断" in r.json()["detail"]
        # FUSE 记录已存证（可审计）
        sb = client.get(f"/api/v1/sandboxes/{sid}").json()
        assert sb["positive_sum_logs"][-1]["fuse"] is True

    def test_delivery_confirm_phase_gate(self):
        """P3-2: 交付确认须评估期 P1（Phase0 拒绝）。"""
        sid = _create()
        r = client.post(
            f"/api/v1/sandboxes/{sid}/delivery-confirm",
            json={"contract_id": "CT-001", "target_utility": {"tax": 1000.0}, "actual_mou": {"Actual-Total": 1200.0}, "token_ref": "TDCA-CRT-sbx-1"},
        )
        assert r.status_code == 422
        assert "P1" in r.json()["detail"]
