"""thingsboard_pool · ThingsBoard M1 测试（DCD-THINGSBOARD-POOL-001 验收 A-1~A-5）

A-1 计量网关: 设备接入/数据流 → 配置权计量正确（计费口径）
A-2 存证: 事件流 → NCA 六要素正确
A-3 不碰核心: ThingsBoard 核心零修改（插件叠加）
A-4 测试: ≥16 用例全绿（M1a 10 + M1b 6）
A-5 回归: 既有基线不破
"""
import json

import pytest

from thingsboard_pool.cli import main as cli_main
from thingsboard_pool.gateway import (
    DEVICE_JOIN_FEE,
    TELEMETRY_FEE,
    ThingsBoardPoolAdapter,
)


def _stream(n_join=2, n_tele=5, n_alarm=1):
    events = [{"type": "device_join", "device": f"d{i}"} for i in range(n_join)]
    events += [{"type": "telemetry", "device": "d0", "key": "temp", "value": 20 + i}
               for i in range(n_tele)]
    events += [{"type": "alarm", "device": "d0", "level": "WARN"} for _ in range(n_alarm)]
    return events


class TestParse:
    """解析。"""

    def test_parse_valid(self):
        adapter = ThingsBoardPoolAdapter()
        events = adapter.parse_device_stream(json.dumps(_stream()))
        assert len(events) == 8

    def test_parse_empty_rejected(self):
        adapter = ThingsBoardPoolAdapter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            adapter.parse_device_stream("")

    def test_parse_invalid_type(self):
        adapter = ThingsBoardPoolAdapter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            adapter.parse_device_stream(json.dumps([{"type": "bogus"}]))


class TestMetering:
    """A-1 计量。"""

    def test_metering_counts(self):
        """设备/遥测/告警计数。"""
        adapter = ThingsBoardPoolAdapter()
        m = adapter.gateway_metering(_stream(n_join=2, n_tele=5, n_alarm=1))
        assert m.devices_joined == 2
        assert m.telemetry_count == 5
        assert m.alarms == 1

    def test_metered_value(self):
        """计费 = joins×单价 + telemetry×单价。"""
        adapter = ThingsBoardPoolAdapter()
        m = adapter.gateway_metering(_stream(n_join=2, n_tele=5, n_alarm=0))
        expected = 2 * DEVICE_JOIN_FEE + 5 * TELEMETRY_FEE
        assert m.metered_value == pytest.approx(expected)

    def test_schedule_tax(self):
        """调度税 = 计量价值 × 2%。"""
        adapter = ThingsBoardPoolAdapter()
        m = adapter.gateway_metering(_stream(n_join=10, n_tele=0, n_alarm=0))
        assert m.schedule_tax == pytest.approx(10 * DEVICE_JOIN_FEE * 0.02)

    def test_empty_stream_zero(self):
        """无事件流 → 计费 0。"""
        adapter = ThingsBoardPoolAdapter()
        m = adapter.gateway_metering([])
        assert m.metered_value == 0.0

    def test_alarm_not_charged(self):
        """告警不计费（仅记录）。"""
        adapter = ThingsBoardPoolAdapter()
        m1 = adapter.gateway_metering(_stream(n_join=1, n_tele=0, n_alarm=0))
        m2 = adapter.gateway_metering(_stream(n_join=1, n_tele=0, n_alarm=5))
        assert m1.metered_value == m2.metered_value


class TestNcaStamping:
    """A-2 存证（事件溯源同构）。"""

    def test_nca_generated(self):
        """事件流 → NCA 存证。"""
        adapter = ThingsBoardPoolAdapter()
        events = _stream()
        nca = adapter.build_event_nca(events, adapter.gateway_metering(events))
        assert nca["Operation-Type"] == "IoT-Gateway-Metering"
        assert nca["NCA-ID"].startswith("NCA-THINGSBOARD-")

    def test_nca_events_hash(self):
        """事件哈希（SHA-256，可复核）。"""
        adapter = ThingsBoardPoolAdapter()
        events = _stream()
        nca = adapter.build_event_nca(events, adapter.gateway_metering(events))
        assert len(nca["Events-Hash"]) == 64

    def test_nca_hash_changes(self):
        """不同事件流 → 不同哈希。"""
        adapter = ThingsBoardPoolAdapter()
        e1 = _stream(n_tele=1)
        e2 = _stream(n_tele=2)
        n1 = adapter.build_event_nca(e1, adapter.gateway_metering(e1))
        n2 = adapter.build_event_nca(e2, adapter.gateway_metering(e2))
        assert n1["Events-Hash"] != n2["Events-Hash"]

    def test_nca_provenance(self):
        """ID92: provenance 标注。"""
        adapter = ThingsBoardPoolAdapter(provenance="REAL-DEVICE")
        events = _stream()
        nca = adapter.build_event_nca(events, adapter.gateway_metering(events))
        assert nca["Provenance"] == "REAL-DEVICE"


class TestL2Market:
    """M1b L2 市场对接。"""

    def test_order_generated(self):
        """计量 → L2 市场订单。"""
        adapter = ThingsBoardPoolAdapter()
        m = adapter.gateway_metering(_stream(n_join=2, n_tele=5))
        order = adapter.l2_market_order(m)
        assert order["asset_id"] == "thingsboard-thingsboard"
        assert order["status"] == "PENDING_SETTLEMENT"

    def test_billing_amount(self):
        """计费 = 计量价值 + 调度税。"""
        adapter = ThingsBoardPoolAdapter()
        m = adapter.gateway_metering(_stream(n_join=10, n_tele=0))
        order = adapter.l2_market_order(m)
        expected = 10 * DEVICE_JOIN_FEE * 1.02
        assert order["billing_amount"] == pytest.approx(expected)

    def test_config_tier(self):
        """配置权四档。"""
        adapter = ThingsBoardPoolAdapter()
        m = adapter.gateway_metering(_stream(n_join=1))
        order = adapter.l2_market_order(m, tier="生态")
        assert order["config_right_tier"] == "生态"


class TestCLIAndConstraints:
    """M1c + A-3 不碰核心。"""

    def test_cli_meter(self, capsys):
        """CLI: meter。"""
        rc = cli_main(["meter", "--stream", json.dumps(_stream(n_join=1, n_tele=2))])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert result["metered"]["devices_joined"] == 1

    def test_cli_market(self, capsys):
        """CLI: market。"""
        rc = cli_main(["market", "--stream", json.dumps(_stream(n_join=1)),
                       "--tier", "商用"])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert result["order"]["config_right_tier"] == "商用"

    def test_no_core_modification(self):
        """不碰核心：独立网关插件（无 import ThingsBoard 核心）。"""
        import inspect
        import thingsboard_pool.gateway as mod
        src = inspect.getsource(mod)
        assert "import thingsboard" not in src
