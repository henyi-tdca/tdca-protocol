# -*- coding: utf-8 -*-
"""Runtime M3 测试：L2-R6 NS-Atlas + L2-R7 合约锚定 + L2-R8 NIA-MACM 整合。"""
import time

import pytest


def _atlas(**kw):
    a = NSAtlas(**kw)
    a.register_source("SEA-ADMISSION-001", admin_signature="HUMAN-FOUNDER-001")
    return a


from ns_runtime import (
    NSAtlas,
    AtlasQueryResult,
    NSFLContractAnchor,
    ContractVerdict,
    NIAMACMIntegrator,
    NIAResult,
)


# ---------------------------------------------------------------------------
# L2-R6 NS-Atlas（对齐 ICD §2.1）
# ---------------------------------------------------------------------------

class TestNSAtlas:
    def test_ingest_and_query_safe(self):
        atlas = _atlas()
        atlas.ingest([
            {"nca_source": "SEA-ADMISSION-001", "subject": "S1", "distance": 0.9, "verdict": "SAFE"},
            {"nca_source": "SEA-ADMISSION-001", "subject": "S1", "distance": 0.85, "verdict": "SAFE"},
            {"nca_source": "SEA-ADMISSION-001", "subject": "S1", "distance": 0.8, "verdict": "SAFE"},
        ])
        res = atlas.query("S1")
        assert isinstance(res, AtlasQueryResult)
        assert res.subject == "S1"
        assert res.trajectory_points == 3
        assert res.nca_ref.startswith("NCA-ATLAS")

    def test_approaching_trend_detected(self):
        """连续距离下降 → APPROACHING + 梯度上升（0.95→0.45 降 52.6% → WARNING 档）。"""
        atlas = _atlas()
        for d in (0.95, 0.70, 0.45):
            atlas.ingest_point("S2", d, source_signature="SEA-ADMISSION-001")
        res = atlas.query("S2")
        assert res.trend == "APPROACHING"
        assert res.gradient > 0.3
        assert res.risk_level == "WARNING"  # 0.526 ≥ 0.35（WARNING）且 < 0.65

    def test_diverging_trend(self):
        atlas = _atlas()
        for d in (0.40, 0.65, 0.90):
            atlas.ingest_point("S3", d, source_signature="SEA-ADMISSION-001")
        res = atlas.query("S3")
        assert res.trend == "DIVERGING"
        assert res.risk_level == "SAFE"

    def test_insufficient_data_fail_closed(self):
        """数据不足（<3 点）→ risk_level=HIGH（fail-closed，ID78）。"""
        atlas = _atlas()
        atlas.ingest_point("S4", 0.9, source_signature="SEA-ADMISSION-001")
        res = atlas.query("S4")
        assert res.risk_level == "HIGH"
        assert res.gradient == 1.0

    def test_no_trajectory_fail_closed(self):
        atlas = _atlas()
        res = atlas.query("NOPE")
        assert res.risk_level == "HIGH"
        assert res.trajectory_points == 0

    def test_window_capped(self):
        atlas = _atlas(window=5)
        for i in range(8):
            atlas.ingest_point("S5", 0.8, source_signature="SEA-ADMISSION-001")
        assert len(atlas.trajectory_of("S5")) == 5

    def test_last_30d_window(self):
        atlas = _atlas()
        old = time.time() - 40 * 86400
        atlas.ingest([{"nca_source": "SEA-ADMISSION-001", "subject": "S6", "distance": 0.9, "timestamp": old},
                      {"nca_source": "SEA-ADMISSION-001", "subject": "S6", "distance": 0.85},
                      {"nca_source": "SEA-ADMISSION-001", "subject": "S6", "distance": 0.8}])
        res = atlas.query("S6", window="LAST_30D")
        assert res.trajectory_points == 2  # 旧点被过滤

    def test_query_result_shape(self):
        atlas = _atlas()
        atlas.ingest_point("S7", 0.9, source_signature="SEA-ADMISSION-001")
        atlas.ingest_point("S7", 0.85, source_signature="SEA-ADMISSION-001")
        atlas.ingest_point("S7", 0.8, source_signature="SEA-ADMISSION-001")
        d = atlas.query("S7").to_dict()
        assert set(d) == {"subject", "trend", "gradient", "risk_level",
                          "trajectory_points", "last_update", "nca_ref"}

    def test_ingest_rejects_invalid_distance(self):
        """恶意 NCA 记录（distance 非法）→ 拒绝（防伪造 SAFE，fail-closed）。"""
        atlas = _atlas()
        with pytest.raises(ValueError):
            atlas.ingest([{"nca_source": "SEA-ADMISSION-001", "subject": "S8", "distance": 99.0}])
        with pytest.raises(ValueError):
            atlas.ingest([{"nca_source": "SEA-ADMISSION-001", "subject": "S8", "distance": -1.0}])
        with pytest.raises(ValueError):
            atlas.ingest([{"nca_source": "SEA-ADMISSION-001", "subject": "S8", "distance": "garbage"}])

    def test_ingest_rejects_unknown_verdict(self):
        """未知 verdict → 拒绝（fail-closed）。"""
        atlas = _atlas()
        with pytest.raises(ValueError):
            atlas.ingest([{"nca_source": "SEA-ADMISSION-001", "subject": "S9", "distance": 0.9, "verdict": "MAYBE"}])

    def test_ingest_rejects_unregistered_source(self):
        """未登记来源签名 → 拒绝（防轨迹投毒伪造 SAFE）。"""
        atlas = _atlas()
        with pytest.raises(PermissionError):
            atlas.ingest([{"nca_source": "EVIL-ATTACKER-001", "subject": "S10",
                           "distance": 1.0, "verdict": "SAFE"}])
        # 合法来源注入不落点
        assert len(atlas.trajectory_of("S10")) == 0

    def test_register_source_requires_admin(self):
        """来源登记无管理员签名 → 拒绝（防自建来源后投毒）。"""
        atlas = NSAtlas()
        with pytest.raises(PermissionError):
            atlas.register_source("EVIL-SOURCE-001")

    def test_immutable(self):
        atlas = _atlas()
        with pytest.raises(AttributeError):
            atlas._points = {}


# ---------------------------------------------------------------------------
# L2-R7 智能合约 Runtime 锚定（对齐 ICD §2.2）
# ---------------------------------------------------------------------------

class TestContractAnchor:
    def _anchor(self):
        a = NSFLContractAnchor()
        a.register_escrow("ESCROW-001", 200000.0, admin_signature="HUMAN-FOUNDER-001")
        a.register_audit_integrity("S_agent_cog-001", 0.98, admin_signature="HUMAN-FOUNDER-001")
        a.register_human_signature("HUMAN-FOUNDER-001", admin_signature="HUMAN-FOUNDER-001")
        return a

    def test_allow_with_all_prereqs(self):
        a = self._anchor()
        res = a.precheck("TRANSACTION", subject="S_agent_cog-001",
                         escrow_ref="ESCROW-001")
        assert res.allowed is True
        assert res.immutable is True  # 不可升级恒真（ID33）
        assert res.contract_version == NSFLContractAnchor.CONTRACT_VERSION

    def test_static_hit_blocks_and_deducts(self):
        a = self._anchor()
        res = a.precheck("data.leak", subject="S_agent_cog-001",
                         escrow_ref="ESCROW-001")
        assert res.allowed is False
        assert res.escrow_deduct == 60000.0  # 30% of 200000（BLOCKED 级）
        assert a.escrow_balance("ESCROW-001") == 140000.0

    def test_missing_escrow_fail_closed(self):
        a = NSFLContractAnchor()
        a.register_audit_integrity("S_agent_cog-001", 0.98, admin_signature="HUMAN-FOUNDER-001")
        res = a.precheck("TRANSACTION", subject="S_agent_cog-001")
        assert res.allowed is False
        assert "质押" in res.reason

    def test_low_audit_integrity_fail_closed(self):
        a = NSFLContractAnchor()
        a.register_escrow("ESCROW-002", 50000.0, admin_signature="HUMAN-FOUNDER-001")
        a.register_audit_integrity("S_agent_cog-001", 0.90, admin_signature="HUMAN-FOUNDER-001")  # < 95%
        res = a.precheck("TRANSACTION", subject="S_agent_cog-001",
                         escrow_ref="ESCROW-002")
        assert res.allowed is False
        assert "备案" in res.reason

    def test_major_operation_requires_huf(self):
        a = self._anchor()
        res = a.precheck("WEIGHT_MODIFICATION", subject="S_agent_cog-001",
                         escrow_ref="ESCROW-001")
        assert res.allowed is False
        assert res.human_sign_required is True
        assert "人类签名" in res.reason

    def test_major_operation_forged_signature_rejected(self):
        """伪造签名（不在册）→ 拒绝（HUF 白名单验证）。"""
        a = self._anchor()
        res = a.precheck("WEIGHT_MODIFICATION", subject="S_agent_cog-001",
                         escrow_ref="ESCROW-001", human_signature="FORGED-SIGNATURE-X")
        assert res.allowed is False
        assert "不在册" in res.reason
        assert res.human_sign_required is True

    def test_register_requires_admin(self):
        """登记接口无管理员签名 → 拒绝（防任意注入质押/备案）。"""
        a = NSFLContractAnchor()
        with pytest.raises(PermissionError):
            a.register_escrow("ESCROW-X", 100.0)
        with pytest.raises(PermissionError):
            a.register_audit_integrity("S1", 0.9)

    def test_admin_credentials_injectable(self):
        """管理员凭据可构造注入（生产环境密钥服务覆盖默认模拟态，D-010 加固）。"""
        a = NSFLContractAnchor(admin_credentials=("PROD-KMS-ADMIN-001",))
        with pytest.raises(PermissionError):
            a.register_escrow("ESCROW-Y", 100.0, admin_signature="HUMAN-FOUNDER-001")
        # 注入凭据生效
        a.register_escrow("ESCROW-Y", 100.0, admin_signature="PROD-KMS-ADMIN-001")
        assert a.escrow_balance("ESCROW-Y") == 100.0

    def test_major_operation_with_huf_allowed(self):
        a = self._anchor()
        res = a.precheck("WEIGHT_MODIFICATION", subject="S_agent_cog-001",
                         escrow_ref="ESCROW-001", human_signature="HUMAN-FOUNDER-001")
        assert res.allowed is True

    def test_cryogenic_escrow_lock_after_block(self):
        """负空间命中后 escrow 扣罚生效（BLOCKED 级 30%）；CRYOGENIC 100% 冻结属
        R8 决策后人类处置（HumanGate），非合约自动全额扣罚。"""
        a = NSFLContractAnchor()
        a.register_escrow("ESCROW-003", 50000.0, admin_signature="HUMAN-FOUNDER-001")
        a.register_audit_integrity("S_agent_cog-001", 0.98, admin_signature="HUMAN-FOUNDER-001")
        res = a.precheck("circumvent guard", subject="S_agent_cog-001",
                         escrow_ref="ESCROW-003")
        assert res.allowed is False
        assert res.escrow_deduct == 15000.0  # 30% of 50000
        assert a.escrow_balance("ESCROW-003") == 35000.0

    def test_no_double_deduct_same_delta(self):
        """同一 delta 重复 precheck 不重复扣罚。"""
        a = NSFLContractAnchor()
        a.register_escrow("ESCROW-004", 50000.0, admin_signature="HUMAN-FOUNDER-001")
        a.register_audit_integrity("S_agent_cog-001", 0.98, admin_signature="HUMAN-FOUNDER-001")
        r1 = a.precheck("circumvent guard", subject="S_agent_cog-001",
                        escrow_ref="ESCROW-004", delta_ref="DELTA-1")
        r2 = a.precheck("circumvent guard", subject="S_agent_cog-001",
                        escrow_ref="ESCROW-004", delta_ref="DELTA-1")
        assert r1.escrow_deduct == 15000.0
        assert r2.escrow_deduct == 0.0  # 重复 → 不扣
        assert a.escrow_balance("ESCROW-004") == 35000.0

    def test_verdict_shape(self):
        a = self._anchor()
        res = a.precheck("TRANSACTION", subject="S_agent_cog-001",
                         escrow_ref="ESCROW-001")
        d = res.to_dict()
        assert set(d) == {"allowed", "reason", "escrow_deduct", "contract_version",
                          "immutable", "nca_ref", "human_sign_required"}

    def test_immutable(self):
        a = NSFLContractAnchor()
        with pytest.raises(AttributeError):
            a._escrow_balance = {}


# ---------------------------------------------------------------------------
# L2-R8 NIA-MACM 整合（对齐 ICD §2.3）
# ---------------------------------------------------------------------------

class TestNIAMACM:
    def _ready(self):
        """齐备依赖：合约已注册 + Atlas 有轨迹 + Sensor 可用。"""
        contract = NSFLContractAnchor()
        contract.register_escrow("ESCROW-001", 200000.0, admin_signature="HUMAN-FOUNDER-001")
        contract.register_audit_integrity("S_agent_cog-001", 0.98, admin_signature="HUMAN-FOUNDER-001")
        contract.register_human_signature("HUMAN-FOUNDER-001", admin_signature="HUMAN-FOUNDER-001")
        atlas = _atlas()
        for d in (0.9, 0.85, 0.8):
            atlas.ingest_point("S_agent_cog-001", d, source_signature="SEA-ADMISSION-001")
        return NIAMACMIntegrator(contract=contract, atlas=atlas)

    def test_allow_path(self):
        nia = self._ready()
        res = nia.process(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "CODE_MODIFICATION", "delta_c": "refactor logging module",
             "escrow_ref": "ESCROW-001", "human_signature": "HUMAN-FOUNDER-001"},
        )
        # Sensor SAFE + Atlas SAFE + 合约通过 → ALLOW
        assert res.decision == "ALLOW"
        assert res.constitutional_check == "PASS"
        assert res.alt_path is None

    def test_constitutional_block(self):
        """合约前置未满足 → 宪法审查 BLOCK。"""
        nia = NIAMACMIntegrator()  # 无 escrow 注册
        res = nia.process(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "TRANSACTION"},
        )
        assert res.constitutional_check == "BLOCK"
        assert res.decision in ("BLOCK", "FREEZE")

    def test_sensor_blocked_fuses(self):
        nia = self._ready()
        res = nia.process(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "CODE_MODIFICATION", "delta_c": "disable fuse guard",
             "escrow_ref": "ESCROW-001", "human_signature": "HUMAN-FOUNDER-001"},
        )
        # Sensor BLOCKED → decision BLOCK
        assert res.decision == "BLOCK"
        assert res.alt_path is not None  # 动态微调触发 Alt-Path

    def test_sensor_cryogenic_freezes(self):
        nia = self._ready()
        res = nia.process(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "CODE_MODIFICATION", "delta_c": "modify my own planner",
             "escrow_ref": "ESCROW-001", "human_signature": "HUMAN-FOUNDER-001"},
        )
        assert res.decision == "FREEZE"  # CRYOGENIC → Atomic 冻结

    def test_injection_ignored_without_trust(self):
        """外部伪造注入（未 trusted）→ 忽略，强制内部计算（防绕过 fail-closed）。"""
        nia = self._ready()
        res = nia.process(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "CODE_MODIFICATION", "delta_c": "disable fuse guard",
             "escrow_ref": "ESCROW-001", "human_signature": "HUMAN-FOUNDER-001"},
            sensor_verdict="SAFE",          # 伪造 SAFE
            atlas_result={"risk_level": "SAFE", "trajectory_points": 10},
            contract_verdict={"allowed": True},
        )
        # 注入被忽略 → Sensor 真实判 BLOCKED → BLOCK
        assert res.decision == "BLOCK"

    def test_trusted_injection_honored(self):
        """trusted_injection=True + 正确 token → 注入生效（内部可信编排器）。"""
        nia = self._ready()
        res = nia.process(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "CODE_MODIFICATION", "delta_c": "refactor logging",
             "escrow_ref": "ESCROW-001", "human_signature": "HUMAN-FOUNDER-001"},
            sensor_verdict="SAFE",
            atlas_result={"risk_level": "SAFE", "trajectory_points": 10,
                          "trend": "STABLE", "gradient": 0.1},
            contract_verdict={"allowed": True, "escrow_deduct": 0.0},
            trusted_injection=True,
            inject_token=nia.inject_token(),
        )
        assert res.decision == "ALLOW"

    def test_trusted_injection_rejects_forged_token(self):
        """trusted_injection=True 但 token 伪造 → 注入忽略（防自证 bool 绕过）。"""
        nia = self._ready()
        res = nia.process(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "CODE_MODIFICATION", "delta_c": "disable fuse guard",
             "escrow_ref": "ESCROW-001", "human_signature": "HUMAN-FOUNDER-001"},
            sensor_verdict="SAFE",          # 伪造 SAFE + 伪造 token
            atlas_result={"risk_level": "SAFE", "trajectory_points": 10},
            contract_verdict={"allowed": True},
            trusted_injection=True,
            inject_token="FORGED-TOKEN-123",
        )
        # token 不匹配 → 注入忽略 → Sensor 真实判 BLOCKED → BLOCK
        assert res.decision == "BLOCK"

    def test_atlas_high_blocks(self):
        """Atlas risk_level=HIGH → BLOCK（动态负空间检查；sensor 显式 SAFE 隔离变量）。"""
        nia = self._ready()
        res = nia.process(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "CODE_MODIFICATION", "delta_c": "refactor logging",
             "escrow_ref": "ESCROW-001", "human_signature": "HUMAN-FOUNDER-001"},
            sensor_verdict="SAFE",
            atlas_result={"risk_level": "HIGH", "trajectory_points": 10,
                          "trend": "APPROACHING", "gradient": 0.8},
            trusted_injection=True,
            inject_token=nia.inject_token(),
        )
        assert res.decision == "BLOCK"

    def test_audit_chain_built(self):
        nia = self._ready()
        res = nia.process(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "TRANSACTION", "escrow_ref": "ESCROW-001"},
        )
        assert len(res.audit_chain) >= 2  # constitutional + nested + atlas
        assert all(c.startswith("NCA-NIA-") for c in res.audit_chain)

    def test_result_shape(self):
        nia = self._ready()
        res = nia.process(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "TRANSACTION", "escrow_ref": "ESCROW-001"},
        )
        d = res.to_dict()
        assert set(d) == {"decision", "alt_path", "constitutional_check", "audit_chain"}


# ---------------------------------------------------------------------------
# A-4 热路径时延 <50ms（M3 沿用 M2 标准）
# ---------------------------------------------------------------------------

class TestPerfM3:
    def test_atlas_query_under_50ms(self):
        atlas = _atlas()
        for d in (0.9, 0.85, 0.8):
            atlas.ingest_point("P1", d, source_signature="SEA-ADMISSION-001")
        times = []
        for _ in range(100):
            t0 = time.perf_counter()
            atlas.query("P1")
            times.append((time.perf_counter() - t0) * 1000)
        times.sort()
        assert times[int(len(times) * 0.95)] < 50

    def test_contract_precheck_under_50ms(self):
        a = NSFLContractAnchor()
        a.register_escrow("ESCROW-P", 200000.0, admin_signature="HUMAN-FOUNDER-001")
        a.register_audit_integrity("S_agent_cog-P", 0.98, admin_signature="HUMAN-FOUNDER-001")
        times = []
        for _ in range(100):
            t0 = time.perf_counter()
            a.precheck("TRANSACTION", subject="S_agent_cog-P", escrow_ref="ESCROW-P")
            times.append((time.perf_counter() - t0) * 1000)
        times.sort()
        assert times[int(len(times) * 0.95)] < 50

    def test_nia_process_under_50ms(self):
        nia = NIAMACMIntegrator()
        times = []
        for _ in range(100):
            t0 = time.perf_counter()
            nia.process(
                {"S_agent_cog": {"id": "S_agent_cog-X"}},
                {"type": "TRANSACTION"},
            )
            times.append((time.perf_counter() - t0) * 1000)
        times.sort()
        assert times[int(len(times) * 0.95)] < 50
