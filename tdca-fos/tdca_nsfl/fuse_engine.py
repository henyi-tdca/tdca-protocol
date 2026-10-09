# -*- coding: utf-8 -*-
"""
TDCA NSFL 运行时熔断引擎 — 负空间函数语言 Runtime 实现
制度锚定: ID85 / ID86 / TDCA-PRINCIPLE-NSFL-001 | LEGAL-BOUNDARY-002
版本: V1.0 | 状态: M2-CODED | FC: TDCA-FC-20260804-006-M2

三不可原则: 不可算计、不可个人化、不可精确化
三可原则: 可场景化比较、可共情观察、可模糊计算
LEGAL 负空间: 绝对熔断、无替代路径、不可重置（ID86）
NSFL-Declaration:
  - FuseType.LEGAL 的 alt_path 强制为 None，不可通过任何参数注入替代路径
  - 任何 CRITICAL 级事件必须经慢系统网关，不可在快系统中自动恢复
SPDX-License-Identifier: TDCA-Internal
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import time


class FuseType(Enum):
    ETHICAL = "ETHICAL"      # 情绪/共情/审美/信仰/道德
    LEGAL = "LEGAL"          # 法律禁止 — 绝对熔断，无替代路径
    EMOTIONAL = "EMOTIONAL"
    BELIEF = "BELIEF"
    TECHNICAL = "TECHNICAL"


class FuseState(Enum):
    CLOSED = "CLOSED"        # 正常
    OPEN = "OPEN"            # 熔断中
    HALF_OPEN = "HALF_OPEN"  # 试探（仅非 LEGAL 类型）


@dataclass
class FuseEvent:
    fuse_id: str
    rule_id: str
    fuse_type: FuseType
    state: FuseState
    reason: str
    alt_path: Optional[str]  # LEGAL 类型必须为 None
    nca_ref: str
    timestamp: int
    human_escalated: bool = False


class NSFLEngine:
    """
    负空间函数语言运行时熔断引擎 — M2 完整实现
    :param nca_generator: NCA 生成器（generate 接口）
    :param slow_system_gateway: 慢系统网关（escalate 接口）
    """

    def __init__(self, nca_generator=None, slow_system_gateway=None):
        self.nca = nca_generator
        self.slow = slow_system_gateway
        self.active_fuses: Dict[str, FuseEvent] = {}
        self.fuse_history: List[FuseEvent] = []
        self._fuse_seq = 0

    def trigger(self, rule_id: str, severity: int, reason: str,
                alt_path: str, nca_ref: str,
                fuse_type: FuseType = FuseType.ETHICAL) -> str:
        """
        触发熔断器
        LEGAL 类型: 绝对熔断，无替代路径，直接阻断 + 自动上报慢系统
        其他类型: 熔断 + 替代路径路由
        """
        self._fuse_seq += 1
        fuse_id = f"FUSE-{int(time.time() * 1000)}-{self._fuse_seq}-{rule_id}"

        # LEGAL 负空间：绝对熔断，无替代路径（ID86）——强制置空并阻断注入
        if fuse_type == FuseType.LEGAL:
            alt_path = None  # 强制置空
            state = FuseState.OPEN
            human_escalated = True  # 自动上报慢系统
        else:
            state = FuseState.OPEN
            human_escalated = False

        event = FuseEvent(
            fuse_id=fuse_id, rule_id=rule_id, fuse_type=fuse_type,
            state=state, reason=reason, alt_path=alt_path,
            nca_ref=nca_ref, timestamp=int(time.time()),
            human_escalated=human_escalated,
        )

        self.active_fuses[fuse_id] = event
        self.fuse_history.append(event)

        # 生成熔断 NCA
        self._record_nca(fuse_id, rule_id, fuse_type, reason, alt_path)

        # LEGAL 类型自动上报慢系统（不可在快系统内恢复）
        if fuse_type == FuseType.LEGAL and self.slow is not None:
            self.slow.escalate(
                title=f"LEGAL负空间熔断: {rule_id}",
                description=reason,
                nca_ref=nca_ref,
                required_action="法律审查，无替代路径",
            )

        return fuse_id

    def attempt_reset(self, fuse_id: str,
                      human_signature: Optional[str] = None) -> bool:
        """
        尝试重置熔断器（半开状态试探）
        LEGAL 类型: 不可重置，除非法律变更（ID86）
        其他类型: 需人类签名确认（ID71）
        """
        fuse = self.active_fuses.get(fuse_id)
        if not fuse:
            return False

        # LEGAL 负空间：永久熔断，不可重置（ID86）
        if fuse.fuse_type == FuseType.LEGAL:
            return False

        # 非 LEGAL：需人类签名
        if not human_signature:
            raise PermissionError("非 LEGAL 熔断器重置需人类签名（慢系统）")

        fuse.state = FuseState.HALF_OPEN
        return True

    def get_active_fuses(self,
                         fuse_type: Optional[FuseType] = None) -> List[FuseEvent]:
        """获取活跃熔断器列表"""
        if fuse_type is not None:
            return [f for f in self.active_fuses.values()
                    if f.fuse_type == fuse_type]
        return list(self.active_fuses.values())

    def is_path_blocked(self, rule_id: str) -> bool:
        """检查某规则是否处于熔断状态"""
        for fuse in self.active_fuses.values():
            if fuse.rule_id == rule_id and fuse.state == FuseState.OPEN:
                return True
        return False

    def fuse_history_count(self) -> int:
        return len(self.fuse_history)

    # ---- 内部 ----

    def _record_nca(self, fuse_id: str, rule_id: str, fuse_type: FuseType,
                    reason: str, alt_path: Optional[str]):
        """生成熔断 NCA — ID91"""
        if self.nca is None:
            return
        if hasattr(self.nca, "generate"):
            self.nca.generate(
                type="INSTITUTIONAL", layer=3,
                content={
                    "event": "NSFL_FUSE_TRIGGERED",
                    "fuse_id": fuse_id,
                    "rule_id": rule_id,
                    "fuse_type": fuse_type.value,
                    "reason": reason,
                    "alt_path": alt_path,
                    "absolute_block": fuse_type == FuseType.LEGAL,
                },
            )
