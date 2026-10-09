# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     F3 激活系数引擎测试——SV-1 硬编码阈值 + 决策门三档 + 出盒资格
# 约束矩阵:     FC-SBX-OPS-001 SV-1（>1.2 硬编码）+ 开发纪律 1（数据性质标注）
# 先验分布:     任务书 §二 F3 + KB-ECON-001 §7
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F3 激活系数引擎测试（SV-1 硬编码）。"""

from __future__ import annotations

import pytest

from app.activation_engine import (
    ACTIVATION_THRESHOLD,
    BREAKEVEN_THRESHOLD,
    check_exit_eligibility,
    compute_activation,
)


class TestComputeActivation:
    """决策门三档 + SV-1 硬编码阈值。"""

    def test_alpha_gt_12_selffinanced(self):
        # α = (130 + 20) / 100 = 1.5 > 1.2 → 财政自给性达成
        r = compute_activation(pcr_input=100.0, tax_revenue=130.0, employment_ss=20.0)
        assert r["coefficient"] == 1.5
        assert r["status"] == "财政自给性达成"
        assert r["exit_required"] is True  # SV-1: >1.2 出盒必要条件
        assert r["decision"] == "政策可复制推广"

    def test_alpha_exactly_12_not_exit(self):
        # α = 1.2 恰等于阈值 → 不满足 >1.2（SV-1 严格大于）
        r = compute_activation(pcr_input=100.0, tax_revenue=120.0, employment_ss=0.0)
        assert r["coefficient"] == 1.2
        assert r["status"] == "基本盈亏平衡"
        assert r["exit_required"] is False
        assert r["decision"] == "条件续期"

    def test_alpha_between_1_and_12_breakeven(self):
        r = compute_activation(pcr_input=100.0, tax_revenue=110.0, employment_ss=0.0)
        assert r["coefficient"] == 1.1
        assert r["status"] == "基本盈亏平衡"
        assert r["exit_required"] is False

    def test_alpha_exactly_1_unsustainable(self):
        r = compute_activation(pcr_input=100.0, tax_revenue=100.0, employment_ss=0.0)
        assert r["coefficient"] == 1.0
        assert r["status"] == "财政不可持续"
        assert r["exit_required"] is False

    def test_alpha_lt_1_unsustainable_fuse(self):
        r = compute_activation(pcr_input=100.0, tax_revenue=50.0, employment_ss=10.0)
        assert r["coefficient"] == 0.6
        assert r["status"] == "财政不可持续"
        assert r["decision"] == "负空间熔断 / 资产清算"

    def test_round_display_vs_raw_gate(self):
        """门判定用原始精度，显示用 round(6)：α=1.2000004 显示 1.2 但可出盒（SV-1 严格 >）。"""
        r = compute_activation(pcr_input=100.0, tax_revenue=120.00004, employment_ss=0.0)
        assert r["coefficient"] == 1.2  # round(6) 显示
        assert r["exit_required"] is True  # 原始值 1.2000004 > 1.2

    def test_threshold_hardcoded_constant(self):
        # SV-1: 阈值硬编码（1.2），不可被外部参数覆盖
        assert ACTIVATION_THRESHOLD == 1.2
        assert BREAKEVEN_THRESHOLD == 1.0

    def test_pcr_zero_rejected(self):
        with pytest.raises(ValueError):
            compute_activation(pcr_input=0.0, tax_revenue=10.0, employment_ss=0.0)

    def test_negative_inputs_rejected(self):
        with pytest.raises(ValueError):
            compute_activation(pcr_input=100.0, tax_revenue=-1.0, employment_ss=0.0)
        with pytest.raises(ValueError):
            compute_activation(pcr_input=100.0, tax_revenue=10.0, employment_ss=-5.0)

    def test_invalid_data_nature_rejected(self):
        # 开发纪律 1：数据性质必须显式标注（real/simulated），不可缺省伪造
        with pytest.raises(ValueError):
            compute_activation(pcr_input=100.0, tax_revenue=10.0, employment_ss=0.0, data_nature="mock")

    def test_real_data_nature_allowed(self):
        r = compute_activation(pcr_input=100.0, tax_revenue=150.0, employment_ss=0.0, data_nature="real")
        assert r["data_nature"] == "real"
        assert r["status"] == "财政自给性达成"


class TestExitEligibility:
    """出盒资格：SV-1（α>1.2）+ SV-6（三方签名）双必要条件。"""

    def _sig_complete(self):
        return {
            "complete": True,
            "roles": ["innovator", "investor", "government"],
            "count": 3,
            "missing": [],
            "required": 3,
            "reasons": [],
        }

    def test_both_conditions_eligible(self):
        activation = {"exit_required": True, "coefficient": 1.5}
        r = check_exit_eligibility(activation, self._sig_complete())
        assert r["eligible"] is True
        assert r["reasons"] == []

    def test_activation_fail_blocks(self):
        activation = {"exit_required": False, "coefficient": 1.1}
        r = check_exit_eligibility(activation, self._sig_complete())
        assert r["eligible"] is False
        assert any("SV-1" in x for x in r["reasons"])

    def test_signatures_fail_blocks(self):
        activation = {"exit_required": True, "coefficient": 1.5}
        sig = {"complete": False, "roles": ["innovator"], "count": 1, "missing": ["investor", "government"], "required": 3, "reasons": []}
        r = check_exit_eligibility(activation, sig)
        assert r["eligible"] is False
        assert any("SV-6" in x for x in r["reasons"])
