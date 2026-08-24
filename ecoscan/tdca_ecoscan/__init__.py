"""tdca_ecoscan · 生态雷达扫描与常态赋能引擎（DCD-ECOSCAN-001 M1 + M2）

主动赋能基础设施——每日全景扫描开源仓库，提供 TDCA 赋能（挂载/化合双轨 + 调用即分润）。

M1 模块:
  - scanner: GitHub API 雷达扫描（关键词 + 活跃过滤 + 增量）
  - diagnoser: 候选诊断（制度契合度：非侵入/可审计/分账痛点/License 合规 AUDIT-001）
  - inviter: 邀请函生成（挂载/化合双轨话术 + NCA 存证编号）
  - ledger: 台账登记（扫描/诊断/邀请全量落 NCA，可追溯防重复）
M2 新增:
  - pipeline: 邀请自动化全链流水线（候选→诊断→邀请→台账 + 分润细则执行）

合规红线（内置，不可绕过）:
  - AUDIT-001 仓库优先（公开仓 + OSI 许可 + 实时数据）
  - BIDIR-001 只赋能不改码（扫描≠掠夺）；礼貌邀请 ≤2 条/周/目标
  - TDCA-OPEN-COLLAB-001 宣言（开源项目方授权优先 / 动态分润 15%）

制度锚定: DCD-ECOSCAN-001（ACCEPT）｜ AUDIT-001 ｜ BIDIR-001 ｜ TDCA-OPEN-COLLAB-001
NSFL-Declaration: 扫描数据为公开信息标注；诊断/邀请为 SIMULATED 输出（ID92），真实发送由 Kimi 执行
SPDX-License-Identifier: Apache-2.0
"""
from .scanner import EcoScanner, ScanTarget
from .diagnoser import CandidateDiagnoser, CandidateProfile, TIER_A, TIER_B, TIER_C
from .inviter import InviteGenerator, InviteLetter
from .ledger import EcoLedger
from .pipeline import InvitePipeline, PipelineResult, PipelineStep, PROFIT_SHARE_DEFAULT
from .forker import AutoForker, ForkPlan, PERMISSIVE_LICENSES

__all__ = [
    "EcoScanner",
    "ScanTarget",
    "CandidateDiagnoser",
    "CandidateProfile",
    "TIER_A",
    "TIER_B",
    "TIER_C",
    "InviteGenerator",
    "InviteLetter",
    "EcoLedger",
    "InvitePipeline",
    "PipelineResult",
    "PipelineStep",
    "PROFIT_SHARE_DEFAULT",
    "AutoForker",
    "ForkPlan",
    "PERMISSIVE_LICENSES",
]
