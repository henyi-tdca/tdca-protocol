# -*- coding: utf-8 -*-
"""Phase 5: 全链路冒烟（15 用例）
覆盖: 端到端流程（创建智能体 → 9 Phase 调度 → NCA 审计 → MOU 结算）+ 跨模块联动
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fc012.flow_engine import FlowEngine          # FC-012（封装）
from asp_protocol import ASPAdapter, ASPState    # EIOS M2
from cks_deployment import CKSSyncAdapter        # EIOS M3
from nm_device_driver import NMDeviceDriver      # EIOS M4


class TestPhase5E2E(unittest.TestCase):
    """SMOKE-5-01 ~ 5-15: 全链路端到端"""

    @staticmethod
    def _full_advance(adapter, flow_id):
        """P0→P8 完整推进"""
        ctxs = [
            {'connection_weight': 0.8, 'intent_clear': True},
            {'six_complete': True, 'intent_confidence': 0.9},
            {'constraints_failed': [], 'token_status': 'valid'},
            {'sandbox_passed': True, 'delta_utility': 10},
            {'puf_bound': True, 'quad_bind': True},
            {'copyright_registered': True, 'nca_onchain': True},
            {'interface_registered': True},
            {'eri': 0.8, 'cci': 0.3},
        ]
        for ctx in ctxs:
            adapter.advance(flow_id, ctx)

    def test_01_full_lifecycle(self):
        """SMOKE-5-01: 完整生命周期（创建→9Phase→批准→COMPLETED）"""
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        state = engine.start({'intent': 'e2e'})
        self._full_advance(adapter, state.flow_id)
        state = adapter.approve(state.flow_id, {'tax_in': 10, 'tax_out': 5})
        self.assertEqual(state.phase, 'COMPLETED')

    def test_02_mou_not_closed_fuse(self):
        """SMOKE-5-02: MOU 未闭环 → 人类批准熔断"""
        from fc012.phase_machine import PhaseMachine
        machine = PhaseMachine()
        new, _, fuse = machine.transition('P8', 'HUMAN_APPROVE', {'human_signature': True, 'mou_total': 0})
        self.assertTrue(fuse is not None or new != 'COMPLETED')

    def test_03_rollback_mid_flow(self):
        """SMOKE-5-03: 中途回退（P3→P0）"""
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        state = engine.start({'intent': 'rb'})
        adapter.advance(state.flow_id, {'connection_weight': 0.8, 'intent_clear': True})
        state = adapter.rollback(state.flow_id, ASPState.CREATED)
        self.assertEqual(state.phase, 'P0')

    def test_04_p4_anchor_nmd(self):
        """SMOKE-5-04: P4 节点锚定调用 NMDeviceDriver（硬件预留）"""
        drv = NMDeviceDriver()
        puf = drv.read_puf()
        td = drv.generate_td_id(puf, 'sha256:const', 'E2E-BATCH')
        rec = drv.register_to_l1(td, {'owner_did': 'did:tdca:创始人', 'config_right_hash': 'e2e'})
        self.assertTrue(rec['registered'])
        self.assertIn('TDID', rec['tdid'])

    def test_05_asp_cks_linked(self):
        """SMOKE-5-05: ASP 调度 + CKS 知识同步联动"""
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        state = engine.start({'intent': 'link'})
        adapter.advance(state.flow_id, {'connection_weight': 0.9, 'intent_clear': True})
        # 调度后同步知识（CKS）
        a, b = CKSSyncAdapter('agent-X'), CKSSyncAdapter('agent-Y')
        b.update_memory(state.flow_id, {'phase': state.phase, 'mou': {'total': 7}})
        result = a.sync_with(b)
        self.assertIn(state.flow_id, result['resolved'])

    def test_06_asp_timeline_for_dashboard(self):
        """SMOKE-5-06: ASP timeline 输出（看板数据源）"""
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        state = engine.start({'intent': 'tl'})
        self._full_advance(adapter, state.flow_id)
        tl = adapter.timeline(state.flow_id)
        self.assertGreaterEqual(len(tl), 9)  # P0~P8 每阶段 NCA

    def test_07_nca_audit_pipeline(self):
        """SMOKE-5-07: NCA 生成→存证→审计轨迹"""
        engine = FlowEngine()
        state = engine.start({'intent': 'audit'})
        self.assertIn('P0', [n['phase'] for n in state.nca_records])

    def test_08_mou_settlement(self):
        """SMOKE-5-08: MOU 结算闭环（P8 后 total > 0）"""
        from fc012.mou_closer import MOUCloser        # FC-012 MOU 闭环
        closer = MOUCloser()
        result = closer.close('FLOW-E2E', 10, 5)
        self.assertTrue(result['mou_total'] > 0)
        self.assertTrue(result['closed'])

    def test_09_nsfl_fuse_full_chain(self):
        """SMOKE-5-09: 负空间熔断全链路（LEVEL_3）"""
        engine = FlowEngine()
        state = engine.start({'intent': 'nsfl'})
        state = engine.fuse(state.flow_id, '法律禁止操作', 'LEVEL_3')
        self.assertEqual(state.phase, 'FUSE')

    def test_10_constitutional_convergence_chain(self):
        """SMOKE-5-10: 宪法收敛全链路（签名权覆盖正和）"""
        a, b = CKSSyncAdapter('A'), CKSSyncAdapter('B')
        a.update_memory('C1', {'mou': {'total': 999}})
        b.update_memory('C1', {'mou': {'total': 1}, 'human_signature': True})
        a.sync_with(b)
        self.assertTrue(a.protocol._memory_store['C1']['content'].get('human_signature'))

    def test_11_multi_agent_parallel(self):
        """SMOKE-5-11: 多智能体并行调度（2 agent 独立推进）"""
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        s1 = engine.start({'intent': 'p1'})
        s2 = engine.start({'intent': 'p2'})
        adapter.advance(s1.flow_id, {'connection_weight': 0.8, 'intent_clear': True})
        adapter.advance(s2.flow_id, {'connection_weight': 0.6, 'intent_clear': True})
        self.assertEqual(engine.states[s1.flow_id].phase, 'P1')
        self.assertEqual(engine.states[s2.flow_id].phase, 'P1')
        self.assertNotEqual(s1.flow_id, s2.flow_id)

    def test_12_fuse_then_rollback_recover(self):
        """SMOKE-5-12: 熔断后回退重试恢复"""
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        state = engine.start({'intent': 'retry'})
        state = engine.fuse(state.flow_id, '条件不满足', 'LEVEL_1')
        self.assertEqual(state.phase, 'FUSE')
        state = adapter.rollback(state.flow_id, ASPState.CREATED)
        self.assertEqual(state.phase, 'P0')

    def test_13_all_modules_importable(self):
        """SMOKE-5-13: 端到端模块全通（覆盖率冒烟）"""
        import tdca_nca_generator
        from tdca_utility_genie import TDCAUtilityGenie
        from tdca_kg_compiler import TDCAKnowledgeGraphCompiler
        from fc012.flow_engine import FlowEngine
        from src.cks_protocol import CKSProtocol
        self.assertTrue(all([
            callable(tdca_nca_generator.TDCANCAGenerator),
            TDCAUtilityGenie.VERSION,
            callable(TDCAKnowledgeGraphCompiler),
            callable(FlowEngine),
            callable(CKSProtocol),
        ]))

    def test_14_advance_response_contract(self):
        """SMOKE-5-14: advance 响应契约（FlowState 结构）"""
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        state = engine.start({'intent': 'contract'})
        st = adapter.advance(state.flow_id, {'connection_weight': 0.8, 'intent_clear': True})
        self.assertEqual(st.phase, 'P1')
        self.assertEqual(st.phase_seq, ['P0', 'P1'])
        self.assertTrue(hasattr(st, 'nca_records'))

    def test_15_audit_trail_integrity(self):
        """SMOKE-5-15: 审计轨迹完整性（phase_seq 顺序 + NCA 记录数）"""
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        state = engine.start({'intent': 'trail'})
        self._full_advance(adapter, state.flow_id)
        state = adapter.approve(state.flow_id, {'tax_in': 10, 'tax_out': 5})
        expected = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'COMPLETED']
        self.assertEqual(state.phase_seq, expected)
        self.assertGreaterEqual(len(state.nca_records), 10)


if __name__ == '__main__':
    unittest.main()
