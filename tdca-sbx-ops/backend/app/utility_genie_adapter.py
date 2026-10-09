# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F6 正和博弈实时验证适配层——效用精灵只读对接
# 约束矩阵:     任务书 SV-1~7 + KB-ECON-001 §3（S_synergy>0）+ 开发纪律（正和不可 mock）
# 先验分布:     任务书 §二 F6 + §6.3 + KB-ECON-001 §3/§9 + tdca-utility-genie
# 配置权边界:    L2 层；效用精灵只读引用（不写入外部工程）
# 预期分配:     正和求解/正和校验/交付确认；失败=效用精灵不可用（不可 mock）
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F6 正和博弈实时验证适配层（效用精灵只读对接）。

制度锚定: 任务书 §二 F6 + §6.3 + KB-ECON-001 §3 | SPDX-License-Identifier: TDCA-Internal

正和公式（KB-ECON-001 §3）:
  S_synergy = U_actual − ΣU_individual > 0
  PositiveSumIndex = Σ(协作产出) / Σ(独立产出) > 1.0

效用精灵只读引用（开发纪律）: 正和判定必须走效用精灵计算，不可硬编码通过；
效用精灵不可用时显式报错（RuntimeError），不提供 mock 降级。

路径划分:
  - positive_sum_check: KB-ECON-001 §3 公式直接实现（确定性快路径，S_synergy>0 校验）
  - solve_positive_sum / delivery_confirm: 效用精灵完整求解/确认路径（真实引擎）
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 效用精灵工程目录（只读引用）：<workspace>/tdca-utility-genie
GENIE_DIR = Path(__file__).resolve().parents[3] / "tdca-utility-genie"


def _load_genie() -> Any:
    """加载效用精灵（只读引用；不可用时显式失败，不 mock）。

    六要素声明:
    目标函数: 加载 TDCAUtilityGenie（F6 正和验证引擎）
    约束矩阵: 输入——无；输出——genie 实例；禁止——模块缺失降级模拟
    先验分布: tdca-utility-genie 工程
    配置权边界: L2；只读
    预期分配: 返回 genie；失败=RuntimeError（效用精灵不可用，正和验证不可 mock）
    审计轨迹: 无（加载动作）
    """
    if not GENIE_DIR.exists():
        raise RuntimeError(f"效用精灵工程不存在: {GENIE_DIR}（F6 正和验证不可 mock，须真实引擎）")
    if str(GENIE_DIR) not in sys.path:
        sys.path.insert(0, str(GENIE_DIR))
    try:
        from tdca_utility_genie import TDCAUtilityGenie

        return TDCAUtilityGenie()
    except ImportError as e:
        raise RuntimeError(f"效用精灵加载失败（F6 不可 mock）: {e}") from e


def positive_sum_check(
    coalition_utility: float,
    independent_utilities: List[float],
) -> Dict[str, Any]:
    """正和性校验（KB-ECON-001 §3：S_synergy > 0）——公式快路径（确定性校验）。

    注: 本函数为 KB-ECON-001 §3 公式直接实现（快路径）；完整正和求解走
    solve_positive_sum（效用精灵 PositiveSumSolver，含负空间熔断/个体理性/NCA 轨迹）。

    六要素声明:
    目标函数: 正和判定（F6）——S_synergy = U_actual − ΣU_individual > 0
    约束矩阵: 输入——coalition_utility、independent_utilities（非空）；输出——判定结果；
              禁止——非正和判通过（→ FUSE 熔断标记）
    先验分布: KB-ECON-001 §3（正和博弈经济模型）
    配置权边界: L2；纯计算
    预期分配: 返回 {is_positive_sum, delta, index, fuse}；失败=ValueError
    审计轨迹: 判定结果随沙盒操作 NCA 存证
    """
    if not independent_utilities or any(u < 0 for u in independent_utilities):
        raise ValueError("independent_utilities 非空且 ≥ 0")
    indep_sum = sum(independent_utilities)
    delta = coalition_utility - indep_sum
    index = coalition_utility / indep_sum if indep_sum > 0 else 0.0
    is_positive = delta > 0
    return {
        "is_positive_sum": is_positive,
        "coalition_utility": coalition_utility,
        "independent_sum": round(indep_sum, 6),
        "delta": round(delta, 6),  # S_synergy
        "positive_sum_index": round(index, 6),
        "fuse": not is_positive,  # 非正和 → 负空间熔断标记（SV-3 方向）
    }


def solve_positive_sum(
    participants: List[Dict[str, Any]],
    objective_functions: List[Callable],
    reservation_utilities: List[float],
    nsfl_boundaries: Optional[List[str]] = None,
    time_budget: float = 10.0,
) -> Dict[str, Any]:
    """正和效用满意解求解（F6，效用精灵 PositiveSumSolver 只读对接）。

    六要素声明:
    目标函数: 正和求解（F6）——效用精灵 solve_positive_sum（ID84）
    约束矩阵: 输入——participants（{agent_id, capability}）、objective_functions、reservation_utilities、
              nsfl_boundaries；输出——解 + 正和判定；禁止——效用精灵缺失降级、非正和解放行
    先验分布: 任务书 §6.3 + tdca-utility-genie solvers/positive_sum_solver.py
    配置权边界: L2；效用精灵只读
    预期分配: 返回 {solution, is_positive_sum, delta, fuse}；失败=RuntimeError/ValueError
    审计轨迹: 解 + nca_trace 随 NCA 存证
    """
    genie = _load_genie()
    from solvers.positive_sum_solver import Agent  # noqa: E402（效用精灵工程）

    agents = [Agent(agent_id=p["agent_id"], capability=p.get("capability", 1.0)) for p in participants]
    solution = genie.solve_positive_sum(
        participants=agents,
        objective_functions=objective_functions,
        constraint_matrix=[],
        reservation_utilities=reservation_utilities,
        time_budget=time_budget,
        nsfl_boundaries=nsfl_boundaries or [],
    )
    d = solution.to_dict() if hasattr(solution, "to_dict") else vars(solution)
    return {
        "solution": d,
        "is_positive_sum": d.get("is_positive_sum"),
        "delta": d.get("delta"),
        "total_utility": d.get("total_utility"),
        "independent_sum": d.get("independent_sum"),
        "fuse": not d.get("is_positive_sum", False) or d.get("touched_nsfl", False),
    }


def delivery_confirm(
    contract_id: str,
    target_utility: Dict[str, float],
    actual_mou: Dict[str, float],
    token_ref: str,
) -> Dict[str, Any]:
    """出盒正和交付确认（F6，效用精灵 ContractDeliveryValidator 只读对接）。

    六要素声明:
    目标函数: 正和交付确认（F6/任务书 §6.3）——MOU 税收锚定硬验证（ID79+ID43）
    约束矩阵: 输入——contract_id/target_utility/actual_mou/token_ref；输出——交付报告；
              禁止——效用精灵缺失降级
    先验分布: 任务书 §6.3 + tdca-utility-genie validators/contract_delivery_validator.py
    配置权边界: L2；效用精灵只读
    预期分配: 返回交付确认报告；失败=RuntimeError
    审计轨迹: 确认报告随出盒 NCA 存证
    """
    genie = _load_genie()
    report = genie.validate_delivery(
        contract_id=contract_id,
        target_utility=target_utility,
        actual_mou=actual_mou,
        execution_trace={"errors": []},
        token_ref=token_ref,
    )
    return report.to_dict() if hasattr(report, "to_dict") else vars(report)
