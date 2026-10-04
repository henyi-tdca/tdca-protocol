"""L1 适配器层（R-CLS-5 E-2）：CLS ↔ MICROTAX 复用桥

铁律: MICROTAX **只读复用**（零改动，183 绿保持）——适配器仅调用不修改。
"""
from __future__ import annotations
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

# MICROTAX 只读复用（PYTHONPATH 注入 tdca-microtax）
from microtax.models import MicroDelivery, DeliveryCallType, TaxEventType
from microtax.tax_calculator import MicroTaxCalculator
from microtax.tax_ledger import RealTimeTaxLedger
from microtax.tax_nca import TaxNCA, TaxNCAFactory


@dataclass
class CLSTaxResult:
    """CLS 结算计税结果（R-CLS-4 L1 硬约束）"""
    amount: float
    dispatch_tax: float      # 配置权调度税（T-031 通用 2% 默认）
    royalty: float
    trade_fee: float
    total_tax: float
    net_value: float         # 税后净额
    mou_ok: bool             # C_MOU(>0) 硬验证（ID79）


class CLSTaxAdapter:
    """多边净额支付计税适配器（复用 MicroTaxCalculator.compute_taxes）"""

    def __init__(self, calculator: Optional[MicroTaxCalculator] = None):
        self.calc = calculator or MicroTaxCalculator()

    def compute_for_settlement(self, payer: str, payee: str, amount: float,
                               scene: str = "supply-chain",
                               royalty_base: float = 0.0,
                               simulated: bool = True) -> CLSTaxResult:
        """净额支付（DPI amount）同刻计税（票款同步 T-038）"""
        delivery = MicroDelivery(
            delivery_id=f"CLS:{payer}->{payee}:{amount}",
            scene=scene,
            value=amount,
            call_type=DeliveryCallType.DISPOSABLE,
            royalty_base=royalty_base,
            participants={payer: 1.0},
            taxes=None,
            net_value=amount,
            prepay_status="none",
            prepay_ref=None,
            simulated=simulated,
            event_type=TaxEventType.CONFIG_RIGHT_CALL,
            tax_in=0.0,
            tax_out=0.0,
            delivery_form=None,
            dispute_status=None,
            tax_fact_recorded=False,
            tax_violation=None,
        )
        tb = self.calc.compute_taxes(delivery)
        mou_ok = self.calc.validate_mou(tb)
        return CLSTaxResult(
            amount=amount,
            dispatch_tax=tb.dispatch_tax,
            royalty=tb.royalty,
            trade_fee=tb.trade_fee,
            total_tax=tb.total,
            net_value=tb.net_value,
            mou_ok=mou_ok,
        )


class CLSLedgerAdapter:
    """跨主体 MOU 台账聚合（复用 RealTimeTaxLedger）"""

    def __init__(self, ledger: Optional[RealTimeTaxLedger] = None):
        self.ledger = ledger or RealTimeTaxLedger("cls-ledger")

    def record_settlement(self, tx_id: str, agent: str, tax: float,
                          event_type: str = "CLS_SETTLEMENT") -> None:
        """结算税收入台账（复用 RealTimeTaxLedger.append_event——V2PrepayRecord）"""
        from microtax.v2_prepay_adapter import V2PrepayRecord
        record = V2PrepayRecord(
            delivery_id=agent,
            transaction_id=tx_id,
            amount=Decimal(str(round(tax, 6))),   # ledger 内部 Decimal 运算（tax_ledger:53-54）
            tax_breakdown={"dispatch_tax": float(tax)},
            status="PREPAID",
            tax_fact_recorded=True,
            escrow_account="cls-escrow",
            timestamp=int(time.time()),
            data_hash=f"hash:{tx_id}",
            signature=f"sig:{tx_id}",
            simulated=True,
        )
        self.ledger.append_event(record)

    def aggregate_mou(self, start_time=None, end_time=None) -> float:
        """跨主体 MOU 聚合（生态周期评估 L3 输入）"""
        return self.ledger.get_mou_aggregate(start_time, end_time)

    def total_settled(self) -> float:
        return float(self.ledger.total_tax_settled)   # property（非方法）


class CLSNCAAdapter:
    """CLS 结算 NCA 存证（复用 TaxNCA 审计轨迹——R-CLS-1 I-4）"""

    def __init__(self):
        self.nc_as: List[TaxNCA] = []

    def from_settlement(self, tx_id: str, payer: str, payee: str, amount: float,
                        tax_result: CLSTaxResult, cycle_ref: str = "") -> TaxNCA:
        """DPI 结算生成 NCA（tax_nca + 全域比配 + 合约执行轨迹）"""
        nca = TaxNCA(
            nca_id=f"NCA-CLS-{tx_id}",
            timestamp=time.time(),
            event_type="CLS_SETTLEMENT",
            transaction_id=tx_id,
            tax_amount=Decimal(str(round(tax_result.total_tax, 6))),
            mou_value=Decimal(str(round(tax_result.amount, 6))),   # MOU 锚定值=结算金额（模拟态）
            audit_trail=[],
            simulated=True,
        )
        nca.add_audit_entry("DPI", "SETTLED", {"amount": amount, "payer": payer, "payee": payee,
                                               "conditions": "C_MOU∧C_delivery∧C_dpi", "cycle_ref": cycle_ref})
        nca.add_audit_entry("TAX", "COMPUTED", {"dispatch_tax": tax_result.dispatch_tax,
                                                "total_tax": tax_result.total_tax})
        self.nc_as.append(nca)
        return nca

    def all_ncas(self) -> List[TaxNCA]:
        return self.nc_as
