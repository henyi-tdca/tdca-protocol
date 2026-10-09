"""paperclip_nca · CLI（M1c 端到端入口）。

用法:
  python -m paperclip_nca.cli compile --orch <json>    # 编排 → 协作语义 + NCA
  python -m paperclip_nca.cli summary --orch <json>    # 编排结构摘要
"""
from __future__ import annotations

import argparse
import json
import sys

from .adapter import PaperclipAdapter


def _load(raw: str) -> str:
    if raw.startswith("@"):
        with open(raw[1:], encoding="utf-8") as f:
            return f.read()
    return raw


def cmd_compile(args) -> int:
    adapter = PaperclipAdapter(provenance=args.provenance)
    orch = adapter.parse_orchestration(_load(args.orch))
    calls = adapter.compile_to_collab(orch)
    ncas = adapter.build_collab_ncas(calls, orchestration_id=orch.get("orchestration_id", "orch-1"))
    out = {
        "collab_calls": [c.to_dict() for c in calls],
        "nca_records": [n.to_dict() for n in ncas],
        "summary": adapter.orchestration_summary(orch),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_summary(args) -> int:
    adapter = PaperclipAdapter(provenance=args.provenance)
    orch = adapter.parse_orchestration(_load(args.orch))
    print(json.dumps(adapter.orchestration_summary(orch), ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="paperclip_nca", description="Paperclip → TDCA 协作编译")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in (("compile", cmd_compile), ("summary", cmd_summary)):
        p = sub.add_parser(name)
        p.add_argument("--orch", required=True, help="编排协议 JSON 字符串或 @文件路径")
        p.add_argument("--provenance", default="SIMULATED")
        p.set_defaults(func=fn)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
