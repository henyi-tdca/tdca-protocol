"""TDCA-FC-20260802-004 模块D 单元测试 — CognitiveStateCalculator
Granted-By: ID8
NSFL-Declaration: 测试用模拟数据，缺失维度标记 [DEFAULT] 而非伪造
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tdca_cognitive_state import CognitiveStateCalculator


class TestCognitiveState(unittest.TestCase):
    def setUp(self):
        self.calc = CognitiveStateCalculator()

    def test_compute_full(self):
        """全维度计算（含 history 供 L 学习速度计算）"""
        calc = CognitiveStateCalculator(history=[0.8, 0.85, 0.9])
        state = calc.compute(
            embedding_similarity=0.85,
            constraint_satisfaction_rate=0.92,
            cross_domain_success_rate=13,
            total_calls=20,
            negative_space_detection_accuracy=0.95,
        )
        self.assertEqual(state['A'], 0.85)
        self.assertEqual(state['D'], 0.92)
        self.assertAlmostEqual(state['SC'], 0.95)
        self.assertAlmostEqual(state['C'], 0.65)  # 13/20
        self.assertEqual(state['Default-Flagged'], [])

    def test_defaults_flagged(self):
        """缺失维度 → 默认值 0.5 + 标记 [DEFAULT]"""
        state = self.calc.compute()
        self.assertEqual(state['A'], 0.5)
        self.assertEqual(state['D'], 0.5)
        self.assertEqual(state['L'], 0.5)
        self.assertEqual(state['C'], 0.5)
        self.assertEqual(state['SC'], 0.5)
        self.assertEqual(len(state['Default-Flagged']), 5)

    def test_validate_pass(self):
        """有效状态通过验证"""
        state = self.calc.compute(embedding_similarity=0.8)
        self.calc.validate(state)  # 不应抛异常

    def test_nsfl_trigger_out_of_range(self):
        """超出 [0,1] → NSFL-TRIGGER"""
        bad = {'A': 1.5, 'D': 0.5, 'L': 0.5, 'C': 0.5, 'SC': 0.5}
        with self.assertRaises(ValueError) as ctx:
            self.calc.validate(bad)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_nsfl_trigger_missing_dim(self):
        """缺失维度 → NSFL-TRIGGER"""
        bad = {'A': 0.5, 'D': 0.5}  # 缺 L/C/SC
        with self.assertRaises(ValueError) as ctx:
            self.calc.validate(bad)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_extend_nca_v3(self):
        """扩展 NCA 记录添加 Cognitive-State"""
        nca = {'NCA-ID': 'TDCA-NCA-001'}
        state = self.calc.compute(embedding_similarity=0.8)
        extended = self.calc.extend_nca(nca, state)
        self.assertIn('Cognitive-State', extended)
        self.assertEqual(extended['NCA-Schema-Version'], 'v3.0')

    def test_extend_nca_none_compatible(self):
        """state=None → 字段可空（v2.0 兼容）"""
        nca = {'NCA-ID': 'TDCA-NCA-001'}
        extended = self.calc.extend_nca(nca, None)
        self.assertIsNone(extended['Cognitive-State'])
        self.assertEqual(extended['NCA-Schema-Version'], 'v3.0')


if __name__ == '__main__':
    unittest.main()
