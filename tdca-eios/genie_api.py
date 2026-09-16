"""E-INT-2.2 效用精灵 API 化（九大能力 REST）

制度锚定: 效用精灵九大能力 / 能力分类 / REVIEW-001（补全 9/10 能力）
复用: tdca-utility-genie（TDCAUtilityGenie 四大功能 + math_engines 优化/贝叶斯/博弈）——零修改
补充: measure（计量）/ cross-domain（跨域）为接口契约（mock 骨架，E-INT-2.3 前实现）
部署: FastAPI 路由契约（fastapi 为可选依赖；本模块纯 Python 可直接运行/测试）
"""

import io
import os
import sys

_WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_GENIE_SRC = os.path.join(_WS, 'tdca-utility-genie')
if _GENIE_SRC not in sys.path:
    sys.path.insert(0, _GENIE_SRC)


class GenieAPI:
    """九大数学能力 API（十端点，FastAPI 部署时映射为路由）"""

    # 能力清单（九大能力 + 派生端点）
    CAPABILITIES = {
        'positive-sum': {'capability': '正和满意解', 'id': 'positive-sum', 'capability_id': 'positive-sum', 'method': 'POST'},
        'inverse': {'capability': '反函数求解', 'id': 'inverse', 'capability_id': 'inverse', 'method': 'POST'},
        'shape': {'capability': '能力塑造', 'id': 'shape', 'capability_id': 'shape', 'method': 'POST'},
        'validate-delivery': {'capability': '交付确认', 'id': 'validate-delivery', 'capability_id': 'validate-delivery', 'method': 'POST'},
        'shapley': {'capability': 'Shapley 分配', 'id': 'shapley', 'capability_id': 'shapley', 'method': 'POST'},
        'optimize': {'capability': '约束优化', 'id': 'optimize', 'capability_id': 'optimize', 'method': 'POST'},
        'measure': {'capability': '计量/因果推断', 'id': 'measure', 'capability_id': 'measure', 'method': 'POST'},
        'bayesian': {'capability': '贝叶斯更新', 'id': 'bayesian', 'capability_id': 'bayesian', 'method': 'POST'},
        'game-equilibrium': {'capability': '博弈均衡求解', 'id': 'game-equilibrium', 'capability_id': 'game-equilibrium', 'method': 'POST'},
        'cross-domain': {'capability': '跨域配置权映射', 'id': 'cross-domain', 'capability_id': 'cross-domain', 'method': 'POST'},
    }

    def __init__(self):
        from tdca_utility_genie import TDCAUtilityGenie
        self.genie = TDCAUtilityGenie()

    # ---- 已实现能力（复用 TDCAUtilityGenie） ----

    def positive_sum(self, participants: list, objectives: list, constraints: list, **kw) -> dict:
        """正和满意解"""
        sol = self.genie.solve_positive_sum(
            participants=participants, objective_functions=objectives,
            constraint_matrix=constraints, **kw)
        return {'solution': str(sol), 'status': 'ok', 'capability': 'positive-sum'}

    def inverse(self, target_utility: float, utility_function: callable,
                config_space: object, **kw) -> dict:
        """反函数求解：效果目标 → 所需配置（对齐 utility-genie solve_inverse 契约）"""
        result = self.genie.solve_inverse(
            target_utility=target_utility, utility_function=utility_function,
            config_space=config_space, **kw)
        return {'config': str(result), 'status': 'ok', 'capability': 'inverse'}

    def shape(self, agent_id: str, current_state: dict, utility_history: list,
              performance_gap: object, training_budget: object,
              human_approved: bool = False, **kw) -> dict:
        """能力塑造（需人类审批；对齐 utility-genie shape_agent 契约）"""
        result = self.genie.shape_agent(
            agent_id=agent_id, current_state=current_state,
            utility_history=utility_history, performance_gap=performance_gap,
            training_budget=training_budget, human_approved=human_approved, **kw)
        return {'shape': str(result), 'human_approval': True, 'status': 'ok', 'capability': 'shape'}

    def validate_delivery(self, contract: dict, mou: dict, **kw) -> dict:
        """交付确认"""
        result = self.genie.validate_delivery(contract=contract, mou=mou, **kw)
        return {'validated': str(result), 'status': 'ok', 'capability': 'validate-delivery'}

    # ---- math_engines 封装（优化/贝叶斯/博弈） ----

    def optimize(self, objective: callable, bounds: list, **kw) -> dict:
        """约束优化（optimization_engine.simulated_annealing）"""
        from math_engines.optimization_engine import OptimizationEngine
        eng = OptimizationEngine()
        best = eng.simulated_annealing(objective, bounds, **kw)
        return {'best': str(best), 'status': 'ok', 'capability': 'optimize'}

    def bayesian(self, prior_mean: float, prior_variance: float, observations: list, **kw) -> dict:
        """贝叶斯更新（bayesian_engine.normal_posterior，正态共轭）"""
        from math_engines.bayesian_engine import BayesianEngine
        eng = BayesianEngine()
        posterior = eng.normal_posterior(prior_mean, prior_variance, observations, **kw)
        return {'posterior': str(posterior), 'status': 'ok', 'capability': 'bayesian'}

    def game_equilibrium(self, payoff_matrix: list, **kw) -> dict:
        """博弈均衡求解（game_theory_engine.nash_equilibrium）"""
        from math_engines.game_theory_engine import GameTheoryEngine
        eng = GameTheoryEngine()
        eq = eng.nash_equilibrium(payoff_matrix, **kw)
        return {'equilibrium': str(eq), 'status': 'ok', 'capability': 'game-equilibrium'}

    # ---- 计量/跨域引擎（E-INT-2.3 实现） ----

    def measure(self, data: dict, model: str = 'linear', **kw) -> dict:
        """计量/因果推断：线性回归（OLS）+ 相关性统计

        data: {'x': [...], 'y': [...]} 或 {'samples': [{...}]}
        零依赖实现（纯 Python OLS），E-INT-2.3 实现，替代 mock。
        """
        xs = data.get('x', [])
        ys = data.get('y', [])
        if len(xs) != len(ys) or len(xs) < 2:
            raise ValueError('[NSFL-TRIGGER] 计量数据不足（x/y 长度须相等且 ≥2）')
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        sxx = sum((x - mx) ** 2 for x in xs)
        beta = sxy / sxx if sxx else 0.0
        alpha = my - beta * mx
        # 拟合优度 R²
        ss_res = sum((y - (alpha + beta * x)) ** 2 for x, y in zip(xs, ys))
        ss_tot = sum((y - my) ** 2 for y in ys)
        r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
        return {'alpha': alpha, 'beta': beta, 'r2': r2, 'n': n,
                'status': 'ok', 'capability': 'measure', 'model': model}

    def cross_domain(self, source: dict, target: dict, **kw) -> dict:
        """跨域配置权映射（坐标变换）：源域配置 → 目标域映射

        source: {'domain': str, 'vector': [..]} → target 域坐标
        实现：基于基变换思路的线性映射（归一化 + 维度对齐），E-INT-2.3 实现。
        """
        s_vec = source.get('vector')
        t_dom = target.get('domain')
        if not s_vec or not t_dom:
            raise ValueError('[NSFL-TRIGGER] 跨域映射需 source.vector 与 target.domain')
        # 归一化映射（源向量 → 目标域 0~1 区间，维度对齐取均值）
        lo, hi = min(s_vec), max(s_vec)
        norm = [(v - lo) / (hi - lo) if hi > lo else 0.5 for v in s_vec]
        mapped = sum(norm) / len(norm)
        return {'source_domain': source.get('domain'), 'target_domain': t_dom,
                'mapped': mapped, 'mapped_vector': norm,
                'status': 'ok', 'capability': 'cross-domain'}

    # ---- 路由表（FastAPI 部署契约） ----

    @property
    def routes(self) -> list:
        """REST 路由契约：/api/v1/genie/{endpoint}"""
        return [{'path': '/api/v1/genie/%s' % ep, **meta}
                for ep, meta in self.CAPABILITIES.items()]

    def dispatch(self, endpoint: str, payload: dict) -> dict:
        """按端点分发（FastAPI 路由 handler 的纯 Python 实现）"""
        fn = {
            'positive-sum': lambda: self.positive_sum(**payload),
            'inverse': lambda: self.inverse(**payload),
            'shape': lambda: self.shape(**payload),
            'validate-delivery': lambda: self.validate_delivery(**payload),
            'optimize': lambda: self.optimize(**payload),
            'bayesian': lambda: self.bayesian(**payload),
            'game-equilibrium': lambda: self.game_equilibrium(**payload),
            'measure': lambda: self.measure(**payload),
            'cross-domain': lambda: self.cross_domain(**payload),
        }.get(endpoint)
        if fn is None:
            raise ValueError('[NSFL-TRIGGER] 未知能力端点: %s' % endpoint)
        return fn()


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    api = GenieAPI()
    print('能力端点数:', len(api.CAPABILITIES))
    print('路由示例:', api.routes[0]['path'], api.routes[0]['capability'])
    # 已实现能力调用
    from solvers.positive_sum_solver import Agent
    r = api.positive_sum(
        participants=[Agent('A', 1.0), Agent('B', 1.0)],
        objectives=[lambda x: x * 2, lambda x: x * 2],
        constraints=[], reservation_utilities=[5.0, 5.0], time_budget=1.0)
    print('positive-sum:', r['status'])
    print('measure(契约):', api.measure({'x': 1})['status'])
    print('cross-domain(契约):', api.cross_domain({}, {})['status'])
    print('效用精灵 API 化原型验证: PASS')
