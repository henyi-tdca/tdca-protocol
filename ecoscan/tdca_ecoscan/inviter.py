"""tdca_ecoscan · 邀请函生成（DCD-ECOSCAN-001 M1 inviter）

挂载/化合双轨话术（BIDIR-001 不留痕 + 礼貌邀请）+ NCA 存证编号。
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .diagnoser import CandidateProfile, TIER_A

# 周频率限制（宣言 §五：≤2 条/周/目标）
WEEKLY_INVITE_LIMIT = 2


@dataclass(frozen=True)
class InviteLetter:
    """邀请函（挂载/化合双轨）。"""
    invite_id: str
    repo_full: str
    mode: str                    # mount（挂载）| compound（化合）
    tier: str
    body: str
    nca_ref: str                 # NCA 存证编号
    created_at: str
    provenance: str

    def to_dict(self) -> dict:
        return {
            "invite_id": self.invite_id,
            "repo_full": self.repo_full,
            "mode": self.mode,
            "tier": self.tier,
            "body": self.body,
            "nca_ref": self.nca_ref,
            "created_at": self.created_at,
            "provenance": self.provenance,
        }


class InviteGenerator:
    """邀请函生成器（M1 inviter）。"""

    def __init__(self, provenance: str = "SIMULATED"):
        self._provenance = provenance

    def generate(self, profile: CandidateProfile,
                 mode: Optional[str] = None) -> InviteLetter:
        """生成邀请函。

        mode: 未指定时按契合信号自动选（可审计+分账 → compound；仅可挂载 → mount）
        """
        if profile.tier != TIER_A:
            raise ValueError(f"[NSFL-TRIGGER] 仅 TIER-A 可邀请（当前 {profile.tier}）——"
                             "B/C 档不发出邀请（礼貌纪律）")
        if mode is None:
            mode = "compound" if (profile.auditable and profile.settlement_pain) else "mount"
        if mode not in ("mount", "compound"):
            raise ValueError(f"[NSFL-TRIGGER] 非法模式: {mode}")

        now = datetime.now(timezone.utc)
        digest = hashlib.sha256(
            f"{profile.target.repo_full}:{mode}:{now.isoformat()}".encode()
        ).hexdigest()[:12]
        invite_id = f"INV-{digest.upper()}"
        nca_ref = f"NCA-ECOSCAN-{now.strftime('%Y%m%d')}-{invite_id}"

        body = self._build_body(profile, mode, nca_ref)
        return InviteLetter(
            invite_id=invite_id, repo_full=profile.target.repo_full,
            mode=mode, tier=profile.tier, body=body,
            nca_ref=nca_ref, created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            provenance=self._provenance,
        )

    @staticmethod
    def _build_body(profile: CandidateProfile, mode: str, nca_ref: str) -> str:
        repo = profile.target.repo_full
        if mode == "mount":
            return (
                f"尊敬的 {repo} 项目方："
                f"我们发现您的项目缺少可信的审计与分账协议层。"
                f"TDCA 提供轻量级 MCP 适配器（不改变您的任何代码，只在外部挂载协议层），"
                f"可为主权信用合规提供支持。您可以选择使用或不用——这是您的配置权。"
                f"（存证: {nca_ref}，调用即分润：动态分润，默认版权被权调用方 15%，"
                f"按贵方开源授权规定执行；无明确收费约定时按开源规则合法挂载，"
                f"收益默认支付 15% 版税给贵方或贵方社区基金会）"
            )
        return (
            f"尊敬的 {repo} 项目方："
            f"贵项目与 TDCA 制度框架高度同构（可审计事件流 ↔ NCA 存证链）。"
            f"我们诚邀化合协作——您的资产与 TDCA 制度函数化合生成高级 NCA，"
            f"调用后您作为原创方获得分润与永久版税（Shapley 分配）。"
            f"（存证: {nca_ref}，只赋能不改码；以贵方开源授权规定为优先，"
            f"无明确收费约定时按开源规则合法化合，"
            f"收益默认支付 15% 版税给贵方或贵方社区基金会）"
        )
