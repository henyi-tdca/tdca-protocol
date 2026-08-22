"""thingsboard_pool · CLI（M1c 端到端入口）。

用法:
  python -m thingsboard_pool.cli meter --stream <json>     # 设备流 → 配置权计量
  python -m thingsboard_pool.cli market --stream <json>    # 计量 → L2 市场订单
"""
from __future__ import annotations

import argparse
import json
import sys

from .gateway import ThingsBoardPoolAdapter


def _load(raw: str) -> str:
    if raw.startswith("@"):
        with open(raw[1:], encoding="utf-8") as f:
            return f.read()
    return raw


def cmd_meter(args) -> int:
    adapter = ThingsBoardPoolAdapter(provenance=args.provenance)
    events = adapter.parse_device_stream(_load(args.stream))
    meter = adapter.gateway_metering(events, stream_id=args.stream_id)
    nca = adapter.build_event_nca(events, meter)
    out = {"metered": meter.to_dict(), "nca": nca}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_market(args) -> int:
    adapter = ThingsBoardPoolAdapter(provenance=args.provenance)
    events = adapter.parse_device_stream(_load(args.stream))
    meter = adapter.gateway_metering(events, stream_id=args.stream_id)
    order = adapter.l2_market_order(meter, asset_id=args.asset, tier=args.tier)
    print(json.dumps({"order": order}, ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="thingsboard_pool", description="ThingsBoard 配置权计量网关")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in (("meter", cmd_meter), ("market", cmd_market)):
        p = sub.add_parser(name)
        p.add_argument("--stream", required=True, help="设备事件流 JSON/JSONL 或 @文件路径")
        p.add_argument("--provenance", default="SIMULATED")
        p.add_argument("--stream-id", default="stream-1")
        if name == "market":
            p.add_argument("--asset", default="thingsboard-thingsboard")
            p.add_argument("--tier", default="基础", choices=["基础", "商用", "生态", "协议"])
        p.set_defaults(func=fn)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
