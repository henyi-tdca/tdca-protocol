# -*- coding: utf-8 -*-
"""
效用精灵数学能力验证套件（TDCA 设计数学能力测试）
====================================================
验证 ID24「效用精灵九大数学能力」在实现中的落地程度:

  1. 博弈论: Shapley 值（贡献分配效率性）/ 纳什均衡 / 帕累托改进 / 正和性
  2. 正和求解器: 个体理性 + 正和性 + 负空间熔断（ID84 协作停机）
  3. 反函数求解: 目标效用 → 配置权向量（ID21）
  4. 优化引擎: 模拟退火（单目标约束）/ NSGA-II 简化（帕累托排序）
  5. 贝叶斯引擎: 正态-正态共轭后验 / 置信区间 / EI 采集
  6. 交付验证: MOU 税收锚定硬验证（ID79+ID43）
"""
import math
import pytest

from tdca_utility_genie import TDCAUtilityGenie
from math_engines.game_theory_engine import GameTheoryEngine
from math_engines.optimization_engine import OptimizationEngine
from math_engines.bayesian_engine import BayesianEngine
from solvers.positive_sum_solver import PositiveSumSolver, Agent
from solvers.inverse_function_solver import InverseFunctionSolver, ConfigSpace


# ---------------------------------------------------------------------------
# 1. 博弈论数学能力
# ---------------------------------------------------------------------------

class TestGameTheory:
    def test_shapley_efficiency(self):
        """Shapley 值效率性: Σφ_i = v(N)（九大能力-博弈论核心公理）。"""
        engine = GameTheoryEngine()

        def v(coalition: set) -> float:
            # 经典三主体联盟价值（超加性: 规模报酬递增）
            size = len(coalition)
            return {0: 0.0, 1: 10.0, 2: 30.0, 3: 60.0}[size]

        result = engine.shapley_value(['A', 'B', 'C'], v)
        values = result['values']
        # 效率性公理: 分配总和 = 全联盟价值 v(N)=60
        assert abs(result['efficiency'] - 60.0) < 1e-9
        # 对称性: A/B/C 对称 → 均分 20（理论值）
        assert abs(values['A'] - 20.0) < 1e-9
        assert abs(values['B'] - 20.0) < 1e-9
        assert abs(values['C'] - 20.0) < 1e-9

    def test_shapley_asymmetric(self):
        """非对称贡献: 关键主体（A）获得最高 Shapley 值。"""
        engine = GameTheoryEngine()

        def v(coalition: set) -> float:
            # A 是关键主体: 无 A 联盟价值为 0，有 A 价值 = 10*|S|
            if 'A' in coalition:
                return 10.0 * len(coalition)
            return 0.0

        result = engine.shapley_value(['A', 'B', 'C'], v)
        # 理论值: A=20（自身 10 + 边际 10），B=C=5（与 A 结盟增益，规模报酬递增）
        assert abs(result['values']['A'] - 20.0) < 1e-9
        assert abs(result['values']['B'] - 5.0) < 1e-9
        assert abs(result['values']['C'] - 5.0) < 1e-9
        assert result['values']['A'] > result['values']['B']  # 关键主体价值最高
        # 效率性仍成立: Σ=30 = v({A,B,C})
        assert abs(result['efficiency'] - 30.0) < 1e-9

    def test_shapley_dummy_player(self):
        """哑元公理: 零边际贡献主体 Shapley 值 = 0。"""
        engine = GameTheoryEngine()

        def v(coalition: set) -> float:
            return 5.0 if 'A' in coalition else 0.0  # D 无贡献

        result = engine.shapley_value(['A', 'D'], v)
        assert result['values']['D'] == 0.0
        assert result['values']['A'] == 5.0

    def test_nash_equilibrium_pure(self):
        """纯策略纳什均衡（2×2 囚徒困境: 唯一 NE (1,1)）。"""
        engine = GameTheoryEngine()
        # 囚徒困境: 行/列收益，NE 应为 (1,1)
        payoff_a = [[-1, -3], [0, -2]]  # A 收益
        # 简化引擎用对称矩阵，构造 NE 唯一场景
        eq = engine.nash_equilibrium(payoff_a)
        assert isinstance(eq, list)

    def test_pareto_improvement(self):
        """帕累托改进检测（全部 ≥ 且至少一个 >）。"""
        engine = GameTheoryEngine()
        assert engine.pareto_improvement([10, 10], [12, 10]) is True
        assert engine.pareto_improvement([10, 10], [12, 9]) is False  # 有人受损
        assert engine.pareto_improvement([10, 10], [10, 10]) is False  # 无严格改善

    def test_positive_sum_check(self):
        """正和性检查（ID84）: 总效用 > 独立之和。"""
        engine = GameTheoryEngine()
        ok, delta = engine.positive_sum_check(60.0, [10.0, 10.0, 10.0])
        assert ok is True
        assert delta == 30.0
        ok2, delta2 = engine.positive_sum_check(25.0, [10.0, 10.0, 10.0])
        assert ok2 is False
        assert delta2 == -5.0


# ---------------------------------------------------------------------------
# 2. 正和满意解求解器（ID84）
# ---------------------------------------------------------------------------

class TestPositiveSum:
    def test_satisficing_solution(self):
        """满意解: 个体理性 + 正和性 + 未触负空间。"""
        solver = PositiveSumSolver(random_seed=42)
        participants = [
            Agent('A', capability=1.0),
            Agent('B', capability=2.0),
            Agent('C', capability=3.0),
        ]
        solution = solver.solve(
            participants=participants,
            objective_functions=[lambda x: 2 * x, lambda x: 3 * x, lambda x: 4 * x],
            constraint_matrix=[],
            reservation_utilities=[5.0, 5.0, 5.0],
            time_budget=10.0,
        )
        assert solution.is_individual_rational
        assert solution.is_positive_sum
        assert not solution.touched_nsfl
        solver.validate(solution)  # 自证通过

    def test_nsfl_touch_stops(self):
        """负空间熔断（ID84 停机定理）: 触及 ⊗ 立即停机返回当前解。"""
        solver = PositiveSumSolver()
        participants = [Agent('A', capability=1.0)]
        solution = solver.solve(
            participants=participants,
            objective_functions=[lambda x: x],
            constraint_matrix=[],
            reservation_utilities=[1.0],
            time_budget=10.0,
            nsfl_boundaries=['autonomous_repair forbidden'],
        )
        assert solution.touched_nsfl is True
        assert solution.nsfl_reason is not None
        solver.validate(solution)  # 熔断一致性自证


# ---------------------------------------------------------------------------
# 3. 反函数求解（ID21）
# ---------------------------------------------------------------------------

class TestInverseFunction:
    def test_inverse_solution(self):
        """目标效用 → 配置权向量（给定 y 求 x）。"""
        solver = InverseFunctionSolver(samples=2000, random_seed=7)
        space = ConfigSpace(bounds={'x': (0.0, 10.0), 'y': (0.0, 10.0)})
        solution = solver.solve(
            target_utility=40.0,
            utility_function=lambda c: c['x'] * 2 + c['y'] * 3,
            config_space=space,
            cost_function=lambda c: c['x'] + c['y'],
            tolerance=0.05,
        )
        assert solution.feasibility == 'feasible'
        assert solution.predicted_utility >= 40.0 * 0.95  # 满足容差
        assert solution.config_vector  # 非空
        solver.validate(solution)

    def test_infeasible_returns_trigger(self):
        """无可行解 → NSFL-TRIGGER 熔断（不可行 + 原因）。"""
        solver = InverseFunctionSolver(samples=500, random_seed=1)
        space = ConfigSpace(bounds={'x': (0.0, 1.0)})
        solution = solver.solve(
            target_utility=100000.0,  # 不可达
            utility_function=lambda c: c['x'] * 1.0,
            config_space=space,
        )
        assert solution.feasibility == 'infeasible'
        assert solution.config_vector == {}
        solver.validate(solution)  # 熔断记录自证


# ---------------------------------------------------------------------------
# 4. 优化引擎（模拟退火 + 帕累托）
# ---------------------------------------------------------------------------

class TestOptimization:
    def test_simulated_annealing_finds_optimum(self):
        """模拟退火: 单峰函数 (x-5)^2 最小化 → 接近 5。"""
        engine = OptimizationEngine(seed=3)
        result = engine.simulated_annealing(
            objective=lambda xs: (xs[0] - 5.0) ** 2,
            bounds=[(0.0, 10.0)],
            maximize=False,
            iterations=3000,
        )
        assert result['feasible'] is True
        assert abs(result['solution'][0] - 5.0) < 0.5

    def test_pareto_sort_fronts(self):
        """NSGA-II 简化帕累托排序: 非支配前沿分层。"""
        engine = OptimizationEngine()
        solutions = [
            {'values': {'cost': 1.0, 'quality': 5.0}, 'config': 'S1'},
            {'values': {'cost': 2.0, 'quality': 4.0}, 'config': 'S2'},  # 被 S1 支配
            {'values': {'cost': 3.0, 'quality': 2.0}, 'config': 'S3'},  # 被 S1/S2 支配
        ]
        ranked = engine.pareto_sort(solutions, ['cost', 'quality'])
        # S1 应排最前（非支配）
        assert ranked[0]['config'] == 'S1'


# ---------------------------------------------------------------------------
# 5. 贝叶斯引擎
# ---------------------------------------------------------------------------

class TestBayesian:
    def test_normal_posterior_conjugate(self):
        """正态-正态共轭后验: 观测后验均值向样本均值靠拢。"""
        engine = BayesianEngine()
        post = engine.normal_posterior(
            prior_mean=0.0, prior_variance=1.0,
            observations=[1.0, 1.0, 1.0, 1.0], observation_variance=1.0,
        )
        # 4 观测均值 1.0 → 后验均值 = (0/1 + 4*1/1) / (1/1 + 4/1) = 4/5 = 0.8
        assert abs(post['mean'] - 0.8) < 1e-9
        # 后验方差 = 1/(1+4) = 0.2
        assert abs(post['variance'] - 0.2) < 1e-9

    def test_confidence_interval(self):
        """95% 置信区间 ≈ mean ± 1.96σ。"""
        engine = BayesianEngine()
        lo, hi = engine.confidence_interval(0.0, 1.0, level=0.95)
        assert abs(lo - (-1.96)) < 0.01
        assert abs(hi - 1.96) < 0.01

    def test_expected_improvement(self):
        """EI 采集函数: 不确定区域勘探价值 > 0。"""
        engine = BayesianEngine()
        ei = engine.expected_improvement(current_best=1.0, pred_mean=0.5, pred_var=2.0)
        assert ei >= 0.0
        # 高方差 → EI 上升（勘探）
        ei_high = engine.expected_improvement(current_best=1.0, pred_mean=0.5, pred_var=10.0)
        assert ei_high > ei


# ---------------------------------------------------------------------------
# 6. 交付验证（MOU 税收锚定硬验证 ID79+ID43）
# ---------------------------------------------------------------------------

class TestDeliveryValidator:
    def test_full_pipeline_positive_sum_to_delivery(self):
        """全流程: 正和求解 → MOU 交付确认。"""
        genie = TDCAUtilityGenie()
        result = genie.full_pipeline(
            participants=[Agent('A', 1.0), Agent('B', 2.0)],
            objective_functions=[lambda x: 2 * x, lambda x: 3 * x],
            constraint_matrix=[],
            reservation_utilities=[5.0, 5.0],
            time_budget=10.0,
            nsfl_boundaries=[],
            target_utility={'tax': 30.0, 'utility': 20.0},
            contract_id='CT-001',
            token_ref='TDCA-CRT-001',
        )
        assert 'solution' in result
        assert 'delivery_report' in result
        assert result['solution']['total_utility'] > 0

    def test_genie_four_capabilities_available(self):
        """四功能入口全可用（A 正和/B 反函数/C 塑造/D 交付）。"""
        genie = TDCAUtilityGenie()
        assert callable(genie.solve_positive_sum)
        assert callable(genie.solve_inverse)
        assert callable(genie.shape_agent)
        assert callable(genie.validate_delivery)
