"""util_value · 评估服务 CLI（M1 本地可跑）

用法:
  python -m util_value.cli assess --asset <id> --tx <json>
  python -m util_value.cli assess --asset <id> --tx <json> --proposed <val>
"""
from __future__ import annotations

import argparse
import json
import sys

from .engine import UtilValueService
from .notary import UtilValueNotary
from .report import build_assessment_report


def cmd_assess(args) -> int:
    svc = UtilValueService()
    txs = json.loads(args.tx) if args.tx else []
    floor = svc.observable_floor(args.asset, txs, provenance=args.provenance)
    tiers = svc.tier_assessment(args.asset, txs, provenance=args.provenance)
    safety = svc.safety_check(args.proposed, floor.u_observed) if args.proposed is not None else None
    report = build_assessment_report(
        floor, tiers=tiers, safety=safety,
        report_id=args.report_id or f"cli-{args.asset}",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.notarize:
        UtilValueNotary().record(report, operation_type="UtilValueAssess")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="util_value", description="效用价值评估服务 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("assess", help="入表评估（地板+五阶分层+安全熔断）")
    p.add_argument("--asset", required=True, help="资产标识")
    p.add_argument("--tx", help="交易流 JSON: [{\"direction\":\"output|input\",\"amount\":n}]")
    p.add_argument("--proposed", type=float, help="拟议估值（触发安全熔断检查）")
    p.add_argument("--provenance", default="SIMULATED")
    p.add_argument("--report-id")
    p.add_argument("--notarize", action="store_true", help="评估后落 NCA 存证")
    p.set_defaults(func=cmd_assess)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
