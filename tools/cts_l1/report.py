# FC-ID: TDCA-TASK-CTS-L1-001 | 一致性报告 + 声明签发（badge）
import hashlib
import json
from datetime import datetime, timezone

from . import PROFILE_ID, PROFILE_VERSION


def build_report(agent_id: str, registry_version: str, results: list) -> dict:
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    return {
        "profile": PROFILE_ID,
        "profile_version": PROFILE_VERSION,
        "agent_id": agent_id,
        "registry_version": registry_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": len(results), "passed": len(passed), "failed": len(failed),
        "all_pass": not failed,
        "cases": [{"case_id": r.case_id, "requirement": r.requirement,
                   "passed": r.passed, "detail": r.detail,
                   "elapsed_ms": r.elapsed_ms, "provenance": r.provenance}
                  for r in results],
        "data_provenance": "simulated",
    }


def issue_declaration(report: dict) -> dict | None:
    """全 PASS → 签发机器可读《一致性声明》（声明本身按 C-2 上链由调用方落 NCA）。"""
    if not report.get("all_pass"):
        return None
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True)
    return {
        "declaration_type": "TDCA-Native-L1",
        "agent_id": report["agent_id"],
        "profile": report["profile"],
        "profile_version": report["profile_version"],
        "registry_version": report["registry_version"],
        "passed_cases": [c["case_id"] for c in report["cases"]],
        "issued_at": report["timestamp"],
        "declaration_hash": "sha256:" + hashlib.sha256(payload.encode()).hexdigest(),
        "data_provenance": "simulated",
        "note": "测试通过即原生（技术核查非行政审批）；争议裁决归人类签批。",
    }


def report_md(report: dict, declaration: dict | None) -> str:
    lines = [f"# CTS-L1 一致性报告 — {report['agent_id']}", "",
             f"- 轮廓: {report['profile']} {report['profile_version']} ｜ 注册表: {report['registry_version']}",
             f"- 结果: {report['passed']}/{report['total']} PASS ｜ 时间: {report['timestamp']}",
             f"- 数据性质: simulated（ID92 合成测试向量）", "", "| 用例 | 要求 | 结果 | 说明 |",
             "|---|---|---|---|"]
    for c in report["cases"]:
        lines.append(f"| {c['case_id']} | {c['requirement']} | {'✅ PASS' if c['passed'] else '❌ FAIL'} | {c['detail'][:60]} |")
    lines += ["", "**一致性声明**: " + (f"✅ 已签发 `{declaration['declaration_hash'][:24]}…`" if declaration else "❌ 未签发（存在 FAIL 用例）")]
    return "\n".join(lines)
