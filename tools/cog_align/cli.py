"""cog_align · 评测服务 CLI（M1 本地可跑）

用法:
  python -m cog_align.cli measure --a <id> --state-a <json> --b <id> --state-b <json>
  python -m cog_align.cli event --event <e> --states <json>
  python -m cog_align.cli convergence --a <id> --b <id> --series <json>
"""
from __future__ import annotations

import argparse
import json
import sys

from .engine import CogAlignService
from .notary import CogAlignNotary
from .report import build_convergence_report, build_multi_report, build_pair_report
from .scenarios import CogAlignScenarios


def _load_json(raw: str) -> dict:
    return json.loads(raw)


def cmd_measure(args) -> int:
    svc = CogAlignService()
    s_a = _load_json(args.state_a)
    s_b = _load_json(args.state_b)
    measure = svc.measure(args.a, s_a, args.b, s_b, provenance=args.provenance)
    report = build_pair_report(measure, args.report_id or f"cli-{args.a}-{args.b}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.notarize:
        CogAlignNotary().record(report, operation_type="CogAlignMeasure")
    return 0


def cmd_event(args) -> int:
    svc = CogAlignService()
    states = _load_json(args.states)
    measure = svc.evaluate_event(args.event, states, provenance=args.provenance)
    report = build_multi_report(measure, args.report_id or f"cli-event-{args.event}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.notarize:
        CogAlignNotary().record(report, operation_type="CogAlignMeasure")
    return 0


def cmd_convergence(args) -> int:
    svc = CogAlignService()
    series = _load_json(args.series)  # [ [ts, s_a, s_b], ... ]
    trace = svc.convergence(args.a, args.b, series, provenance=args.provenance)
    report = build_convergence_report(trace, args.report_id or f"cli-conv-{args.a}-{args.b}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.notarize:
        CogAlignNotary().record(report, operation_type="CogAlignConvergence")
    return 0


def cmd_scenario(args) -> int:
    svc = CogAlignService()
    scenarios = CogAlignScenarios(svc)
    if args.scenario == "thought-virus":
        result = scenarios.thought_virus_defense(
            subject=args.subject,
            state_series=[tuple(x) for x in _load_json(args.series)],
            baseline_state=_load_json(args.baseline),
            provenance=args.provenance,
        )
    elif args.scenario == "drift-monitor":
        result = scenarios.cognitive_drift_monitor(
            subject_a=args.a, subject_b=args.b,
            state_series=[tuple(x) for x in _load_json(args.series)],
            provenance=args.provenance,
        )
    elif args.scenario == "tiering":
        result = scenarios.alignment_tiering(
            args.a, _load_json(args.state_a), args.b, _load_json(args.state_b),
            provenance=args.provenance,
        )
    else:
        raise ValueError(f"[NSFL-TRIGGER] 未知场景: {args.scenario}")
    report = result.to_dict()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.notarize:
        CogAlignNotary().record(report, operation_type=f"CogAlignScenario-{args.scenario}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cog_align", description="认知对齐评测服务 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_measure = sub.add_parser("measure", help="单对不对称评测")
    p_measure.add_argument("--a", required=True, help="主体 A 标识")
    p_measure.add_argument("--state-a", required=True, help="主体 A 五维认知状态 JSON")
    p_measure.add_argument("--b", required=True, help="主体 B 标识")
    p_measure.add_argument("--state-b", required=True, help="主体 B 五维认知状态 JSON")
    p_measure.add_argument("--provenance", default="SIMULATED")
    p_measure.add_argument("--report-id")
    p_measure.add_argument("--notarize", action="store_true", help="评测后落 NCA 存证")
    p_measure.set_defaults(func=cmd_measure)

    p_event = sub.add_parser("event", help="多主体矩阵评测")
    p_event.add_argument("--event", required=True)
    p_event.add_argument("--states", required=True, help="{subject: 五维状态} JSON")
    p_event.add_argument("--provenance", default="SIMULATED")
    p_event.add_argument("--report-id")
    p_event.add_argument("--notarize", action="store_true")
    p_event.set_defaults(func=cmd_event)

    p_conv = sub.add_parser("convergence", help="收敛轨迹")
    p_conv.add_argument("--a", required=True)
    p_conv.add_argument("--b", required=True)
    p_conv.add_argument("--series", required=True, help="[[ts, s_a, s_b], ...] JSON")
    p_conv.add_argument("--provenance", default="SIMULATED")
    p_conv.add_argument("--report-id")
    p_conv.add_argument("--notarize", action="store_true")
    p_conv.set_defaults(func=cmd_convergence)

    p_scen = sub.add_parser("scenario", help="评测场景（M2 产品化）")
    p_scen.add_argument("--scenario", required=True,
                        choices=["thought-virus", "drift-monitor", "tiering"])
    p_scen.add_argument("--subject", help="思想病毒防御: 被测主体")
    p_scen.add_argument("--baseline", help="思想病毒防御: 基准认知状态 JSON")
    p_scen.add_argument("--series", help="思想病毒防御/漂移监测: [[ts, state], ...] 或 [[ts, s_a, s_b], ...] JSON")
    p_scen.add_argument("--a", help="漂移监测/分档: 主体 A")
    p_scen.add_argument("--b", help="漂移监测/分档: 主体 B")
    p_scen.add_argument("--state-a", help="分档: 主体 A 状态 JSON")
    p_scen.add_argument("--state-b", help="分档: 主体 B 状态 JSON")
    p_scen.add_argument("--provenance", default="SIMULATED")
    p_scen.add_argument("--notarize", action="store_true")
    p_scen.set_defaults(func=cmd_scenario)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
