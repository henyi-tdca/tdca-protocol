"""TDCA-FC-20260802-004 模块B 单元测试 — TDCAConstraintInterpreter
Granted-By: TDCA-PRINCIPLE-FC-NCA-COH-001
NSFL-Declaration: 测试验证三态判定逻辑，不产生真实解释上链
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tdca_constraint_interpreter import (
    TDCAConstraintInterpreter,
    InterpretationResult,
    InterpretationStatus,
)


class TestConstraintInterpreter(unittest.TestCase):
    def setUp(self):
        self.interp = TDCAConstraintInterpreter()

    def test_allow_allowed_operation(self):
        """允许的合法操作 → ALLOWED"""
        ctx = {'eri_positive': True, 'risk_level': 'LOW'}
        r = self.interp.interpret(ctx, 'normal_call', '正和约束')
        self.assertEqual(r.status, InterpretationStatus.ALLOWED)

    def test_deny_forbidden_operation(self):
        """触碰禁止集合 → DENIED"""
        ctx = {'eri_positive': True}
        r = self.interp.interpret(ctx, 'data_corruption', '数据完整性')
        self.assertEqual(r.status, InterpretationStatus.DENIED)

    def test_deny_unmet_requirement(self):
        """前置条件未满足 → DENIED"""
        ctx = {'eri_positive': False}  # 正和要求未满足
        r = self.interp.interpret(ctx, 'normal_call', '正和约束')
        self.assertEqual(r.status, InterpretationStatus.DENIED)

    def test_nsfl_trigger_unknown_constraint(self):
        """无法识别的约束 → HUMAN_REQUIRED（NSFL触发）"""
        ctx = {}
        r = self.interp.interpret(ctx, 'op', '完全不存在的约束条款XYZ')
        self.assertEqual(r.status, InterpretationStatus.HUMAN_REQUIRED)
        self.assertEqual(r.constraint_id, 'UNKNOWN')

    def test_high_risk_requires_human(self):
        """HIGH 风险 → HUMAN_REQUIRED"""
        ctx = {'eri_positive': True, 'risk_level': 'HIGH'}
        r = self.interp.interpret(ctx, 'normal_call', '正和约束')
        self.assertEqual(r.status, InterpretationStatus.HUMAN_REQUIRED)

    def test_write_operation_no_signature(self):
        """写操作无签名 → HUMAN_REQUIRED"""
        ctx = {'eri_positive': True, 'risk_level': 'LOW', 'human_signature': None}
        r = self.interp.interpret(ctx, 'FileEdit', '数据完整性')
        # 数据完整性本身 deny_on_unmet + human_required=True
        self.assertIn(r.status, (InterpretationStatus.DENIED, InterpretationStatus.HUMAN_REQUIRED))

    def test_result_to_dict(self):
        """结果可序列化为 dict"""
        ctx = {'eri_positive': True}
        r = self.interp.interpret(ctx, 'normal_call', '正和约束')
        d = r.to_dict()
        self.assertIn('status', d)
        self.assertIn('constraint_id', d)
        self.assertIn('reason', d)

    def test_tax_anchor_rule_exists(self):
        """税收锚定规则存在"""
        self.assertIn('TAX_ANCHOR', self.interp.rules)


if __name__ == '__main__':
    unittest.main()
