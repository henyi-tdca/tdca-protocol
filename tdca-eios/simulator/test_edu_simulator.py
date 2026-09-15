# -*- coding: utf-8 -*-
"""E-EDU-4.1 模拟器引擎单元测试（制度约束验证）"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edu_simulator import (
    StudentProfile, StudentTier, UnlockEngine, NSFLGuard, TrainingOrchestrator,
)


class TestUnlockEngine(unittest.TestCase):
    """四级解锁判定"""

    def test_01_cognitive_default(self):
        """认知版默认可达"""
        eng = UnlockEngine()
        self.assertTrue(eng.can_access(StudentTier.COGNITIVE, StudentProfile('S1')))
        self.assertEqual(eng.unlock(StudentProfile('S1')), StudentTier.COGNITIVE)

    def test_02_basic_requires_quiz(self):
        """基础版需测验通过"""
        eng = UnlockEngine()
        p = StudentProfile('S1')
        self.assertFalse(eng.can_access(StudentTier.BASIC, p))
        eng.pass_quiz(p)
        self.assertTrue(eng.can_access(StudentTier.BASIC, p))
        self.assertEqual(eng.unlock(p), StudentTier.BASIC)

    def test_03_advanced_requires_3_cases(self):
        """进阶版需 3 基础案例"""
        eng = UnlockEngine()
        p = StudentProfile('S1')
        eng.pass_quiz(p)
        for _ in range(2):
            eng.complete_basic_case(p)
        self.assertFalse(eng.can_access(StudentTier.ADVANCED, p))
        eng.complete_basic_case(p)
        self.assertTrue(eng.can_access(StudentTier.ADVANCED, p))

    def test_04_expert_requires_5_cases_exam(self):
        """专家版需 5 进阶案例 + 考试"""
        eng = UnlockEngine()
        p = StudentProfile('S1')
        eng.pass_quiz(p)
        for _ in range(3):
            eng.complete_basic_case(p)
        for _ in range(4):
            eng.complete_advanced_case(p)
        self.assertFalse(eng.can_access(StudentTier.EXPERT, p))
        eng.complete_advanced_case(p)
        self.assertFalse(eng.can_access(StudentTier.EXPERT, p))  # 缺考试
        eng.pass_exam(p)
        self.assertTrue(eng.can_access(StudentTier.EXPERT, p))

    def test_05_unlock_writes_nca(self):
        """解锁写入学生档案 NCA（制度性确认）"""
        eng = UnlockEngine()
        p = StudentProfile('S1')
        nca = eng.pass_quiz(p)
        self.assertTrue(nca.startswith('NCA-STU-'))
        self.assertEqual(len(p.nca_records), 1)


class TestNSFLGuard(unittest.TestCase):
    """NSFL 关键词锁定（可见不可改）"""

    def test_06_locked_keyword_blocked(self):
        """锁定关键词不可修改（NSFL 保护）"""
        guard = NSFLGuard()
        with self.assertRaises(ValueError) as ctx:
            guard.check(['诈骗类调用'])
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_07_benign_constraints_ok(self):
        """正常约束可声明"""
        guard = NSFLGuard()
        result = guard.check(['拒绝营销', '仅教育场景'])
        self.assertEqual(len(result), 2)


class TestTrainingOrchestrator(unittest.TestCase):
    """四个实训流程"""

    def setUp(self):
        self.eng = UnlockEngine()
        self.orch = TrainingOrchestrator()
        self.stu = StudentProfile('S-TEST')

    def _to_advanced(self):
        self.eng.pass_quiz(self.stu)
        for _ in range(3):
            self.eng.complete_basic_case(self.stu)

    def _to_expert(self):
        self._to_advanced()
        for _ in range(5):
            self.eng.complete_advanced_case(self.stu)
        self.eng.pass_exam(self.stu)

    def test_08_scenario1_cognitive_blocked(self):
        """认知版不可操作实训一（需测验解锁）"""
        with self.assertRaises(PermissionError):
            self.orch.scenario1_create_agent(
                StudentProfile('S-X'), {'config_boundary': 'x', 'constraints': []})

    def test_09_scenario1_basic_ok(self):
        """基础版实训一通过（NSFL 检查 + NCA）"""
        self.eng.pass_quiz(self.stu)
        nca = self.orch.scenario1_create_agent(
            self.stu, {'config_boundary': '仅教育场景', 'constraints': ['拒绝营销']})
        self.assertTrue(nca.startswith('NCA-STU-'))

    def test_10_scenario2_nine_phase(self):
        """实训二 9 Phase 全流程（不可跳过）→ COMPLETED"""
        self._to_advanced()
        phases = self.orch.scenario2_nine_phase(self.stu)
        self.assertEqual(phases[-1], 'COMPLETED')
        self.assertEqual(len(phases), 10)  # P0~P8 + COMPLETED

    def test_11_scenario3_mou_calculation(self):
        """实训三 MOU 计算与生产一致（进项 6% + 出项 10%）"""
        self._to_advanced()
        result = self.orch.scenario3_nca_mou(self.stu, 100, 50)
        self.assertEqual(result['mou'], 11.0)  # 100*0.06 + 50*0.10

    def test_12_scenario3_mou_zero_blocked(self):
        """MOU ≤ 0 触发 NSFL（不可虚构）"""
        self._to_advanced()
        with self.assertRaises(ValueError) as ctx:
            self.orch.scenario3_nca_mou(self.stu, 0, 0)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_13_scenario4_expert_required(self):
        """实训四需专家版（未达条件被阻断）"""
        self._to_advanced()
        with self.assertRaises(PermissionError):
            self.orch.scenario4_multi_agent(self.stu)

    def test_14_scenario4_multi_agent(self):
        """实训四多智能体（CKS 宪法收敛 R2/R4 + 基变换可逆）"""
        self._to_expert()
        result = self.orch.scenario4_multi_agent(self.stu)
        # R2 人类签名权胜出
        self.assertEqual(result['cks_result']['resolved']['M1'], 'R2 人类签名权（远端）')
        # R4 平局上报慢系统
        self.assertIn('M2', result['r4']['escalated'])
        # 基变换可逆
        self.assertTrue(result['basis_reversible'])


if __name__ == '__main__':
    unittest.main()
