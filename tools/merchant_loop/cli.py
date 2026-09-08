"""merchant_loop · CLI（M1 本地可跑）

用法:
  python -m merchant_loop.cli publish --config <yaml> [--notarize]
  python -m merchant_loop.cli redeem --benefit <yaml> --event <json> [--notarize]
  python -m merchant_loop.cli roi-report --benefit-id <id> --merchant-id <id> \
      --budget <n> --audience <n> [--discount-rate <n>] [--rebate-rate <n>] [--notarize]
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from .engine import MerchantLoopEngine, RedemptionEvent
from .notary import MerchantLoopNotary
from .roi import RoiService


def _load_yaml(path: str) -> dict:
    if yaml is None:
        raise RuntimeError("[NSFL-TRIGGER] 缺 pyyaml——无法解析 YAML 配置")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("[NSFL-TRIGGER] 配置须为 YAML mapping")
    return data


def cmd_publish(args) -> int:
    raw = _load_yaml(args.config)
    engine = MerchantLoopEngine(default_provenance=args.provenance)
    template = engine.validate_template(raw, provenance=args.provenance)
    out = template.to_dict()
    if args.notarize:
        nca = MerchantLoopNotary().record(out, operation_type="MerchantLoopPublish",
                                          scope_note="merchant_loop 权益发布存证")
        out["nca_id"] = nca["NCA-ID"]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_redeem(args) -> int:
    engine = MerchantLoopEngine()
    template = engine.validate_template(_load_yaml(args.benefit), provenance=args.provenance)
    with open(args.event, "r", encoding="utf-8-sig") as f:
        ev = json.load(f)
    event = RedemptionEvent(**ev)
    notary = MerchantLoopNotary()
    nca_id = ""
    if args.notarize:
        pre = notary.record({"status": "redemption_in_progress", "benefit_id": template.benefit_id,
                             "provenance": args.provenance},
                            operation_type="MerchantLoopRedemption",
                            scope_note="merchant_loop 核销闭环存证（NCA 落证前置）")
        nca_id = pre["NCA-ID"]
    result = engine.redeem(template, event, redemption_nca_id=nca_id)
    out = result.to_dict()
    if args.notarize:
        final = notary.record(out, operation_type="MerchantLoopRedemption",
                              scope_note="merchant_loop 核销闭环存证（含 CCA 贡献值记账预留）")
        out["redemption_nca_id"] = final["NCA-ID"]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_roi(args) -> int:
    svc = RoiService()
    report = svc.build_report(
        benefit_id=args.benefit_id,
        merchant_id=args.merchant_id,
        budget_ceiling=args.budget,
        target_audience=args.audience,
        expected_discount_rate=args.discount_rate,
        expected_rebate_rate=args.rebate_rate,
    )
    out = report.to_dict()
    if args.notarize:
        nca = MerchantLoopNotary().record(out, operation_type="MerchantLoopRoiReport",
                                          scope_note="merchant_loop ROI 三情景仪表盘存证")
        out["nca_id"] = nca["NCA-ID"]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="merchant_loop", description="商家消费权益循环增值服务 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("publish", help="权益发布（模板校验 + 可选 NCA 存证）")
    p.add_argument("--config", required=True, help="权益 YAML 配置")
    p.add_argument("--provenance", default="SIMULATED", help="ID92 数据性质（默认 SIMULATED）")
    p.add_argument("--notarize", action="store_true", help="发布后落 NCA 存证")
    p.set_defaults(func=cmd_publish)

    p2 = sub.add_parser("redeem", help="核销闭环（核销事件→NCA→CCA 贡献值记账预留）")
    p2.add_argument("--benefit", required=True, help="权益 YAML（已发布模板）")
    p2.add_argument("--event", required=True, help="核销事件 JSON")
    p2.add_argument("--provenance", default="SIMULATED", help="ID92 数据性质（默认 SIMULATED）")
    p2.add_argument("--notarize", action="store_true", help="核销落 NCA 存证")
    p2.set_defaults(func=cmd_redeem)

    p3 = sub.add_parser("roi-report", help="ROI 三情景仪表盘（预算平移对照，无资产升值因子）")
    p3.add_argument("--benefit-id", required=True)
    p3.add_argument("--merchant-id", required=True)
    p3.add_argument("--budget", type=float, required=True, help="平移预算（≤历史预算）")
    p3.add_argument("--audience", type=float, required=True, help="权益触达人数（SIMULATED）")
    p3.add_argument("--discount-rate", type=float, default=0.10, help="平均折扣深度")
    p3.add_argument("--rebate-rate", type=float, default=0.03, help="平均让利深度")
    p3.add_argument("--provenance", default="SIMULATED", help="ID92 数据性质（默认 SIMULATED）")
    p3.add_argument("--notarize", action="store_true", help="报告落 NCA 存证")
    p3.set_defaults(func=cmd_roi)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
