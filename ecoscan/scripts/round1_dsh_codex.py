"""DSH/Codex 首轮实测（TDCA-HANDOFF-M2-001 线 2 #5）——真实 GitHub 扫描。

输出: research/ 或 reports/ 目录下 JSON 报告（GITHUB-LIVE 标注）。
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tdca-ecoscan/
sys.path.insert(0, ROOT)

from tdca_ecoscan.ledger import EcoLedger
from tdca_ecoscan.pipeline import InvitePipeline
from tdca_ecoscan.scanner import EcoScanner

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "reports")
os.makedirs(OUT_DIR, exist_ok=True)

# 聚焦 DSH/Codex 关键词（宣言 §六 目标优先级 1/2）
pipe = InvitePipeline(ledger=EcoLedger(target_dir=os.path.join(OUT_DIR, ".ledger")),
                      provenance="GITHUB-LIVE")
pipe._scanner = EcoScanner(keywords=["deepseek harness", "codex harness", "agent harness"],
                           max_results_per_query=10)
r = pipe.run_github(max_queries=3, max_invites=4)

report = {
    "doc": "TDCA-ECOSCAN-M2-DSH-CODEX-001",
    "provenance": "GITHUB-LIVE",
    "date": "2026-08-23",
    "candidates": [c.to_dict() for c in r.candidates],
    "invited": [l.to_dict() for l in r.invited],
    "skipped": r.skipped,
    "ledger": r.ledger_report,
}
path = os.path.join(OUT_DIR, "dsh-codex-round1.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print("WROTE", path)
print("candidates:", len(r.candidates), "invited:", len(r.invited))
for l in r.invited:
    print("-", l.repo_full, l.mode, l.tier, l.nca_ref)
