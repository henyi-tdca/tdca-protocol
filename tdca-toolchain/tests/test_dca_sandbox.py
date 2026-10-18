"""dca_sandbox · DCA-重塑版沙盒 M1 装配测试套件（DCD-DCA-SANDBOX-001 M1）

装配验收:
  A1 装配: merchant_loop 权益模板经 FROZEN validate_template 校验（6 要素/红线）
  A2 模拟: 周推进日清（逐笔即时让利、现金零滞留、零穿池）
  A3 指标: 核销率聚合/连续达标检测/0 金融化违例/激活系数
  A4 回归: 不破既有（toolchain 全套）
"""
import json

import pytest

from dca_sandbox.cli import main as cli_main
from dca_sandbox.engine import (
    ACTIVATION_THRESHOLD,
    DcaSandboxSimulation,
    MerchantConfig,
    NUCLEAR_RATE_CONSEC_WEEKS,
    NUCLEAR_RATE_TARGET,
    VIOLATION_TERMS,
)
from merchant_loop.engine import BenefitTemplate

# 合法权益模板（六要素齐备，无红线词正向）
def _benefit(bid="B-DCA-1", mid="M-DCA-1"):
    return {
        "benefit_id": bid, "merchant_id": mid, "title": "沙盒权益",
        "discount": {"rate": 0.10}, "rebate": {"rate": 0.03, "cap": 10.0},
        "valid_from": "2026-09-01", "valid_until": "2027-12-31",
        "stores": ["S-1"], "conditions": {"min_spend": 20.0},
        "budget_ceiling": 10000.0, "scene_type": "dine",
        "objective": "o", "constraint": "双边不进 CLS", "prior": "p",
        "config_boundary": "b", "distribution": "d", "audit": "a",
    }


def _merchants(n=1):
    return [
        MerchantConfig(merchant_id=f"M-{i}", benefit_raw=_benefit(f"B-{i}", f"M-{i}"),
                       customer_base=2000.0, arrival_rate=0.30,
                       avg_ticket=100.0, ticket_sigma=25.0)
        for i in range(1, n + 1)
    ]


class TestAssembleA1:
    """A1 装配（merchant_loop FROZEN 接入校验）。"""

    def test_assemble_valid(self):
        sim = DcaSandboxSimulation()
        tpls = sim.assemble(_merchants(2))
        assert len(tpls) == 2
        assert all(isinstance(t, BenefitTemplate) for t in tpls)
        assert [t.benefit_id for t in tpls] == ["B-1", "B-2"]

    def test_assemble_forbidden_rejected(self):
        """红线模板 → merchant_loop validate 拒绝 → Phase0 fail-closed。"""
        raw = _benefit()
        raw["objective"] = "承诺权益升值回馈"   # 正向红线词
        sim = DcaSandboxSimulation()
        with pytest.raises(ValueError, match="红线词"):
            sim.assemble([MerchantConfig("M-1", raw, customer_base=100.0)])


class TestSimulationA2:
    """A2 模拟运行（日清/零穿池/逐笔即时）。"""

    def test_run_short_generates_weeks(self):
        sim = DcaSandboxSimulation()
        sim.assemble(_merchants(1))
        res = sim.run(weeks=4, seed=1)
        assert res.weeks_run == 4
        assert len(res.weekly) == 4
        assert res.phase == "P1"

    def test_cashflow_zero_piercing(self):
        """日清逐笔即时 → 无滞留 → 零穿池恒真。"""
        sim = DcaSandboxSimulation()
        sim.assemble(_merchants(2))
        res = sim.run(weeks=6, seed=42)
        assert res.zero_piercing is True
        for w in res.weekly:
            assert w.cashflow_balance == 0.0   # 逐笔即时让利，无聚合滞留
            assert w.net_revenue >= 0 or w.allowance_cost >= 0  # 非负结构（让利≤消费额）

    def test_redemption_rate_metric(self):
        sim = DcaSandboxSimulation()
        sim.assemble(_merchants(1))
        res = sim.run(weeks=8, seed=7)
        assert 0.0 <= res.avg_redemption_rate <= 1.0
        for w in res.weekly:
            assert 0.0 <= w.redemption_rate <= 1.0


class TestMetricsA3:
    """A3 出盒指标检测器（预埋——M3 评估用）。"""

    def test_no_violations(self):
        sim = DcaSandboxSimulation()
        sim.assemble(_merchants(2))
        res = sim.run(weeks=5, seed=3)
        assert res.violations == []          # 0 金融化违例

    def test_exit_gate_structure(self):
        sim = DcaSandboxSimulation()
        sim.assemble(_merchants(1))
        res = sim.run(weeks=13, seed=20260908)
        gate = res.to_dict()["exit_gate"]
        assert set(gate) == {
            "nuclear_rate_60pct_8wk", "zero_piercing_26wk",
            "zero_financialization_violation", "activation_gt_1_2",
        }
        assert gate["zero_piercing_26wk"] is True
        assert gate["zero_financialization_violation"] is True
        assert isinstance(gate["activation_gt_1_2"], bool)

    def test_cca_signal_present(self):
        sim = DcaSandboxSimulation()
        sim.assemble(_merchants(1))
        res = sim.run(weeks=3, seed=5)
        assert all(w.cca_signal >= 0 for w in res.weekly)   # SIMULATED 占位信号


class TestCli:
    """CLI run 冒烟。"""

    def test_cli_run(self, capsys):
        rc = cli_main(["run", "--weeks", "3", "--seed", "1"])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["phase"] == "P1"
        assert report["weeks_run"] == 3
        assert "assembled_benefits" in report

    def test_cli_run_notarize(self, capsys):
        rc = cli_main(["run", "--weeks", "2", "--seed", "2", "--notarize"])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["nca_id"].startswith("NCA-DCASANDBOX-")
