# -*- coding: utf-8 -*-
"""覆盖率补充用例（非冒烟用例，不计入 69 冒烟数）

目的: 补齐 EIOS 交付模块（asp_protocol/cks_deployment/nm_device_driver）的
      成功路径与边界分支，达成冒烟规格硬性指标"覆盖率 ≥90%"。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCoverageBonus(unittest.TestCase):
    """覆盖率补充（COV-01 ~ COV-10）"""

    # ---- NMDeviceDriver 成功路径 ----

    def test_cov_01_fuse_success_levels(self):
        """COV-01: 物理熔断成功路径（LEVEL_1/2/3）"""
        from nm_device_driver import NMDeviceDriver
        drv = NMDeviceDriver()
        for lv in ('LEVEL_1', 'LEVEL_2', 'LEVEL_3'):
            self.assertTrue(drv.trigger_physical_fuse('测试原因', lv))

    def test_cov_02_ota_success(self):
        """COV-02: OTA 升级成功路径"""
        from nm_device_driver import NMDeviceDriver
        drv = NMDeviceDriver()
        self.assertTrue(drv.ota_update(
            'sha256:abcd1234', {'version': 'TDCA-CONST-v3.1.2', 'delta_items': []}))

    # ---- CKS 补充分支 ----

    def test_cov_03_cks_propose_institutional(self):
        """COV-03: CKS L0/L1 制度提案（Raft 强一致）"""
        from cks_deployment import CKSSyncAdapter
        a = CKSSyncAdapter('node-L0')
        idx = a.propose_institutional({'clause': 'C1', 'version': 'v3.1.2'})
        self.assertEqual(idx, 1)
        committed = a.protocol.get_institutional_committed()
        self.assertEqual(len(committed), 1)

    def test_cov_04_cks_mou_scalar(self):
        """COV-04: MOU 标量（非 dict）分支"""
        from cks_deployment import ConstitutionalConflictResolver
        resolver = ConstitutionalConflictResolver()
        rec = {'content': {'mou': 88}}
        self.assertEqual(resolver._mou_total(rec), 88.0)

    def test_cov_05_cks_sync_direct(self):
        """COV-05: sync_with 直接同步（远端唯一，SYNC 分支）"""
        from cks_deployment import CKSSyncAdapter
        a, b = CKSSyncAdapter('A'), CKSSyncAdapter('B')
        b.update_memory('ONLY-B', {'mou': {'total': 3}})
        result = a.sync_with(b)
        self.assertEqual(result['resolved']['ONLY-B'], 'SYNC 直接同步（远端唯一）')

    def test_cov_06_cks_r2_local_signature(self):
        """COV-06: R2 本地签名胜出分支"""
        from cks_deployment import CKSSyncAdapter
        a, b = CKSSyncAdapter('A'), CKSSyncAdapter('B')
        a.update_memory('M-SIG', {'mou': {'total': 1}, 'human_signature': True})
        b.update_memory('M-SIG', {'mou': {'total': 500}})
        a.sync_with(b)
        self.assertTrue(a.protocol._memory_store['M-SIG']['content'].get('human_signature'))

    # ---- ASP 补充分支 ----

    def test_cov_07_asp_to_fc_string(self):
        """COV-07: to_fc 字符串参数（枚举转换分支）"""
        from asp_protocol import ASPAdapter
        self.assertEqual(ASPAdapter().to_fc('COMPILING'), 'P2')

    def test_cov_08_asp_rollback_no_engine(self):
        """COV-08: rollback 未注入引擎触发破例识别"""
        from asp_protocol import ASPAdapter, ASPState, ID38Exception
        with self.assertRaises(ID38Exception):
            ASPAdapter().rollback('A1', ASPState.CREATED)

    def test_cov_09_asp_engine_rollback(self):
        """COV-09: rollback 委托引擎（注入后）"""
        from fc012.flow_engine import FlowEngine
        from asp_protocol import ASPAdapter, ASPState
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        state = engine.start({'intent': 'rb2'})
        state = adapter.rollback(state.flow_id, ASPState.CREATED)
        self.assertEqual(state.phase, 'P0')

    def test_cov_10_asp_approve_with_context(self):
        """COV-10: approve 显式 context 覆盖默认值"""
        from fc012.flow_engine import FlowEngine
        from asp_protocol import ASPAdapter
        engine = FlowEngine()
        adapter = ASPAdapter(flow_engine=engine)
        state = engine.start({'intent': 'ctx'})
        state = adapter.approve(state.flow_id, {'tax_in': 5, 'tax_out': 3})
        self.assertIsNotNone(state)


if __name__ == '__main__':
    unittest.main()
