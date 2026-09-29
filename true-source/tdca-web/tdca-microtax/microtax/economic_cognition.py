# -*- coding: utf-8 -*-
"""C-3 完整经济认知引擎（EconomicCognitionEngine）——多主体认知 × 效用精灵 × 税收计算。

TDCA-TASK-COGNITION-001（V1.0-FROZEN，DCD-COGNITION-001，裁决① microtax 扩展）：
用户洞见——「多主体认知，效用精灵加上税收计算 才能让智能体对经济事实产生的正和效用有完整的认知」。

闭环:
```
多主体交付（participants + 五维认知状态 S_i）
  → C-1 多主体认知: CognitiveDistanceCalculator（距离矩阵 + 对齐难度 + 协商触发 0.35）
  → 税收计算: TaxOfficerAgent.on_delivery（计税 → 预缴 → 税后净额 + 法规约束 fail-closed）
  → C-2 效用精灵: PositiveSumSolver.solve(resource_pool=税后净额) 正和求解
  → C-4 融合验证: U_正和（TREATISE-026 三条件：ΔMOU>0 ∧ min(S_协作)≥θ ∧ 生态溢出）
  → 完整经济认知报告（认知 + 税收 + 正和 + 判定 + 法规轨迹 + NCA）
```

制度锚定: TREATISE-026（U_正和 三条件合取，R5=B 人类裁决）+ T-007（θ=0.70 已登记）
         + SWU=MOU×SC（认知×税收融合）+ 四符号体系（T-001：S_协作）
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import MicroDelivery, TaxEventType
from .tax_officer import TaxOfficerAgent
from .subject_eco_weight import SubjectEcoWeightEngine

# 多主体认知距离（tdca-toolchain；运行时自举，fail-closed）
try:
    from tdca_cognitive_distance import CognitiveDistanceCalculator  # type: ignore
except ImportError:  # pragma: no cover - 运行时自举
    import sys as _sys
    from pathlib import Path as _Path
    _toolchain = _Path(__file__).resolve().parent.parent.parent / "tdca-toolchain"
    if not _toolchain.exists():
        raise RuntimeError(
            "[NSFL-TRIGGER] 多主体认知基座缺失（tdca-toolchain）——完整经济认知须 fail-closed")
    _sys.path.insert(0, str(_toolchain))
    from tdca_cognitive_distance import CognitiveDistanceCalculator  # noqa: E402

# 效用精灵（tdca-utility-genie；C-2 resource_pool 注入）
try:
    from solvers.positive_sum_solver import Agent, PositiveSumSolver  # type: ignore
except ImportError:  # pragma: no cover - 运行时自举
    import sys as _sys2
    from pathlib import Path as _Path2
    _genie = _Path2(__file__).resolve().parent.parent.parent / "tdca-utility-genie"
    if not _genie.exists():
        raise RuntimeError(
            "[NSFL-TRIGGER] 效用精灵基座缺失（tdca-utility-genie）——完整经济认知须 fail-closed")
    _sys2.path.insert(0, str(_genie))
    from solvers.positive_sum_solver import Agent, PositiveSumSolver  # noqa: E402

# TREATISE-026 参数（T-007 已登记，不得改值）
POSITIVE_SUM_THETA = 0.70          # 认知状态下限 θ
POSITIVE_SUM_PHI = 0.30            # 生态溢出比例 ϕ（演示参数，场景自适应待标定）


@dataclass
class EconomicCognitionReport:
    """完整经济认知报告（认知 + 税收 + 正和 + 判定 + 主体生态）。"""
    delivery_id: str
    cognition: dict                 # 认知距离矩阵/对齐难度/协商触发
    taxation: dict                  # 计税/预缴/税后净额/法规轨迹
    positive_sum: dict              # 效用精灵正和求解（分配/总效用/增量）
    verdict: dict                   # U_正和 三条件判定（ΔMOU/min(S_协作)/生态溢出）
    subject_econ: dict              # ECOWEIGHT-001: 主体生态权重 + 零和负和熔断（E-4）
    full_cognition: bool            # 完整经济认知达成
    simulated: bool = True          # ID92 模拟态标注

    def to_dict(self) -> dict:
        return {
            "delivery_id": self.delivery_id,
            "cognition": self.cognition,
            "taxation": self.taxation,
            "positive_sum": self.positive_sum,
            "verdict": self.verdict,
            "subject_econ": self.subject_econ,
            "full_cognition": self.full_cognition,
            "simulated": self.simulated,
        }


class EconomicCognitionEngine:
    """C-3 完整经济认知引擎（tdca-microtax 扩展，裁决①）。"""

    def __init__(self, tax_officer: Optional[TaxOfficerAgent] = None,
                 cognitive: Optional[CognitiveDistanceCalculator] = None,
                 solver: Optional[PositiveSumSolver] = None,
                 eco_weight: Optional[SubjectEcoWeightEngine] = None):
        self._officer = tax_officer or TaxOfficerAgent()
        self._cognitive = cognitive or CognitiveDistanceCalculator()
        self._solver = solver or PositiveSumSolver()
        self._eco = eco_weight or SubjectEcoWeightEngine()

    def cognize(self, delivery: MicroDelivery,
                cognitive_states: Dict[str, Dict[str, float]],
                synergy: float = 1.2,
                eco_spillover: float = 0.0,
                subject_eco: Optional[Dict[str, Dict[str, float]]] = None) -> EconomicCognitionReport:
        """完整经济认知（四段闭环 + 主体生态段）。

        :param delivery: 微交付实体（须含 participants 贡献）
        :param cognitive_states: 多主体五维认知状态 {agent_id: {A,D,L,C,SC}}
        :param synergy: 正和价值函数协同（对齐 MOUSplitContract 默认 1.2）
        :param eco_spillover: 生态溢出值（生态溢出/核心MOU 比例，C-4 验证输入）
        :param subject_eco: 主体级买卖数据 {agent_id: {buy, sell}}——ECOWEIGHT-001 E-4
        """
        # ===== 段 1: 多主体认知（C-1）=====
        event_id = f"COG-{delivery.delivery_id}"
        align = self._cognitive.evaluate_event(event_id, cognitive_states)
        # 认知状态矩阵 → 各主体认知势（min(S_协作) 判定输入）
        levels = {s: self._cognitive._cognitive_level(st) for s, st in cognitive_states.items()}
        min_cognitive = min(levels.values()) if levels else 0.0
        negotiation = any(
            self._cognitive.negotiation_required(cognitive_states[a], cognitive_states[b])
            for i, a in enumerate(cognitive_states)
            for b in list(cognitive_states)[i + 1:])

        cognition_block = {
            "event": event_id,
            "subject_count": len(cognitive_states),
            "distance_matrix": align.distance_matrix,
            "asymmetric_pairs": align.asymmetric_pairs,
            "asymmetry_ratio": align.asymmetry_ratio,
            "min_cognitive_level": round(min_cognitive, 4),
            "negotiation_required": negotiation,
        }

        # ===== 段 2: 税收计算（税务官）=====
        tax_result = self._officer.on_delivery(delivery)   # 计税→预缴→账本→NCA（法规 fail-closed）
        net_value = delivery.net_value
        tax_total = delivery.tax_total

        taxation_block = {
            "taxes": tax_result["taxes"],
            "tax_total": tax_total,            # 计税金额 T(y_t)
            "mou_value": float(delivery.mou_value),   # 场景总效用 = 进项+出项（正和判定依据）
            "net_value": net_value,            # 税后净额（分配语义，非正和度量）
            "prepay": tax_result["prepay"],
            "regulatory": tax_result["regulatory"],
            "nca": tax_result["nca"],
        }

        # ===== 段 3: 效用精灵正和求解（C-2，场景总效用资源池）=====
        # 本体论（用户纠偏 2026-08-12 + 权威 MOU=进项+出项，TERMS-001:147）:
        # 正和效用不是税后净额（买卖剩余），而是 MOU（进项+出项税收总额）=
        # 场景总效用正和——resource_pool 注入 MOU。
        participants = list(delivery.participants or {})
        if not participants:
            raise ValueError("[NSFL-TRIGGER] 无参与方贡献——完整经济认知须多主体输入")
        agents = [Agent(agent_id=p, capability=1.0) for p in participants]
        objective_fns = [lambda x: x] * len(agents)
        reservations = [0.0] * len(agents)     # 保留效用（模拟；个体理性基准）
        mou_pool = float(delivery.mou_value)   # 场景总效用 = MOU（进项+出项）
        solution = self._solver.solve(
            participants=agents,
            objective_functions=objective_fns,
            constraint_matrix=[],
            reservation_utilities=reservations,
            time_budget=5.0,
            resource_pool=mou_pool,            # C-2: MOU 场景总效用资源池
        )

        positive_sum_block = {
            "pool_semantics": "mou",          # 场景总效用正和（进项+出项），非税后净额
            "resource_pool": round(mou_pool, 2),
            "allocations": {k: round(v, 2) for k, v in solution.allocations.items()},
            "total_utility": round(solution.total_utility, 2),
            "independent_sum": round(solution.independent_sum, 2),
            "delta": round(solution.delta, 2),
            "is_positive_sum": solution.is_positive_sum,
            "is_individual_rational": solution.is_individual_rational,
            "solve_time": round(solution.solve_time, 4),
        }

        # ===== 段 4: 融合验证 U_正和（C-4，TREATISE-026 三条件）=====
        mou_value = float(delivery.mou_value)
        mou_delta_ok = mou_value > 0                              # ΔMOU > 0（进项+出项总额）
        cognitive_ok = min_cognitive >= POSITIVE_SUM_THETA             # min(S_协作) ≥ θ=0.70
        spillover_ok = (eco_spillover / mou_value) > POSITIVE_SUM_PHI if mou_value > 0 \
            else False                                                 # 生态溢出/核心MOU > ϕ
        positive_sum_ok = solution.is_positive_sum                     # 正和性（效用精灵）

        # U_正和 = 1 if ΔMOU>0 ∧ min(S_协作)≥θ ∧ (生态溢出/核心MOU)>ϕ（TREATISE-026）
        full_ok = mou_delta_ok and cognitive_ok and spillover_ok and positive_sum_ok

        verdict_block = {
            "mou_delta_ok": mou_delta_ok,          # ΔMOU > 0
            "min_cognitive_ok": cognitive_ok,      # min(S_协作) ≥ 0.70
            "spillover_ok": spillover_ok,          # 生态溢出/核心MOU > 0.30
            "positive_sum_ok": positive_sum_ok,    # 效用精灵正和性
            "u_positive_sum": 1.0 if full_ok else 0.0,
            "theta": POSITIVE_SUM_THETA,
            "phi": POSITIVE_SUM_PHI,
        }

        # ===== 段 5: 主体经济生态（ECOWEIGHT-001 E-4）=====
        # 主体配置权场景价值 = 买卖总量（MOU_i=buy+sell）→ 生态权重；
        # 零和/负和 → 经济熔断 → 沙盒重塑/休眠 → 禁入该场景 → 配置价值低
        subject_econ_block = {}
        if subject_eco:
            assessments = self._eco.assess(subject_eco)
            subject_econ_block = {
                "assessments": [a.to_dict() for a in assessments],
                "weights": {a.subject_id: a.weight for a in assessments},
                "fused_subjects": [a.subject_id for a in assessments
                                   if a.economic_fused],
                "scene_config_blocked": [a.subject_id for a in assessments
                                         if a.scene_config_blocked],
            }

        return EconomicCognitionReport(
            delivery_id=delivery.delivery_id,
            cognition=cognition_block,
            taxation=taxation_block,
            positive_sum=positive_sum_block,
            verdict=verdict_block,
            subject_econ=subject_econ_block,
            full_cognition=full_ok,
            simulated=delivery.simulated,
        )
