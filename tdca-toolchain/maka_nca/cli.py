"""maka_nca · CLI（M1c 端到端入口）

用法:
  python -m maka_nca.cli convert --log <jsonl/json>   # Event Log → NCA 审计链
  python -m maka_nca.cli validate --log <jsonl/json>   # 正和验证
  python -m maka_nca.cli endtoend --log <jsonl/json>   # 端到端（转换+验证+上链）
"""
from __future__ import annotations

import argparse
import json
import sys

from .converter import MakaNcaConverter
from .validator import PositiveSumValidator


def _load_log(raw: str) -> str:
    # 支持直接传 JSON 字符串或文件路径（@file）
    if raw.startswith("@"):
        with open(raw[1:], encoding="utf-8") as f:
            return f.read()
    return raw


def cmd_convert(args) -> int:
    conv = MakaNcaConverter(operator=args.operator, provenance=args.provenance)
    events = conv.parse_event_log(_load_log(args.log))
    chain = conv.build_audit_chain(events)
    out = {"records": [r.to_dict() for r in chain],
           "chain_integrity": conv.verify_chain(chain)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_validate(args) -> int:
    conv = MakaNcaConverter(operator=args.operator, provenance=args.provenance)
    events = conv.parse_event_log(_load_log(args.log))
    v = PositiveSumValidator().validate(events, session_id=args.session)
    print(json.dumps(v.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_endtoend(args) -> int:
    conv = MakaNcaConverter(operator=args.operator, provenance=args.provenance)
    events = conv.parse_event_log(_load_log(args.log))
    chain = conv.build_audit_chain(events)
    verdict = PositiveSumValidator().validate(events, session_id=args.session)
    out = {
        "records": [r.to_dict() for r in chain],
        "chain_integrity": conv.verify_chain(chain),
        "positive_sum": verdict.to_dict(),
        "note": "端到端：Event Log → NCA 上链 + 正和验证（SIMULATED 数据，ID92）",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="maka_nca", description="Maka Event Log → TDCA-NCA")
    sub = parser.add_subparsers(dest="cmd", required=True)

    for name, fn in (("convert", cmd_convert), ("validate", cmd_validate),
                     ("endtoend", cmd_endtoend)):
        p = sub.add_parser(name)
        p.add_argument("--log", required=True, help="Event Log JSON/JSONL 字符串或 @文件路径")
        p.add_argument("--operator", default="maka-agent")
        p.add_argument("--provenance", default="SIMULATED")
        if name in ("validate", "endtoend"):
            p.add_argument("--session", default="maka-session")
        p.set_defaults(func=fn)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
