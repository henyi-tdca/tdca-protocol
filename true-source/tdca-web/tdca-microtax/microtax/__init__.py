# -*- coding: utf-8 -*-
"""
TDCA 微交付税收模块（TDCA-TASK-MICROTAX-001，V1.0-FROZEN）
=========================================================
M-1 微交付计税器（MicroTaxCalculator）→ T(y_t) 分项金额（调度税/版税/交易费 + 合计）
M-2 税收预缴合约适配器（TaxPrepayAdapter）→ 税款代扣托管（预缴语义，模拟态 D-011）

制度锚定: ID79（MOU 不可降）/ ID90（最小化合——复用 CALL-RULES TaxRates + MOU 管线）
         / ID71（快慢分工——计税 <10ms 快系统）/ ID92（模拟态显式标注）/ F-4+BV-3（税款托管隔离）
NSFL-Declaration:
  - 税款不得绕过预缴（MOU 不可降）
  - 计税不得损害正和性判定
  - 预缴为模拟态（D-011 cbdc_anchor 参数），真实 DCEP 接入后转硬数据
  - 税款账户托管隔离，资金不可挪用
SPDX-License-Identifier: TDCA-Internal
"""

from .models import (MicroDelivery, DeliveryCallType, TaxEventType,
                     DeliveryForm, DisputeStatus)
from .tax_calculator import MicroTaxCalculator, TaxBreakdown
from .prepay_adapter import TaxPrepayAdapter, TaxPrepayRecord
from .positive_sum_integration import TaxAfterPositiveSumSettlement
from .event_tax_calculator import EventTaxCalculator, EventTaxBreakdown
from .v2_prepay_adapter import V2TaxPrepayAdapter, V2PrepayRecord
from .aggregation import AggregatedTaxPayer, BatchTaxReport
from .tax_ledger import RealTimeTaxLedger
from .delivery_settlement import (ContractForm, DeliveryState,
                                  DeliverySettlementStateMachine, SettlementResult)
from .dispute_chain import (ArbitrationStage, CreditMeasure,
                            DisputeResolutionChain, ArbitrationVerdict)
from .tax_nca import TaxNCA, TaxNCAFactory
from .tax_officer import TaxOfficerAgent
from .economic_cognition import EconomicCognitionEngine, EconomicCognitionReport
from .subject_eco_weight import SubjectEcoWeightEngine, SubjectEcoAssessment
from .configurator import EconomicConfigurator, ConfigDecisionReport

__all__ = [
    "MicroDelivery",
    "DeliveryCallType",
    "TaxEventType",
    "DeliveryForm",
    "DisputeStatus",
    "TaxBreakdown",
    "MicroTaxCalculator",
    "TaxPrepayAdapter",
    "TaxPrepayRecord",
    "TaxAfterPositiveSumSettlement",
    "EventTaxCalculator",
    "EventTaxBreakdown",
    "V2TaxPrepayAdapter",
    "V2PrepayRecord",
    "AggregatedTaxPayer",
    "BatchTaxReport",
    "RealTimeTaxLedger",
    "ContractForm",
    "DeliveryState",
    "DeliverySettlementStateMachine",
    "SettlementResult",
    "ArbitrationStage",
    "CreditMeasure",
    "DisputeResolutionChain",
    "ArbitrationVerdict",
    "TaxNCA",
    "TaxNCAFactory",
    "TaxOfficerAgent",
    "EconomicCognitionEngine",
    "EconomicCognitionReport",
    "SubjectEcoWeightEngine",
    "SubjectEcoAssessment",
    "EconomicConfigurator",
    "ConfigDecisionReport",
]

__version__ = "0.1.0"
