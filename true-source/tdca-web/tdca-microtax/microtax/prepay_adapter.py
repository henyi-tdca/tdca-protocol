# -*- coding: utf-8 -*-
"""M-2 税收预缴合约适配器：税款代扣托管（预缴语义——区别于既有预算 escrow）。

语义区分:
  - 既有 mou_escrow（MOUEscrowVerifier）= 预算 escrow：pcr_budget 按 Shapley 分割锁定（非税收）
  - 本适配器 = 税收预缴：M-1 计税额 T(y_t) 全额代扣托管至税收智能合约（预缴语义）

制度锚定: ID79（税款不得绕过预缴——预缴额 = 计税额，零漂移 A-2）
         / F-4+BV-3（税款账户托管隔离，资金不可挪用——无提款路径）
         / ID92（模拟态显式标注，D-011 cbdc_anchor 参数）
         / ID91（哈希审计轨迹——每笔预缴 data_hash + signature）
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from .models import MicroDelivery

# 模拟预缴签名密钥（ID92：严禁用于真实数据；真实 DCEP 后转 CA/SM2 硬件签名）
SIMULATED_PREPAY_KEY = "TDCA-SIMULATED-PREPAY-KEY-0001"
SIMULATED_SOURCE = "SIMULATED-TAX-PREPAY-ESCROW"


@dataclass
class TaxPrepayRecord:
    """税收预缴托管记录（预缴语义）。"""
    delivery_id: str
    transaction_id: str
    amount: float                       # 预缴额 = 计税额（零漂移 A-2）
    tax_breakdown: Dict[str, float]     # 分项明细（调度税/版税/交易费/合计）
    escrow_account: str                 # 托管账户（隔离账户，不可挪用）
    timestamp: int
    data_hash: str
    signature: str
    simulated: bool = True              # ID92 模拟态标注（D-011）

    def verify_semantic(self) -> bool:
        """预缴语义校验：预缴额 = 计税额（零漂移）。"""
        expected = round(float(self.tax_breakdown.get("total", 0.0)), 2)
        return abs(round(self.amount, 2) - expected) < 1e-9


class TaxPrepayAdapter:
    """M-2 税收预缴合约适配器（慢系统：智能合约托管语义，模拟态 D-011）。

    托管隔离纪律（F-4/BV-3）: 本适配器仅提供 prepay/verify 只写只读路径，
    无任何 withdraw/transfer 提款接口——税款资金不可挪用。
    """

    def __init__(self, escrow_account: str = "TAX-ESCROW-D011-001",
                 signing_key: str = SIMULATED_PREPAY_KEY):
        self.escrow_account = escrow_account
        self.signing_key = signing_key
        self._records: Dict[str, TaxPrepayRecord] = {}

    # ---- 预缴（代扣托管）----

    def prepay(self, delivery: MicroDelivery, transaction_id: Optional[str] = None) -> TaxPrepayRecord:
        """税款代扣托管：预缴额 = M-1 计税额（零漂移 A-2）。

        :param delivery: 微交付实体（须已计税——taxes 非空且 T(y_t)>0）
        :param transaction_id: 交易 ID（默认派生自 delivery_id）
        :raises ValueError: 未计税 / 计税额非正（MOU 不可降，ID79）
        """
        if not delivery.taxes:
            raise ValueError("[NSFL-TRIGGER] 微交付未计税，禁止预缴（MOU 不可降，ID79）")
        total = float(delivery.taxes.get("total", 0.0))
        if total <= 0:
            raise ValueError("[NSFL-TRIGGER] 计税额 T(y_t) <= 0，禁止预缴（ID79 归零）")

        tx_id = transaction_id or f"TAXPRE-{delivery.delivery_id}"
        timestamp = int(time.time())
        breakdown = {
            "dispatch_tax": round(float(delivery.taxes.get("dispatch_tax", 0.0)), 2),
            "royalty": round(float(delivery.taxes.get("royalty", 0.0)), 2),
            "trade_fee": round(float(delivery.taxes.get("trade_fee", 0.0)), 2),
            "total": round(total, 2),
        }
        payload = self._canonical_payload(
            tx_id, total, breakdown, timestamp, self.escrow_account)
        data_hash = hashlib.sha256(payload.encode()).hexdigest()
        signature = hashlib.sha256(
            f"{data_hash}:{self.signing_key}".encode()).hexdigest()

        record = TaxPrepayRecord(
            delivery_id=delivery.delivery_id,
            transaction_id=tx_id,
            amount=round(total, 2),
            tax_breakdown=breakdown,
            escrow_account=self.escrow_account,
            timestamp=timestamp,
            data_hash=data_hash,
            signature=signature,
            simulated=delivery.simulated,
        )
        self._records[tx_id] = record
        # 回写微交付实体预缴状态
        delivery.prepay_status = "PREPAID"
        delivery.prepay_ref = tx_id
        return record

    # ---- 完整性校验（ID91 哈希审计）----

    def verify(self, record: TaxPrepayRecord) -> bool:
        """预缴记录完整性校验：哈希 + 签名 + 预缴语义（零漂移）。"""
        if not record.verify_semantic():
            return False
        payload = self._canonical_payload(
            record.transaction_id, record.amount, record.tax_breakdown,
            record.timestamp, record.escrow_account)
        if hashlib.sha256(payload.encode()).hexdigest() != record.data_hash:
            return False
        expect = hashlib.sha256(
            f"{record.data_hash}:{self.signing_key}".encode()).hexdigest()
        return record.signature == expect

    # ---- 查询 ----

    def get(self, transaction_id: str) -> Optional[TaxPrepayRecord]:
        """按交易 ID 查询预缴记录。"""
        return self._records.get(transaction_id)

    def total_prepaid(self) -> float:
        """已预缴税款总额（审计）。"""
        return round(sum(r.amount for r in self._records.values()), 2)

    @staticmethod
    def _canonical_payload(transaction_id: str, amount: float,
                           breakdown: Dict[str, float], timestamp: int,
                           escrow_account: str) -> str:
        """规范化载荷（字段序固定，防注入/歧义）。"""
        parts = "|".join(f"{k}:{round(v, 2)}" for k, v in sorted(breakdown.items()))
        return f"{transaction_id}|{round(amount, 2)}|{parts}|{timestamp}|{escrow_account}"
