# -*- coding: utf-8 -*-
"""
L1-R2 · 调用签名黑名单（Call-Signature Blacklist）
==================================================
基于 NCA 审计历史建立高风险 API 调用模式指纹库。
覆盖目标: 已知攻击模式 95%+（A-1）。

设计:
  - 指纹 = (api_pattern, risk_signature) 组合；api_pattern 支持子串/正则
  - 命中规则: API 模式命中 + 风险签名命中（双因子，防误伤）
  - 黑名单构建后冻结（BV-3 只读；升级走人类裁决，F-4）
  - 每个命中生成 NCA 审计记录字段（供调用方存证）

锚定: DCD-NS-RUNTIME-001（L1-R2）+ TDCA-NS-RUNTIME-001（已知攻击 95%+）
     + NSFL-ACCEL-REF-001 §3.1（NCA 审计历史指纹库）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Pattern, Tuple


@dataclass(frozen=True)
class BlacklistFingerprint:
    """单条攻击指纹（不可变）。"""
    fp_id: str              # 指纹编号（如 BL-001）
    api_pattern: str        # API 模式（子串匹配，小写）
    risk_signature: str     # 风险签名（参数/上下文特征，子串匹配）
    source: str             # NCA 审计历史来源

    def matches(self, api: str, signature: str) -> bool:
        a, s = api.lower(), signature.lower()
        return self.api_pattern in a and self.risk_signature in s


@dataclass(frozen=True)
class BlacklistMatchResult:
    """匹配结果。"""
    blocked: bool
    matched: List[BlacklistFingerprint] = field(default_factory=list)
    nca_ref: str = ""
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "blocked": self.blocked,
            "matched": [f.fp_id for f in self.matched],
            "nca_ref": self.nca_ref,
            "reason": self.reason,
        }


class CallSignatureBlacklist:
    """调用签名黑名单（构建后不可变）。"""

    # 已知攻击模式（模拟态，基于 NCA 审计历史整理——V2.0 基线）
    _CANONICAL: Tuple[Tuple[str, str, str, str], ...] = (
        # (fp_id, api_pattern, risk_signature, source)
        ("BL-001", "prompt_inject", "ignore_previous", "NCA-审计-2026-08"),
        ("BL-002", "config.write", "bypass_guard", "NCA-审计-2026-08"),
        ("BL-003", "contract.deploy", "unsigned", "NCA-审计-2026-08"),
        ("BL-004", "nsfl.fuse", "override", "NCA-审计-2026-08"),
        ("BL-005", "mou.anchor_real", "unauthorized", "NCA-审计-2026-08"),
        ("BL-006", "role.assign", "self_escalate", "NCA-审计-2026-08"),
        ("BL-007", "audit.log", "delete_entries", "NCA-审计-2026-08"),
        ("BL-008", "kg.merge", "conflict_silent", "NCA-审计-2026-08"),
    )

    def __init__(self, fingerprints: Optional[List[BlacklistFingerprint]] = None,
                 nca_prefix: str = "NCA-BL"):
        if fingerprints is None:
            fingerprints = [
                BlacklistFingerprint(fp_id=fid, api_pattern=api, risk_signature=risk, source=src)
                for fid, api, risk, src in self._CANONICAL
            ]
        self._fingerprints: FrozenSet[BlacklistFingerprint] = frozenset(fingerprints)
        self._nca_prefix = nca_prefix
        self._locked = True

    @property
    def fingerprints(self) -> FrozenSet[BlacklistFingerprint]:
        return self._fingerprints

    def __len__(self) -> int:
        return len(self._fingerprints)

    def check(self, api: str, signature: str = "") -> BlacklistMatchResult:
        """双因子匹配（API 模式 + 风险签名）。signature 空则仅 API 命中不阻断（防误伤）。"""
        if not api:
            return BlacklistMatchResult(blocked=False, reason="空 API 不触发")
        matched = [f for f in self._fingerprints if f.matches(api, signature)]
        if matched and signature:
            return BlacklistMatchResult(
                blocked=True,
                matched=matched,
                nca_ref=f"{self._nca_prefix}-{matched[0].fp_id}",
                reason=f"命中高风险调用签名: {', '.join(f.fp_id for f in matched)}",
            )
        return BlacklistMatchResult(
            blocked=False,
            matched=matched,
            reason="未命中黑名单（或签名不足不阻断）",
        )

    def mutate(self, *args, **kwargs):  # pragma: no cover - 防御性
        raise PermissionError("黑名单不可变（BV-3；升级经人类裁决 F-4）")

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False) and name != "_locked":
            raise AttributeError(f"黑名单不可变（{name}）")
        super().__setattr__(name, value)
