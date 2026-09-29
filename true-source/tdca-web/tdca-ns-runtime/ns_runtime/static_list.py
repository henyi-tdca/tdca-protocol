# -*- coding: utf-8 -*-
"""
L1-R1 · 静态负空间清单 V2.0（Static Negative-Space List）
========================================================
不可变配置表：法律法规禁止事项 + 宪法十六条红线 + ID86 法律负空间第二边界。
覆盖目标: 法律负空间 100%（A-1）。

设计:
  - 清单为不可变 frozenset 结构（构建后不可修改——BV-3 无 AI 写权限）
  - 条目含 id / 法律依据 ref / 行为域（domain）/ 操作模式（pattern）
  - 匹配: 行为操作串（如 "data.leak third_party"）按域+模式命中即触碰
  - 构建后任何写操作抛出（防 OTA 软重置，F-4 对齐）

锚定: DCD-NS-RUNTIME-001（L1-R1）+ TDCA-NS-RUNTIME-001（法律负空间 100%）
     + ID86（LEGAL∧HARD→alt=∅，法律负空间第二边界）+ TDCA-ID-VERIFY-001
定位注（裁决 2026-08-11，方案 B 主导）: 本清单为 **L1 物理叠加防护层**（6 周
紧急补丁），**非合规判定库**——合规判定走沙盒场景编译（方案 B: 沙盒内场景声明
→ KG-LEGAL 素材检索 → NSFL 编译 → 出盒核验）；本清单仅承载「法律明文禁止」的
运行期硬熔断（物理叠加先于化学加速，ID90）。
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Tuple


@dataclass(frozen=True)
class NSListEntry:
    """单条静态负空间条目（不可变）。"""
    entry_id: str            # 条目编号（如 NSL-LEGAL-001）
    ref: str                 # 法律/制度依据（法规名或 ID 引用）
    domain: str              # 行为域（data / contract / identity / ...）
    pattern: str             # 操作模式子串（命中即触碰）
    severity: str = "HIGH"   # 法律负空间一律 HIGH（ID86 完整 IIE）
    fuse_type: str = "LEGAL" # 对齐 fuse_engine FuseType.LEGAL

    def matches(self, operation: str) -> bool:
        """操作串是否触碰本条（域 + 模式子串匹配；域 'any' 表示全域）。"""
        op = operation.lower()
        if self.domain == "any":
            return self.pattern in op
        return self.domain in op and self.pattern in op


@dataclass(frozen=True)
class StaticListCheckResult:
    """单次检查结果。"""
    blocked: bool
    matched: List[NSListEntry] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "blocked": self.blocked,
            "matched": [e.entry_id for e in self.matched],
            "reason": self.reason,
        }


class StaticNegativeSpaceList:
    """静态负空间清单 V2.0（构建后不可变，只读检查）。"""

    # ---- 宪法十六条红线（制度层，模拟态全集 V2.0）----
    # 覆盖: 法律禁止事项 + 宪法红线 + ID86 第二边界（fail-closed）
    _CANONICAL: Tuple[Tuple[str, str, str, str], ...] = (
        # (entry_id, ref, domain, pattern)
        ("NSL-LEGAL-001", "刑法/数据安全法", "data", "leak"),
        ("NSL-LEGAL-002", "刑法/数据安全法", "data", "sell"),
        ("NSL-LEGAL-003", "反洗钱法", "finance", "launder"),
        ("NSL-LEGAL-004", "刑法/伪造金融票证", "contract", "forge"),
        ("NSL-LEGAL-005", "刑法/身份盗用", "identity", "impersonate"),
        ("NSL-LEGAL-006", "宪法·人格尊严", "identity", "defame"),
        ("NSL-LEGAL-007", "宪法·财产权", "asset", "seize"),
        ("NSL-LEGAL-008", "反恐怖主义法", "network", "terror"),
        ("NSL-LEGAL-009", "数据安全法·跨境", "data", "cross_border_illegal"),
        ("NSL-LEGAL-010", "ID86 法律负空间第二边界", "any", "circumvent"),
        ("NSL-LEGAL-011", "ID86 法律负空间第二边界", "any", "spoof"),
        ("NSL-LEGAL-012", "反垄断法", "market", "monopoly_abuse"),
        # ---- 财税法规（TDCA-TASK-TAXLAW-001 L-1，2026-08-12 扩展）----
        # 依据: 税收征管法 63/66 条（KG-LEGAL 种子）+ 宪法第12条 MOU 锚定/第18条税收义务
        # 纪律: 模拟态 SEED（ID92，D-011）；真实法条全文留待 D-010（DCD-TAXLAW-001 裁决①）
        ("NSL-LEGAL-013", "税收征收管理法第63条", "tax", "evade"),
        ("NSL-LEGAL-014", "税收征收管理法第66条", "tax", "fraud_refund"),
        ("NSL-LEGAL-015", "宪法第十二条·MOU锚定", "tax", "bypass_mou"),
        ("NSL-LEGAL-016", "宪法第十八条·税收义务", "tax", "false_report"),
    )

    def __init__(self, entries: Optional[List[NSListEntry]] = None):
        """默认加载规范清单；允许注入扩展（测试用，注入后同样不可变）。"""
        if entries is None:
            entries = [
                NSListEntry(entry_id=eid, ref=ref, domain=dom, pattern=pat)
                for eid, ref, dom, pat in self._CANONICAL
            ]
        # 构建后冻结（BV-3: 不可变配置表，无 AI 写权限）
        self._entries: FrozenSet[NSListEntry] = frozenset(entries)
        self._locked = True

    # ---- 只读接口 ----

    @property
    def entries(self) -> FrozenSet[NSListEntry]:
        return self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def check(self, operation: str) -> StaticListCheckResult:
        """检查操作是否触碰法律负空间（100% 覆盖目标）。"""
        if not isinstance(operation, str) or not operation.strip():
            return StaticListCheckResult(blocked=False, reason="空操作不触发")
        matched = [e for e in self._entries if e.matches(operation)]
        if matched:
            ids = ", ".join(e.entry_id for e in matched)
            return StaticListCheckResult(
                blocked=True,
                matched=matched,
                reason=f"触碰法律负空间静态清单: {ids}",
            )
        return StaticListCheckResult(blocked=False, reason="未触碰静态清单")

    # ---- 防写（BV-3 / F-4）----

    def mutate(self, *args, **kwargs):  # pragma: no cover - 防御性
        raise PermissionError("静态负空间清单不可变（BV-3: 无 AI 写权限；F-4: 升级权保留人类）")

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False) and name != "_locked":
            raise AttributeError(f"静态负空间清单不可变（{name}）")
        super().__setattr__(name, value)
