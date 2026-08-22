"""cypress_pool · CLI（M1c 端到端入口）。

用法:
  python -m cypress_pool.cli meter --run <json>     # 测试运行 → 配置权计量
  python -m cypress_pool.cli market --run <json>    # 计量 → L2 市场订单
"""
from __future__ import annotations

import argparse
import json
import sys

from .meter import CypressPoolAdapter


def _load(raw: str) -> str:
    if raw.startswith("@"):
        with open(raw[1:], encoding="utf-8") as f:
            return f.read()
    return raw


def cmd_meter(args) -> int:
    adapter = CypressPoolAdapter(provenance=args.provenance)
    run = adapter.parse_test_run(_load(args.run))
    meter = adapter.metering(run, unit_price=args.price)
    nca = adapter.build_metric_nca(meter)
    out = {"metered": meter.to_dict(), "nca": nca}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_market(args) -> int:
    adapter = CypressPoolAdapter(provenance=args.provenance)
    run = adapter.parse_test_run(_load(args.run))
    meter = adapter.metering(run, unit_price=args.price)
    order = adapter.l2_market_order(meter, asset_id=args.asset, tier=args.tier)
    out = {"order": order.to_dict()}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cypress_pool", description="Cypress 配置权计量")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in (("meter", cmd_meter), ("market", cmd_market)):
        p = sub.add_parser(name)
        p.add_argument("--run", required=True, help="测试运行结果 JSON 或 @文件路径")
        p.add_argument("--provenance", default="SIMULATED")
        p.add_argument("--price", type=float, default=None, help="单价（计费口径）")
        if name == "market":
            p.add_argument("--asset", default="cypress-io-cypress")
            p.add_argument("--tier", default="基础", choices=["基础", "商用", "生态", "协议"])
        p.set_defaults(func=fn)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
