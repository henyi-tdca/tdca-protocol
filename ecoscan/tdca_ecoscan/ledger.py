"""tdca_ecoscan · 台账登记（DCD-ECOSCAN-001 M1 ledger）

扫描/诊断/邀请全量落 NCA——可追溯、防重复、防轰炸（≤2 条/周/目标）。
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .inviter import InviteLetter, WEEKLY_INVITE_LIMIT

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", ".tdca-nca", "services", "ecoscan",
)


class EcoLedger:
    """生态雷达台账（M1 ledger）。"""

    def __init__(self, target_dir: Optional[str] = None, operator: str = "Reasonix"):
        self._dir = os.path.abspath(target_dir or _DEFAULT_DIR)
        os.makedirs(self._dir, exist_ok=True)
        self._operator = operator

    # ---- 记录 ----

    def record_scan(self, targets: List[dict], query: str = "scan") -> dict:
        """扫描记录落 NCA。"""
        return self._record({
            "type": "scan", "query": query,
            "target_count": len(targets),
            "targets": targets[:50],   # 裁剪防超限
        })

    def record_invite(self, letter: InviteLetter) -> dict:
        """邀请记录落 NCA（含频率校验）。"""
        if self._weekly_invite_count(letter.repo_full) >= WEEKLY_INVITE_LIMIT:
            raise ValueError(
                f"[NSFL-TRIGGER] 周邀请频率超限（>{WEEKLY_INVITE_LIMIT}/周）: {letter.repo_full}——礼貌纪律")
        return self._record({
            "type": "invite", "invite_id": letter.invite_id,
            "repo_full": letter.repo_full, "mode": letter.mode,
            "nca_ref": letter.nca_ref, "body": letter.body,
        })

    def record_comment(self, record) -> dict:
        """评论记录落 NCA（评论模式 M1——repo_full/issue_n/url/时间/response_status）。"""
        return self._record({
            "type": "comment", "comment_id": record.comment_id,
            "repo_full": record.repo_full, "issue_n": record.issue_n,
            "url": record.url, "ecoact_nca": record.ecoact_nca,
            "response_status": record.response_status, "body": record.body,
        })

    def weekly_touch_count(self, repo_full: str) -> int:
        """周触达计数：邀请与评论共享 ≤2 条/周/目标预算（评论=触达计数）。

        与 _weekly_invite_count 同口径（台账全量计数，不超发）。
        """
        count = 0
        for r in self._load_all():
            if r.get("type") in ("invite", "comment") and r.get("repo_full") == repo_full:
                count += 1
        return count

    def weekly_report(self) -> dict:
        """周报汇总（台账可追溯）。"""
        records = self._load_all()
        invites = [r for r in records if r.get("type") == "invite"]
        scans = [r for r in records if r.get("type") == "scan"]
        comments = [r for r in records if r.get("type") == "comment"]
        return {
            "total_records": len(records),
            "scan_count": len(scans),
            "invite_count": len(invites),
            "comment_count": len(comments),
            "invited_repos": sorted({r["repo_full"] for r in invites}),
            "commented_repos": sorted({r["repo_full"] for r in comments}),
        }

    # ---- 工具 ----

    def _record(self, payload: dict) -> dict:
        ts = datetime.now(timezone.utc)
        digest = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        record_hash = hashlib.sha256(digest.encode("utf-8")).hexdigest()
        nca_id = f"NCA-ECOSCAN-{ts.strftime('%Y%m%d')}-{self._next_seq()}"
        record = {
            "NCA-ID": nca_id,
            "Operation-Type": f"EcoScan-{payload['type']}",
            "Operator": self._operator,
            "Timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Payload-Hash": f"sha256:{record_hash}",
            "Payload": payload,
        }
        path = os.path.join(self._dir, f"{nca_id}.yaml")
        self._write(path, record)
        return record

    def _next_seq(self) -> int:
        existing = [f for f in os.listdir(self._dir) if f.startswith("NCA-ECOSCAN-")]
        return len(existing) + 1

    def _weekly_invite_count(self, repo_full: str) -> int:
        count = 0
        for r in self._load_all():
            if r.get("type") == "invite" and r.get("repo_full") == repo_full:
                count += 1
        return count

    def _load_all(self) -> List[dict]:
        out = []
        for f in os.listdir(self._dir):
            if not f.endswith(".yaml"):
                continue
            try:
                with open(os.path.join(self._dir, f), encoding="utf-8") as fh:
                    rec = self._read(fh.read())
                    out.append(rec.get("Payload", {}))
            except Exception:
                continue
        return out

    @staticmethod
    def _read(raw: str) -> dict:
        try:
            import yaml
            return yaml.safe_load(raw)
        except ImportError:
            return json.loads(raw)

    @staticmethod
    def _write(path: str, record: dict) -> None:
        try:
            import yaml
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(record, f, allow_unicode=True, sort_keys=False)
        except ImportError:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
