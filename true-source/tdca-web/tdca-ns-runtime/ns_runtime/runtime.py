# -*- coding: utf-8 -*-
"""
Layer 1 物理叠加层总入口（Runtime）
=================================
编排 L1-R1（静态清单）→ L1-R2（黑名单）→ L1-R3（MOU 预计算）→ L1-R4（熔断器），
输出统一判定（BLOCK / PASS / ESCALATE）——快系统承载 99.9%，慢系统守护 0.1%（ID71）。

判定语义:
  - 任一模块命中负空间 → 整体 BLOCK（fail-closed）
  - 需要人类裁决（MOU 未知域 / LEGAL 熔断）→ ESCALATE（慢系统上报）
  - 全部通过 → PASS

锚定: DCD-NS-RUNTIME-001（M1 Layer 1）+ TDCA-NS-RUNTIME-001 + ID71（快慢战略）
     + ID90（最小化合——物理叠加先于化学加速）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .blacklist import CallSignatureBlacklist
from .breaker_v05 import BreakerVerdict, NegativeSpaceBreakerV05
from .mou_precompute import MOUPrecomputeInterceptor
from .static_list import StaticNegativeSpaceList


class Layer1Verdict(Enum):
    PASS = "PASS"            # 放行
    BLOCK = "BLOCK"          # 负空间命中，阻断
    ESCALATE = "ESCALATE"    # 需人类裁决（慢系统）


@dataclass
class Layer1CheckResult:
    """Layer 1 整体判定结果。"""
    verdict: Layer1Verdict
    checks: Dict[str, dict] = field(default_factory=dict)
    reason: str = ""
    duration_ms: float = 0.0
    nca_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict.value,
            "checks": self.checks,
            "reason": self.reason,
            "duration_ms": round(self.duration_ms, 3),
            "nca_refs": self.nca_refs,
        }


class Layer1Runtime:
    """Layer 1 物理叠加防护层（编排器，线程安全无状态）。"""

    def __init__(self, static_list: Optional[StaticNegativeSpaceList] = None,
                 blacklist: Optional[CallSignatureBlacklist] = None,
                 mou: Optional[MOUPrecomputeInterceptor] = None,
                 breaker: Optional[NegativeSpaceBreakerV05] = None):
        self.static_list = static_list or StaticNegativeSpaceList()
        self.blacklist = blacklist or CallSignatureBlacklist()
        self.mou = mou or MOUPrecomputeInterceptor()
        self.breaker = breaker or NegativeSpaceBreakerV05()

    # ---- 主入口 ----

    def preflight(self, operation: str, api: str = "", signature: str = "",
                  behavior_domain: str = "", value: float = 0.0,
                  rule_id: str = "RULE-UNKNOWN",
                  fuse_type: str = "TECHNICAL",
                  failure: bool = False,
                  severe: bool = False) -> Layer1CheckResult:
        """Layer 1 全链路预检（A-4 热路径 <10ms）。"""
        t0 = time.perf_counter()
        checks: Dict[str, dict] = {}
        nca_refs: List[str] = []

        # 1. L1-R1 静态负空间清单（法律 100%）
        static_res = self.static_list.check(operation)
        checks["static_list"] = static_res.to_dict()
        if static_res.blocked:
            return self._finalize(Layer1Verdict.BLOCK, checks, static_res.reason, t0)

        # 2. L1-R2 调用签名黑名单（已知攻击 95%+）
        bl_res = self.blacklist.check(api, signature)
        checks["blacklist"] = bl_res.to_dict()
        if bl_res.nca_ref:
            nca_refs.append(bl_res.nca_ref)
        if bl_res.blocked:
            return self._finalize(Layer1Verdict.BLOCK, checks, bl_res.reason, t0)

        # 3. L1-R3 MOU 预计算（经济 100%）
        mou_res = self.mou.check(behavior_domain, value)
        checks["mou_precompute"] = mou_res.to_dict()
        if mou_res.blocked:
            return self._finalize(Layer1Verdict.ESCALATE, checks, mou_res.reason, t0)

        # 4. L1-R4 熔断器 v0.5（运行时异常）
        brk_res = self.breaker.decide(
            rule_id=rule_id, fuse_type=fuse_type,
            failure=failure, severe=severe,
            human_escalated=(fuse_type == "LEGAL" and severe),
        )
        checks["breaker"] = brk_res.to_dict()
        if brk_res.nca_ref:
            nca_refs.append(brk_res.nca_ref)
        if brk_res.verdict == BreakerVerdict.ESCALATE:
            return self._finalize(Layer1Verdict.ESCALATE, checks, brk_res.reason, t0)
        if brk_res.verdict == BreakerVerdict.FUSE:
            return self._finalize(Layer1Verdict.BLOCK, checks, brk_res.reason, t0)

        return self._finalize(Layer1Verdict.PASS, checks, "Layer 1 全链路通过", t0)

    def check(self, **kwargs) -> Layer1CheckResult:
        """别名（对齐既有 precheck 惯例）。"""
        return self.preflight(**kwargs)

    # ---- 内部 ----

    @staticmethod
    def _finalize(verdict: Layer1Verdict, checks: Dict[str, dict],
                  reason: str, t0: float) -> Layer1CheckResult:
        return Layer1CheckResult(
            verdict=verdict,
            checks=checks,
            reason=reason,
            duration_ms=(time.perf_counter() - t0) * 1000,
        )
