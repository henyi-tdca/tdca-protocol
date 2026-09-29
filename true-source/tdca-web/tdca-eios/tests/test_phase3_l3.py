# -*- coding: utf-8 -*-
"""Phase 3: L3 应用层冒烟（14 用例）
覆盖: 看板 HTML 结构契约（UI-001~007 复用）/ EIOS 集成契约（ASP/CKS/NMDeviceDriver 联动）
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DASHBOARD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'dashboard', 'index.html')


def _read_dashboard() -> str:
    with open(DASHBOARD, encoding='utf-8') as f:
        return f.read()


class TestPhase3L3(unittest.TestCase):
    """SMOKE-3-01 ~ 3-14: L3 应用层"""

    # ---- 看板 HTML 结构契约（SMOKE-3-01~08） ----

    def test_01_dashboard_exists(self):
        """SMOKE-3-01: 看板 HTML 存在"""
        self.assertTrue(os.path.exists(DASHBOARD))

    def test_02_four_panels(self):
        """SMOKE-3-02: 四面板组件齐全"""
        c = _read_dashboard()
        for fn in ['AgentListPanel', 'TimelinePanel', 'NCAAuditPanel', 'MOUBoardPanel']:
            self.assertIn('function %s' % fn, c)

    def test_03_five_layer_vars(self):
        """SMOKE-3-03: 五层视觉变量（--L1~--L5）"""
        c = _read_dashboard()
        for v in ['--L5:#8B0000', '--L1:#0000CD', '--L3:#FFD700']:
            self.assertIn(v, c)

    def test_04_ui_reuse_annotations(self):
        """SMOKE-3-04: UI-001~007 复用标注"""
        c = _read_dashboard()
        for ui in ['UI-001', 'UI-003', 'UI-005', 'UI-007']:
            self.assertIn(ui, c)

    def test_05_dashboard_api_annotations(self):
        """SMOKE-3-05: dashboard API 对接注释（agents/nca/mou）"""
        c = _read_dashboard()
        for ep in ['/api/v1/dashboard/agents', '/api/v1/dashboard/nca', '/api/v1/dashboard/mou']:
            self.assertIn(ep, c)

    def test_06_asp_timeline_endpoint(self):
        """SMOKE-3-06: ASP timeline 端点注释（委托 FC-012）"""
        c = _read_dashboard()
        self.assertIn('/api/v1/asp/agents/', c)
        self.assertIn('timeline', c)

    def test_07_tag_balance(self):
        """SMOKE-3-07: div 标签配对"""
        c = _read_dashboard()
        self.assertEqual(c.count('<div'), c.count('</div>') + c.count('<div/>'))

    def test_08_react_mount(self):
        """SMOKE-3-08: React 18 createRoot 挂载"""
        c = _read_dashboard()
        self.assertIn('createRoot', c)
        self.assertIn('react@18', c)

    # ---- EIOS 集成契约（SMOKE-3-09~14） ----

    def test_09_asp_timeline_delegates(self):
        """SMOKE-3-09: ASP timeline 委托 FC-012 trajectory"""
        from fc012.flow_engine import FlowEngine
        from asp_protocol import ASPAdapter
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        engine.start({'intent': 'x'})
        flow_id = next(iter(engine.states))
        tl = adapter.timeline(flow_id)
        self.assertGreaterEqual(len(tl), 1)  # P0 NCA

    def test_10_asp_approve_default_context(self):
        """SMOKE-3-10: ASP approve 默认 context（human_signature + tax）"""
        from fc012.flow_engine import FlowEngine
        from asp_protocol import ASPAdapter
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        engine.start({'intent': 'x'})
        flow_id = next(iter(engine.states))
        state = adapter.approve(flow_id)  # 非 P8 → 不完成但不应异常
        self.assertIsNotNone(state)

    def test_11_cks_two_nodes_sync(self):
        """SMOKE-3-11: CKS 双节点同步集成"""
        from cks_deployment import CKSSyncAdapter
        a, b = CKSSyncAdapter('node-A'), CKSSyncAdapter('node-B')
        b.update_memory('K1', {'mou': {'total': 42}})
        result = a.sync_with(b)
        self.assertIn('K1', result['resolved'])

    def test_12_nmd_asp_integration(self):
        """SMOKE-3-12: NMDeviceDriver + 锚定语义（P4 委托）"""
        from nm_device_driver import NMDeviceDriver
        drv = NMDeviceDriver()
        puf = drv.read_puf()
        td = drv.generate_td_id(puf, 'sha256:const', 'BATCH-1')
        rec = drv.register_to_l1(td, {'owner_did': 'did:tdca:创始人', 'config_right_hash': 'cfg-9'})
        self.assertEqual(rec['tdid'], td)
        self.assertTrue(rec['registered'])

    def test_13_mou_aggregation_semantics(self):
        """SMOKE-3-13: MOU 聚合语义（L3 效用记忆 aggregate）"""
        from src.l3_utility_memory import L3UtilityMemory
        l3 = L3UtilityMemory()
        l3.record_utility('F1', 10, 5, 0.7, 0.3)
        l3.record_utility('F2', 20, 10, 0.8, 0.2)
        agg = l3.aggregate_mou()
        self.assertEqual(agg['total_mou'], 45)

    def test_14_dashboard_mock_contract(self):
        """SMOKE-3-14: 看板 mock 数据契约（智能体含 phase 字段）"""
        c = _read_dashboard()
        self.assertIn("phase:'P8 DELIVERING'", c)
        self.assertIn('MOCK_AGENTS', c)
        self.assertIn('MOCK_NCA', c)
        self.assertIn('MOCK_MOU', c)


if __name__ == '__main__':
    unittest.main()
