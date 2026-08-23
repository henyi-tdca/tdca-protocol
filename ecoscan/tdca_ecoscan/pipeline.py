"""tdca_ecoscan · 邀请自动化流水线（DCD-ECOSCAN-001 M2 pipeline）

全链自动化：候选（scanner）→ 诊断（diagnoser）→ 邀请函（inviter）→ 台账（ledger）。
M2 增量：把 M1 四模块串成可执行流水线，内置：
  - 分润细则执行（宣言 §三：动态分润 15% + 开源方优先 + 无明确收费时合法化合挂载 + 15% 版税）
  - 邀请纪律（BIDIR-001：仅 TIER-A；≤2 条/周/目标 防轰炸）
  - 幂等防重复（同一 repo 每周仅 1 封邀请；台账去重）
  - 全链 NCA 落账（扫描/诊断/邀请各环节可追溯）

数据纪律（ID92）: 流水线默认 SIMULATED 输出——真实邀请发送由 Kimi 执行，本模块只产邀请函与台账。
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .diagnoser import CandidateDiagnoser, CandidateProfile, TIER_A
from .inviter import InviteGenerator, InviteLetter
from .ledger import EcoLedger
from .scanner import EcoScanner, ScanTarget

# 分润细则（TDCA-OPEN-COLLAB-001 §三，逐字一致校验锚点）
PROFIT_SHARE_DEFAULT = 0.15          # 默认版权被权调用方 15%
PROFIT_SHARE_TEXT = "15%"            # 邀请函措辞锚点
PROFIT_SHARE_CLAUSES = (
    "开源授权规定",   # 开源项目方授权优先
    "社区基金会",     # 无明确收费时版税给社区基金会
    "合法",           # 无明确收费时合法化合/挂载
)


@dataclass
class PipelineStep:
    """流水线单步记录（可追溯）。"""
    stage: str              # scan|diagnose|invite
    repo_full: str
    detail: Dict[str, any]
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))


@dataclass
class PipelineResult:
    """流水线单次执行结果。"""
    steps: List[PipelineStep]
    candidates: List[CandidateProfile]          # 全部诊断画像
    invited: List[InviteLetter]                 # 实际发出邀请（TIER-A + 频率闸通过）
    skipped: List[Dict[str, any]]               # 跳过项（非 A 档/重复/频率超限）及原因
    ledger_report: Dict[str, any]

    def to_dict(self) -> dict:
        return {
            "candidates": [p.to_dict() for p in self.candidates],
            "invited": [l.to_dict() for l in self.invited],
            "skipped": self.skipped,
            "ledger": self.ledger_report,
            "steps": [{"stage": s.stage, "repo_full": s.repo_full, "detail": s.detail} for s in self.steps],
        }


class InvitePipeline:
    """邀请自动化流水线（M2）。

    用法:
        pipe = InvitePipeline(ledger_dir=tmp)
        result = pipe.run(repos=[...])   # 静态注入（SIMULATED）
        result = pipe.run_github(token=...)  # 真实 GitHub 扫描
    """

    def __init__(self,
                 scanner: Optional[EcoScanner] = None,
                 diagnoser: Optional[CandidateDiagnoser] = None,
                 inviter: Optional[InviteGenerator] = None,
                 ledger: Optional[EcoLedger] = None,
                 provenance: str = "SIMULATED"):
        self._scanner = scanner or EcoScanner()
        self._diagnoser = diagnoser or CandidateDiagnoser()
        self._inviter = inviter or InviteGenerator(provenance=provenance)
        self._ledger = ledger or EcoLedger()
        self._provenance = provenance
        # 幂等去重：repo -> 本次流水线已邀请
        self._invited_this_run: set[str] = set()

    # ---- 主入口 ----

    def run(self, repos: Optional[List[dict]] = None,
            max_invites: int = 4) -> PipelineResult:
        """静态注入流水线（测试/离线，SIMULATED）。

        repos: 候选仓库 dict 列表（scanner.scan_static 格式）
        max_invites: 本次流水线上限（防批量轰炸）
        """
        if repos is None:
            repos = []
        targets = self._scanner.scan_static(repos) if repos else []
        return self._execute(targets, max_invites)

    def run_github(self, token: Optional[str] = None,
                   max_queries: int = 3, max_invites: int = 4) -> PipelineResult:
        """真实 GitHub 扫描流水线（公开数据，AUDIT-001 合规）。"""
        targets = self._scanner.scan_github(token=token, max_queries=max_queries)
        return self._execute(targets, max_invites)

    # ---- 执行核心 ----

    def _execute(self, targets: List[ScanTarget], max_invites: int) -> PipelineResult:
        steps: List[PipelineStep] = []
        skipped: List[Dict[str, any]] = []

        # ① 扫描落账
        if targets:
            self._ledger.record_scan([t.to_dict() for t in targets],
                                     query="m2-pipeline")
            steps.append(PipelineStep("scan", "pipeline",
                                      {"target_count": len(targets)}))

        # ② 诊断 + 分级路由
        routed = self._diagnoser.route(targets)
        candidates: List[CandidateProfile] = []
        for tier in (TIER_A,):
            candidates.extend(routed[tier])
        # 非 A 档记入 skipped（可追溯：礼貌纪律 BIDIR-001——B/C 不发出邀请）
        for tier in ("B", "C"):
            for p in routed[tier]:
                skipped.append({"repo_full": p.target.repo_full,
                                "reason": f"tier_{tier}_not_invited (BIDIR-001 polite discipline)"})

        # ③ 邀请（仅 TIER-A + 频率闸 + 幂等 + 上限）
        invited: List[InviteLetter] = []
        for profile in candidates:
            if len(invited) >= max_invites:
                skipped.append({"repo_full": profile.target.repo_full,
                                "reason": "pipeline_max_invites_reached"})
                continue
            if profile.target.repo_full in self._invited_this_run:
                skipped.append({"repo_full": profile.target.repo_full, "reason": "duplicate_in_run"})
                continue
            try:
                letter = self._inviter.generate(profile)  # 自动选轨（mount/compound）
            except ValueError as e:
                skipped.append({"repo_full": profile.target.repo_full, "reason": str(e)})
                continue
            # 台账频率闸（≤2/周/目标）+ 落账
            try:
                self._ledger.record_invite(letter)
            except ValueError as e:
                skipped.append({"repo_full": profile.target.repo_full, "reason": str(e)})
                continue
            self._invited_this_run.add(profile.target.repo_full)
            invited.append(letter)
            steps.append(PipelineStep("invite", profile.target.repo_full,
                                      {"mode": letter.mode, "nca_ref": letter.nca_ref}))

        # ④ 台账周报
        report = self._ledger.weekly_report()
        return PipelineResult(steps=steps, candidates=candidates,
                              invited=invited, skipped=skipped,
                              ledger_report=report)

    # ---- 分润细则校验（宣言 §三 措辞一致性）----

    @staticmethod
    def validate_profit_sharing(letter: InviteLetter) -> List[str]:
        """校验邀请函是否含分润细则锚点；返回缺失项列表（空 = 合规）。"""
        missing = []
        if PROFIT_SHARE_TEXT not in letter.body:
            missing.append("profit_share_15pct")
        for clause in PROFIT_SHARE_CLAUSES:
            if clause not in letter.body:
                missing.append(f"clause:{clause}")
        return missing

    # ---- 邀请函防篡改摘要（台账核验用）----

    @staticmethod
    def letter_digest(letter: InviteLetter) -> str:
        """邀请函内容哈希（防篡改：台账比对用）。"""
        payload = f"{letter.invite_id}|{letter.repo_full}|{letter.mode}|{letter.body}"
        return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
