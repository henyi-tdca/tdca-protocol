"""tdca_ecoscan · 自主 Fork 模块（TDCA-AUTOFORK-001 半自动全链）

全链：扫描候选 → 五门标准判定 → 生成 Fork 材料（README 声明 + TDCA-Agreement.yaml）
    → 待创始人确认（半自动）→ Fork 执行（GitHub API）→ NCA 存证 → 台账。

半自动（当前，模拟态）：
  扫描/判定/材料自动生成 → fork_plan 输出供创始人确认 → 确认后执行 fork。

法律红线（硬前提）:
  - 仅宽松许可（MIT/Apache/BSD——GPL 传染性拒绝）
  - 保留上游版权声明（LICENSE 不动 + README 注明）
  - 中国境内法规：不涉个人数据/内容合规/分润模拟态非证券
  - 不冒充原创（"TDCA 协议层附加版本"声明）
  - 可撤销（上游许可变更 → 停止）

模拟态账本（创始人裁定 2026-08-24）：记账为体验期正式账本，
真实结算/税务接口开通后凭账本转实际结算（NCA + ERI 权重）。
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .scanner import EcoScanner, ScanTarget
from .diagnoser import CandidateDiagnoser, CandidateProfile, TIER_A, TIER_B

# 宽松许可白名单（MIT/Apache/BSD——GPL 传染性拒绝）
PERMISSIVE_LICENSES = {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "MPL-2.0"}


@dataclass
class ForkPlan:
    """Fork 计划（半自动：材料就绪，待创始人确认）。"""
    target: ScanTarget
    tier: str
    fit_score: float
    agreement_yaml: str        # TDCA-Agreement.yaml 内容
    readme_snippet: str        # README 顶部附加声明
    rationale: str
    license_ok: bool
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    def to_dict(self) -> dict:
        return {
            "repo_full": self.target.repo_full,
            "tier": self.tier,
            "fit_score": self.fit_score,
            "license_spdx": self.target.license_spdx,
            "rationale": self.rationale,
            "license_ok": self.license_ok,
            "generated_at": self.generated_at,
        }


class AutoForker:
    """自主 Fork 执行器（半自动：生成计划 → 创始人确认 → 执行）。"""

    def __init__(self,
                 scanner: Optional[EcoScanner] = None,
                 diagnoser: Optional[CandidateDiagnoser] = None):
        self._scanner = scanner or EcoScanner()
        self._diagnoser = diagnoser or CandidateDiagnoser()

    # ---- ① 扫描 + 五门判定 ----

    def plan(self, repos: Optional[List[dict]] = None,
             max_plans: int = 5) -> List[ForkPlan]:
        """扫描候选 → 标准判定 → 生成 Fork 计划（不执行，待确认）。"""
        targets = self._scanner.scan_static(repos) if repos else []
        plans: List[ForkPlan] = []
        for t in targets:
            # 门 1：License（宽松许可）
            if t.license_spdx not in PERMISSIVE_LICENSES:
                continue
            # 门 2-4：诊断契合（活跃/契合/去重由调用方台账负责）
            p = self._diagnoser.diagnose(t)
            if p.tier not in (TIER_A, TIER_B):
                continue
            if len(plans) >= max_plans:
                break
            plans.append(self._build_plan(p))
        return plans

    # ---- ② Fork 材料生成 ----

    def _build_plan(self, profile: CandidateProfile) -> ForkPlan:
        t = profile.target
        agreement = (
            f"tdca_agreement:\n"
            f"  version: \"1.0\"\n"
            f"  upstream:\n"
            f"    repo: \"{t.repo_full}\"\n"
            f"    license: \"{t.license_spdx}\"\n"
            f"    source_url: \"https://github.com/{t.repo_full}\"\n"
            f"  mount_mode: \"fork-append\"\n"
            f"  attestation:\n"
            f"    nca_ref: \"NCA-ECOSCAN-FORK-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{{seq}}\"\n"
            f"  profit_sharing:\n"
            f"    default_rate: 0.15\n"
            f"    mode: \"simulated\"\n"
            f"    priority: \"upstream_license_first\"\n"
            f"  nsfl:\n"
            f"    red_lines: [\"no-source-modify\", \"no-license-violation\", \"no-misrepresentation\"]\n"
        )
        readme = (
            f"# {t.repo_full}（TDCA 协议层附加版本）\n\n"
            f"> ⚠️ **TDCA 协议层附加版本**：原始代码版权归原作者所有（{t.repo_full}），\n"
            f"> 本 Fork **未修改任何上游源码**，仅增加 TDCA 制度赋能配置（协议层）。\n"
            f"> 上游原始仓库：[{t.repo_full}](https://github.com/{t.repo_full})\n\n"
            f"## 许可与分润\n"
            f"- 上游代码：遵循上游 License（{t.license_spdx}）\n"
            f"- TDCA 协议层：Apache-2.0（独立许可，不覆盖上游）\n"
            f"- 分润：调用/化合产生收益时，版权被权调用方（原作者）默认 15% 版税\n"
            f"  （模拟态：NCA 确权 + ERI 权重记账，真实结算接口开通后凭账本转实际结算）\n"
            f"- 授权优先：以上游项目方授权规定为准\n\n"
            f"## 无侵入声明\n"
            f"您可以选择使用或不用本协议层——这是您的配置权（TDCA 只赋能不改码）。\n"
        )
        return ForkPlan(
            target=t, tier=profile.tier, fit_score=profile.fit_score,
            agreement_yaml=agreement, readme_snippet=readme,
            rationale=profile.rationale, license_ok=True,
        )

    # ---- ③ 半自动确认 → 执行（GitHub API，需 token）----

    def execute(self, plan: ForkPlan, token: str) -> Dict:
        """执行 Fork（GitHub API POST /repos/{owner}/{repo}/forks）。

        半自动：仅创始人确认后的 plan 执行；NCA 存证随台账。
        """
        import urllib.request
        url = f"https://api.github.com/repos/{plan.target.repo_full}/forks"
        req = urllib.request.Request(url, method="POST", headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "tdca-ecoscan-forker",
            "Accept": "application/vnd.github+json",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())

    # ---- 台账存证 ----

    @staticmethod
    def ledger_record(plan: ForkPlan, executed: bool) -> dict:
        """Fork 台账记录（NCA 存证——模拟态账本，凭账本转实际结算）。"""
        digest = hashlib.sha256(
            f"{plan.target.repo_full}|{plan.agreement_yaml}".encode("utf-8")).hexdigest()[:16]
        return {
            "NCA-ID": f"NCA-ECOSCAN-FORK-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "repo_full": plan.target.repo_full,
            "license_spdx": plan.target.license_spdx,
            "tier": plan.tier,
            "fit_score": plan.fit_score,
            "executed": executed,
            "payload_hash": f"sha256:{digest}",
            "mode": "simulated",   # 体验期记账，真实结算开通后凭账本转实际（创始人裁定）
            "generated_at": plan.generated_at,
        }
