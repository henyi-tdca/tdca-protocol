# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     F1 沙盒生命周期状态机测试——全流程 + 非法转移拒绝 + SV-1/SV-6 出盒门
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 宪法十六条（可观测）
# 先验分布:     任务书 §二 F1 + §3.2 状态机
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F1 沙盒生命周期状态机测试。"""

from __future__ import annotations

import pytest

from app import store
from app.models import Phase
from app.sandbox_core import SandboxCore

core = SandboxCore()

_SIX = {
    "目标函数": "测试沙盒",
    "约束矩阵": "FC-SBX-OPS-001 SV-1~7",
    "先验分布": "任务书 FROZEN",
    "配置权边界": "L2 层",
    "预期分配": "测试",
    "审计轨迹": "TDCA-NCA-{YYYYMMDD}-{SEQ}",
}


def _create(name="测试沙盒", initiator_did="did:tdca:INNOVATOR-001", initiator_role="innovator"):
    return core.create(name, initiator_did, initiator_role, dict(_SIX))


def _sig_all():
    return [
        {"role": "innovator", "did": "did:tdca:INNOVATOR-001", "signature": "sig-innovator"},
        {"role": "investor", "did": "did:tdca:INVESTOR-001", "signature": "sig-investor"},
        {"role": "government", "did": "did:tdca:GOV-001", "signature": "sig-gov"},
    ]


class TestCreate:
    def test_create_phase0_with_nca(self):
        sb = _create()
        assert sb.phase == Phase.PHASE0
        assert sb.sandbox_id.startswith("did:tdca:sandbox:")
        assert len(sb.nca_ids) == 1  # SV-7: 创建即存证
        assert store.load_sandbox(sb.sandbox_id) is not None

    def test_create_rejects_incomplete_six_elements(self):
        with pytest.raises(ValueError):
            core.create("x", "did:tdca:INNOVATOR-001", "innovator", {"目标函数": "only"})

    def test_create_rejects_invalid_initiator_role(self):
        """V-20 修复：发起方必须为五主体之一（任务书 §二 F1）。"""
        with pytest.raises(ValueError) as exc:
            core.create("x", "did:tdca:INNOVATOR-001", "hacker", dict(_SIX))
        assert "五主体" in str(exc.value)

    def test_create_rejects_empty_fields(self):
        with pytest.raises(ValueError):
            core.create("", "did:tdca:INNOVATOR-001", "innovator", dict(_SIX))


class TestConfigure:
    def test_configure_pucr_recorded(self):
        sb = _create()
        sb = core.configure(sb.sandbox_id, pucr={"amount": 50000, "data_nature": "simulated"})
        assert sb.pucr["amount"] == 50000
        assert sb.phase == Phase.PHASE0

    def test_configure_rejects_nonpositive_pucr(self):
        sb = _create()
        with pytest.raises(ValueError):
            core.configure(sb.sandbox_id, pucr={"amount": 0})


class TestLifecycle:
    def test_full_flow_to_exit(self):
        """Phase0 → P0 → P1 → Exit 全流程（SV-1 α>1.2 + SV-6 三方签名）。"""
        sb = _create()
        core.configure(sb.sandbox_id, pucr={"amount": 10000})
        sb = core.start_experiment(sb.sandbox_id, operator_did="did:tdca:INNOVATOR-001")
        assert sb.phase == Phase.P0

        sb = core.run_iteration(sb.sandbox_id, {"metric": "users", "value": 100})
        assert len(sb.eng003_log) == 1  # ENG-003 日志预埋（开发纪律 5）
        sb = core.run_iteration(sb.sandbox_id, {"metric": "users", "value": 200})
        assert len(sb.eng003_log) == 2

        sb = core.evaluate(sb.sandbox_id, pcr_input=100.0, tax_revenue=150.0, employment_ss=20.0)
        assert sb.phase == Phase.P1
        assert sb.activation_logs[-1]["coefficient"] == 1.7
        assert sb.activation_logs[-1]["status"] == "财政自给性达成"

        sb = core.exit(sb.sandbox_id, _sig_all(), human_signatory="did:tdca:HUMAN-FOUNDER-001")
        assert sb.phase == Phase.EXIT

    def test_invalid_transition_phase0_to_p1_rejected(self):
        sb = _create()
        with pytest.raises(ValueError):
            core.evaluate(sb.sandbox_id, pcr_input=100.0, tax_revenue=150.0, employment_ss=20.0)  # Phase0→P1 非法

    def test_run_only_in_p0(self):
        sb = _create()
        with pytest.raises(ValueError):
            core.run_iteration(sb.sandbox_id, {"m": 1})  # 准入期不可运行

    def test_exit_requires_activation_greater_than_12(self):
        """SV-1: 激活系数 ≤1.2 出盒被拒。"""
        sb = _create()
        core.start_experiment(sb.sandbox_id, "did:tdca:INNOVATOR-001")
        core.evaluate(sb.sandbox_id, pcr_input=100.0, tax_revenue=110.0, employment_ss=0.0)  # α=1.1
        with pytest.raises(ValueError) as exc:
            core.exit(sb.sandbox_id, _sig_all(), human_signatory="did:tdca:HUMAN-FOUNDER-001")
        assert "SV-1" in str(exc.value)

    def test_exit_requires_trinity_signatures(self):
        """SV-6: 三方签名不足出盒被拒。"""
        sb = _create()
        core.start_experiment(sb.sandbox_id, "did:tdca:INNOVATOR-001")
        core.evaluate(sb.sandbox_id, pcr_input=100.0, tax_revenue=150.0, employment_ss=0.0)  # α=1.5
        partial = _sig_all()[:1]  # 仅创新者 1 签
        with pytest.raises(ValueError) as exc:
            core.exit(sb.sandbox_id, partial, human_signatory="did:tdca:HUMAN-FOUNDER-001")
        assert "SV-6" in str(exc.value)

    def test_exit_without_evaluation_rejected(self):
        sb = _create()
        core.start_experiment(sb.sandbox_id, "did:tdca:INNOVATOR-001")
        with pytest.raises(ValueError):
            core.exit(sb.sandbox_id, _sig_all(), human_signatory="did:tdca:HUMAN-FOUNDER-001")

    def test_exit_rejects_empty_human_signatory(self):
        """V-06 修复：出盒人类最终签批不可为空（任务书 §七）。"""
        sb = _create()
        core.start_experiment(sb.sandbox_id, "did:tdca:INNOVATOR-001")
        core.evaluate(sb.sandbox_id, pcr_input=100.0, tax_revenue=150.0, employment_ss=0.0)  # α=1.5
        with pytest.raises(ValueError) as exc:
            core.exit(sb.sandbox_id, _sig_all(), human_signatory="")
        assert "人类最终签名" in str(exc.value)


class TestClose:
    def test_close_unsustainable_alpha(self):
        """α ≤ 1.0 → 负空间熔断路径（SV-3 预埋）。"""
        sb = _create()
        core.start_experiment(sb.sandbox_id, "did:tdca:INNOVATOR-001")
        sb = core.evaluate(sb.sandbox_id, pcr_input=100.0, tax_revenue=50.0, employment_ss=0.0)  # α=0.5
        assert sb.activation_logs[-1]["status"] == "财政不可持续"
        sb = core.close(
            sb.sandbox_id,
            trigger_role="government",
            reason="负空间熔断：财政不可持续",
            human_signatory="did:tdca:HUMAN-FOUNDER-001",
        )
        assert sb.phase == Phase.CLOSED

    def test_close_fuse_marker_inherited_from_activation(self):
        """V-07 修复：熔断标记结构化继承（reason 不含关键词时仍标 FUSE）。"""
        from app.nca_logger import load_nca

        sb = _create()
        core.start_experiment(sb.sandbox_id, "did:tdca:INNOVATOR-001")
        core.evaluate(sb.sandbox_id, pcr_input=100.0, tax_revenue=40.0, employment_ss=0.0)  # α=0.4 财政不可持续
        sb = core.close(
            sb.sandbox_id,
            trigger_role="government",
            reason="财政自给性未达成，进入资产清算",  # 不含"熔断/负空间"关键词
            human_signatory="did:tdca:HUMAN-FOUNDER-001",
        )
        nca = load_nca(sb.nca_ids[-1])
        assert nca is not None
        assert nca["negative_space_check"] == "FUSE"  # 继承 activation_log 判定，非文本启发式

    def test_close_trinity_termination_sv4(self):
        """SV-4: 三方任何一方可触发终止。"""
        sb = _create()
        sb = core.close(sb.sandbox_id, trigger_role="investor", reason="三方终止", human_signatory="did:tdca:HUMAN-FOUNDER-001")
        assert sb.phase == Phase.CLOSED

    def test_close_rejects_non_trinity_role(self):
        sb = _create()
        with pytest.raises(ValueError):
            core.close(sb.sandbox_id, trigger_role="platform", reason="x", human_signatory="did:tdca:HUMAN-FOUNDER-001")

    def test_close_terminal_state_rejected(self):
        sb = _create()
        core.close(sb.sandbox_id, trigger_role="government", reason="熔断", human_signatory="did:tdca:HUMAN-FOUNDER-001")
        with pytest.raises(ValueError):
            core.close(sb.sandbox_id, trigger_role="government", reason="again", human_signatory="did:tdca:HUMAN-FOUNDER-001")


class TestNcaIntegration:
    def test_every_operation_has_nca(self):
        sb = _create()
        sb = core.configure(sb.sandbox_id, pucr={"amount": 10000})
        sb = core.start_experiment(sb.sandbox_id, "did:tdca:INNOVATOR-001")
        sb = core.run_iteration(sb.sandbox_id, {"m": 1})
        sb = core.evaluate(sb.sandbox_id, pcr_input=100.0, tax_revenue=150.0, employment_ss=20.0)
        # 每操作一个 NCA（SV-7 全操作存证）
        assert len(sb.nca_ids) == 5  # create/configure/start/run/evaluate
