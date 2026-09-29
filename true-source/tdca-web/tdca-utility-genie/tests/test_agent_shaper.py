"""TDCA-FC-20260802-004 子模块C 测试 — AgentCapabilityShaper
Granted-By: ID8
NSFL-Declaration: 测试验证能力塑造/人类审批/预算约束
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shapers.agent_capability_shaper import (
    AgentCapabilityShaper, PerformanceGap, TrainingBudget,
)


class TestAgentCapabilityShaper(unittest.TestCase):
    def setUp(self):
        self.shaper = AgentCapabilityShaper()

    def test_shape_with_approval(self):
        """人类审批后生成塑造方案"""
        plan = self.shaper.shape(
            agent_id='agent-1',
            current_state={'A': 0.8, 'D': 0.7, 'L': 0.6, 'C': 0.3, 'SC': 0.9},
            utility_history=[],
            performance_gap=PerformanceGap('C', 0.7),
            training_budget=TrainingBudget(10.0),
            human_approved=True,
        )
        self.assertEqual(plan.dimension_focus, 'C')
        self.assertIn('C', plan.dimension_focus)
        self.assertTrue(0 <= plan.expected_improvement <= 1)

    def test_nsfl_trigger_no_approval(self):
        """无人类审批 → PermissionError"""
        with self.assertRaises(PermissionError) as ctx:
            self.shaper.shape(
                agent_id='agent-1',
                current_state={},
                utility_history=[],
                performance_gap=PerformanceGap('A', 0.5),
                training_budget=TrainingBudget(10.0),
                human_approved=False,
            )
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_nsfl_trigger_zero_budget(self):
        """预算为0 → ValueError"""
        with self.assertRaises(ValueError) as ctx:
            self.shaper.shape(
                agent_id='agent-1',
                current_state={},
                utility_history=[],
                performance_gap=PerformanceGap('A', 0.5),
                training_budget=TrainingBudget(0.0),
                human_approved=True,
            )
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_validate_pass(self):
        """有效方案通过验证"""
        plan = self.shaper.shape(
            agent_id='agent-1',
            current_state={'A': 0.5, 'D': 0.5, 'L': 0.5, 'C': 0.5, 'SC': 0.5},
            utility_history=[],
            performance_gap=PerformanceGap('SC', 0.6),
            training_budget=TrainingBudget(10.0),
            human_approved=True,
        )
        self.shaper.validate(plan)

    def test_dimension_priority(self):
        """预算优先级覆盖最弱维度"""
        plan = self.shaper.shape(
            agent_id='agent-1',
            current_state={'A': 0.9, 'D': 0.9, 'L': 0.9, 'C': 0.9, 'SC': 0.9},
            utility_history=[],
            performance_gap=PerformanceGap('C', 0.3),  # 弱差距
            training_budget=TrainingBudget(10.0, priority_dimensions=['A']),
            human_approved=True,
        )
        self.assertEqual(plan.dimension_focus, 'A')


if __name__ == '__main__':
    unittest.main()
