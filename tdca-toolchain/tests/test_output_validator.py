"""TDCA-FC-20260802-004 模块C 单元测试 — TDCAOutputValidator
Granted-By: TDCA-PRINCIPLE-FC-NCA-COH-002
NSFL-Declaration: 测试验证快系统校验与三级降级策略，内部重试不生成新NCA
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


def identity_target(x):
    return x


class TestOutputValidator(unittest.TestCase):
    def test_pass_with_embedding_func(self):
        """主路径 embedding 函数 → PASS"""
        v = TDCAOutputValidator(embedding_func=lambda a, b: 0.98)
        r = v.validate("output", identity_target, {'forbidden': []}, tolerance=0.05)
        self.assertEqual(r.status, ValidationStatus.PASS)
        self.assertEqual(r.embedding_level, EmbeddingLevel.API)

    def test_nsfl_trigger_forbidden(self):
        """触碰 ⊗ 禁止集合 → FAIL（NSFL-TRIGGER）"""
        v = TDCAOutputValidator(embedding_func=lambda a, b: 0.98)
        r = v.validate("contains __FORBIDDEN__", identity_target,
                       {'forbidden': ['__FORBIDDEN__']}, tolerance=0.05)
        self.assertEqual(r.status, ValidationStatus.FAIL)
        self.assertEqual(r.retry_count, 0)  # NSFL 立即拒绝，不重试

    def test_jaccard_degradation(self):
        """降级2: Jaccard 相似度路径"""
        v = TDCAOutputValidator()  # 无 embedding 函数, 无 sentence-transformers
        r = v.validate("abcde", lambda x: "abcde", {'forbidden': []}, tolerance=0.1)
        # Jaccard("abcde","abcde") = 1.0 ≥ 0.9 → PASS
        self.assertEqual(r.status, ValidationStatus.PASS)
        self.assertEqual(r.embedding_level, EmbeddingLevel.JACCARD)

    def test_human_required_after_retries(self):
        """重试耗尽 → HUMAN_REQUIRED"""
        v = TDCAOutputValidator(embedding_func=lambda a, b: 0.01)  # 永远不匹配
        r = v.validate("output", identity_target, {'forbidden': []}, tolerance=0.05)
        self.assertEqual(r.status, ValidationStatus.HUMAN_REQUIRED)
        self.assertEqual(r.retry_count, TDCAOutputValidator.MAX_RETRY)

    def test_retry_count_within_limit(self):
        """内部重试不超过 MAX_RETRY=3"""
        calls = []

        def low_sim(a, b):
            calls.append(1)
            return 0.01

        v = TDCAOutputValidator(embedding_func=low_sim)
        v.validate("output", identity_target, {'forbidden': []}, tolerance=0.05)
        # 初始 + 3次重试 = 4次调用
        self.assertEqual(len(calls), TDCAOutputValidator.MAX_RETRY + 1)

    def test_audit_trail_generated(self):
        """降级路径生成 Audit-Trail"""
        v = TDCAOutputValidator()  # 走 Jaccard 降级
        r = v.validate("same", lambda x: "same", {'forbidden': []}, tolerance=0.5)
        self.assertTrue(len(r.audit_trail) > 0)
        # audit 记录包含 similarity 步骤
        self.assertTrue(any('similarity' in step.get('step', '') for step in r.audit_trail))

    def test_no_new_config_right_calls(self):
        """内部重试不生成新的配置权调用记录（audit 仅含技术层步骤）"""
        v = TDCAOutputValidator(embedding_func=lambda a, b: 0.5)
        r = v.validate("x", identity_target, {'forbidden': []}, tolerance=0.9)
        # audit_trail 不应含 config_right / token 相关记录
        for step in r.audit_trail:
            self.assertNotIn('config_right', step.get('step', '').lower())


if __name__ == '__main__':
    unittest.main()
