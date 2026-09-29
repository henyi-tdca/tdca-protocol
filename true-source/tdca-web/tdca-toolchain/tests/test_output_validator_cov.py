"""TDCA-FC-20260802-004 模块C 覆盖率补强
Granted-By: TDCA-PRINCIPLE-FC-NCA-COH-002
NSFL-Declaration: 测试覆盖 embedding 降级与边界路径
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tdca_output_validator import (
    TDCAOutputValidator,
    ValidationStatus,
    EmbeddingLevel,
)


class TestOutputValidatorCoverage(unittest.TestCase):
    def test_embedding_func_raises_falls_through(self):
        """embedding 函数抛异常 → 降级到 Jaccard"""
        def bad_func(a, b):
            raise RuntimeError("API down")

        v = TDCAOutputValidator(embedding_func=bad_func)
        r = v.validate("hello world", lambda x: "hello world", {'forbidden': []}, tolerance=0.5)
        # Jaccard("hello world","hello world") = 1.0 ≥ 0.5 → PASS
        self.assertEqual(r.status, ValidationStatus.PASS)
        self.assertEqual(r.embedding_level, EmbeddingLevel.JACCARD)

    def test_mid_tolerance_pass_after_retry(self):
        """低相似度首次失败 → 重试后通过"""
        sims = iter([0.4, 0.7, 0.95])  # 首次失败，重试2次后通过

        def progressive(a, b):
            return next(sims)

        v = TDCAOutputValidator(embedding_func=progressive)
        r = v.validate("out", lambda x: "t", {'forbidden': []}, tolerance=0.1)
        self.assertEqual(r.status, ValidationStatus.PASS)
        self.assertEqual(r.retry_count, 2)

    def test_validation_result_to_dict(self):
        """ValidationResult 可序列化"""
        v = TDCAOutputValidator(embedding_func=lambda a, b: 0.9)
        r = v.validate("x", lambda x: "y", {'forbidden': []}, tolerance=0.2)
        d = r.to_dict()
        self.assertIn('status', d)
        self.assertIn('similarity', d)
        self.assertIn('embedding_level', d)
        self.assertIn('audit_trail', d)

    def test_jaccard_identity_low_tolerance(self):
        """完全匹配 + 高容差 → PASS 单次"""
        v = TDCAOutputValidator()  # 无 embedding → Jaccard
        r = v.validate("test string", lambda x: "test string", {'forbidden': []}, tolerance=0.01)
        self.assertEqual(r.status, ValidationStatus.PASS)
        self.assertEqual(r.retry_count, 0)


if __name__ == '__main__':
    unittest.main()
