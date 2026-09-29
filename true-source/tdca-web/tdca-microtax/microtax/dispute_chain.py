# -*- coding: utf-8 -*-
"""M-7 争议仲裁增信保险联动（领域二，模拟态）。

用户论述: 某次交付后有争议 → 事后仲裁与诉讼 → 对本次配置效用进行记录，
对后续过错方配置需要增信或者增加保险。

制度依据（校验查证）:
  - 第30条争议解决三级路径: 效用精灵均衡求解 → TDCA 审计智能体分布式审查 → 法定仲裁机构
  - NSFL 过渡协议保险兜底: 三类保险产品 + 保险资金池（<120% 触发 FUSE_PAUSE）+ MOU 联动
  - 增信 = 保证金质押（边界条件四类之一: 增信→保证金质押）

制度锚定: ID79（争议不绕过税收）/ ID91（争议全程 NCA 存证）/ ID92（模拟态标注）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .models import DisputeStatus, MicroDelivery


class ArbitrationStage(str, Enum):
    """第30条三级仲裁路径（模拟）。"""
    UTILITY_GENIE = "utility_genie"           # 一级: 效用精灵均衡求解
    AUDIT_AGENT = "audit_agent"               # 二级: 审计智能体分布式审查
    LEGAL_ARBITRATION = "legal_arbitration"   # 三级: 法定仲裁机构


class CreditMeasure(str, Enum):
    """过错方配置处置（增信/保险联动）。"""
    NONE = "none"
    BOND_PLEDGE = "bond_pledge"               # 增信: 保证金质押（后续配置须增信）
    INSURANCE_LINKED = "insurance_linked"     # 保险: 链接 NSFL 保险兜底资金池
    BOTH = "both"                             # 增信 + 保险


@dataclass
class ArbitrationVerdict:
    """仲裁裁决记录。"""
    delivery_id: str
    dispute_reason: str
    stage: ArbitrationStage
    at_fault_agent: Optional[str]
    verdict: str                              # FAULT / NO_FAULT / PARTIAL
    utility_recorded: bool                    # 配置效用记录完成
    credit_measure: CreditMeasure             # 过错方增信/保险联动
    nca_stamp: str = ""                       # 争议 NCA 水印（ID91）
    simulated: bool = True                    # ID92 模拟态标注


class DisputeResolutionChain:
    """M-7 争议仲裁增信保险联动（模拟态，第30条三级路径）。"""

    def __init__(self, insurance_pool_ratio: float = 1.5):
        self.insurance_pool_ratio = insurance_pool_ratio  # 保险资金池充足率（<120% 熔断）

    def arbitrate(self, delivery: MicroDelivery, dispute_reason: str,
                  at_fault_agent: Optional[str] = None,
                  stage: ArbitrationStage = ArbitrationStage.AUDIT_AGENT,
                  insurance_triggered: bool = False) -> ArbitrationVerdict:
        """仲裁/诉讼（第30条三级路径模拟）。

        流程:
          1. 争议挂起（delivery.dispute_status → ARBITRATING）
          2. 仲裁（三级路径：效用精灵 → 审计智能体 → 法定仲裁，模拟）
          3. 配置效用记录（delivery.dispute_status → ARBITRATED，效用已记录）
          4. 过错方处置: 增信（保证金质押）/ 保险（NSFL 保险兜底联动）
        """
        if delivery.dispute_status != DisputeStatus.DISPUTED:
            # 未挂起则先挂起（状态机 M-6 dispute 已置位时跳过）
            delivery.dispute_status = DisputeStatus.ARBITRATING

        # 三级路径推进（模拟——stage 参数指定入口，实际链路逐级）
        stages_used = [ArbitrationStage.UTILITY_GENIE, stage]

        # 裁决: 过错方判定（模拟；at_fault_agent 显式给出则采纳）
        fault = bool(at_fault_agent)
        verdict = "FAULT" if fault else "NO_FAULT"
        if dispute_reason.startswith("PARTIAL"):
            verdict = "PARTIAL"

        # 过错方处置（增信/保险联动）
        if fault:
            credit = CreditMeasure.BOTH if insurance_triggered else CreditMeasure.BOND_PLEDGE
        elif insurance_triggered:
            credit = CreditMeasure.INSURANCE_LINKED
        else:
            credit = CreditMeasure.NONE

        # 保险资金池充足率熔断（NSFL 过渡协议: <120% 触发 FUSE_PAUSE）
        pool_fused = self.insurance_pool_ratio < 1.2

        # 配置效用记录（本次争议对配置效用的影响已记录）
        delivery.dispute_status = DisputeStatus.ARBITRATED
        if credit != CreditMeasure.NONE:
            delivery.dispute_status = DisputeStatus.CREDIT_ADJUSTED

        verdict_record = ArbitrationVerdict(
            delivery_id=delivery.delivery_id,
            dispute_reason=dispute_reason,
            stage=stage,
            at_fault_agent=at_fault_agent,
            verdict=verdict,
            utility_recorded=True,
            credit_measure=credit,
            nca_stamp=f"ARB-{delivery.delivery_id}",
            simulated=delivery.simulated,
        )
        if pool_fused and credit != CreditMeasure.NONE:
            # 资金池不足时保险联动暂停（记录仍成立）
            verdict_record.credit_measure = CreditMeasure.BOND_PLEDGE
        return verdict_record
