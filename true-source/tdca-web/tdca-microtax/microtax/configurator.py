# -*- coding: utf-8 -*-
"""S-15 整合编排层（EconomicConfigurator）——经济事实 → 完整认知 → 多主体配置 一键闭环。

TDCA-TASK-ECOCOG-001（V1.0-FROZEN，DCD-ECOCOG-001，人类最终审定后开发）：
整合 6 个冻结子体系为统一编排入口（ID90——不新建平行体系，仅接线）：

  经济事实 → ① 计税/预缴/法规（TaxOfficerAgent，fail-closed）
           → ② 完整经济认知（EconomicCognitionEngine.cognize：认知+税收+正和+主体生态）
           → ③ 多主体配置（cross_scene_match：偏态互补筛选 + 正和满意解值高者优先
                ——满意解值衔接自 cognize positive_sum.allocations）

本体论（人类确认）: 正和效用 = MOU（进项+出项）；净额仅分配语义。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .economic_cognition import EconomicCognitionEngine, EconomicCognitionReport
from .models import MicroDelivery
from .subject_eco_weight import SubjectEcoWeightEngine
from .tax_officer import TaxOfficerAgent


@dataclass
class ConfigDecisionReport:
    """多主体配置决策报告（整合编排输出）。"""
    delivery_id: str
    cognition: EconomicCognitionReport    # 完整经济认知（认知+税收+正和+主体生态+判定）
    config_matches: List[dict]            # 跨场景配置匹配排序（互补筛选+满意解值高者优先）
    top_candidate: Optional[dict]         # 最优配置候选
    full_cognition: bool                  # 完整经济认知达成
    simulated: bool = True

    def to_dict(self) -> dict:
        return {
            "delivery_id": self.delivery_id,
            "cognition": self.cognition.to_dict(),
            "config_matches": self.config_matches,
            "top_candidate": self.top_candidate,
            "full_cognition": self.full_cognition,
            "simulated": self.simulated,
        }


class EconomicConfigurator:
    """S-15 整合编排层（多主体配置统一入口）。"""

    def __init__(self,
                 officer: Optional[TaxOfficerAgent] = None,
                 cognition: Optional[EconomicCognitionEngine] = None,
                 eco_weight: Optional[SubjectEcoWeightEngine] = None):
        self._officer = officer or TaxOfficerAgent()
        self._cognition = cognition or EconomicCognitionEngine()
        self._eco = eco_weight or SubjectEcoWeightEngine()

    def configure(self, delivery: MicroDelivery,
                  cognitive_states: Dict[str, Dict[str, float]],
                  subject_eco: Dict[str, Dict[str, float]],
                  enterer_bias: float,
                  target_scene_bias: Dict[str, float],
                  eco_spillover: float = 0.0,
                  synergy: float = 1.2) -> ConfigDecisionReport:
        """经济事实 → 完整认知 → 多主体配置（一键闭环）。

        :param delivery: 微交付实体（参与方贡献）
        :param cognitive_states: 多主体五维认知状态 {agent_id: {A,D,L,C,SC}}
        :param subject_eco: 主体级买卖 {agent_id: {buy, sell}}（生态权重/偏态）
        :param enterer_bias: 进入者偏态（跨场景配置决策）
        :param target_scene_bias: 目标场景主体偏态 {subject_id: bias}
        :param eco_spillover: 生态溢出值（U_正和 三条件输入）
        :param synergy: 正和协同
        """
        # 段 1: 计税/预缴/法规（fail-closed）——经 cognize 内部 on_delivery
        report: EconomicCognitionReport = self._cognition.cognize(
            delivery, cognitive_states,
            synergy=synergy, eco_spillover=eco_spillover,
            subject_eco=subject_eco)

        # 段 2: 满意解值来源衔接——cognize positive_sum.allocations（主体分得效用）
        allocations = report.positive_sum.get("allocations", {})
        satisfaction_values = {
            sid: float(allocations.get(sid, 0.0)) for sid in target_scene_bias
        }

        # 段 3: 多主体配置（偏态互补筛选 + 满意解值高者优先）
        matches = self._eco.cross_scene_match(
            enterer_bias, target_scene_bias,
            satisfaction_values=satisfaction_values)

        top = matches[0] if matches else None

        return ConfigDecisionReport(
            delivery_id=delivery.delivery_id,
            cognition=report,
            config_matches=matches,
            top_candidate=top,
            full_cognition=report.full_cognition,
            simulated=delivery.simulated,
        )
