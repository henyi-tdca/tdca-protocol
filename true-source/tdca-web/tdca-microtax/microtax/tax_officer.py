# -*- coding: utf-8 -*-
"""税务官智能体编排层（TaxOfficerAgent）——聚合 tdca-microtax 全模块总调度。

对齐上传材料 TaxOracleAgent（clipboard-20260812-171622）的总调度结构（校验采纳），
纪律修正（TDCA-MICROTAX-VALIDATE-001 + DCD-MICROTAX-003/004 裁决）:
  - 税率全链 CALL-001 三档（裁决①: 2%/7.5%/0.75%，模拟态 D-011）
  - 无三池分流（裁决②: DRAFT 不入实现，税收去向=预缴托管归集）
  - 周期报告税 0（裁决③）
  - 熔断器第四态不实现（遵循 DCD-NSFL-M1-FROZEN-001，引用 L2-R5 分级）
  - ID 纪律: ID79/ID80/ID43/ID71/ID85/ID91/ID92/ID56；不引用 ID69/ID70
  - 本体论基线: 调用即产生纳税事实（tax_fact_recorded 全路径 True）

核心循环: ECE/上游输出 → 计税（双向贡献）→ 预缴（fail-closed）→ 账本（事件溯源）
          → 领域二结算（状态机）→ 争议联动（仲裁增信保险）→ 税收 NCA（自反化合）
"""
from __future__ import annotations

import time
from decimal import Decimal
from typing import Dict, List, Optional

from .aggregation import AggregatedTaxPayer, BatchTaxReport
from .delivery_settlement import (ContractForm, DeliverySettlementStateMachine,
                                  DeliveryState)
from .dispute_chain import ArbitrationVerdict, DisputeResolutionChain
from .event_tax_calculator import EventTaxBreakdown, EventTaxCalculator
from .models import DeliveryForm, MicroDelivery, TaxEventType
from .tax_ledger import RealTimeTaxLedger
from .tax_nca import TaxNCA, TaxNCAFactory
from .v2_prepay_adapter import V2PrepayRecord, V2TaxPrepayAdapter

# TAXLAW-001: 财税法规素材（tdca-nsfl-compiler 提供）
# fail-closed（ID85）: 法规基座缺失 → 拒绝税务决策（禁止静默降级为空）
try:
    from nsfl_compiler.tax_regulations import (TAX_REGULATIONS,
                                               load_tax_regulations,
                                               resolve_violation_law)
except ImportError:  # pragma: no cover - 运行时自举
    import sys as _sys
    from pathlib import Path as _Path
    _compiler_dir = _Path(__file__).resolve().parent.parent.parent / "tdca-nsfl-compiler"
    if not _compiler_dir.exists():
        raise RuntimeError(
            "[NSFL-TRIGGER] 财税法规基座缺失（tdca-nsfl-compiler）——"
            "税务决策须 fail-closed（TAXLAW-001）")
    _sys.path.insert(0, str(_compiler_dir))
    from nsfl_compiler.tax_regulations import (TAX_REGULATIONS,  # noqa: E402
                                               load_tax_regulations,
                                               resolve_violation_law)

# 自动检测阈值: 大额且 MOU=0 → 疑似场外规避税收锚定（TDCA-ART-12）
BYPASS_MOU_VALUE_THRESHOLD = 1000.0


class TaxOfficerAgent:
    """税务官智能体（TDCA 智能体矩阵扩展，L3 效用计量层税收节点）。

    agent_id: 智能体身份（NCA 存证关联）；模拟态 D-011（ID92）。
    """

    def __init__(self, agent_id: str = "TAX-OFFICER-001",
                 calculator: Optional[EventTaxCalculator] = None,
                 prepay: Optional[V2TaxPrepayAdapter] = None,
                 ledger: Optional[RealTimeTaxLedger] = None,
                 aggregator: Optional[AggregatedTaxPayer] = None,
                 dispute_chain: Optional[DisputeResolutionChain] = None):
        self.agent_id = agent_id
        self._calc = calculator or EventTaxCalculator()
        self._prepay = prepay or V2TaxPrepayAdapter()
        self._ledger = ledger or RealTimeTaxLedger()
        self._aggregator = aggregator or AggregatedTaxPayer()
        self._dispute = dispute_chain or DisputeResolutionChain()
        self._stats = {
            "total_deliveries": 0,
            "total_tax_settled": Decimal("0"),
            "total_fused": 0,
            "total_fail_closed": 0,
            "total_settled_d2": 0,
            "total_disputes": 0,
            "avg_latency_ms": 0.0,
        }

    # ---- 法规决策依据（TAXLAW-001 L-4）----

    def check_regulatory_compliance(self, delivery: MicroDelivery) -> list:
        """TAX 域财税法规合规检查（税务官决策依据，fail-closed）。

        依据: TDCA-TASK-TAXLAW-001（DCD-TAXLAW-001 裁决①）——制度条款 + KG-LEGAL 种子。

        检查路径:
          1. 显式违规标记 delivery.tax_violation → 法规解析（TAX_VIOLATION_TO_LAW）
          2. 自动检测: MOU=0 且 value ≥ 阈值 → 疑似场外规避税收锚定（TDCA-ART-12，bypass_mou）

        返回: 违规清单 [{violation, law_id, title, article, point, severity}]（空=合规）。
        决策轨迹: 违规 law_id 由调用方写入结果（B-3）。
        """
        violations = []

        # 1. 显式违规标记
        if delivery.tax_violation:
            law = resolve_violation_law(delivery.tax_violation)
            if law:
                violations.append({
                    "violation": delivery.tax_violation,
                    "law_id": law["law_id"], "title": law["title"],
                    "article": law["article"], "point": law["point"],
                    "severity": law["severity"],
                })

        # 2. 自动检测: 场外规避税收锚定（MOU=0 且大额；负空间熔断事件豁免——
        #    fuse 事件本身已表达负空间归零，非规避锚定）
        if (delivery.event_type != TaxEventType.NEGATIVE_SPACE_FUSE
                and delivery.mou_value <= 0
                and delivery.value >= BYPASS_MOU_VALUE_THRESHOLD):
            law = TAX_REGULATIONS.get("TDCA-ART-12")
            if law:
                violations.append({
                    "violation": "tax_bypass_mou",
                    "law_id": law["law_id"], "title": law["title"],
                    "article": law["article"], "point": law["point"],
                    "severity": law["severity"],
                })

        return violations

    def _enforce_regulatory(self, delivery: MicroDelivery) -> list:
        """法规强制检查（fail-closed）: 触碰财税法规 → 拒绝（NSFL-TRIGGER）。"""
        violations = self.check_regulatory_compliance(delivery)
        if violations:
            law_ids = ", ".join(v["law_id"] for v in violations)
            raise ValueError(
                f"[NSFL-TRIGGER] 财税法规约束（fail-closed）: 触碰 {law_ids} —— "
                f"{violations[0]['point']}")
        return violations

    # ---- 统一入口: 计税 → 预缴 → 账本 → NCA ----

    def on_delivery(self, delivery: MicroDelivery) -> dict:
        """微交付税收全流程（领域一/二共用入口，对齐 TaxOracleAgent.on_ece_output）。

        法规决策依据（TAXLAW-001 L-4）: 计税前先过财税法规检查（fail-closed）。
        返回: 计税分项 + 预缴记录 + 账本事件 + NCA 水印 + 法规轨迹（完整审计轨迹）。
        """
        t0 = time.perf_counter()

        # 0. 财税法规合规检查（fail-closed，B-2）
        regulatory = self._enforce_regulatory(delivery)

        # 1. 计税（事件分档 + 双向贡献）
        bd: EventTaxBreakdown = self._calc.compute(delivery)
        delivery.taxes = bd.to_v1_taxes()
        delivery.net_value = float(bd.net_value)

        # 2. 预缴（fail-closed）
        rec: V2PrepayRecord = self._prepay.prepay(delivery, bd)

        # 3. 账本（事件溯源）
        event_id = self._ledger.append_event(rec)

        # 4. NCA（自反化合基座）
        nca = TaxNCAFactory.from_prepay_record(rec)

        # 5. 统计
        latency_ms = (time.perf_counter() - t0) * 1000.0
        self._stats["total_deliveries"] += 1
        self._stats["avg_latency_ms"] = (
            (self._stats["avg_latency_ms"] * (self._stats["total_deliveries"] - 1)
             + latency_ms) / self._stats["total_deliveries"])
        if rec.status == "PREPAID":
            self._stats["total_tax_settled"] += rec.amount
        elif bd.event_type.value == "negative_space_fuse":
            self._stats["total_fused"] += 1
        else:
            self._stats["total_fail_closed"] += 1

        return {
            "agent_id": self.agent_id,
            "delivery_id": delivery.delivery_id,
            "taxes": bd.to_v1_taxes(),
            "net_value": delivery.net_value,
            "prepay": {"transaction_id": rec.transaction_id,
                       "amount": str(rec.amount), "status": rec.status,
                       "tax_fact_recorded": rec.tax_fact_recorded},
            "ledger_event": event_id,
            "nca": nca.to_dict(),
            "regulatory": regulatory,              # B-3: 法规决策轨迹（law_id 引用）
            "latency_ms": round(latency_ms, 3),
        }

    # ---- 领域一: 聚合缴纳 ----

    def domain1_aggregate(self, deliveries: List[MicroDelivery]) -> dict:
        """领域一: 小散高频批量计税 + 聚合申报（Σ=Σ单笔）。"""
        report: BatchTaxReport = self._aggregator.compute_batch(deliveries)
        # 逐笔入账（聚合申报后仍逐笔预缴+账本——逐笔计算不省略）
        for d in deliveries:
            self.on_delivery(d)
        return {
            "batch_id": report.batch_id,
            "count": report.count,
            "total_tax": str(report.total_tax),
            "drift_verified": report.drift_verified,
            "batch_hash": report.batch_hash,
        }

    # ---- 领域二: 交付结算状态机 ----

    def domain2_settle(self, delivery: MicroDelivery,
                       contract_form: ContractForm) -> dict:
        """领域二: 合约事实交付结算（线上/线下/混合 × 合约形态）。

        要求: 已计税 + 已预缴（on_delivery 先行）；未完成线下交付禁止结算（A-8）。
        法规决策依据: 结算前防御性法规检查（fail-closed，TAXLAW-001 L-4）。
        """
        self._enforce_regulatory(delivery)          # 防御性二次检查（法规约束）
        sm = DeliverySettlementStateMachine(contract_form, delivery.delivery_form)
        agree = sm.agree(delivery)
        if delivery.delivery_form == DeliveryForm.ONLINE:
            sm.complete_offline(delivery)     # 幂等（线上无线下环节）
        else:
            sm.complete_offline(delivery)
        result = sm.settle(delivery)
        if result.settled:
            self._stats["total_settled_d2"] += 1
        return {
            "delivery_id": delivery.delivery_id,
            "contract_form": contract_form.value,
            "delivery_form": delivery.delivery_form.value,
            "state": result.state.value,
            "settled": result.settled,
            "transitions": result.transitions,
        }

    # ---- 争议联动 ----

    def handle_dispute(self, delivery: MicroDelivery, reason: str,
                       at_fault_agent: Optional[str] = None,
                       insurance_triggered: bool = False) -> dict:
        """争议 → 仲裁/诉讼（第30条三级模拟）→ 效用记录 → 增信/保险。"""
        sm = DeliverySettlementStateMachine(
            ContractForm.MULTILATERAL, delivery.delivery_form)
        sm.dispute(delivery, reason)
        verdict: ArbitrationVerdict = self._dispute.arbitrate(
            delivery, reason, at_fault_agent=at_fault_agent,
            insurance_triggered=insurance_triggered)
        self._stats["total_disputes"] += 1
        return {
            "delivery_id": delivery.delivery_id,
            "verdict": verdict.verdict,
            "utility_recorded": verdict.utility_recorded,
            "credit_measure": verdict.credit_measure.value,
            "dispute_status": delivery.dispute_status.value,
            "nca_stamp": verdict.nca_stamp,
        }

    # ---- 实时仪表盘（对齐 TaxOracleAgent.get_realtime_dashboard，无三池）----

    def dashboard(self) -> dict:
        """实时税收仪表盘（宏观治理输入）。"""
        return {
            "agent_id": self.agent_id,
            "ledger_events": self._ledger.event_count,
            "total_tax_settled": str(self._ledger.total_tax_settled),
            "total_deliveries": self._stats["total_deliveries"],
            "fused_count": self._stats["total_fused"],
            "fail_closed_count": self._stats["total_fail_closed"],
            "settled_domain2": self._stats["total_settled_d2"],
            "disputes": self._stats["total_disputes"],
            "avg_latency_ms": round(self._stats["avg_latency_ms"], 3),
            "simulated": True,                       # ID92 模拟态标注
        }

    # ---- 周期报告 NCA（ID91 自反化合，报告税 0）----

    def periodic_report(self, period_start: float, period_end: float) -> dict:
        """周期税收报告 NCA（可递归化合；报告税 0，裁决③）。"""
        total = self._ledger.get_mou_aggregate(period_start, period_end)
        nca: TaxNCA = TaxNCAFactory.periodic_report(period_start, period_end, total)
        return nca.to_dict()
