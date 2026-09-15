# -*- coding: utf-8 -*-
"""Phase 2: L2 认知层冒烟（20 用例）
覆盖: ASP 12 态映射 / 破例识别偏离检测 / CKS 宪法收敛（R1~R4）/ 复用 TIMA VersionVector
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPhase2L2(unittest.TestCase):
    """SMOKE-2-01 ~ 2-20: L2 认知层"""

    # ---- ASP 状态映射（SMOKE-2-01~06） ----

    def test_01_asp_mapping_12_states(self):
        """SMOKE-2-01: ASP 12 态映射完整"""
        from asp_protocol import ASP_TO_FC, ASPState
        self.assertEqual(len(ASP_TO_FC), 12)
        self.assertEqual(len(ASPState), 12)

    def test_02_asp_mapping_fc012_consistent(self):
        """SMOKE-2-02: 映射集合与 FC-012 ALL_STATES 一致"""
        from asp_protocol import ASP_TO_FC
        from fc012.models import ALL_STATES
        self.assertEqual(set(ASP_TO_FC.values()), set(ALL_STATES))

    def test_03_asp_created_to_p0(self):
        """SMOKE-2-03: CREATED → P0 映射"""
        from asp_protocol import ASPAdapter, ASPState
        self.assertEqual(ASPAdapter().to_fc(ASPState.CREATED), 'P0')

    def test_04_asp_delivering_to_p8(self):
        """SMOKE-2-04: DELIVERING → P8 映射"""
        from asp_protocol import ASPAdapter, ASPState
        self.assertEqual(ASPAdapter().to_fc(ASPState.DELIVERING), 'P8')

    def test_05_asp_from_fc_reverse(self):
        """SMOKE-2-05: FC-012 P5 → REGISTERING 反向映射"""
        from asp_protocol import ASPAdapter
        self.assertEqual(ASPAdapter().from_fc('P5').value, 'REGISTERING')

    def test_06_asp_validate_mapping_clean(self):
        """SMOKE-2-06: validate_mapping 无问题"""
        from asp_protocol import ASPAdapter
        self.assertEqual(ASPAdapter().validate_mapping(), [])

    # ---- ASP 破例识别偏离检测（SMOKE-2-07~12） ----

    def test_07_id38_invalid_state(self):
        """SMOKE-2-07: 非法 ASP 状态触发破例识别"""
        from asp_protocol import ASPAdapter, ID38Exception
        with self.assertRaises(ID38Exception):
            ASPAdapter().to_fc('PAUSED')

    def test_08_id38_unknown_fc_phase(self):
        """SMOKE-2-08: 未知 FC-012 phase 触发破例识别"""
        from asp_protocol import ASPAdapter, ID38Exception
        with self.assertRaises(ID38Exception):
            ASPAdapter().from_fc('P99')

    def test_09_id38_no_engine_advance(self):
        """SMOKE-2-09: 未注入引擎 advance 触发破例识别"""
        from asp_protocol import ASPAdapter, ID38Exception
        with self.assertRaises(ID38Exception):
            ASPAdapter().advance('A1', {})

    def test_10_id38_no_engine_approve(self):
        """SMOKE-2-10: 未注入引擎 approve 触发破例识别"""
        from asp_protocol import ASPAdapter, ID38Exception
        with self.assertRaises(ID38Exception):
            ASPAdapter().approve('A1')

    def test_11_id38_no_engine_timeline(self):
        """SMOKE-2-11: 未注入引擎 timeline 触发破例识别"""
        from asp_protocol import ASPAdapter, ID38Exception
        with self.assertRaises(ID38Exception):
            ASPAdapter().timeline('A1')

    def test_12_id38_message_format(self):
        """SMOKE-2-12: 破例识别异常消息含触发器标记"""
        from asp_protocol import ASPAdapter, ID38Exception
        try:
            ASPAdapter().to_fc('BOGUS')
        except ID38Exception as e:
            self.assertIn('[ID38-TRIGGER]', str(e))
        else:
            self.fail('未触发破例识别')

    # ---- CKS 宪法收敛（SMOKE-2-13~19） ----

    def test_13_vv_merge_max(self):
        """SMOKE-2-13: TIMA VersionVector merge max 策略（复用）"""
        from src.cks_protocol import VersionVector
        v1 = VersionVector('A')
        v1.counters = {'A': 2, 'B': 1}
        v2 = VersionVector('B')
        v2.counters = {'A': 1, 'B': 3}
        merged = v1.merge(v2)
        self.assertEqual(merged.counters, {'A': 2, 'B': 3})

    def test_14_vv_dominates(self):
        """SMOKE-2-14: 版本向量支配判定"""
        from src.cks_protocol import VersionVector
        v1 = VersionVector('A')
        v1.counters = {'A': 3}
        v2 = VersionVector('B')
        v2.counters = {'A': 2}
        self.assertTrue(v1.dominates(v2))
        self.assertFalse(v2.dominates(v1))

    def test_15_cks_r1_positive_sum(self):
        """SMOKE-2-15: R1 正和博弈优先（MOU 高者胜）"""
        from cks_deployment import CKSSyncAdapter
        a, b = CKSSyncAdapter('A'), CKSSyncAdapter('B')
        a.update_memory('M1', {'mou': {'total': 100}})
        b.update_memory('M1', {'mou': {'total': 50}})
        a.sync_with(b)
        self.assertEqual(a.protocol._memory_store['M1']['content']['mou']['total'], 100)

    def test_16_cks_r2_human_signature(self):
        """SMOKE-2-16: R2 人类签名权不可覆盖（签名版胜）"""
        from cks_deployment import CKSSyncAdapter
        a, b = CKSSyncAdapter('A'), CKSSyncAdapter('B')
        a.update_memory('M2', {'mou': {'total': 999}})                      # MOU 高但无签名
        b.update_memory('M2', {'mou': {'total': 1}, 'human_signature': True})  # 有签名
        a.sync_with(b)
        self.assertTrue(a.protocol._memory_store['M2']['content'].get('human_signature'))

    def test_17_cks_r2_both_signatures_escalate(self):
        """SMOKE-2-17: 双侧签名 → R4 上报慢系统"""
        from cks_deployment import CKSSyncAdapter
        a, b = CKSSyncAdapter('A'), CKSSyncAdapter('B')
        a.update_memory('M3', {'mou': {'total': 10}, 'human_signature': True})
        b.update_memory('M3', {'mou': {'total': 20}, 'human_signature': True})
        result = a.sync_with(b)
        self.assertIn('M3', result['escalated'])

    def test_18_cks_r3_version_dominance(self):
        """SMOKE-2-18: R3 版本向量支配胜出（R1 平局时兜底）"""
        from cks_deployment import ConstitutionalConflictResolver
        resolver = ConstitutionalConflictResolver()
        local = {'memory_id': 'M4', 'content': {'mou': {'total': 30}},
                 'version_vector': {'agent-A': 3, 'agent-B': 2}, 'agent': 'agent-A'}
        remote = {'memory_id': 'M4', 'content': {'mou': {'total': 30}},
                  'version_vector': {'agent-A': 2, 'agent-B': 2}, 'agent': 'agent-B'}
        winner, reason = resolver.resolve(local, remote)
        self.assertEqual(winner['agent'], 'agent-A')
        self.assertIn('R3', reason)

    def test_19_cks_r4_tie_escalate(self):
        """SMOKE-2-19: R4 平局冲突上报慢系统"""
        from cks_deployment import CKSSyncAdapter
        a, b = CKSSyncAdapter('A'), CKSSyncAdapter('B')
        a.update_memory('M5', {'mou': {'total': 30}})
        b.update_memory('M5', {'mou': {'total': 30}})
        result = a.sync_with(b)
        self.assertIn('M5', result['escalated'])

    def test_20_cks_sync_result_structure(self):
        """SMOKE-2-20: sync_with 返回结构（merged_vector/resolved/escalated）"""
        from cks_deployment import CKSSyncAdapter
        a, b = CKSSyncAdapter('A'), CKSSyncAdapter('B')
        a.update_memory('M6', {'mou': {'total': 5}})
        result = a.sync_with(b)
        self.assertIn('merged_vector', result)
        self.assertIsInstance(result['resolved'], dict)
        self.assertIsInstance(result['escalated'], list)


if __name__ == '__main__':
    unittest.main()
