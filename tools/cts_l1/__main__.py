# FC-ID: TDCA-TASK-CTS-L1-001 | CLI 入口
"""用法: python -m cts_l1 --target tools.cts_l1.reference.ref_agent:make_agent
        [--json out.json] [--md out.md] [--declaration out.json]
--target 格式: <模块>:<工厂函数>，工厂返回被测目标对象（接口约定见 runners/base.py docstring）
退出码: 0=全 PASS（声明已签发）/ 1=存在 FAIL / 2=加载失败
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from .report import build_report, issue_declaration, report_md
from .runners import run_all


def _load_target(spec: str):
    mod_name, _, factory = spec.partition(":")
    if not factory:
        factory = "make_agent"
    mod = importlib.import_module(mod_name)
    return getattr(mod, factory)()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cts_l1", description="CTS-L1 一致性测试套件 [SIMULATED]")
    ap.add_argument("--target", required=True, help="被测实现 <module>:<factory>")
    ap.add_argument("--json", help="机器可读报告输出路径")
    ap.add_argument("--md", help="人读报告输出路径")
    ap.add_argument("--declaration", help="一致性声明输出路径（全 PASS 才写）")
    args = ap.parse_args(argv)

    print("[SIMULATED] CTS-L1 —— 测试向量全合成；测试通过即原生，争议裁决归人类", file=sys.stderr)
    try:
        target = _load_target(args.target)
    except Exception as e:
        print(f"FAIL: 目标加载失败 {e}", file=sys.stderr)
        return 2

    results = run_all(target)
    report = build_report(getattr(target, "agent_id", "unknown"),
                          getattr(target, "registry_version", "unknown"), results)
    decl = issue_declaration(report)

    for c in report["cases"]:
        print(f"{'PASS' if c['passed'] else 'FAIL'}  {c['case_id']:<7} {c['detail'][:70]}")
    print(f"\n{report['passed']}/{report['total']} PASS ｜ 声明: {'已签发' if decl else '未签发'}")

    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.md:
        Path(args.md).write_text(report_md(report, decl), encoding="utf-8")
    if decl is not None and args.declaration:
        Path(args.declaration).write_text(json.dumps(decl, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
