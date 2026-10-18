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
from .accounting import UtilValueAccounting


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


def cmd_entry(args) -> int:
    acct = UtilValueAccounting()
    txs = json.loads(args.tx) if args.tx else []
    report = acct.full_entry_report(
        asset_id=args.asset, transactions=txs,
        period=args.period,
        proposed_valuation=args.proposed,
        account=args.account,
        provenance=args.provenance,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.notarize:
        UtilValueNotary().record(report, operation_type="UtilValueEntry")
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

    p2 = sub.add_parser("entry", help="M2 入表服务（会计口径报告 + 版权链存证）")
    p2.add_argument("--asset", required=True, help="资产标识")
    p2.add_argument("--tx", help="交易流 JSON")
    p2.add_argument("--period", default="2026-08", help="会计期间（YYYY-MM）")
    p2.add_argument("--proposed", type=float, help="拟议估值（触发安全熔断检查）")
    p2.add_argument("--account", help="会计科目（默认 无形资产-版权资产）")
    p2.add_argument("--provenance", default="SIMULATED")
    p2.add_argument("--notarize", action="store_true", help="评估后落 NCA 存证")
    p2.set_defaults(func=cmd_entry)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
