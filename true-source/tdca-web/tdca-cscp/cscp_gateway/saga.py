# -*- coding: utf-8 -*-
"""
CSCP 跨场景协作握手协议 · Saga 补偿事务（T-CSCP-001）
锚定: TDCA-TASK-CSCP-HANDSHAKE-001 §2.2（Step 超时自动回滚 / Saga 模式补偿事务）
     + CCP T4 escrowRefund（M-4 权限修复，REV2.1）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

# 回滚动作注册表（跨模块引用，供 state_machine._rollback 审计）
ROLLBACK_ACTIONS = [
    "SANDBOX_UNLOCK",       # 沙盒解除锁定（Step-3 补偿）
    "ESCROW_REFUND",        # escrowRefund（Step-4 补偿，CCP T4 M-4）
    "TRANSLATOR_RESERVE_RELEASE",  # 翻译器预留释放（Step-3 补偿）
    "WORKORDER_CANCEL",     # 调度单取消（Step-5 补偿）
]


@dataclass
class SagaStep:
    name: str
    compensate: Callable[[], None]
    executed: bool = False


class Saga:
    """补偿事务链：按注册顺序执行，回滚时逆序补偿（Last-In-First-Out）。"""

    def __init__(self, refund_fn: Optional[Callable] = None,
                 unlock_fn: Optional[Callable] = None,
                 cancel_fn: Optional[Callable] = None,
                 release_fn: Optional[Callable] = None):
        self._steps: List[SagaStep] = []
        # 可注入补偿实现（模拟态）；缺省为 no-op 记录
        self._impl = {
            "ESCROW_REFUND": refund_fn,
            "SANDBOX_UNLOCK": unlock_fn,
            "WORKORDER_CANCEL": cancel_fn,
            "TRANSLATOR_RESERVE_RELEASE": release_fn,
        }

    def register(self, name: str) -> None:
        """注册一个已执行的原子动作（后续可被补偿）。"""
        if name not in self._impl:
            raise ValueError(f"未知补偿动作: {name}（可选: {list(self._impl)}）")
        fn = self._impl[name] or (lambda: None)
        self._steps.append(SagaStep(name=name, compensate=fn, executed=True))

    def rollback(self, reason: str = "") -> List[str]:
        """逆序执行全部补偿，返回已补偿动作清单。"""
        compensated: List[str] = []
        for step in reversed(self._steps):
            if step.executed:
                step.compensate()
                step.executed = False
                compensated.append(f"{step.name}:COMPENSATED")
        return compensated

    def pending(self) -> List[str]:
        return [s.name for s in self._steps if s.executed]
