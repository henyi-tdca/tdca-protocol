"""Codex 目标补发邀请函（openai/codex 重试：Search API 未命中，静态注入真实数据补发）。

数据来源: GitHub API 直接查询（GITHUB-LIVE，repo openai/codex 2026-08-23 05:01 UTC）。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tdca_ecoscan.ledger import EcoLedger
from tdca_ecoscan.pipeline import InvitePipeline, InvitePipeline as _P

OUT_DIR = os.path.join(ROOT, "reports")
os.makedirs(OUT_DIR, exist_ok=True)

# 真实数据（GitHub API 直接查询 2026-08-23）：openai/codex
codex_repo = {
    "repo_full": "openai/codex",
    "stars": 113851,
    "license_spdx": "Apache-2.0",
    "description": "Lightweight coding agent that runs in your terminal",
    "pushed_at": "2026-08-23T05:01:49Z",
    "keywords": ["codex agent", "coding agent", "terminal"],
    "url": "https://github.com/openai/codex",
}

pipe = InvitePipeline(ledger=EcoLedger(target_dir=os.path.join(OUT_DIR, ".ledger")),
                      provenance="GITHUB-LIVE")
result = pipe.run([codex_repo], max_invites=1)

report = {
    "doc": "TDCA-ECOSCAN-M2-CODEX-RETRY-002",
    "provenance": "GITHUB-LIVE",
    "date": "2026-08-23",
    "note": "openai/codex（目标 #2）补发：Search API 关键词未命中，改用 repo 直接查询数据注入",
    "candidates": [c.to_dict() for c in result.candidates],
    "invited": [l.to_dict() for l in result.invited],
    "skipped": result.skipped,
    "ledger": result.ledger_report,
}
path = os.path.join(OUT_DIR, "codex-retry-round2.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print("WROTE", path)
for l in result.invited:
    print("INVITED:", l.repo_full, l.mode, l.tier, l.nca_ref)
    print("BODY:", l.body[:120], "...")
