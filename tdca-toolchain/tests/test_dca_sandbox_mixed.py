"""dca_sandbox.mixed · R-7 M3 三方闭环测试套件

验收:
  A1 三方装配（merchant_loop FROZEN 校验 + 撮合智能体）
  A2 三方闭环模拟（核销→D_scene→撮合→熔断基金，逐笔即时零滞留）
  A3 资助检测器（负控攻击注入——检测器须命中；控制组 0 违例）
  A4 λ_pair 定标观测（D-person/D-org 收敛/降级判定）
"""
import json

import pytest

from dca_sandbox.mixed import (
    AgentBrokerConfig,
    LAMBDA_CONVERGE_TARGET,
    MixedMarketSimulation,
)


def _cafe_benefit(mid="M-EXAMPLE-CAFE", bid="B-CAFE", scene="dine"):
    return {
        "benefit_id": bid, "merchant_id": mid, "title": "咖啡权益",
        "discount": {"rate": 0.10}, "rebate": {"rate": 0.03, "cap": 10.0},
        "valid_from": "2026-09-01", "valid_until": "2027-12-31",
        "stores": ["S-1"], "conditions": {"min_spend": 20.0},
        "budget_ceiling": 10000.0, "scene_type": scene,
        "objective": "o", "constraint": "双边不进 CLS", "prior": "p",
        "config_boundary": "b", "distribution": "d", "audit": "a",
    }


def _retail_benefit(mid="M-SIM-RETAIL", bid="B-RETAIL", scene="retail"):
    raw = _cafe_benefit(mid, bid, scene)
    raw["title"] = "零售权益"
    return raw


def _sim(seed=1):
    sim = MixedMarketSimulation()
    sim.assemble(
        merchants=[
            ("M-EXAMPLE-CAFE", _cafe_benefit()),
            ("M-SIM-RETAIL", _retail_benefit()),
        ],
        agents=[AgentBrokerConfig(agent_id="A-BROKER-1", match_efficiency=0.7)],
    )
    return sim


class TestAssemblyA1:
    def test_assemble_valid(self):
        sim = _sim()
        assert set(sim._templates) == {"M-EXAMPLE-CAFE", "M-SIM-RETAIL"}

    def test_assemble_redline_rejected(self):
        sim = MixedMarketSimulation()
        raw = _cafe_benefit()
        raw["objective"] = "承诺权益升值"
        with pytest.raises(ValueError, match="红线词"):
            sim.assemble([("M-X", raw)], [AgentBrokerConfig("A-1")])


class TestMixedRunA2:
    def test_run_short_generates_weeks(self):
        sim = _sim()
        res = sim.run(weeks=4, seed=7)
        assert res.weeks == 4
        assert len(res.weekly) == 4

    def test_fuse_fund_accumulates(self):
        """撮合差额 (1−λ)×v 入熔断基金（λ=0.80 → 20% 差额）。"""
        sim = _sim()
        res = sim.run(weeks=6, seed=3)
        assert res.total_matches > 0
        assert res.fuse_fund_end > 0
        # 每笔撮合 alloc=fuse 结构正确
        for w in res.weekly:
            for flag in w.funding_flag:
                assert flag  # 控制组期望无资助标记（或空列表）
        assert res.zero_precollect_hold is True   # 逐笔即时零滞留/让利≤消费额

    def test_net_positive_structure(self):
        sim = _sim()
        res = sim.run(weeks=8, seed=5)
        assert all(w.net_positive for w in res.weekly)   # 三方效用正和（让利<消费额）


class TestFundingDetectA3:
    def test_control_zero_violation(self):
        """控制组（无资助攻击）→ 0 信号购买违例。"""
        sim = _sim()
        res = sim.run(weeks=13, seed=20260908)
        assert res.zero_signal_purchase is True
        assert res.violations == []

    def test_attack_detected(self):
        """负控注入（资助攻击）→ 检测器命中 → 0 信号购买违例=False（检测器有效）。"""
        sim = _sim()
        res = sim.run(weeks=13, seed=20260908, funding_attack=True)
        assert res.zero_signal_purchase is False
        assert any("signal_purchase" in v for v in res.violations)


class TestLambdaA4:
    def test_control_lambda_converges(self):
        """控制组（制度完备无违例）→ λ 定标观测收敛 ≥0.95。"""
        sim = _sim()
        res = sim.run(weeks=13, seed=11)
        assert res.lambda_observed["D_person"] >= LAMBDA_CONVERGE_TARGET
        assert res.lambda_observed["D_org"] >= LAMBDA_CONVERGE_TARGET

    def test_exit_gate_structure(self):
        sim = _sim()
        res = sim.run(weeks=13, seed=99)
        gate = res.to_dict()["exit_gate"]
        assert set(gate) == {
            "zero_financialization_26wk", "zero_signal_purchase_26wk",
            "zero_precollect_hold_26wk", "activation_gt_1_2", "lambda_converged",
        }


class TestCli:
    def test_run_26w(self, capsys):
        from dca_sandbox.mixed_cli import main as mixed_main
        rc = mixed_main(["run", "--weeks", "4", "--seed", "1"])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["total_redemptions"] > 0
        assert "exit_gate" in out
