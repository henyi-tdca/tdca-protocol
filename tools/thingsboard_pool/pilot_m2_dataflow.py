# -*- coding: utf-8 -*-
"""thingsboard_pool · 数据流 M2 试点（TDCA-HANDOFF-KIMI-M2ME-001 / GSEQ-0693）

设备流 → COP 动态决策 端到端实证（real 标注，ID92）：
  真实公开数据源（open-meteo 免费无密钥气象 API，实时值）
  → 设备事件流（telemetry 事件，真实值薄映射，映射规则本文件内公开）
  → ThingsBoardContextProvider（复用 gateway.parse_device_stream 零改动）
  → ProviderRegistry + resolve_context（律三 v2 新鲜度门，SLA 15s）
  → nsfl_dynamic_check（负空间熔断联动）
  → COP 决策（pass → proceed + 配置权计量 + NCA 存证；frozen → 熔断拒动）

数据源说明（预算纪律：免费 API 优先、收费禁用）：
  M1 声明的 demo.thingsboard.io 公开遥测端点需租户凭证、test.mosquitto.org 为
  MQTT 协议（本运行层为 HTTP 通道），均不适用于本试点；选用 open-meteo 免费公开
  API（无需密钥、非商业用途免费），真实实时数据，provenance=real。

用法: python tools/thingsboard_pool/pilot_m2_dataflow.py [--out <evidence.json>]
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # tools/ 入路径

from context_provider import (PROVENANCE_REAL, ProviderRegistry,  # noqa: E402
                              nsfl_dynamic_check, resolve_context)
from thingsboard_pool.gateway import EVENT_TELEMETRY, ThingsBoardPoolAdapter  # noqa: E402
from thingsboard_pool.tb_context_adapter import ThingsBoardContextProvider  # noqa: E402

# 真实数据源（免费公开、无密钥；北京气象实时值）
# 选型记录：open-meteo 本网络超时（实测 12s 无响应）；wttr.in 实测 200 可达，采用之
REAL_SOURCE_URL = "https://wttr.in/Beijing?format=j1"

# wttr.in current_condition 数值字段 → 遥测键白名单（薄映射，键名透传不捏造）
_TELEMETRY_KEYS = ("temp_C", "FeelsLikeC", "humidity", "windspeedKmph", "pressure")

# COP 负空间规则（试点口径）：极端实时状态 → frozen
NSFL_RULES = [
    {"key": "critical_alarm", "op": "==", "value": True,
     "reason": "严重告警在场——负空间禁区，冻结动态决策"},
    {"key": "event_count", "op": "<", "value": 1,
     "reason": "空事件流——无有效实时状态，冻结"},
]


def fetch_real_telemetry(url: str = REAL_SOURCE_URL, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "tdca-dataflow-m2-pilot"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def to_event_stream(payload: dict) -> str:
    """真实气象当前值 → 设备事件流（薄映射，白名单键透传不捏造）。"""
    cur = payload["current_condition"][0]
    obs_time = cur.get("observation_time")
    events = [
        {"type": EVENT_TELEMETRY, "key": f"wttr.{k}", "value": float(cur[k]),
         "ts": obs_time}
        for k in _TELEMETRY_KEYS if k in cur
    ]
    return json.dumps(events, ensure_ascii=False)


def run_pilot(out_path: str | None = None) -> dict:
    gw = ThingsBoardPoolAdapter(provenance=PROVENANCE_REAL)
    raw_payload = fetch_real_telemetry()
    stream = to_event_stream(raw_payload)

    provider = ThingsBoardContextProvider(
        stream_source=lambda: stream, provenance=PROVENANCE_REAL, gateway=gw)
    registry = ProviderRegistry()
    registry.register(provider)

    resolved = resolve_context(registry, "thingsboard", sla={"max_staleness_s": 15})
    fuse = nsfl_dynamic_check(resolved["context"], NSFL_RULES)

    events = gw.parse_device_stream(stream)
    meter = gw.gateway_metering(events, stream_id="m2-pilot-openmeteo-20260829")
    nca = gw.build_event_nca(events, meter)

    decision = "frozen" if fuse["decision"] == "frozen" else "proceed"
    evidence = {
        "doc": "TDCA-DATAFLOW-M2-PILOT-001",
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provenance": PROVENANCE_REAL,
        "source": {"url": REAL_SOURCE_URL, "kind": "free-public-no-key",
                   "note": "wttr.in 实时气象（免费 API 纪律内）；声明源 demo.thingsboard.io "
                           "需租户凭证 / test.mosquitto.org 为 MQTT / open-meteo 本网络超时，"
                           "均不适用，如实记录"},
        "source_time": (raw_payload.get("current_condition") or [{}])[0].get("observation_time"),
        "events": events,
        "context": resolved,
        "nsfl_fuse": fuse,
        "cop_decision": decision,
        "metering": meter.to_dict(),
        "nca": nca,
    }
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(evidence, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
    return evidence


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pilot_m2_dataflow")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    ev = run_pilot(args.out)
    print(json.dumps({
        "cop_decision": ev["cop_decision"],
        "provenance": ev["provenance"],
        "gate": ev["context"]["gate"],
        "staleness_s": ev["context"]["staleness_s"],
        "fuse": ev["nsfl_fuse"]["decision"],
        "metered": ev["metering"]["metered_value"],
        "nca_id": ev["nca"]["NCA-ID"],
        "events": len(ev["events"]),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
