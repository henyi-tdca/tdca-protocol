"""dca_sandbox.mixed_cli · R-7 M3 三方闭环模拟 CLI

用法:
  python -m dca_sandbox.mixed_cli run --weeks 26 [--seed N] [--attack] [--notarize]
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from .mixed import AgentBrokerConfig, MixedMarketSimulation


def _benefit(mid, bid, scene, title):
    return {
        "benefit_id": bid, "merchant_id": mid, "title": title,
        "discount": {"rate": 0.10}, "rebate": {"rate": 0.03, "cap": 10.0},
        "valid_from": "2026-09-01", "valid_until": "2027-12-31",
        "stores": ["S-1"], "conditions": {"min_spend": 20.0},
        "budget_ceiling": 10000.0, "scene_type": scene,
        "objective": "三方闭环模拟", "constraint": "双边不进 CLS",
        "prior": "预算平移", "config_boundary": "b", "distribution": "d", "audit": "a",
    }


def cmd_run(args) -> int:
    sim = MixedMarketSimulation(default_provenance=args.provenance)
    sim.assemble(
        merchants=[
            ("M-EXAMPLE-CAFE", _benefit("M-EXAMPLE-CAFE", "B-CAFE", "dine", "咖啡权益（沙盒）")),
            ("M-SIM-RETAIL", _benefit("M-SIM-RETAIL", "B-RETAIL", "retail", "零售权益（沙盒）")),
        ],
        agents=[AgentBrokerConfig(agent_id="A-BROKER-1", match_efficiency=0.7)],
    )
    res = sim.run(weeks=args.weeks, seed=args.seed, funding_attack=args.attack)
    out = res.to_dict()
    out["provenance"] = args.provenance
    if args.notarize:
        from .notary import DcaSandboxNotary
        nca = DcaSandboxNotary().record(out, operation_type="R7M3MixedRun",
                                        scope_note="R-7 M3 混合配置市场三方闭环模拟存证")
        out["nca_id"] = nca["NCA-ID"]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="dca_sandbox.mixed", description="R-7 M3 三方闭环模拟 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run", help="三方闭环模拟运行（默认 26 周）")
    p.add_argument("--weeks", type=int, default=26)
    p.add_argument("--seed", type=int, default=20260908)
    p.add_argument("--attack", action="store_true", help="注入资助诱导（负控测试）")
    p.add_argument("--provenance", default="SIMULATED")
    p.add_argument("--notarize", action="store_true")
    p.set_defaults(func=cmd_run)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
