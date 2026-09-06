# SPDX-License-Identifier: Apache-2.0
"""TDCA-FC-012 C-3 单元测试 — FlowEngine / PhaseMachine
Granted-By: TDCA-FC-012-DESIGN-002
NSFL: 测试验证状态转移/穿越条件/熔断/MOU闭环
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.flow_engine import FlowEngine
from src.phase_machine import PhaseMachine
from src.models import ALL_STATES, PHASES


class TestPhaseMachine(unittest.TestCase):
    def setUp(self):
        self.machine = PhaseMachine()

    def test_advance_conditions_met(self):
        """条件满足时推进"""
        new, nca, fuse = self.machine.transition('P0', 'ADVANCE', {
            'connection_weight': 0.8, 'intent_clear': True, 'nsfl_triggered': False,
        })
        self.assertEqual(new, 'P1')
        self.assertTrue(nca)
        self.assertIsNone(fuse)

    def test_advance_conditions_unmet_fuse(self):
        """条件不满足 → 熔断"""
        new, nca, fuse = self.machine.transition('P0', 'ADVANCE', {
            'connection_weight': 0.2, 'intent_clear': False,
        })
        self.assertEqual(new, 'FUSE')
        self.assertIsNotNone(fuse)
        self.assertEqual(fuse['level'], 'LEVEL_1')

    def test_p8_human_approve(self):
        """P8 人类批准 → COMPLETED"""
        new, nca, fuse = self.machine.transition('P8', 'HUMAN_APPROVE', {
            'mou_total': 100, 'human_signature': True,
        })
        self.assertEqual(new, 'COMPLETED')

    def test_p8_approve_unmet(self):
        """P8 条件不满足 → 熔断"""
        new, nca, fuse = self.machine.transition('P8', 'HUMAN_APPROVE', {
            'mou_total': 0, 'human_signature': False,
        })
        self.assertEqual(new, 'FUSE')

    def test_fuse_reject_terminated(self):
        """FUSE + HUMAN_REJECT → TERMINATED"""
        new, _, _ = self.machine.transition('FUSE', 'HUMAN_REJECT', {})
        self.assertEqual(new, 'TERMINATED')

    def test_get_conditions(self):
        """查询穿越条件"""
        conds = self.machine.get_conditions('P1', 'P2')
        self.assertIn('six_complete', conds)
        self.assertIn('confidence', conds)

    # OPT-C3-001: 时间价值衰减测试
    def test_time_decay_violation(self):
        """P7→P8 求解超时 → 熔断（时间价值衰减）"""
        from datetime import datetime, timedelta, timezone
        # start_time 为 10 天前，max_duration 仅 1 秒 → 超时
        old_start = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        new, nca, fuse = self.machine.transition('P7', 'ADVANCE', {
            'eri': 0.8, 'cci': 0.3,
            'start_time': old_start, 'max_duration': 1,
        })
        self.assertEqual(new, 'FUSE')
        self.assertIsNotNone(fuse)

    def test_time_decay_ok(self):
        """P7→P8 求解未超时 → 推进"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        new, nca, fuse = self.machine.transition('P7', 'ADVANCE', {
            'eri': 0.8, 'cci': 0.3,
            'start_time': now, 'max_duration': 3600,
        })
        self.assertEqual(new, 'P8')


class TestFlowEngine(unittest.TestCase):
    def setUp(self):
        self.engine = FlowEngine()

    def test_start(self):
        """启动生命周期"""
        state = self.engine.start({'desc': '政府采购投标'})
        self.assertEqual(state.phase, 'P0')
        self.assertEqual(state.phase_seq, ['P0'])
        self.assertEqual(len(state.nca_records), 1)  # P0 NCA

    def test_full_progression(self):
        """P0→P8 全流程推进"""
        state = self.engine.start({})
        # 各 Phase 穿越条件上下文
        contexts = [
            {'connection_weight': 0.8, 'intent_clear': True},          # P0→P1
            {'six_complete': True, 'intent_confidence': 0.9},         # P1→P2
            {'constraints_failed': [], 'token_status': 'valid'},      # P2→P3
            {'sandbox_passed': True, 'delta_utility': 10},            # P3→P4
            {'puf_bound': True, 'quad_bind': True},                   # P4→P5
            {'copyright_registered': True, 'nca_onchain': True},      # P5→P6
            {'interface_registered': True},                           # P6→P7
            {'eri': 0.8, 'cci': 0.3},                                 # P7→P8
        ]
        for ctx in contexts:
            state = self.engine.advance(state.flow_id, ctx)
            self.assertNotEqual(state.phase, 'FUSE', f"熔断: {state.fuse_history}")

        self.assertEqual(state.phase, 'P8')
        self.assertEqual(len(state.phase_seq), 9)  # P0~P8

    def test_fuse_and_rollback(self):
        """熔断 + 回退"""
        state = self.engine.start({})
        state = self.engine.fuse(state.flow_id, '意图不明确', 'LEVEL_1')
        self.assertEqual(state.phase, 'FUSE')
        self.assertEqual(len(state.fuse_history), 1)
        state = self.engine.rollback(state.flow_id, 'P0')
        self.assertEqual(state.phase, 'P0')

    def _advance_to_p8(self, engine, flow_id):
        """辅助：推进到 P8"""
        contexts = [
            {'connection_weight': 0.8, 'intent_clear': True},
            {'six_complete': True, 'intent_confidence': 0.9},
            {'constraints_failed': [], 'token_status': 'valid'},
            {'sandbox_passed': True, 'delta_utility': 10},
            {'puf_bound': True, 'quad_bind': True},
            {'copyright_registered': True, 'nca_onchain': True},
            {'interface_registered': True},
            {'eri': 0.8, 'cci': 0.3},
        ]
        for ctx in contexts:
            engine.advance(flow_id, ctx)

    def test_human_approve_mou_close(self):
        """人类批准 + MOU 闭环（先推进到 P8）"""
        state = self.engine.start({})
        self._advance_to_p8(self.engine, state.flow_id)
        state = self.engine._get_state(state.flow_id)
        self.assertEqual(state.phase, 'P8')
        # 人类批准 + MOU
        state = self.engine.human_approve(state.flow_id, {
            'tax_in': 100, 'tax_out': 50, 'human_signature': True,
        })
        self.assertEqual(state.phase, 'COMPLETED')

    def test_nsfl_trigger_mou_not_closed(self):
        """MOU 未闭环 → 熔断（条件不满足，非崩溃）"""
        state = self.engine.start({})
        self._advance_to_p8(self.engine, state.flow_id)
        state = self.engine.human_approve(state.flow_id, {
            'tax_in': 0, 'tax_out': 0, 'human_signature': True,
        })
        # MOU 未闭环 → P8->COMPLETED 条件不满足 → 熔断
        self.assertEqual(state.phase, 'FUSE')
        self.assertTrue(len(state.fuse_history) > 0)

    def test_nsfl_trigger_unknown_flow(self):
        """未知 flow_id → NSFL-TRIGGER"""
        with self.assertRaises(KeyError) as ctx:
            self.engine.advance('UNKNOWN', {})
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_trajectory(self):
        """全流程轨迹"""
        state = self.engine.start({})
        traj = self.engine.trajectory(state.flow_id)
        self.assertEqual(len(traj), 1)  # P0 NCA


if __name__ == '__main__':
    unittest.main()
