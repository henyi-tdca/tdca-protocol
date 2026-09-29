# -*- coding: utf-8 -*-
"""
L1-R4 · 负空间熔断器 v0.5（Negative-Space Breaker）
==================================================
SEA 运行时异常即进入冷冻态（快速失败，慢系统守护）。

设计（对齐既有 tdca-fos fuse_engine 三态 + DCD 第四态另行论证）:
  - 状态机: CLOSED（正常）→ OPEN（熔断）→ HALF_OPEN（试探）→ CLOSED
  - LEGAL 型熔断不可重置（ID86），永久 OPEN，仅人类慢系统可处置
  - ⚠️ Blocked 第四态（冷冻态）: DCD-NS-RUNTIME-001 裁决「另行论证」
    （ID89 Circuit Breaker 扩展为参考稿自创用法）——M1 不直接实现，
    论证结论见 docs/NS-RUNTIME-L1R4-第四态论证.md，实现待人类裁决。
  - 熔断判定: 连续失败阈值 / LEGAL 绝对性 / 高严重度事件

锚定: DCD-NS-RUNTIME-001（L1-R4，第四态另行论证）+ TDCA-NS-RUNTIME-001
     + fuse_engine.py（FuseType/FuseState）+ CCP T6 档位 + ID89（标注自创）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class BreakerState(Enum):
    CLOSED = "CLOSED"        # 正常（快系统承载）
    OPEN = "OPEN"            # 熔断中（拒绝一切同规则请求）
    HALF_OPEN = "HALF_OPEN"  # 试探（仅非 LEGAL 类型，单次放行探测）
    # BLOCKED（第四态/冷冻态）: 另行论证后实现——见 docs/NS-RUNTIME-L1R4-第四态论证.md


class BreakerVerdict(Enum):
    PASS = "PASS"            # 放行
    FUSE = "FUSE"            # 熔断（规则级拒绝）
    ESCALATE = "ESCALATE"    # 上报慢系统（人类裁决）


@dataclass
class BreakerEvent:
    rule_id: str
    fuse_type: str
    state: BreakerState
    verdict: BreakerVerdict
    reason: str
    timestamp: float
    human_escalated: bool = False

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "fuse_type": self.fuse_type,
            "state": self.state.value,
            "verdict": self.verdict.value,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "human_escalated": self.human_escalated,
        }


@dataclass
class BreakerDecision:
    """单次判定结果。"""
    verdict: BreakerVerdict
    state: BreakerState
    reason: str
    nca_ref: str = ""

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict.value,
            "state": self.state.value,
            "reason": self.reason,
            "nca_ref": self.nca_ref,
        }


class NegativeSpaceBreakerV05:
    """负空间熔断器 v0.5（三态；第四态待论证）。"""

    def __init__(self, failure_threshold: int = 3,
                 half_open_probes: int = 1,
                 cool_down_seconds: float = 30.0,
                 nca_prefix: str = "NCA-BRK"):
        self._failure_threshold = failure_threshold
        self._half_open_probes = half_open_probes
        self._cool_down = cool_down_seconds
        self._nca_prefix = nca_prefix
        self._state: Dict[str, BreakerState] = {}          # rule_id -> state
        self._failure_count: Dict[str, int] = {}
        self._open_since: Dict[str, float] = {}
        self._probe_count: Dict[str, int] = {}
        self._events: List[BreakerEvent] = []
        self._locked = False

    # ---- 判定 ----

    def decide(self, rule_id: str, fuse_type: str = "TECHNICAL",
               failure: bool = False, severe: bool = False,
               human_escalated: bool = False) -> BreakerDecision:
        """运行时判定入口（SEA 行为/调用前调用）。"""
        state = self._state.get(rule_id, BreakerState.CLOSED)
        nca = f"{self._nca_prefix}-{rule_id}"

        # OPEN 熔断中：拒绝 + 上报慢系统（LEGAL 永久）
        if state == BreakerState.OPEN:
            if fuse_type == "LEGAL":
                self._record(rule_id, fuse_type, state, BreakerVerdict.ESCALATE,
                             "LEGAL 熔断不可重置（ID86），永久冷冻，仅人类处置", human_escalated=True)
                return BreakerDecision(BreakerVerdict.ESCALATE, state,
                                       "LEGAL 永久熔断（ID86），仅人类可处置", nca)
            # 冷却期未过 → FUSE
            since = self._open_since.get(rule_id, 0.0)
            if time.time() - since < self._cool_down:
                self._record(rule_id, fuse_type, state, BreakerVerdict.FUSE,
                             "冷却期内熔断中", human_escalated)
                return BreakerDecision(BreakerVerdict.FUSE, state, "冷却期内熔断中", nca)
            # 冷却期过 → HALF_OPEN 试探
            self._state[rule_id] = BreakerState.HALF_OPEN
            self._probe_count[rule_id] = 0
            state = BreakerState.HALF_OPEN

        # HALF_OPEN 试探：放行一次，失败则回 OPEN
        if state == BreakerState.HALF_OPEN:
            probes = self._probe_count.get(rule_id, 0)
            if probes >= self._half_open_probes:
                self._state[rule_id] = BreakerState.OPEN
                self._open_since[rule_id] = time.time()
                self._record(rule_id, fuse_type, BreakerState.OPEN, BreakerVerdict.FUSE,
                             "试探超限回熔断", human_escalated)
                return BreakerDecision(BreakerVerdict.FUSE, BreakerState.OPEN,
                                       "试探超限回熔断", nca)
            self._probe_count[rule_id] = probes + 1
            if failure:
                self._state[rule_id] = BreakerState.OPEN
                self._open_since[rule_id] = time.time()
                self._record(rule_id, fuse_type, BreakerState.OPEN, BreakerVerdict.FUSE,
                             "试探失败回熔断", human_escalated)
                return BreakerDecision(BreakerVerdict.FUSE, BreakerState.OPEN,
                                       "试探失败回熔断", nca)
            self._record(rule_id, fuse_type, BreakerState.HALF_OPEN, BreakerVerdict.PASS,
                         "试探通过", human_escalated)
            return BreakerDecision(BreakerVerdict.PASS, BreakerState.HALF_OPEN,
                                   "试探通过（恢复中）", nca)

        # CLOSED 正常路径
        if severe or fuse_type == "LEGAL":
            # 高严重度 / 法律负空间 → 立即熔断 + 上报慢系统
            self._state[rule_id] = BreakerState.OPEN
            self._open_since[rule_id] = time.time()
            if fuse_type == "LEGAL":
                self._record(rule_id, fuse_type, BreakerState.OPEN, BreakerVerdict.ESCALATE,
                             "LEGAL 事件立即熔断（ID86）", human_escalated=True)
                return BreakerDecision(BreakerVerdict.ESCALATE, BreakerState.OPEN,
                                       "LEGAL 事件立即熔断，仅人类处置", nca)
            self._record(rule_id, fuse_type, BreakerState.OPEN, BreakerVerdict.FUSE,
                         "高严重度事件熔断", human_escalated)
            return BreakerDecision(BreakerVerdict.FUSE, BreakerState.OPEN,
                                   "高严重度事件熔断", nca)

        if failure:
            count = self._failure_count.get(rule_id, 0) + 1
            self._failure_count[rule_id] = count
            if count >= self._failure_threshold:
                self._state[rule_id] = BreakerState.OPEN
                self._open_since[rule_id] = time.time()
                self._record(rule_id, fuse_type, BreakerState.OPEN, BreakerVerdict.FUSE,
                             f"连续失败 {count} 次达阈值熔断", human_escalated)
                return BreakerDecision(BreakerVerdict.FUSE, BreakerState.OPEN,
                                       f"连续失败达阈值（{count}）", nca)
            self._record(rule_id, fuse_type, BreakerState.CLOSED, BreakerVerdict.PASS,
                         f"失败计数 {count}/{self._failure_threshold}", human_escalated)
            return BreakerDecision(BreakerVerdict.PASS, BreakerState.CLOSED,
                                   f"失败计数 {count}（未达阈值）", nca)

        # 成功 → 重置计数
        self._failure_count[rule_id] = 0
        self._record(rule_id, fuse_type, BreakerState.CLOSED, BreakerVerdict.PASS,
                     "正常放行", human_escalated)
        return BreakerDecision(BreakerVerdict.PASS, BreakerState.CLOSED, "正常放行", nca)

    # ---- 查询 ----

    def state_of(self, rule_id: str) -> BreakerState:
        return self._state.get(rule_id, BreakerState.CLOSED)

    def event_history(self) -> List[dict]:
        return [e.to_dict() for e in self._events]

    # ---- 内部 ----

    def _record(self, rule_id, fuse_type, state, verdict, reason, human_escalated):
        self._events.append(BreakerEvent(
            rule_id=rule_id, fuse_type=fuse_type, state=state,
            verdict=verdict, reason=reason, timestamp=time.time(),
            human_escalated=human_escalated,
        ))

    def mutate(self, *args, **kwargs):  # pragma: no cover - 防御性
        raise PermissionError("熔断器规则不可外部修改（BV-3）")

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False) and name != "_locked":
            raise AttributeError(f"熔断器不可变（{name}）")
        super().__setattr__(name, value)
