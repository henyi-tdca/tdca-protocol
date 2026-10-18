# SPDX-License-Identifier: Apache-2.0
"""tdca_ecoscan · 候选诊断（DCD-ECOSCAN-001 M1 diagnoser）

制度契合度评估：非侵入可挂载 / 可审计日志 / 分账痛点 / License 合规（AUDIT-001）。
分级路由：A 优先赋能 / B 观察 / C 暂缓。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .license_tier import (  # W-4 接线（license_tier 已入主干；本导入不构成环：tier→scanner）
    OUTCOME_CAPPED, OUTCOME_NORMAL, OUTCOME_REJECT, OUTCOME_UNJUDGEABLE,
    apply_cap, classify_license,
)
from .scanner import ScanTarget

# 分级
TIER_A = "A"    # 优先赋能（DSH/Codex 类——插件化/可审计/分账痛点）
TIER_B = "B"    # 观察（有契合点但未完全成熟）
TIER_C = "C"    # 暂缓（契合度不足或不合规）


@dataclass(frozen=True)
class CandidateProfile:
    """候选诊断画像。"""
    target: ScanTarget
    non_invasive: bool            # 非侵入可挂载（插件/协议层接口）
    auditable: bool               # 可审计（append-only 日志/事件流）
    settlement_pain: bool         # 分账痛点（多智能体协作需分润/审计）
    license_compliant: bool       # License 合规（AUDIT-001：OSI 许可）
    fit_score: float              # 契合度 0-1
    tier: str                     # A/B/C
    rationale: str
    # W-4/W-5 增列（⛔ 默认值保证旧构造与旧 to_dict 消费不受影响）
    source_type: Optional[str] = None     # 来源类型（W-1 三字段透传，报告分列用）
    unjudgeable: bool = False             # 许可不可判（⛔ 与「契合度低」分列，不混）

    def to_dict(self) -> dict:
        return {
            "repo_full": self.target.repo_full,
            "stars": self.target.stars,
            "license_spdx": self.target.license_spdx,
            "non_invasive": self.non_invasive,
            "auditable": self.auditable,
            "settlement_pain": self.settlement_pain,
            "license_compliant": self.license_compliant,
            "fit_score": round(self.fit_score, 3),
            "tier": self.tier,
            "rationale": self.rationale,
            "source_type": self.source_type,
            "unjudgeable": self.unjudgeable,
        }


class CandidateDiagnoser:
    """候选诊断器（M1）。"""

    # 契合信号关键词
    INVASIVE_HINTS = ("plugin", "adapter", "bridge", "sdk", "extension",
                      "middleware", "framework", "api", "protocol", "interface",
                      "agent", "toolkit", "harness", "module")
    AUDIT_HINTS = ("log", "audit", "event", "trace", "session", "append",
                   "history", "record", "journal", "stream", "transcript")
    SETTLEMENT_HINTS = ("agent", "collaborat", "workflow", "orchestrat",
                        "multi", "task", "team", "coordinate", "share", "tool")

    # 目标优先级白名单（TDCA-OPEN-COLLAB-001 §六：DSH/Codex 优先切入）
    # 身份匹配（repo 名/描述含 deepseek/codex 且 harness）→ 定向加分，不泛化
    TARGET_PRIORITY_HINTS = ("deepseek", "codex")

    def diagnose(self, target: ScanTarget) -> CandidateProfile:
        """单仓库诊断 → 画像 + 分级。"""
        desc = (target.description or "").lower()
        kw = " ".join(target.keywords).lower()
        repo = target.repo_full.lower()

        # License 合规（AUDIT-001 硬前置；legacy 窄白名单——W-4 分档路以 license_tier 全 OSI 表为准）
        license_compliant = target.license_spdx in ("MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "MPL-2.0")

        non_invasive = any(h in desc or h in kw for h in self.INVASIVE_HINTS)
        auditable = any(h in desc or h in kw for h in self.AUDIT_HINTS)
        settlement_pain = any(h in desc or h in kw for h in self.SETTLEMENT_HINTS)

        # 契合度 = 加权（License 不合规直接 0）
        if not license_compliant:
            return CandidateProfile(
                target=target, non_invasive=non_invasive, auditable=auditable,
                settlement_pain=settlement_pain, license_compliant=False,
                fit_score=0.0, tier=TIER_C,
                rationale="License 不合规（AUDIT-001 仓库优先拒绝）——不得纳入",
            )

        score, tier, rationale = self._score(target, non_invasive, auditable,
                                             settlement_pain, desc, repo)

        return CandidateProfile(
            target=target, non_invasive=non_invasive, auditable=auditable,
            settlement_pain=settlement_pain, license_compliant=True,
            fit_score=score, tier=tier, rationale=rationale,
        )

    def _score(self, target: ScanTarget, non_invasive: bool, auditable: bool,
               settlement_pain: bool, desc: str, repo: str):
        """契合度打分 + 定级（diagnose 与 W-4 分档路共用，⛔ 公式唯一）。"""
        score = (0.35 * int(non_invasive) + 0.30 * int(auditable) +
                 0.35 * int(settlement_pain))
        # 高星加分（生态影响）
        if target.stars >= 1000:
            score = min(1.0, score + 0.1)

        # 目标优先级加分（宣言 §六：DSH/Codex 类 harness 优先切入——不泛化，仅身份命中）
        # 0.35(非侵入) + 0.1(高星) + 0.3 = 0.75 → TIER-A（优先级目标直达 A 档）
        if "harness" in (repo + " " + desc) and any(h in repo or h in desc for h in self.TARGET_PRIORITY_HINTS):
            score = min(1.0, score + 0.3)

        score = round(score, 3)  # 浮点边界修正（0.44999→0.45）

        if score >= 0.75:
            tier, rationale = TIER_A, "高契合：可挂载/可审计/分账痛点——优先赋能（挂载或化合双轨）"
        elif score >= 0.45:
            tier, rationale = TIER_B, "中契合：有接口或审计信号——观察待深化"
        else:
            tier, rationale = TIER_C, "低契合或无契合信号——暂缓"
        return score, tier, rationale

    def route(self, targets: List[ScanTarget],
              license_tiered: bool = False) -> Dict[str, List[CandidateProfile]]:
        """批量诊断 + 分级路由（A/B/C 三档）。

        license_tiered=False（默认·旧行为不变）：纯契合度分级。
        license_tiered=True（W-4）：接线许可分档——
          · 明示禁止 → 强制 C（拒收，rationale 标注）；
          · 无声明   → 强制 C·不可判（unjudgeable=True，⛔ 与「契合度低」分列）；
          · 非 OSI   → 档位上限 B（apply_cap 强制，⛔ 永不升 A——红线测试锚点）；
          · OSI 白名单 → 照原分级。
        """
        routed: Dict[str, List[CandidateProfile]] = {TIER_A: [], TIER_B: [], TIER_C: []}
        for t in targets:
            p = self.diagnose(t)
            if license_tiered:
                p = self._apply_license_tier(p)
            routed[p.tier].append(p)
        # 每档内按契合度降序
        for tier in routed:
            routed[tier].sort(key=lambda p: p.fit_score, reverse=True)
        return routed

    @classmethod
    def _apply_license_tier(cls, p: CandidateProfile) -> CandidateProfile:
        """W-4 许可分档接线（返回新画像；原画像 immutable）。

        OUTCOME_NORMAL 且旧窄名单曾判不合规者（如 GPL 系——license_tier 全 OSI
        表认定为合规）：按共用打分函数重评，保证分档口径唯一。
        """
        decision = classify_license(p.target.license_spdx)
        base = p.target
        if decision.outcome == OUTCOME_REJECT:
            return CandidateProfile(
                target=base, non_invasive=p.non_invasive, auditable=p.auditable,
                settlement_pain=p.settlement_pain, license_compliant=False,
                fit_score=p.fit_score, tier=TIER_C,
                rationale=f"拒收：{decision.reason}",
                source_type=base.source_type, unjudgeable=False)
        if decision.outcome == OUTCOME_UNJUDGEABLE:
            return CandidateProfile(
                target=base, non_invasive=p.non_invasive, auditable=p.auditable,
                settlement_pain=p.settlement_pain, license_compliant=False,
                fit_score=p.fit_score, tier=TIER_C,
                rationale=f"不可判：{decision.reason}",
                source_type=base.source_type, unjudgeable=True)
        if decision.outcome in (OUTCOME_NORMAL, OUTCOME_CAPPED) and not p.license_compliant:
            # 旧窄名单早退件（fit=0）在分档路按共用打分函数重评：
            #   NORMAL → 全 OSI 合规照评（GPL/LGPL/AGPL 系）；CAPPED → 先评后压上限 B。
            desc = (base.description or "").lower()
            repo = base.repo_full.lower()
            score, tier0, rationale0 = cls()._score(
                base, p.non_invasive, p.auditable, p.settlement_pain, desc, repo)
            if decision.outcome == OUTCOME_NORMAL:
                return CandidateProfile(
                    target=base, non_invasive=p.non_invasive, auditable=p.auditable,
                    settlement_pain=p.settlement_pain, license_compliant=True,
                    fit_score=score, tier=tier0, rationale=rationale0,
                    source_type=base.source_type, unjudgeable=False)
            tier = apply_cap(tier0, decision.cap)
            if tier != tier0:
                rationale = f"{rationale0}；降档：{decision.reason}"
            else:
                rationale = f"{rationale0}（非 OSI 上限 B：{decision.reason}）"
            return CandidateProfile(
                target=base, non_invasive=p.non_invasive, auditable=p.auditable,
                settlement_pain=p.settlement_pain, license_compliant=False,
                fit_score=score, tier=tier, rationale=rationale,
                source_type=base.source_type, unjudgeable=False)
        tier = apply_cap(p.tier, decision.cap)
        rationale = p.rationale
        if decision.outcome == OUTCOME_CAPPED and tier != p.tier:
            rationale = f"{p.rationale}；降档：{decision.reason}"
        elif decision.outcome == OUTCOME_CAPPED:
            rationale = f"{p.rationale}（非 OSI 上限 B：{decision.reason}）"
        return CandidateProfile(
            target=base, non_invasive=p.non_invasive, auditable=p.auditable,
            settlement_pain=p.settlement_pain, license_compliant=p.license_compliant,
            fit_score=p.fit_score, tier=tier, rationale=rationale,
            source_type=base.source_type, unjudgeable=False)
