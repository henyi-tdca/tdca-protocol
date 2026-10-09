# -*- coding: utf-8 -*-
"""
TDCA 快/慢系统网关 — 人类价值判断入口
制度锚定: ID71（快系统先行、慢系统跟进）| ID85/ID86
版本: V1.0 | 状态: M2-CODED | FC: TDCA-FC-20260804-006-M2

快系统解决 99.9% 确定性操作；慢系统处理边界案例：
  CRITICAL 级熔断、宪法级 OTA 更新、负空间事件
NSFL-Declaration:
  - 任何 CRITICAL 级事件必须经慢系统网关，不可在快系统中自动恢复
  - 人类签名是慢系统放行的唯一凭据（LEGAL 负空间除外，永久熔断）
SPDX-License-Identifier: TDCA-Internal
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import time


@dataclass
class SlowSystemTicket:
    ticket_id: str
    title: str
    description: str
    nca_ref: str
    required_action: str
    status: str  # PENDING / APPROVED / REJECTED
    created_at: int
    human_signature: Optional[str] = None
    resolved_at: Optional[int] = None


class SlowSystemGateway:
    """
    慢系统网关 — 人类价值判断的入口
    """

    def __init__(self):
        self.tickets: Dict[str, SlowSystemTicket] = {}
        self.pending_queue: List[str] = []
        self._ticket_seq = 0

    def escalate(self, title: str, description: str, nca_ref: str,
                 required_action: str) -> str:
        """
        快系统上报慢系统
        触发条件：CRITICAL 级熔断、宪法级 OTA 更新、负空间事件
        """
        self._ticket_seq += 1
        ticket_id = f"SLOW-{int(time.time())}-{self._ticket_seq}"
        ticket = SlowSystemTicket(
            ticket_id=ticket_id, title=title, description=description,
            nca_ref=nca_ref, required_action=required_action,
            status="PENDING", created_at=int(time.time()),
        )
        self.tickets[ticket_id] = ticket
        self.pending_queue.append(ticket_id)
        return ticket_id

    def human_sign(self, ticket_id: str, signature: str) -> bool:
        """人类签名确认"""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return False
        if ticket.status != "PENDING":
            return False
        ticket.human_signature = signature
        ticket.status = "APPROVED"
        ticket.resolved_at = int(time.time())
        return True

    def reject(self, ticket_id: str, signature: str = "") -> bool:
        """人类拒绝（签名留痕）"""
        ticket = self.tickets.get(ticket_id)
        if not ticket or ticket.status != "PENDING":
            return False
        ticket.human_signature = signature or "REJECTED"
        ticket.status = "REJECTED"
        ticket.resolved_at = int(time.time())
        return True

    def get_pending(self) -> List[SlowSystemTicket]:
        """获取待处理队列"""
        return [self.tickets[tid] for tid in self.pending_queue
                if self.tickets[tid].status == "PENDING"]

    def get_ticket(self, ticket_id: str) -> Optional[SlowSystemTicket]:
        return self.tickets.get(ticket_id)

    def is_approved(self, ticket_id: str) -> bool:
        """检查工单是否已获人类批准"""
        ticket = self.tickets.get(ticket_id)
        return ticket is not None and ticket.status == "APPROVED"

    def pending_count(self) -> int:
        return len(self.get_pending())
