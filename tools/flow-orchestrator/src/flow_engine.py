"""
TDCA-FC-012 C-3 修正声明: 无（首版）
制度锚定: TDCA-FC-012-DESIGN-002（FlowEngine 接口预留）
Granted-By: TDCA-FC-012-DESIGN-002

NSFL-Declaration:
  - 快系统推进前提是慢系统制度编码完成（ID84）
  - P8 交付前必须人类最终签名
  - MOU 闭环验证：Tax_in + Tax_out > 0（ID79）
SPDX-License-Identifier: Apache-2.0
"""

from datetime import datetime, timezone
from typing import Optional
from .models import FlowState, PHASES
from .phase_machine import PhaseMachine


class FlowEngine:
    """
    9 Phase 生命周期编排引擎（DESIGN-002 Section 6）

    接口（8 方法）:
      PhaseMachine: __init__ / transition / get_conditions
      FlowEngine:   start / advance / fuse / rollback / trajectory
    """

    def __init__(self, nca_generator: Optional[callable] = None,
                 mou_recorder: Optional[callable] = None):
        self.machine = PhaseMachine()
        self._nca_generator = nca_generator   # FC-001
        self._mou_recorder = mou_recorder     # FC-003A
        self.states = {}                      # flow_id -> FlowState

    # ---- 生命周期操作 ----

    def start(self, intent: dict) -> FlowState:
        """启动生命周期（Phase 0 意图孕育）"""
        now = self._now()
        state = FlowState(
            phase='P0',
            phase_seq=['P0'],
            context={'intent': intent},
            created_at=now,
            updated_at=now,
        )
        state.validate()
        self.states[state.flow_id] = state
        self._generate_nca(state, 'P0')
        return state

    def advance(self, flow_id: str, context: dict) -> FlowState:
        """推进下一 Phase（含穿越条件 + 熔断检查）"""
        state = self._get_state(flow_id)
        new_phase, nca_required, fuse = self.machine.transition(
            state.phase, 'ADVANCE', context)

        if fuse:
            state.phase = 'FUSE' if new_phase == 'FUSE' else state.phase
            self._record_fuse(state, fuse)
            state.updated_at = self._now()
            return state

        if new_phase != state.phase:
            state.phase = new_phase
            state.phase_seq.append(new_phase)
            state.context.update(context)
            if nca_required:
                self._generate_nca(state, new_phase)
            state.updated_at = self._now()
            state.validate()
        return state

    def fuse(self, flow_id: str, reason: str, level: str = 'LEVEL_1') -> FlowState:
        """触发熔断（对接 UI-006）"""
        state = self._get_state(flow_id)
        new_phase, _, fuse = self.machine.transition(state.phase, 'FUSE',
                                                     {'fuse_reason': reason, 'fuse_level': level})
        if new_phase == 'FUSE':
            state.phase = 'FUSE'
            self._record_fuse(state, {'level': level, 'reason': reason})
            state.updated_at = self._now()
        return state

    def rollback(self, flow_id: str, target_phase: str) -> FlowState:
        """回退至指定 Phase"""
        state = self._get_state(flow_id)
        if target_phase in PHASES:
            state.phase = target_phase
            state.phase_seq = state.phase_seq[:PHASES.index(target_phase) + 1]
            state.updated_at = self._now()
            self._generate_nca(state, f"{target_phase}_ROLLBACK")
        return state

    def human_approve(self, flow_id: str, context: dict) -> FlowState:
        """人类批准（P8→COMPLETED）"""
        state = self._get_state(flow_id)
        # 计算 mou_total 供条件检查（mou_closed: tax_in + tax_out > 0）
        mou_total = context.get('tax_in', 0) + context.get('tax_out', 0)
        ctx = dict(context)
        ctx['mou_total'] = mou_total
        new_phase, nca_required, fuse = self.machine.transition(
            state.phase, 'HUMAN_APPROVE', ctx)
        if fuse:
            state.phase = 'FUSE' if new_phase == 'FUSE' else state.phase
            self._record_fuse(state, fuse)
            state.updated_at = self._now()
            return state
        if new_phase in ('COMPLETED',):
            state.phase = new_phase
            state.phase_seq.append(new_phase)
            state.context.update(ctx)
            if nca_required:
                self._generate_nca(state, 'COMPLETED')
                self._close_mou(state, ctx)
            state.updated_at = self._now()
        return state

    def trajectory(self, flow_id: str) -> list:
        """返回全流程 NCA 轨迹"""
        state = self._get_state(flow_id)
        return state.nca_records

    # ---- 内部方法 ----

    def _get_state(self, flow_id: str) -> FlowState:
        if flow_id not in self.states:
            raise KeyError(f"[NSFL-TRIGGER] 生命周期不存在: {flow_id}")
        return self.states[flow_id]

    def _generate_nca(self, state: FlowState, phase: str):
        """调用 FC-001 生成 NCA（不可伪造）"""
        if self._nca_generator:
            nca = self._nca_generator(state.flow_id, phase)
        else:
            # 降级：本地占位 NCA（标记 MOCK）
            nca = {
                'nca_id': f"NCA-{phase}-{state.flow_id}",
                'flow_id': state.flow_id,
                'phase': phase,
                'mock': True,
                'timestamp': self._now(),
            }
        state.nca_records.append(nca)

    def _close_mou(self, state: FlowState, context: dict):
        """MOU 闭环验证（ID79: Tax_in + Tax_out > 0）"""
        tax_in = context.get('tax_in', 0)
        tax_out = context.get('tax_out', 0)
        mou_total = tax_in + tax_out
        if mou_total <= 0:
            raise ValueError(
                f"[NSFL-TRIGGER] MOU 未闭环: Tax_in({tax_in}) + Tax_out({tax_out}) = {mou_total} ≤ 0"
            )
        if self._mou_recorder:
            self._mou_recorder(state.flow_id, tax_in, tax_out)

    def _record_fuse(self, state: FlowState, fuse: dict):
        state.fuse_history.append({
            'phase': state.phase,
            'level': fuse.get('level'),
            'reason': fuse.get('reason'),
            'timestamp': self._now(),
        })

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
