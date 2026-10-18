# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F2 三方协调器测试——注册/审计视图/Shapley 四性质
# 约束矩阵:     KB-ECON-001 §4（Shapley 四性质）+ 开发纪律 3（三方独立审计）
# 先验分布:     任务书 §二 F2 + trinity.py
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F2 三位一体协调器测试（Shapley 四性质）。"""

from __future__ import annotations

import pytest

from app.trinity import ROLE_LABELS, TrinityCoordinator


def _coordinator():
    c = TrinityCoordinator()
    c.register("innovator", "did:tdca:INNOVATOR-001", {"value": 30.0, "type": "ip"}, 5.0)
    c.register("investor", "did:tdca:INVESTOR-001", {"value": 50.0, "type": "capital"}, 8.0)
    c.register("government", "did:tdca:GOV-001", {"value": 20.0, "type": "pcr"}, 2.0)
    return c


def _linear_value(factor=1.0):
    """线性联合价值函数：v(S) = factor * Σ 基础投入（无协同）。"""

    def v(s: frozenset) -> float:
        base = {"innovator": 30.0, "investor": 50.0, "government": 20.0}
        return factor * sum(base.get(r, 0.0) for r in s)

    return v


class TestRegister:
    def test_register_all_three(self):
        c = _coordinator()
        assert set(c.profiles().keys()) == {"innovator", "investor", "government"}

    def test_invalid_role_rejected(self):
        c = TrinityCoordinator()
        with pytest.raises(ValueError):
            c.register("platform", "did:tdca:X", {"value": 1}, 0.0)

    def test_duplicate_role_rejected(self):
        c = _coordinator()
        with pytest.raises(ValueError):
            c.register("innovator", "did:tdca:X2", {"value": 1}, 0.0)

    def test_negative_reservation_rejected(self):
        c = TrinityCoordinator()
        with pytest.raises(ValueError):
            c.register("innovator", "did:tdca:X", {"value": 1}, -1.0)


class TestAuditView:
    def test_audit_view_shows_own_full_peers_summary(self):
        """开发纪律 3：三方独立审计，无单方黑箱（他方仅摘要）。"""
        c = _coordinator()
        view = c.audit_view("innovator")
        assert view["role"] == "innovator"
        assert view["own"]["did"] == "did:tdca:INNOVATOR-001"
        assert view["own"]["contribution"] == {"value": 30.0, "type": "ip"}  # 本方全量
        for peer in view["peers"]:
            assert "contribution" not in peer  # 他方不含贡献明细
            assert peer["did"]  # 他方 DID 可见（审计）

    def test_audit_view_unregistered_rejected(self):
        c = TrinityCoordinator()
        c.register("innovator", "did:tdca:X", {"value": 1}, 0.0)
        with pytest.raises(ValueError):
            c.audit_view("government")  # 合法角色但未注册


class TestShapley:
    def test_efficiency(self):
        """效率性: Σφ_i = v(N)。"""
        c = _coordinator()
        r = c.shapley_allocate(_linear_value())
        assert abs(sum(r["allocations"].values()) - r["total_value"]) < 1e-6
        assert r["properties"]["efficiency"] is True
        # 线性函数 → 各分其基础投入
        assert r["allocations"]["investor"] == 50.0
        assert r["allocations"]["innovator"] == 30.0
        assert r["allocations"]["government"] == 20.0

    def test_symmetry(self):
        """对称性: 同构玩家 → 相同 φ。"""
        c = _coordinator()
        r = c.shapley_allocate(_linear_value())
        assert r["properties"]["symmetry"] is True  # 线性函数下全部同构

    def test_symmetry_exact(self):
        """对称性（精确）: 同价值贡献玩家 → φ 相等。"""

        def v(s: frozenset) -> float:
            return 10.0 * len(s)  # 每加入一个玩家 +10（全员对称）

        c = _coordinator()
        r = c.shapley_allocate(v)
        assert r["properties"]["symmetry"] is True
        assert abs(r["allocations"]["innovator"] - r["allocations"]["investor"]) < 1e-6

    def test_dummy(self):
        """Dummy 性: 无边际贡献玩家 → φ=0。"""

        def v(s: frozenset) -> float:
            # government 无贡献（价值只取决于 innovator+investor 数量）
            base = {"innovator": 40.0, "investor": 40.0, "government": 0.0}
            return sum(base.get(r, 0.0) for r in s)

        c = _coordinator()
        r = c.shapley_allocate(v)
        assert r["properties"]["dummy"] is True
        assert r["allocations"]["government"] == 0.0

    def test_additivity(self):
        """可加性: φ(v1+v2) = φ(v1) + φ(v2)（独立验证方法）。"""
        c = _coordinator()
        assert c.verify_additivity(_linear_value(1.0), _linear_value(2.0)) is True

    def test_missing_trinity_rejected(self):
        c = TrinityCoordinator()
        c.register("innovator", "did:tdca:X", {"value": 1}, 0.0)
        with pytest.raises(ValueError):
            c.shapley_allocate(_linear_value())
