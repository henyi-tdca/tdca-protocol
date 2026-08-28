"""tdca_ecoscan · 评论模式 M1（TDCA-HANDOFF-KIMI-ECOSCAN-COMMENT-M1-001）

对他人仓库 issue/PR 发表评论邀请（POST /repos/{owner}/{repo}/issues/{n}/comments，
无需目标仓权限）。discussion 邀请模式零改动——本模块为独立新增路径。

纪律实现：
- 三段式话术（TDCA-COMMENT-INVITE-001）：诊断 ~40% / TDCA 解法 ~40% / 交流邀请 ~20%，
  500 字左右、不超 700 字（CommentComposer 强制校验）
- ECOACT 七字段存证 fail-closed：无存证不发送（字段缺一即拒）
- 频率闸：≤2 条/周/目标——评论与邀请共享触达预算（评论=触达计数）
- 台账：评论记录（repo_full/issue_n/url/时间/response_status）落 NCA
- 有增量价值（点评+邀请，非广告）；明确拒绝即停止（response_status=rejected 归档）
"""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

# ECOACT 七字段（创始人裁定 §三，fail-closed 强制）
ECOACT_REQUIRED_FIELDS = (
    "repo_full", "mode", "license_spdx", "invite_nca_ref",
    "response_status", "profit_sharing", "compliance",
)

# 频率闸（宣言 §五：≤2 条/周/目标，评论与邀请共享触达预算）
WEEKLY_TOUCH_LIMIT = 2

# 话术长度（TDCA-COMMENT-INVITE-001：500 字左右，不超 700 字）
COMMENT_MIN_LEN = 200
COMMENT_MAX_LEN = 700
# 诊断段下限：过短则无论增量价值（肯定+真问题需展开）
DIAGNOSIS_MIN_LEN = 50

# 评论模式标识（ECOACT mode 字段值）
MODE_COMMENT = "comment"

_SOLUTION_DEFAULT = (
    "这恰好是 TDCA（可信数字协作架构）补位的地方：用 NCA 嵌套认知资产为每次协作留痕确权"
    "（机器可读、不可篡改）；用 NSFL 负空间熔断在制度红线处自动停机；用 MOU 锚定让效用可验证。"
    "全部「只赋能不改码」——贵方源码零改动，配置权全归贵方"
    "（分润按 15% 模拟态记账，NCA 确权，不承诺打款）。"
)

_INVITE_DEFAULT = (
    "如果感兴趣，欢迎来 TDCA 仓库 Discussions 交流——这只是邀请不是要求，选择权完全在贵方。"
)


@dataclass(frozen=True)
class CommentRecord:
    """评论记录（台账回填单元）。"""
    comment_id: str
    repo_full: str
    issue_n: int
    body: str
    ecoact_nca: str
    url: str
    created_at: str
    provenance: str
    response_status: str = "pending"

    def to_dict(self) -> dict:
        return {
            "comment_id": self.comment_id,
            "repo_full": self.repo_full,
            "issue_n": self.issue_n,
            "body": self.body,
            "ecoact_nca": self.ecoact_nca,
            "url": self.url,
            "created_at": self.created_at,
            "provenance": self.provenance,
            "response_status": self.response_status,
        }


class CommentComposer:
    """三段式评论话术组装（TDCA-COMMENT-INVITE-001）。

    诊断段逐目标定制（观察报告方法论）；解法段与邀请段有纪律内默认文案。
    """

    def compose(self, repo_full: str, diagnosis: str,
                solution: Optional[str] = None,
                invite: Optional[str] = None) -> str:
        """组装三段式评论并强制长度校验。

        diagnosis: 定制诊断段（肯定 1-2 句 + 真问题 2-3 句，制度层缺口非技术挑刺）。
        """
        if not diagnosis or not diagnosis.strip():
            raise ValueError("[NSFL-TRIGGER] 诊断段为空——评论须有增量价值（点评+邀请，非广告）")
        if len(diagnosis.strip()) < DIAGNOSIS_MIN_LEN:
            raise ValueError(
                f"[NSFL-TRIGGER] 诊断段过短（{len(diagnosis.strip())} < {DIAGNOSIS_MIN_LEN} 字）"
                "——诊断不足则无论增量价值")
        body = (
            f"【诊断】\n{diagnosis.strip()}\n\n"
            f"【TDCA 解法】\n{(solution or _SOLUTION_DEFAULT).strip()}\n\n"
            f"【交流邀请】\n{(invite or _INVITE_DEFAULT).strip()}"
        )
        n = len(body)
        if n > COMMENT_MAX_LEN:
            raise ValueError(
                f"[NSFL-TRIGGER] 评论超长（{n} > {COMMENT_MAX_LEN} 字）——500 字左右礼貌纪律")
        if n < COMMENT_MIN_LEN:
            raise ValueError(
                f"[NSFL-TRIGGER] 评论过短（{n} < {COMMENT_MIN_LEN} 字）——诊断不足则无论增量价值")
        return body


class Commenter:
    """评论发送器（M1 comment 模式）。

    sender: 可注入发送函数 (repo_full, issue_n, body, token) -> dict（至少含 html_url）。
            默认 GitHubCommentSender（POST issues/{n}/comments）。
    """

    def __init__(self, ledger, sender: Optional[Callable[..., dict]] = None,
                 provenance: str = "SIMULATED"):
        self._ledger = ledger
        self._sender = sender or GitHubCommentSender()
        self._provenance = provenance

    def post(self, repo_full: str, issue_n: int, body: str,
             ecoact: dict, token: Optional[str] = None) -> CommentRecord:
        """发表评论——ECOACT 存证 fail-closed 先于一切发送动作。"""
        # ③ ECOACT 七字段强制（无存证不发送）
        missing = [f for f in ECOACT_REQUIRED_FIELDS if not ecoact.get(f)]
        if missing:
            raise ValueError(
                f"[NSFL-TRIGGER] ECOACT 存证字段缺失 {missing}——无存证不发送（fail-closed）")
        # 无 token 拒绝
        if not token:
            raise ValueError("[NSFL-TRIGGER] 无 token 拒绝发送——凭证纪律")
        # ④ 频率闸：评论与邀请共享 ≤2 条/周/目标触达预算
        touches = self._ledger.weekly_touch_count(repo_full)
        if touches >= WEEKLY_TOUCH_LIMIT:
            raise ValueError(
                f"[NSFL-TRIGGER] 周触达频率超限（{touches} ≥ {WEEKLY_TOUCH_LIMIT}/周）: "
                f"{repo_full}——礼貌纪律")
        # 长度二次校验（手工构造 body 也受约束）
        if not (COMMENT_MIN_LEN <= len(body) <= COMMENT_MAX_LEN):
            raise ValueError(
                f"[NSFL-TRIGGER] 评论长度 {len(body)} 字越界 [{COMMENT_MIN_LEN},{COMMENT_MAX_LEN}]")

        resp = self._sender(repo_full, issue_n, body, token)
        url = resp.get("html_url", "")

        now = datetime.now(timezone.utc)
        digest = hashlib.sha256(
            f"{repo_full}:{issue_n}:{now.isoformat()}".encode()).hexdigest()[:12]
        record = CommentRecord(
            comment_id=f"CMT-{digest.upper()}",
            repo_full=repo_full, issue_n=issue_n, body=body,
            ecoact_nca=str(ecoact["invite_nca_ref"]),
            url=url, created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            provenance=self._provenance,
            response_status=str(ecoact.get("response_status", "pending")),
        )
        # ⑤ 台账回填（发送成功后落账）
        self._ledger.record_comment(record)
        return record


class GitHubCommentSender:
    """GitHub 评论通道（POST /repos/{owner}/{repo}/issues/{n}/comments）。"""

    API = "https://api.github.com"

    def __call__(self, repo_full: str, issue_n: int, body: str, token: str) -> dict:
        url = f"{self.API}/repos/{repo_full}/issues/{issue_n}/comments"
        req = urllib.request.Request(url, method="POST", headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "tdca-ecoscan-commenter",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        }, data=json.dumps({"body": body}).encode("utf-8"))
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"评论发送失败 HTTP {e.code}: {repo_full}#{issue_n}——"
                "fail-closed（不上台账、不重试轰炸）") from e
