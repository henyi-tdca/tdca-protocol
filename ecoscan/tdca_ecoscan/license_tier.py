# SPDX-License-Identifier: Apache-2.0
"""tdca_ecoscan · 许可分档器（发现层扩源 W-2）

四档判定（⛔ 不改 scan_static 硬拒——W-3 另案评审；本器只给分档结论，不接线旧路径）：
  OSI 白名单           → 照现闸（OUTCOME_NORMAL, cap=None）
  有条文但非 OSI        → 降档 · 上限 B（OUTCOME_CAPPED, cap="B"）
  无声明               → C·不可判（OUTCOME_UNJUDGEABLE，⛔ 不与「契合度低」混）
  明示禁止             → 拒收（OUTCOME_REJECT）

不变量落码：
  N-1 非 OSI 资源 ⛔ 永不判 A（apply_cap 强制）；
  N-3 无许可必判不可判（classify_license(None) → UNJUDGEABLE）。
"""
from __future__ import annotations

from typing import NamedTuple, Optional

from .scanner import EcoScanner

# OSI 白名单单一口径：复用 scanner.OSI_LICENSES（⛔ 不另立清单）
OSI_WHITELIST = EcoScanner.OSI_LICENSES
# 大小写归一查表（判定前已 .upper()，白名单项一并归一，避免大小写误判降档）
_OSI_LOOKUP = {lic.upper(): lic for lic in OSI_WHITELIST}

# 明示禁止词面（命中即拒收）
EXPLICIT_DENY = {"PROPRIETARY", "COMMERCIAL-ONLY", "NOACCESS", "RESTRICTED", "ALL-RIGHTS-RESERVED"}

OUTCOME_NORMAL = "normal"            # 照现闸
OUTCOME_CAPPED = "capped"            # 降档（上限 B）
OUTCOME_UNJUDGEABLE = "unjudgeable"  # C·不可判（区别于契合度低）
OUTCOME_REJECT = "reject"            # 拒收

CAP_B = "B"  # 降档上限（签批落地取值：上限 B）


class LicenseDecision(NamedTuple):
    outcome: str                 # 四档之一
    cap: Optional[str]           # 档位上限（NORMAL→None；CAPPED→"B"；其余→None）
    unjudgeable: bool            # True ⟺ 不可判（与「契合度低」分列）
    reason: str


def classify_license(license_spdx: Optional[str]) -> LicenseDecision:
    """许可四档判定（None/空串＝无声明 → 不可判）。"""
    lic = (license_spdx or "").strip().upper() or None
    if lic is None:
        return LicenseDecision(OUTCOME_UNJUDGEABLE, None, True,
                               "无许可声明 → C·不可判（≠ 契合度低）")
    if lic in EXPLICIT_DENY:
        return LicenseDecision(OUTCOME_REJECT, None, False,
                               f"明示禁止（{lic}）→ 拒收")
    if lic in _OSI_LOOKUP:
        return LicenseDecision(OUTCOME_NORMAL, None, False,
                               f"OSI 白名单（{lic}）→ 照现闸")
    return LicenseDecision(OUTCOME_CAPPED, CAP_B, False,
                           f"有条文但非 OSI（{lic}）→ 降档 · 上限 B")


def apply_cap(tier: str, cap: Optional[str]) -> str:
    """档位上限强制（N-1：非 OSI ⛔ 永不判 A）。cap="B" 时 A 一律压回 B。"""
    if cap == CAP_B and tier == "A":
        return CAP_B
    return tier
