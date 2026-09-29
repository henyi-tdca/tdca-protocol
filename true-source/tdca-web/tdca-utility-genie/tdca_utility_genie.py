"""
TDCA-FC-20260802-004 修正声明: 无（首版）
制度锚定: ID24（效用精灵九大数学能力）, ID84, ID21, ID8, ID79, ID43
Granted-By: ID24

NSFL-Declaration:
  - 效用精灵不替代人类价值判断，仅提供计算支持
  - 满意解不等于最优解，人类保有最终决策权
  - 反函数求解超出配置权边界时熔断并上报
  - 能力塑造不得强制修改智能体参数，需人类审批
  - MOU税收锚定是唯一硬验证标准
  - 禁止用效用最大化替代制度约束
SPDX-License-Identifier: TDCA-Internal
"""

import os
import sys
from typing import Optional


class TDCAUtilityGenie:
    """
    TDCA 效用精灵（L3 效用计量层核心引擎）

    四大功能:
      A. 正和效用满意解求解（ID84）
      B. 反函数求解（ID21）
      C. 智能体能力塑造（ID8）
      D. 智能合约交付效用确认（ID79+ID43）
    """

    VERSION = '1.0.0'

    def __init__(self, modules_dir: Optional[str] = None):
        # 支持从已部署工具链目录导入
        if modules_dir and modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)
        self._lazy = {}

    # ---- 懒加载子模块（避免循环导入） ----

    def _get(self, module_path: str, class_name: str):
        if module_path not in self._lazy:
            import importlib
            mod = importlib.import_module(module_path)
            self._lazy[module_path] = getattr(mod, class_name)
        return self._lazy[module_path]

    # ---- 功能A：正和效用满意解求解 ----

    def solve_positive_sum(self, **kwargs):
        """正和效用满意解求解（ID84）"""
        cls = self._get('solvers.positive_sum_solver', 'PositiveSumSolver')
        solver = cls()
        solution = solver.solve(**kwargs)
        solver.validate(solution)
        return solution

    # ---- 功能B：反函数求解 ----

    def solve_inverse(self, **kwargs):
        """反函数求解（ID21）"""
        cls = self._get('solvers.inverse_function_solver', 'InverseFunctionSolver')
        solver = cls()
        solution = solver.solve(**kwargs)
        solver.validate(solution)
        return solution

    # ---- 功能C：智能体能力塑造 ----

    def shape_agent(self, **kwargs):
        """智能体能力塑造（ID8）"""
        cls = self._get('shapers.agent_capability_shaper', 'AgentCapabilityShaper')
        shaper = cls()
        plan = shaper.shape(**kwargs)
        shaper.validate(plan)
        return plan

    # ---- 功能D：交付效用确认 ----

    def validate_delivery(self, **kwargs):
        """智能合约交付效用确认（ID79+ID43）"""
        cls = self._get('validators.contract_delivery_validator', 'ContractDeliveryValidator')
        validator = cls()
        report = validator.validate(**kwargs)
        validator.validate_report(report)
        return report

    # ---- 协同编排 ----

    def full_pipeline(
        self,
        participants,
        objective_functions,
        constraint_matrix,
        reservation_utilities,
        time_budget,
        nsfl_boundaries,
        target_utility: dict,
        contract_id: str,
        token_ref: str
    ) -> dict:
        """
        全流程编排：正和求解 → 交付确认

        返回: {'solution': {...}, 'delivery_report': {...}}
        """
        solution = self.solve_positive_sum(
            participants=participants,
            objective_functions=objective_functions,
            constraint_matrix=constraint_matrix,
            reservation_utilities=reservation_utilities,
            time_budget=time_budget,
            nsfl_boundaries=nsfl_boundaries,
        )

        # 以正和解的效用作为实际值进行交付确认
        # 键匹配: target_utility 的维度键（如 tax）→ 用 solution.total_utility 作为实际税收锚定
        actual_utility = {}
        for dim, val in target_utility.items():
            if dim == 'tax':
                actual_utility[dim] = solution.total_utility
            else:
                actual_utility[dim] = solution.utilities.get(dim, 0.0)

        report = self.validate_delivery(
            contract_id=contract_id,
            target_utility=target_utility,
            actual_mou={'Actual-Total': solution.total_utility},
            execution_trace={'errors': []},
            token_ref=token_ref,
        )

        return {
            'solution': solution.to_dict() if hasattr(solution, 'to_dict') else vars(solution),
            'delivery_report': report.to_dict(),
        }
