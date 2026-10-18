"""cypress_pool · Cypress M1 测试（DCD-CYPRESS-POOL-001 验收 A-1~A-5）

A-1 计量 reporter: 测试运行 → 配置权计量正确（计费口径）
A-2 存证: 执行轨迹 → NCA 六要素正确
A-3 不碰核心: Cypress 核心零修改（reporter 插件叠加）
A-4 测试: ≥16 用例全绿（M1a 10 + M1b 6）
A-5 回归: 既有基线不破
"""
import json

import pytest

from cypress_pool.cli import main as cli_main
from cypress_pool.meter import SCHEDULE_TAX_RATE, CypressPoolAdapter


def _run(run_id="run-1", n_pass=3, n_fail=1):
    tests = [{"name": f"t{i}", "status": "passed"} for i in range(n_pass)]
    tests += [{"name": f"f{i}", "status": "failed"} for i in range(n_fail)]
    return {"run_id": run_id, "tests": tests}


class TestParse:
    """解析。"""

    def test_parse_valid(self):
        adapter = CypressPoolAdapter()
        run = adapter.parse_test_run(json.dumps(_run()))
        assert len(run["tests"]) == 4

    def test_parse_empty_rejected(self):
        adapter = CypressPoolAdapter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            adapter.parse_test_run("")

    def test_parse_missing_tests(self):
        adapter = CypressPoolAdapter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            adapter.parse_test_run(json.dumps({"run_id": "x"}))


class TestMetering:
    """A-1 计量。"""

    def test_metering_counts(self):
        """通过/失败计数正确。"""
        adapter = CypressPoolAdapter()
        m = adapter.metering(_run(n_pass=3, n_fail=1))
        assert m.total_tests == 4
        assert m.passed_tests == 3
        assert m.failed_tests == 1

    def test_pass_rate(self):
        """通过率计算。"""
        adapter = CypressPoolAdapter()
        m = adapter.metering(_run(n_pass=3, n_fail=1))
        assert m.pass_rate == pytest.approx(0.75)

    def test_metered_value(self):
        """计量价值 = 通过数 × 单价。"""
        adapter = CypressPoolAdapter(unit_price=10.0)
        m = adapter.metering(_run(n_pass=3, n_fail=1))
        assert m.metered_value == 30.0

    def test_schedule_tax(self):
        """调度税 = 计量价值 × 税率（L3 资产层，CALL-001）。"""
        adapter = CypressPoolAdapter(unit_price=100.0)
        m = adapter.metering(_run(n_pass=2, n_fail=0))
        assert m.schedule_tax == pytest.approx(200.0 * SCHEDULE_TAX_RATE)

    def test_all_failed(self):
        """全失败 → 计费 0（无正和产出）。"""
        adapter = CypressPoolAdapter()
        m = adapter.metering(_run(n_pass=0, n_fail=4))
        assert m.metered_value == 0.0
        assert m.pass_rate == 0.0

    def test_custom_price_per_call(self):
        """单次调用可传单价。"""
        adapter = CypressPoolAdapter()
        m = adapter.metering(_run(n_pass=2, n_fail=0), unit_price=5.0)
        assert m.metered_value == 10.0


class TestNcaStamping:
    """A-2 存证。"""

    def test_nca_generated(self):
        """计量 → NCA 存证。"""
        adapter = CypressPoolAdapter()
        nca = adapter.build_metric_nca(adapter.metering(_run()))
        assert nca["Operation-Type"] == "Test-Metering"
        assert nca["NCA-ID"].startswith("NCA-CYPRESS-")

    def test_nca_contains_metrics(self):
        """NCA 含计量明细。"""
        adapter = CypressPoolAdapter()
        nca = adapter.build_metric_nca(adapter.metering(_run(n_pass=3, n_fail=1)))
        assert nca["Metered-Run"]["passed_tests"] == 3

    def test_nca_provenance(self):
        """ID92: provenance 标注。"""
        adapter = CypressPoolAdapter(provenance="REAL-CI")
        nca = adapter.build_metric_nca(adapter.metering(_run()))
        assert nca["Provenance"] == "REAL-CI"


class TestL2Market:
    """A-2/M1b L2 市场对接。"""

    def test_order_generated(self):
        """计量 → L2 市场订单。"""
        adapter = CypressPoolAdapter(unit_price=100.0)
        meter = adapter.metering(_run(n_pass=2, n_fail=0))
        order = adapter.l2_market_order(meter)
        assert order.asset_id == "cypress-io-cypress"
        assert order.status == "PENDING_SETTLEMENT"

    def test_billing_amount(self):
        """计费金额 = 计量价值 + 调度税。"""
        adapter = CypressPoolAdapter(unit_price=100.0)
        meter = adapter.metering(_run(n_pass=2, n_fail=0))
        order = adapter.l2_market_order(meter)
        expected = 200.0 + 200.0 * SCHEDULE_TAX_RATE
        assert order.billing_amount == pytest.approx(expected)

    def test_config_tier(self):
        """配置权四档可选。"""
        adapter = CypressPoolAdapter()
        meter = adapter.metering(_run(n_pass=1, n_fail=0))
        order = adapter.l2_market_order(meter, tier="商用")
        assert order.config_right_tier == "商用"

    def test_order_id_unique(self):
        """订单 ID 唯一。"""
        adapter = CypressPoolAdapter()
        o1 = adapter.l2_market_order(adapter.metering(_run(run_id="a")))
        o2 = adapter.l2_market_order(adapter.metering(_run(run_id="b")))
        assert o1.order_id != o2.order_id


class TestCLIAndConstraints:
    """M1c + A-3 不碰核心。"""

    def test_cli_meter(self, capsys):
        """CLI: meter。"""
        rc = cli_main(["meter", "--run", json.dumps(_run()), "--price", "10"])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert result["metered"]["passed_tests"] == 3

    def test_cli_market(self, capsys):
        """CLI: market。"""
        rc = cli_main(["market", "--run", json.dumps(_run(n_pass=2, n_fail=0)),
                       "--price", "100", "--tier", "商用"])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert result["order"]["config_right_tier"] == "商用"

    def test_no_core_modification(self):
        """不碰核心：独立 reporter（无 import Cypress 核心）。"""
        import inspect
        import cypress_pool.meter as mod
        src = inspect.getsource(mod)
        assert "import cypress" not in src
