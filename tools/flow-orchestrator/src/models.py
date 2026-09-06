"""
TDCA-FC-012 C-3 修正声明: 无（首版）
制度锚定: TDCA-FC-012-DESIGN-002（数据模型定义）
Granted-By: TDCA-FC-012-DESIGN-002

NSFL-Declaration:
  - FlowState 的 phase 字段必须符合 12 状态集合
  - NCA 记录必须由 FC-001 生成，禁止伪造
  - context 不得包含敏感/负空间数据
SPDX-License-Identifier: Apache-2.0
"""

import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# 12 状态集合（DESIGN-002 Section 1.1）
PHASES = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8']
TERMINAL_STATES = ['COMPLETED', 'TERMINATED']
FUSE_STATE = 'FUSE'
ALL_STATES = PHASES + [FUSE_STATE] + TERMINAL_STATES

# 8 类事件（DESIGN-002 Section 1.2）
# OPT-C3-003: COMPLETE 已移除（P8→COMPLETED 由 HUMAN_APPROVE 实现，COMPLETE 冗余）
EVENTS = ['START', 'ADVANCE', 'FUSE', 'ROLLBACK', 'RETRY',
          'HUMAN_APPROVE', 'HUMAN_REJECT', 'TERMINATE']


@dataclass
class PhaseTransition:
    """穿越条件（DESIGN-002 Section 4.2）"""
    from_phase: str
    to_phase: str
    conditions: list = field(default_factory=list)  # 条件检查函数列表
    fuse_level: str = 'LEVEL_1'                     # 不满足时熔断级别
    requires_human: bool = False                    # 是否需人类确认


@dataclass
class FlowState:
    """生命周期状态（DESIGN-002 Section 4.1）"""
    flow_id: str = field(default_factory=lambda: f"FLOW-{uuid.uuid4().hex[:8]}")
    phase: str = 'P0'
    phase_seq: list = field(default_factory=list)
    nca_records: list = field(default_factory=list)
    context: dict = field(default_factory=dict)
    fuse_history: list = field(default_factory=list)
    created_at: str = ''
    updated_at: str = ''

    def to_dict(self) -> dict:
        return asdict(self)

    def validate(self) -> None:
        """自证机制：phase 必须属于 12 状态集合"""
        if self.phase not in ALL_STATES:
            raise ValueError(
                f"[NSFL-TRIGGER] 非法状态: {self.phase}，"
                f"必须属于 {ALL_STATES}"
            )
