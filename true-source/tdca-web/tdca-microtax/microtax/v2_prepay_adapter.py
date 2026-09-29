# -*- coding: utf-8 -*-
"""M-2 V2 税收预缴合约适配器（fail-closed + 纳税事实记录）。

TDCA-TASK-MICROTAX-002（DCD-MICROTAX-003）：
  - fail-closed（ID85 纪律）: MOU 硬验证未过/数据不足 → 税收预冻结（不上链清算），非估算
  - 纳税事实: 调用即产生纳税事实——正常/冻结/归零均记录事实（不随税额归零丢失）
  - 维持 V1 语义: 预缴额 = 计税额（零漂移 A-2）；托管隔离无提款路径（F-4/BV-3）
  - 与 V1（TaxPrepayAdapter）关系: V1 FROZEN 不动；本模块为 V2 扩展（接受 V2 计税结果）

ID 纪律: ID79（税款不得绕过预缴）/ID92（模拟态标注）/ID91（哈希审计）；
不引入熔断器第四态 BLOCKED（遵循 DCD-NSFL-M1-FROZEN-001——第四态引用 L2-R5，此处仅 fail-closed 状态）。
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Optional

from .event_tax_calculator import EventTaxBreakdown
from .models import MicroDelivery

SIMULATED_PREPAY_KEY_V2 = "TDCA-SIMULATED-PREPAY-KEY-0002"
SIMULATED_SOURCE_V2 = "SIMULATED-TAX-PREPAY-ESCROW-V2"


@dataclass
class V2PrepayRecord:
    """V2 税收预缴记录（含 fail-closed 状态 + 纳税事实标记）。"""
    delivery_id: str
    transaction_id: str
    amount: Decimal                     # 预缴额 = 计税额（零漂移）或 0（冻结）
    tax_breakdown: Dict[str, str]       # 分项明细（字符串化 Decimal，防浮点歧义）
    status: str                         # PREPAID / FAIL_CLOSED
    tax_fact_recorded: bool             # 纳税事实记录（成立即 True）
    escrow_account: str
    timestamp: int
    data_hash: str
    signature: str
    simulated: bool = True              # ID92 模拟态标注（D-011）

    def verify_zero_drift(self) -> bool:
        """预缴额 = 计税额（零漂移，A-2）；冻结态 amount=0。"""
        expected = Decimal(self.tax_breakdown.get("total", "0"))
        return Decimal(self.amount) == expected


class V2TaxPrepayAdapter:
    """M-2 V2 税收预缴适配器（fail-closed）。

    托管隔离（F-4/BV-3）: 仅 prepay/verify/get，无 withdraw/transfer/refund/release 提款接口。
    """

    def __init__(self, escrow_account: str = "TAX-ESCROW-D011-V2",
                 signing_key: str = SIMULATED_PREPAY_KEY_V2):
        self.escrow_account = escrow_account
        self.signing_key = signing_key
        self._records: Dict[str, V2PrepayRecord] = {}

    def prepay(self, delivery: MicroDelivery, breakdown: EventTaxBreakdown,
               transaction_id: Optional[str] = None) -> V2PrepayRecord:
        """预缴（含 fail-closed 语义）:

        - mou_verified=True（正常）: 预缴额 = total（零漂移），状态 PREPAID
        - mou_verified=False（数据不足/溢出，非负空间）: 预冻结 amount=0，状态 FAIL_CLOSED，不上链
        - 负空间（NEGATIVE_SPACE_FUSE）: 税额归零，纳税事实记录，状态 FAIL_CLOSED
        - 一切路径 tax_fact_recorded=True（调用即产生纳税事实，ID79/语义修正）
        """
        tx_id = transaction_id or f"TAXPREV2-{delivery.delivery_id}"
        timestamp = int(time.time())

        is_fuse = (breakdown.event_type.value == "negative_space_fuse")
        status = "PREPAID" if (breakdown.mou_verified and not is_fuse) else "FAIL_CLOSED"
        amount = breakdown.total if status == "PREPAID" else Decimal("0")

        breakdown_str = {k: str(v) for k, v in {
            "dispatch_tax": breakdown.dispatch_tax,
            "royalty": breakdown.royalty,
            "trade_fee": breakdown.trade_fee,
            "total": breakdown.total,
        }.items()}
        payload = self._canonical_payload(tx_id, amount, breakdown_str,
                                          timestamp, self.escrow_account)
        data_hash = hashlib.sha256(payload.encode()).hexdigest()
        signature = hashlib.sha256(
            f"{data_hash}:{self.signing_key}".encode()).hexdigest()

        record = V2PrepayRecord(
            delivery_id=delivery.delivery_id,
            transaction_id=tx_id,
            amount=amount,
            tax_breakdown=breakdown_str,
            status=status,
            tax_fact_recorded=True,          # 纳税事实成立即记录（不随归零丢失）
            escrow_account=self.escrow_account,
            timestamp=timestamp,
            data_hash=data_hash,
            signature=signature,
            simulated=delivery.simulated,
        )
        self._records[tx_id] = record

        # 回写微交付实体（V2 状态）
        delivery.prepay_status = status
        delivery.prepay_ref = tx_id
        delivery.tax_fact_recorded = True
        return record

    def verify(self, record: V2PrepayRecord) -> bool:
        """完整性校验: 哈希 + 签名 + 零漂移（ID91）。"""
        if not record.verify_zero_drift():
            return False
        payload = self._canonical_payload(
            record.transaction_id, record.amount, record.tax_breakdown,
            record.timestamp, record.escrow_account)
        if hashlib.sha256(payload.encode()).hexdigest() != record.data_hash:
            return False
        expect = hashlib.sha256(
            f"{record.data_hash}:{self.signing_key}".encode()).hexdigest()
        return record.signature == expect

    def get(self, transaction_id: str) -> Optional[V2PrepayRecord]:
        return self._records.get(transaction_id)

    def total_prepaid(self) -> Decimal:
        """已预缴税款总额（仅 PREPAID，冻结不计）。"""
        return sum(
            (r.amount for r in self._records.values() if r.status == "PREPAID"),
            Decimal("0"))

    @staticmethod
    def _canonical_payload(transaction_id: str, amount: Decimal,
                           breakdown: Dict[str, str], timestamp: int,
                           escrow_account: str) -> str:
        parts = "|".join(f"{k}:{v}" for k, v in sorted(breakdown.items()))
        return f"{transaction_id}|{amount}|{parts}|{timestamp}|{escrow_account}"
