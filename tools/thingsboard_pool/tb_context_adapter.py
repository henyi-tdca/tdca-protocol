# -*- coding: utf-8 -*-
"""thingsboard_pool · COP 动态上下文适配层（TDCA-HANDOFF-KIMI-DATAFLOW-M1-001）

ThingsBoard 设备状态流 → context provider（COP 动态上下文注入）。
复用 gateway.parse_device_stream（M1a 零改动），新增 provider 适配。

API 外部依赖（免费优先，收费禁用——预算纪律）:
  - ThingsBoard 社区版公共演示（demo.thingsboard.io，公开遥测端点）
  - 公共 MQTT/HTTP 数据源（如 test.mosquitto.org / 免费 IoT 演示流）
  - 以上均为可选在线通道；M1 默认经注入数据源运行（离线可测），在线失败 fail-closed

数据性质: real 设备流标 real；模拟流标 simulated（ID92）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional

from context_provider import ContextProvider, ContextSnapshot, PROVENANCE_SIMULATED
from thingsboard_pool.gateway import (
    EVENT_ALARM, EVENT_DEVICE_JOIN, EVENT_DEVICE_LEAVE, EVENT_TELEMETRY,
    ThingsBoardPoolAdapter,
)

# 免费公开演示源（收费 API 一律不用）
FREE_DEMO_SOURCES = {
    "thingsboard_ce_demo": "https://demo.thingsboard.io",   # ThingsBoard 社区版公共演示
    "mqtt_public": "test.mosquitto.org",                    # 公共 MQTT 演示代理
}


class ThingsBoardContextProvider(ContextProvider):
    """ThingsBoard 设备状态流 → ContextSnapshot。

    stream_source: 可注入数据源 callable() -> str（原始设备流 JSON），
                   默认 None = 断流（stream_ok=False，fail-closed）。
    """

    name = "thingsboard"

    def __init__(self, stream_source: Optional[Callable[[], str]] = None,
                 provenance: str = PROVENANCE_SIMULATED,
                 gateway: Optional[ThingsBoardPoolAdapter] = None):
        self._source = stream_source
        self._provenance = provenance
        self._gw = gateway or ThingsBoardPoolAdapter()

    def fetch(self) -> ContextSnapshot:
        if self._source is None:
            return ContextSnapshot(source=self.name, values={}, timestamp=time.time(),
                                   stream_ok=False, provenance=self._provenance)
        try:
            raw = self._source()
            events = self._gw.parse_device_stream(raw)
        except Exception:
            return ContextSnapshot(source=self.name, values={}, timestamp=time.time(),
                                   stream_ok=False, provenance=self._provenance)
        if not events:
            return ContextSnapshot(source=self.name, values={}, timestamp=time.time(),
                                   stream_ok=False, provenance=self._provenance)
        values = self._to_context_values(events)
        return ContextSnapshot(source=self.name, values=values, timestamp=time.time(),
                               stream_ok=True, provenance=self._provenance)

    @staticmethod
    def _to_context_values(events) -> Dict[str, Any]:
        """设备事件流 → COP context 键值（设备在线数/最新遥测/告警计数）。"""
        joins = sum(1 for e in events if e.get("type") == EVENT_DEVICE_JOIN)
        leaves = sum(1 for e in events if e.get("type") == EVENT_DEVICE_LEAVE)
        alarms = [e for e in events if e.get("type") == EVENT_ALARM]
        telemetry = [e for e in events if e.get("type") == EVENT_TELEMETRY]
        latest_telemetry: Dict[str, Any] = {}
        for e in telemetry:
            if e.get("key") is not None:
                latest_telemetry[e["key"]] = e.get("value")
        return {
            "devices_online": max(joins - leaves, 0),
            "alarm_count": len(alarms),
            "critical_alarm": any(e.get("level") == "CRITICAL" for e in alarms),
            "telemetry_latest": latest_telemetry,
            "event_count": len(events),
        }


def fetch_public_telemetry(endpoint: str, token: Optional[str] = None,
                           timeout: int = 15) -> str:
    """免费公开遥测通道（HTTP GET → 原始 JSON 串）。

    仅允许 http(s) 免费公开端点；失败抛错由 provider 层 fail-closed 兜底。
    """
    if not endpoint.startswith(("https://", "http://")):
        raise ValueError(f"[NSFL-TRIGGER] 非法端点（仅 http/https 免费公开源）: {endpoint}")
    headers = {"User-Agent": "tdca-thingsboard-context", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(endpoint, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        raise RuntimeError(f"公开源断流: {endpoint}（{e}）——fail-closed") from e


def static_stream(events_json: str) -> Callable[[], str]:
    """字面量/文件注入数据源（离线演示与测试）。"""
    def _src() -> str:
        return events_json
    return _src
