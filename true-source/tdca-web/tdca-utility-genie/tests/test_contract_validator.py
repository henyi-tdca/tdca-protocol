"""TDCA-FC-20260802-004 子模块D 测试 — ContractDeliveryValidator
Granted-By: ID79
NSFL-Declaration: 测试验证交付确认/税收锚定/根因分析
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validators.contract_delivery_validator import (
    ContractDeliveryValidator, DeliveryValidationReport,
)


class TestContractValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ContractDeliveryValidator()

    def test_validate_pass_100(self):
        """达成率 ≥ 100% → 通过"""
        report = self.validator.validate(
            contract_id='C1',
            target_utility={'tax': 100.0},
            actual_mou={'Actual-Total': 100.0},
            execution_trace={'errors': []},
            token_ref='TDCA-CRT-20260801-001',
        )
        self.assertGreaterEqual(report.utility_achievement, 100.0)
        self.assertEqual(report.root_cause, 'none')
        self.assertEqual(report.recommendation, '确认通过，归档 NCA')

    def test_validate_warn_80_100(self):
        """达成率 80-100% → 警告"""
        report = self.validator.validate(
            contract_id='C1',
            target_utility={'tax': 100.0},
            actual_mou={'Actual-Total': 90.0},
            execution_trace={'errors': []},
            token_ref='TDCA-CRT-20260801-001',
        )
        self.assertAlmostEqual(report.utility_achievement, 90.0)
        self.assertIn('警告', report.recommendation)

    def test_root_cause_config(self):
        """税收锚定未通过 → 配置问题"""
        report = self.validator.validate(
            contract_id='C1',
            target_utility={'tax': 100.0},
            actual_mou={'Actual-Total': None},  # 税收锚定失败
            execution_trace={'errors': []},
            token_ref='TDCA-CRT-20260801-001',
        )
        self.assertEqual(report.root_cause, 'config')
        self.assertEqual(report.recommendation, '触发反函数重求解')

    def test_root_cause_execution(self):
        """执行错误 → 执行问题"""
        report = self.validator.validate(
            contract_id='C1',
            target_utility={'tax': 1000.0},
            actual_mou={'Actual-Total': 100.0},
            execution_trace={'errors': ['execution_failed']},
            token_ref='TDCA-CRT-20260801-001',
        )
        self.assertEqual(report.root_cause, 'execution')

    def test_nsfl_trigger_invalid_token(self):
        """无效 Token-Ref → NSFL-TRIGGER"""
        with self.assertRaises(ValueError) as ctx:
            self.validator.validate(
                contract_id='C1',
                target_utility={},
                actual_mou={},
                execution_trace={},
                token_ref='INVALID',
            )
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_validate_report(self):
        """报告自证验证通过"""
        report = self.validator.validate(
            contract_id='C1',
            target_utility={'tax': 100.0},
            actual_mou={'Actual-Total': 120.0},
            execution_trace={'errors': []},
            token_ref='TDCA-CRT-20260801-001',
        )
        self.validator.validate_report(report)

    def test_tax_anchor_verification(self):
        """税收锚定验证标记"""
        report = self.validator.validate(
            contract_id='C1',
            target_utility={'tax': 100.0},
            actual_mou={'Actual-Total': 150.0},
            execution_trace={'errors': []},
            token_ref='TDCA-CRT-20260801-001',
        )
        self.assertTrue(report.tax_anchor_verification)


if __name__ == '__main__':
    unittest.main()
