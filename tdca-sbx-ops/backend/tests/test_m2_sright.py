# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F4 S-Right 场景配置权测试——梯度/PUCR（SV-2）/质押
# 约束矩阵:     FC-SBX-OPS-001 SV-2 + 宪法 C13
# 先验分布:     任务书 §二 F4 + sright.py
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F4 S-Right 场景配置权测试。"""

from __future__ import annotations

import pytest

from app.sright import (
    allocate_sright,
    escalate_gradient,
    mature_pledge,
    pucr_presale,
    SRIGHT_GRADIENTS,
)


class TestAllocate:
    def test_allocate_l0_default(self):
        s = allocate_sright("社区协作", "did:tdca:INNOVATOR-001")
        assert s["gradient"] == "L0"
        assert s["gradient_label"]
        assert s["status"] == "active"

    def test_allocate_all_gradients(self):
        for g in SRIGHT_GRADIENTS:
            s = allocate_sright("场景", "did:tdca:X", gradient=g)
            assert s["gradient"] == g

    def test_invalid_gradient_rejected(self):
        with pytest.raises(ValueError):
            allocate_sright("场景", "did:tdca:X", gradient="L4")

    def test_empty_scene_rejected(self):
        with pytest.raises(ValueError):
            allocate_sright("", "did:tdca:X")


class TestGradient:
    def test_escalate_step_by_step(self):
        s = allocate_sright("场景", "did:tdca:X")
        s = escalate_gradient(s, "L1")
        assert s["gradient"] == "L1"
        s = escalate_gradient(s, "L2")
        assert s["gradient"] == "L2"
        s = escalate_gradient(s, "L3")
        assert s["gradient"] == "L3"

    def test_escalate_skip_level_rejected(self):
        """制度梯度必须逐级推进（L0→L2 越级拒绝）。"""
        s = allocate_sright("场景", "did:tdca:X")
        with pytest.raises(ValueError):
            escalate_gradient(s, "L2")


class TestPucr:
    def test_pucr_presale_sv2(self):
        """SV-2: PUCR 预售产生可验证硬数据（amount + data_nature + mou_anchor 位）。"""
        s = allocate_sright("零数据企业", "did:tdca:INNOVATOR-001")
        s = pucr_presale(s, amount=50000.0, data_nature="simulated")
        assert s["pucr"]["amount"] == 50000.0
        assert s["pucr"]["data_nature"] == "simulated"
        assert s["pucr"]["status"] == "pending_verification"
        assert "mou_anchor" in s["pucr"]  # MOU 锚定验证位

    def test_pucr_nonpositive_rejected(self):
        s = allocate_sright("场景", "did:tdca:X")
        with pytest.raises(ValueError):
            pucr_presale(s, amount=0.0)

    def test_pucr_fake_data_nature_rejected(self):
        s = allocate_sright("场景", "did:tdca:X")
        with pytest.raises(ValueError):
            pucr_presale(s, amount=100.0, data_nature="mock")


class TestPledge:
    def test_mature_pledge(self):
        s = allocate_sright("成熟企业", "did:tdca:COMPANY-001")
        s = mature_pledge(s, pledged_asset="自有专利池", pledged_value=200000.0)
        assert s["pledge"]["status"] == "pledged"
        assert s["pledge"]["value"] == 200000.0

    def test_pledge_invalid_rejected(self):
        s = allocate_sright("场景", "did:tdca:X")
        with pytest.raises(ValueError):
            mature_pledge(s, "", 100.0)
        with pytest.raises(ValueError):
            mature_pledge(s, "资产", 0.0)
