"""thingsboard_pool · ThingsBoard 配置权计量 IoT 网关插件（DCD-THINGSBOARD-POOL-001 M1a，A 配置资产池）

ThingsBoard（thingsboard/thingsboard，Apache-2.0，22,294 stars API 实测）是平台级 IoT——
设备接入/管理/数据流。路径 A 配置资产池（HubPort 替代，物理世界能力节点）。

M1a 功能:
  - parse_device_stream: 解析设备事件流（telemetry/event）
  - gateway_metering: 设备接入/数据流 → 配置权计量（计费口径）
  - build_event_nca: 事件轨迹 → NCA 存证（事件溯源同构）
  - l2_market: 计量 → L2 配置权市场对接（计费 + MOU 锚定）

制度锚定: PATH-001（A 配置池）/ CALL-001（L2 市场）/ BIDIR-001（形态①物理叠加层）/ ID92
NSFL-Declaration:
  - 不修改 ThingsBoard 核心（网关插件叠加——物理叠加层，BIDIR-001）
  - 设备流为合成/演示数据（ID92），真实接入需设备连接验证
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

# 设备流事件类型
EVENT_TELEMETRY = "telemetry"
EVENT_DEVICE_JOIN = "device_join"
EVENT_DEVICE_LEAVE = "device_leave"
EVENT_ALARM = "alarm"
EVENT_TYPES = {EVENT_TELEMETRY, EVENT_DEVICE_JOIN, EVENT_DEVICE_LEAVE, EVENT_ALARM}

# 配置权计量参数
DEVICE_JOIN_FEE = 1.0        # 设备接入计量单价（模拟）
TELEMETRY_FEE = 0.1          # 遥测消息计量单价（模拟）


@dataclass(frozen=True)
class GatewayMetering:
    """设备流配置权计量结果。"""
    stream_id: str
    devices_joined: int
    telemetry_count: int
    alarms: int
    metered_value: float
    schedule_tax: float

    def to_dict(self) -> dict:
        return {
            "stream_id": self.stream_id,
            "devices_joined": self.devices_joined,
            "telemetry_count": self.telemetry_count,
            "alarms": self.alarms,
            "metered_value": round(self.metered_value, 4),
            "schedule_tax": round(self.schedule_tax, 4),
        }


class ThingsBoardPoolAdapter:
    """ThingsBoard 配置权计量网关插件（M1a，A 配置资产池）。"""

    def __init__(self, provenance: str = "SIMULATED",
                 schedule_tax_rate: float = 0.02):
        self._provenance = provenance
        self._tax_rate = schedule_tax_rate

    # ---- 解析 ----

    def parse_device_stream(self, raw: str) -> List[dict]:
        """解析设备事件流（JSON/JSONL）。"""
        raw = raw.strip()
        if not raw:
            raise ValueError("[NSFL-TRIGGER] 空设备流")
        events = json.loads(raw) if raw.startswith("[") else [
            json.loads(l) for l in raw.splitlines() if l.strip()]
        if not events:
            raise ValueError("[NSFL-TRIGGER] 设备流无内容")
        for e in events:
            if e.get("type") not in EVENT_TYPES:
                raise ValueError(f"[NSFL-TRIGGER] 非法设备事件类型: {e.get('type')}")
        return events

    # ---- 计量（A-1）----

    def gateway_metering(self, events: List[dict],
                         stream_id: str = "stream-1") -> GatewayMetering:
        """设备接入/数据流 → 配置权计量。

        计费口径: metered = joins × DEVICE_JOIN_FEE + telemetry × TELEMETRY_FEE
        """
        joins = sum(1 for e in events if e["type"] == EVENT_DEVICE_JOIN)
        telemetry = sum(1 for e in events if e["type"] == EVENT_TELEMETRY)
        alarms = sum(1 for e in events if e["type"] == EVENT_ALARM)
        value = joins * DEVICE_JOIN_FEE + telemetry * TELEMETRY_FEE
        return GatewayMetering(
            stream_id=stream_id, devices_joined=joins,
            telemetry_count=telemetry, alarms=alarms,
            metered_value=value, schedule_tax=value * self._tax_rate,
        )

    # ---- NCA 存证（A-2，事件溯源同构）----

    def build_event_nca(self, events: List[dict], metering: GatewayMetering) -> dict:
        """事件轨迹 → NCA 存证。"""
        ts = datetime.now(timezone.utc)
        digest = hashlib.sha256(
            json.dumps(events, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        return {
            "NCA-ID": f"NCA-THINGSBOARD-{ts.strftime('%Y%m%d')}-001",
            "Operation-Type": "IoT-Gateway-Metering",
            "Timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Scope": f"ThingsBoard 设备流配置权计量存证（{metering.stream_id}）",
            "Events-Hash": digest,
            "Metering": metering.to_dict(),
            "Provenance": self._provenance,
        }

    # ---- L2 市场对接（M1b）----

    def l2_market_order(self, metering: GatewayMetering,
                        asset_id: str = "thingsboard-thingsboard",
                        tier: str = "基础") -> dict:
        """计量 → L2 配置权市场订单。"""
        order_id = hashlib.sha256(
            f"{metering.stream_id}:{asset_id}:{datetime.now(timezone.utc).isoformat()}"
            .encode()).hexdigest()[:16]
        return {
            "order_id": order_id,
            "stream_id": metering.stream_id,
            "asset_id": asset_id,
            "config_right_tier": tier,
            "billing_amount": round(metering.metered_value + metering.schedule_tax, 4),
            "mou_anchor": "SIMULATED-MOU（真实计费需 L2 市场结算接入）",
            "status": "PENDING_SETTLEMENT",
        }
