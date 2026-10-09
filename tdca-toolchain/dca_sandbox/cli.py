"""dca_sandbox · CLI（M1 装配短程验证运行）

用法:
  python -m dca_sandbox.cli run --weeks 13 [--seed 20260908] [--sandbox SBX-DCA-001] [--notarize]
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from .engine import (
    ACTIVATION_THRESHOLD,
    CCA_RESPONSE_TARGET,
    DcaSandboxSimulation,
    MerchantConfig,
    NUCLEAR_RATE_CONSEC_WEEKS,
    NUCLEAR_RATE_TARGET,
)

# 默认商户装配（示例咖啡——复用 merchant_loop examples 权益结构，SIMULATED）
_DEFAULT_BENEFIT = {
    "benefit_id": "B-EXAMPLE-001",
    "merchant_id": "M-EXAMPLE-CAFE",
    "title": "到店消费 9 折 + 即时小额让利（沙盒模拟）",
    "discount": {"rate": 0.10},
    "rebate": {"rate": 0.03, "cap": 10.0},
    "valid_from": "2026-09-01",
    "valid_until": "2027-12-31",
    "stores": ["STORE-CAFE-001"],
    "conditions": {"min_spend": 20.0},
    "budget_ceiling": 10000.0,
    "scene_type": "dine",
    "objective": "沙盒模拟：以预算平移驱动真实消费核销",
    "constraint": "双边消费交易不进 CLS；无资产/无杠杆/无升值承诺；逐笔即时让利",
    "prior": "预算平移自历史营销预算",
    "config_boundary": "商家-消费者双边权益（沙盒模拟态）",
    "distribution": "让利归消费者；平台服务费按调度税口径模拟记账",
    "audit": "每笔核销 NCA 存证（沙盒模拟）",
}


def _default_merchants(arrival_rate: Optional[float] = None) -> list:
    ar = arrival_rate if arrival_rate is not None else 0.30
    return [
        MerchantConfig(
            merchant_id="M-EXAMPLE-CAFE",
            benefit_raw=dict(_DEFAULT_BENEFIT),
            customer_base=2000.0, arrival_rate=ar, avg_ticket=100.0, ticket_sigma=25.0,
        ),
        MerchantConfig(
            merchant_id="M-SIM-RETAIL",
            benefit_raw=dict(_DEFAULT_BENEFIT, benefit_id="B-SIM-002", merchant_id="M-SIM-RETAIL",
                             title="沙盒零售权益", scene_type="retail"),
            customer_base=1500.0, arrival_rate=max(ar - 0.02, 0.10), avg_ticket=120.0, ticket_sigma=30.0,
        ),
    ]


def cmd_run(args) -> int:
    sim = DcaSandboxSimulation(default_provenance=args.provenance)
    templates = sim.assemble(_default_merchants(arrival_rate=getattr(args, "arrival_rate", None)),
                             sandbox_id=args.sandbox)
    result = sim.run(weeks=args.weeks, seed=args.seed, sandbox_id=args.sandbox)
    out = result.to_dict()
    out["assembled_benefits"] = [t.benefit_id for t in templates]
    out["provenance"] = args.provenance
    if args.notarize:
        from .notary import DcaSandboxNotary
        nca = DcaSandboxNotary().record(out, operation_type="DcaSandboxRun",
                                        scope_note="DCA-重塑版沙盒 M1 装配短程运行存证")
        out["nca_id"] = nca["NCA-ID"]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="dca_sandbox", description="DCA-重塑版 SEA 沙盒模拟器 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="装配 + 短程模拟运行（M1 验证；M2 跑 26 周）")
    p.add_argument("--weeks", type=int, default=13, help="模拟周数（默认 13——M2 用 26）")
    p.add_argument("--seed", type=int, default=20260908)
    p.add_argument("--sandbox", default="SBX-DCA-001")
    p.add_argument("--arrival-rate", type=float, default=None,
                   help="周核销到达率校准（M2 目标域 0.65；默认 0.30=M1 短程基线）")
    p.add_argument("--merchants", default="default", help="商户装配（default=示例 2 商户）")
    p.add_argument("--provenance", default="SIMULATED", help="ID92 数据性质（默认 SIMULATED）")
    p.add_argument("--notarize", action="store_true", help="运行结果落 NCA 存证")
    p.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
