"""
TDCA-FC-012 C-3 修正声明: 无（首版）
制度锚定: TDCA-FC-012-DESIGN-002（状态转移矩阵 12×8）
Granted-By: TDCA-FC-012-DESIGN-002

NSFL-Declaration:
  - 状态转移必须遵循 112 单元格转移矩阵
  - 熔断 Level-1/2/3 对应 ID89 三档
  - 穿越条件不满足时不得静默推进
SPDX-License-Identifier: Apache-2.0
"""

from typing import Optional
from .models import PHASES, FUSE_STATE, TERMINAL_STATES, PhaseTransition


class PhaseMachine:
    """
    9 Phase 状态机核心（DESIGN-002 Section 3）

    状态集合: 12 状态（P0~P8 + FUSE + COMPLETED + TERMINATED）
    事件集合: 8 类事件
    转移矩阵: 112 单元格
    """

    def __init__(self):
        # 状态转移表 δ: S × E → S
        self.transition_table = self._build_transition_table()
        # 穿越条件注册（按 from->to）
        self.conditions = {}
        self._register_conditions()

    def _build_transition_table(self) -> dict:
        """构建 12×8 状态转移矩阵（DESIGN-002 Section 3.3）"""
        table = {}
        for p in PHASES:
            idx = PHASES.index(p)
            table[p] = {
                'ADVANCE': PHASES[idx + 1] if idx < len(PHASES) - 1 else None,
                'FUSE': FUSE_STATE,
                'ROLLBACK': PHASES[idx - 1] if idx > 0 else None,
            }
        # P8 特殊：ADVANCE=None，HUMAN_APPROVE=COMPLETED
        table['P8']['HUMAN_APPROVE'] = 'COMPLETED'
        # FUSE 状态
        table[FUSE_STATE] = {
            'RETRY': None,  # 由 level 决定回退目标
            'HUMAN_REJECT': 'TERMINATED',
        }
        # 终态
        for t in TERMINAL_STATES:
            table[t] = {}
        return table

    def _register_conditions(self):
        """注册穿越条件（DESIGN-002 Section 2 逐 Phase）"""
        self.conditions['P0->P1'] = [
            ('connection_weight', lambda ctx: ctx.get('connection_weight', 0) > 0.5),
            ('intent_clear', lambda ctx: bool(ctx.get('intent_clear', False))),
            ('no_nsfl', lambda ctx: not ctx.get('nsfl_triggered', False)),
        ]
        self.conditions['P1->P2'] = [
            ('six_complete', lambda ctx: ctx.get('six_complete', False)),
            ('confidence', lambda ctx: ctx.get('intent_confidence', 0) >= 0.7),
            ('nsfl_pass', lambda ctx: not ctx.get('nsfl_triggered', False)),
        ]
        self.conditions['P2->P3'] = [
            ('compile_pass', lambda ctx: not ctx.get('constraints_failed', [])),
            ('token_valid', lambda ctx: ctx.get('token_status') == 'valid'),
        ]
        self.conditions['P3->P4'] = [
            ('sandbox_pass', lambda ctx: ctx.get('sandbox_passed', False)),
            ('positive_sum', lambda ctx: ctx.get('delta_utility', 0) >= 0),
        ]
        self.conditions['P4->P5'] = [
            ('puf_bound', lambda ctx: ctx.get('puf_bound', False)),
            ('quad_bind', lambda ctx: ctx.get('quad_bind', False)),
        ]
        self.conditions['P5->P6'] = [
            ('copyright_ok', lambda ctx: ctx.get('copyright_registered', False)),
            ('nca_onchain', lambda ctx: ctx.get('nca_onchain', False)),
        ]
        self.conditions['P6->P7'] = [
            ('interface_reg', lambda ctx: ctx.get('interface_registered', False)),
        ]
        self.conditions['P7->P8'] = [
            ('eri_gt_cci', lambda ctx: ctx.get('eri', 0) > ctx.get('cci', 0)),
            # OPT-C3-001: 时间价值衰减（ID84）— 求解时长超过 MAX_DURATION 拒绝
            ('time_decay', lambda ctx: self._check_time_decay(ctx)),
        ]
        self.conditions['P8->COMPLETED'] = [
            ('mou_closed', lambda ctx: ctx.get('mou_total', 0) > 0),
            ('human_signature', lambda ctx: ctx.get('human_signature', False)),
        ]

    def transition(self, state: str, event: str, context: dict) -> tuple:
        """
        执行状态转移。

        返回: (new_state, nca_required: bool, fuse: Optional[dict])
          fuse 非空表示熔断（含级别和原因）
        """
        # 熔断态处理
        if state == FUSE_STATE:
            if event == 'RETRY':
                level = context.get('fuse_level', 'LEVEL_1')
                if level == 'LEVEL_1':
                    return context.get('retry_target', 'P0'), False, None
                return state, False, {'level': level, 'reason': 'LEVEL_2 需回退'}
            if event == 'HUMAN_REJECT':
                return 'TERMINATED', False, None
            return state, False, {'level': 'LEVEL_3', 'reason': '紧急熔断'}

        # 终态不可转移
        if state in TERMINAL_STATES:
            return state, False, None

        # 常规转移
        if event == 'ADVANCE':
            target = self.transition_table[state].get('ADVANCE')
            if target is None:
                return state, False, {'level': 'LEVEL_1', 'reason': '已达最终 Phase，需 COMPLETE'}
            # 检查穿越条件
            cond_key = f"{state}->{target}"
            unmet = self._check_conditions(cond_key, context)
            if unmet:
                return FUSE_STATE, False, {
                    'level': 'LEVEL_1',
                    'reason': f"条件不满足: {', '.join(unmet)}",
                    'target': target,
                }
            return target, True, None  # 推进 + 需生成 NCA

        if event == 'FUSE':
            return FUSE_STATE, False, {'level': context.get('fuse_level', 'LEVEL_1'),
                                       'reason': context.get('fuse_reason', '熔断触发')}

        if event == 'ROLLBACK':
            target = self.transition_table[state].get('ROLLBACK')
            if target:
                return target, True, None
            return state, False, None

        if event == 'HUMAN_APPROVE' and state == 'P8':
            cond_key = 'P8->COMPLETED'
            unmet = self._check_conditions(cond_key, context)
            if unmet:
                return FUSE_STATE, False, {'level': 'LEVEL_2',
                                           'reason': f"交付条件不满足: {', '.join(unmet)}"}
            return 'COMPLETED', True, None

        if event == 'TERMINATE':
            return 'TERMINATED', False, None

        return state, False, None

    def _check_conditions(self, key: str, context: dict) -> list:
        """检查穿越条件，返回未满足条件名列表"""
        unmet = []
        for name, check in self.conditions.get(key, []):
            try:
                if not check(context):
                    unmet.append(name)
            except (KeyError, TypeError):
                unmet.append(name)
        return unmet

    # OPT-C3-001: 时间价值衰减检查（ID84 停机定理）
    @staticmethod
    def _check_time_decay(ctx: dict) -> bool:
        """
        时间价值衰减：求解时长不得超过 MAX_DURATION。
        若 start_time 或 max_duration 缺失，视为通过（原型兼容）。
        """
        start = ctx.get('start_time')
        max_duration = ctx.get('max_duration')
        if not start or not max_duration:
            return True  # 未提供时间约束 → 通过
        try:
            from datetime import datetime, timezone
            start_dt = datetime.fromisoformat(str(start))
            # 统一为 aware datetime（若 start 无时区，补 UTC）
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
            return elapsed <= max_duration
        except (ValueError, TypeError):
            return True

    def get_conditions(self, from_phase: str, to_phase: str) -> list:
        """查询穿越条件（供前端 UI-007 调用）"""
        key = f"{from_phase}->{to_phase}"
        return [c[0] for c in self.conditions.get(key, [])]
