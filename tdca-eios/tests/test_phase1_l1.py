# -*- coding: utf-8 -*-
"""Phase 1: L1 基础层冒烟（15 用例）
覆盖: FC-001 NCA 生成器封装 / FC-004 效用精灵 / FC-005 知识图谱编译器 / NMDeviceDriver 基础
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestPhase1L1(unittest.TestCase):
    """SMOKE-1-01 ~ 1-15: L1 基础层"""

    # ---- FC-001 NCA 生成器封装（SMOKE-1-01~05） ----

    def test_01_nca_generator_fields(self):
        """SMOKE-1-01: NCA 生成字段完整（11 必填字段）"""
        from tdca_nca_generator import TDCANCAGenerator
        import tempfile
        gen = TDCANCAGenerator(
            operation_type='Review', path=os.path.abspath(__file__),
            pre_state_hash='a' * 64, post_state_hash='b' * 64,
            nca_dir=tempfile.mkdtemp())
        record = gen._build_record()
        for f in ['NCA-ID', 'Function-Call-ID', 'Operation-Type', 'Operator',
                  'Timestamp', 'Pre-State', 'Post-State', 'Config-Right-Token',
                  'Audit-Trail', 'Human-Signature', 'Negative-Space-Check']:
            self.assertIn(f, record)

    def test_02_nca_invalid_operation_nsfl(self):
        """SMOKE-1-02: 非法操作类型触发 NSFL"""
        from tdca_nca_generator import TDCANCAGenerator
        import tempfile
        with self.assertRaises(ValueError) as ctx:
            TDCANCAGenerator(operation_type='HACK', path=os.path.abspath(__file__),
                             pre_state_hash='a' * 64, post_state_hash='b' * 64,
                             nca_dir=tempfile.mkdtemp())
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_03_nca_hash_deterministic(self):
        """SMOKE-1-03: SHA-256 哈希计算一致性"""
        from tdca_nca_generator import TDCANCAGenerator
        data = b'TDCA institutional memory'
        h1 = TDCANCAGenerator.hash_bytes(data)
        h2 = TDCANCAGenerator.hash_bytes(data)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_04_nca_negative_space_field(self):
        """SMOKE-1-04: NCA 负空间检查字段（NSFL 版本 + 未触发）"""
        from tdca_nca_generator import TDCANCAGenerator
        import tempfile
        gen = TDCANCAGenerator(operation_type='Audit', path=os.path.abspath(__file__),
                               pre_state_hash='a' * 64, post_state_hash='b' * 64,
                               nca_dir=tempfile.mkdtemp())
        ns = gen._build_record()['Negative-Space-Check']
        self.assertFalse(ns['Triggered'])
        self.assertTrue(ns['NSFL-Version'].startswith('V'))

    def test_05_nca_config_right_token(self):
        """SMOKE-1-05: 配置权令牌六字段完整"""
        from tdca_nca_generator import TDCANCAGenerator
        import tempfile
        gen = TDCANCAGenerator(operation_type='CodeGen', path=os.path.abspath(__file__),
                               pre_state_hash='a' * 64, post_state_hash='b' * 64,
                               nca_dir=tempfile.mkdtemp())
        crt = gen._build_record()['Config-Right-Token']
        for f in ['Scope', 'Rollback', 'Audit-Trail', 'Human-Signature-Required', 'Max-Retry', 'Granted-By']:
            self.assertIn(f, crt)

    # ---- FC-004 效用精灵封装（SMOKE-1-06~08） ----

    def test_06_genie_import(self):
        """SMOKE-1-06: 效用精灵主类可导入"""
        from tdca_utility_genie import TDCAUtilityGenie
        self.assertEqual(TDCAUtilityGenie.VERSION, '1.0.0')

    def test_07_genie_positive_sum(self):
        """SMOKE-1-07: 正和满意解求解返回结构"""
        from tdca_utility_genie import TDCAUtilityGenie
        from solvers.positive_sum_solver import Agent
        genie = TDCAUtilityGenie()
        sol = genie.solve_positive_sum(
            participants=[Agent('A', 1.0), Agent('B', 1.0)],
            objective_functions=[lambda x: x * 2, lambda x: x * 2],
            constraint_matrix=[],
            reservation_utilities=[5.0, 5.0],
            time_budget=1.0)
        self.assertIsNotNone(sol)

    def test_08_genie_nsfl_human_priority(self):
        """SMOKE-1-08: 效用精灵不替代人类价值判断（NSFL 声明存在）"""
        from tdca_utility_genie import TDCAUtilityGenie
        src = open(TDCAUtilityGenie.__module__.replace('.', '/') + '.py', encoding='utf-8').read() if False else ''
        # 验证模块 docstring 含 NSFL 约束
        import tdca_utility_genie
        doc = tdca_utility_genie.__doc__ or ''
        self.assertIn('NSFL', doc)

    # ---- FC-005 知识图谱编译器封装（SMOKE-1-09~11） ----

    def test_09_kg_compiler_import(self):
        """SMOKE-1-09: 知识图谱编译器主类可导入"""
        from tdca_kg_compiler import TDCAKnowledgeGraphCompiler
        self.assertTrue(callable(TDCAKnowledgeGraphCompiler))

    def test_10_kg_compile_prior_signature(self):
        """SMOKE-1-10: compile_prior 接口契约（graph_ref + node_selection）"""
        import inspect
        from tdca_kg_compiler import TDCAKnowledgeGraphCompiler
        sig = inspect.signature(TDCAKnowledgeGraphCompiler.compile_prior)
        params = list(sig.parameters)
        self.assertIn('graph_ref', params)
        self.assertIn('node_selection', params)

    def test_11_kg_extractor_module(self):
        """SMOKE-1-11: NCA 提取器模块可导入（FC-005 子模块）"""
        from extractors.nca_extractor import NCAExtractor  # noqa: F401
        self.assertTrue(True)

    # ---- NMDeviceDriver 基础（SMOKE-1-12~15） ----

    def test_12_nmd_puf_read(self):
        """SMOKE-1-12: PUF 指纹读取非空"""
        from nm_device_driver import NMDeviceDriver
        puf = NMDeviceDriver().read_puf()
        self.assertTrue(len(puf) > 8)
        self.assertIn('SRAM-PUF', puf)

    def test_13_nmd_tdid_deterministic(self):
        """SMOKE-1-13: TDID 生成确定性（同输入同输出）"""
        from nm_device_driver import NMDeviceDriver
        drv = NMDeviceDriver()
        t1 = drv.generate_td_id('fp1', 'sha256:abc', 'B1')
        t2 = drv.generate_td_id('fp1', 'sha256:abc', 'B1')
        self.assertEqual(t1, t2)

    def test_14_nmd_tdid_format(self):
        """SMOKE-1-14: TDID 格式（TDID- + 32 大写 hex）"""
        from nm_device_driver import NMDeviceDriver
        drv = NMDeviceDriver()
        td = drv.generate_td_id('fp', 'sha256:h', 'B2')
        self.assertTrue(td.startswith('TDID-'))
        hexpart = td[5:]
        self.assertEqual(len(hexpart), 32)
        self.assertEqual(hexpart, hexpart.upper())

    def test_15_nmd_register_to_l1(self):
        """SMOKE-1-15: L1 所有权登记返回结构"""
        from nm_device_driver import NMDeviceDriver
        drv = NMDeviceDriver()
        r = drv.register_to_l1('TDID-X', {'owner_did': 'did:tdca:甲', 'config_right_hash': 'cfg'})
        self.assertTrue(r['registered'])
        self.assertIn('nca_ref', r)


if __name__ == '__main__':
    unittest.main()
