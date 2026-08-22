"""pi_nca · CLI（M1c 端到端入口）。

用法:
  python -m pi_nca.cli compile --spec <json>    # 构建协议 → 制度编译 + NCA
  python -m pi_nca.cli guard --spec <json>      # Fair Source 隔离校验
"""
from __future__ import annotations

import argparse
import json
import sys

from .compiler import PiCompiler


def _load(raw: str) -> str:
    if raw.startswith("@"):
        with open(raw[1:], encoding="utf-8") as f:
            return f.read()
    return raw


def cmd_compile(args) -> int:
    compiler = PiCompiler(provenance=args.provenance)
    spec = compiler.parse_agent_spec(_load(args.spec))
    guard = compiler.fair_source_guard(spec)
    steps = compiler.compile_to_tdca(spec)
    ncas = compiler.build_compile_ncas(steps, spec_id=spec.get("spec_id", "agent-1"))
    out = {"guard": guard.to_dict(), "steps": [s.to_dict() for s in steps],
           "nca_records": ncas}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_guard(args) -> int:
    compiler = PiCompiler(provenance=args.provenance)
    spec = compiler.parse_agent_spec(_load(args.spec))
    print(json.dumps(compiler.fair_source_guard(spec).to_dict(), ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="pi_nca", description="Pi → TDCA 制度编译（MIT 层）")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in (("compile", cmd_compile), ("guard", cmd_guard)):
        p = sub.add_parser(name)
        p.add_argument("--spec", required=True, help="构建规格 JSON 字符串或 @文件路径")
        p.add_argument("--provenance", default="SIMULATED")
        p.set_defaults(func=fn)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
