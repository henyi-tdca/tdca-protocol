"""TDCA-FC-20260802-004 模块A 单元测试 — TDCAFunctionCompiler
Granted-By: TDCA-PRINCIPLE-FC-NCA-COH-002
NSFL-Declaration: 测试验证编译与IR验证逻辑，不产生真实解释上链
"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tdca_function_compiler import (
    TDCAFunctionCompiler,
    IntermediateRepresentation,
    CompileStatus,
)


class TestFunctionCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = TDCAFunctionCompiler()

    def test_compile_full(self):
        """完整六要素编译"""
        elements = {
            'objective': {'type': 'NUMERIC', 'expression': 'maximize(utility)'},
            'constraints': {
                'hard': ['正和约束', '版权确权'],
                'soft': ['建议风格'],
                'operation': 'normal_call',
                'context': {'eri_positive': True, 'copyright_registered': True},
            },
            'prior': {'distribution': 'normal', 'mean': 10.0, 'variance': 2.0},
        }
        ir = self.compiler.compile(elements)
        self.assertIsNotNone(ir.target_function_formalized)
        self.assertIsNotNone(ir.constraints_sat)
        self.assertTrue(ir.prior_distribution_params['parameterized'])

    def test_verify_ir_valid(self):
        """有效 IR 通过验证"""
        elements = {
            'objective': {'type': 'NUMERIC', 'expression': 'maximize(utility)'},
            'constraints': {
                'hard': ['正和约束'],
                'operation': 'normal_call',
                'context': {'eri_positive': True},
            },
            'prior': {'mean': 10.0},
        }
        ir = self.compiler.compile(elements)
        self.assertTrue(self.compiler.verify_ir(ir))

    def test_prior_parameterized(self):
        """先验参数化：均值/方差"""
        ir = self.compiler.compile({
            'objective': {'expression': 'maximize(x)'},
            'constraints': {'hard': ['正和约束'], 'context': {'eri_positive': True}},
            'prior': {'mean': 5.0, 'variance': 1.0},
        })
        params = ir.prior_distribution_params
        self.assertEqual(params['parameters']['mean'], 5.0)
        self.assertEqual(params['parameters']['variance'], 1.0)
        self.assertTrue(params['parameterized'])

    def test_ir_contains_core_fields(self):
        """IR 包含三核心字段（硬约束）"""
        ir = self.compiler.compile({})
        d = ir.to_dict()
        self.assertIn('target_function_formalized', d)
        self.assertIn('constraints_sat', d)
        self.assertIn('prior_distribution_params', d)

    def test_unknown_constraint_human(self):
        """无法识别的约束 → interpret 返回 HUMAN_REQUIRED（非布尔化）"""
        ir = self.compiler.compile({
            'objective': {'expression': 'maximize(x)'},
            'constraints': {'hard': ['完全不存在的约束XYZ'], 'context': {}},
        })
        self.assertFalse(ir.constraints_sat['booleanized'])


if __name__ == '__main__':
    unittest.main()
