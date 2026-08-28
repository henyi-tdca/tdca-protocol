# -*- coding: utf-8 -*-
"""COP 动态数据流 M1 测试（TDCA-HANDOFF-KIMI-DATAFLOW-M1-001）

C-1 provider 注册机制: 注册/获取/未注册 fail-closed
C-2 数据性质标注: real/simulated 强制（ID92），非法标注拒绝
C-3 fail-closed: 无数据流/断流/陈旧 → 拒动态决策
C-4 NSFL 熔断联动: 实时状态触发负空间禁区 → frozen
C-5 ThingsBoard 适配: 设备流 → context 键值
"""
import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from context_provider import (  # noqa: E402
    CallableProvider, ContextSnapshot, NoContextError,
    ProviderRegistry, nsfl_dynamic_check, resolve_context,
)
from thingsboard_pool.tb_context_adapter import (  # noqa: E402
    ThingsBoardContextProvider, static_stream,
)


def _stream(events):
    return static_stream(json.dumps(events, ensure_ascii=False))


class TestRegistry:
    def test_register_and_get(self):
        reg = ProviderRegistry()
        p = CallableProvider("demo", lambda: {"k": 1})
        reg.register(p)
        assert reg.get("demo") is p
        assert reg.list() == ["demo"]

    def test_unregistered_fail_closed(self):
        reg = ProviderRegistry()
        with pytest.raises(NoContextError, match="未注册"):
            reg.get("ghost")

    def test_nameless_provider_rejected(self):
        reg = ProviderRegistry()
        p = CallableProvider("x", lambda: {"k": 1})
        p.name = ""
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            reg.register(p)


class TestProvenanceLabeling:
    def test_simulated_label(self):
        s = ContextSnapshot(source="t", values={}, timestamp=time.time(),
                            stream_ok=True, provenance="simulated")
        assert s.provenance == "simulated"

    def test_real_label(self):
        s = ContextSnapshot(source="t", values={}, timestamp=time.time(),
                            stream_ok=True, provenance="real")
        assert s.provenance == "real"

    def test_invalid_provenance_rejected(self):
        """数据性质标注强制：缺标/错标 → 拒绝（ID92）。"""
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            ContextSnapshot(source="t", values={}, timestamp=time.time(),
                            stream_ok=True, provenance="unknown")


class TestFailClosed:
    def test_no_stream_fail_closed(self):
        """无数据流（source=None）→ 拒动态决策。"""
        reg = ProviderRegistry()
        reg.register(ThingsBoardContextProvider(stream_source=None))
        with pytest.raises(NoContextError, match="fail-closed|冻结"):
            resolve_context(reg, "thingsboard")

    def test_broken_stream_fail_closed(self):
        """数据源异常 → 断流 → fail-closed。"""
        def boom():
            raise ConnectionError("net down")
        reg = ProviderRegistry()
        reg.register(ThingsBoardContextProvider(stream_source=boom))
        with pytest.raises(NoContextError):
            resolve_context(reg, "thingsboard")

    def test_stale_snapshot_frozen(self):
        """陈旧快照（超 SLA）→ 冻结拒决策。"""
        old = time.time() - 3600
        reg = ProviderRegistry()
        reg.register(CallableProvider("stale", lambda: {"k": 1, "timestamp": old}))
        with pytest.raises(NoContextError, match="陈旧|冻结"):
            resolve_context(reg, "stale", sla={"max_staleness_s": 10})

    def test_non_snapshot_return_fail_closed(self):
        class Bad:
            name = "bad"
            def fetch(self):
                return {"not": "snapshot"}
        reg = ProviderRegistry()
        reg.register(Bad())
        with pytest.raises(NoContextError, match="非快照"):
            resolve_context(reg, "bad")


class TestDynamicInjection:
    def test_context_values_injected(self):
        reg = ProviderRegistry()
        reg.register(CallableProvider("wx", lambda: {"temp": 26.5, "city": "bj"}))
        out = resolve_context(reg, "wx", sla={"max_staleness_s": 60})
        assert out["context"] == {"temp": 26.5, "city": "bj"}
        assert out["provenance"] == "simulated" and out["gate"] == "pass"

    def test_streaming_updates(self):
        """流式更新：两次 fetch 反映最新值。"""
        seq = iter([{"v": 1}, {"v": 2}])
        reg = ProviderRegistry()
        reg.register(CallableProvider("seq", lambda: next(seq)))
        assert resolve_context(reg, "seq")["context"]["v"] == 1
        assert resolve_context(reg, "seq")["context"]["v"] == 2

    def test_real_provenance_propagates(self):
        reg = ProviderRegistry()
        reg.register(CallableProvider("iot", lambda: {"temp": 20},
                                      provenance="real"))
        assert resolve_context(reg, "iot")["provenance"] == "real"


class TestNsflFusion:
    RULES = [{"key": "critical_alarm", "op": "==", "value": True,
              "reason": "严重告警——负空间熔断"}]

    def test_critical_alarm_triggers_frozen(self):
        out = nsfl_dynamic_check({"critical_alarm": True}, self.RULES)
        assert out["decision"] == "frozen" and out["hit"]["key"] == "critical_alarm"

    def test_normal_state_pass(self):
        out = nsfl_dynamic_check({"critical_alarm": False}, self.RULES)
        assert out["decision"] == "pass"

    def test_threshold_rule(self):
        rules = [{"key": "temp", "op": ">", "value": 80, "reason": "超温"}]
        assert nsfl_dynamic_check({"temp": 91}, rules)["decision"] == "frozen"
        assert nsfl_dynamic_check({"temp": 50}, rules)["decision"] == "pass"

    def test_missing_key_no_false_trigger(self):
        """键缺失/类型不可比 → 不熔断（保守不误熔）。"""
        assert nsfl_dynamic_check({"other": 1}, self.RULES)["decision"] == "pass"
        assert nsfl_dynamic_check({"temp": "hot"},
                                  [{"key": "temp", "op": ">", "value": 80}])["decision"] == "pass"


class TestThingsBoardAdapter:
    EVENTS = [
        {"type": "device_join", "device": "d1"},
        {"type": "device_join", "device": "d2"},
        {"type": "device_leave", "device": "d2"},
        {"type": "telemetry", "device": "d1", "key": "temp", "value": 23.5},
        {"type": "alarm", "device": "d1", "level": "WARN"},
    ]

    def test_device_stream_to_context(self):
        p = ThingsBoardContextProvider(stream_source=_stream(self.EVENTS))
        snap = p.fetch()
        assert snap.stream_ok and snap.values["devices_online"] == 1
        assert snap.values["alarm_count"] == 1
        assert snap.values["critical_alarm"] is False
        assert snap.values["telemetry_latest"] == {"temp": 23.5}

    def test_end_to_end_via_registry(self):
        reg = ProviderRegistry()
        reg.register(ThingsBoardContextProvider(stream_source=_stream(self.EVENTS)))
        out = resolve_context(reg, "thingsboard", sla={"max_staleness_s": 30})
        assert out["context"]["devices_online"] == 1
        assert out["provenance"] == "simulated"

    def test_invalid_stream_fail_closed(self):
        p = ThingsBoardContextProvider(stream_source=_stream([{"type": "bogus"}]))
        snap = p.fetch()
        assert snap.stream_ok is False  # 非法事件类型 → 断流 fail-closed

    def test_real_label_for_real_stream(self):
        """real 设备流标 real（ID92 数据性质纪律）。"""
        p = ThingsBoardContextProvider(stream_source=_stream(self.EVENTS),
                                       provenance="real")
        assert p.fetch().provenance == "real"
