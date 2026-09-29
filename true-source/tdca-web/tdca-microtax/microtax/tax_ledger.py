# -*- coding: utf-8 -*-
"""M-8 实时税收账本：事件溯源不可变追加（ID80 审计复杂度 O(n)）。

对齐上传代码 RealTimeTaxLedger 结构（校验采纳），修正:
  - mou_aggregate 完整实现（上传代码为 pass 占位）
  - 不引入三池分流（裁决② DRAFT 不入实现）——税收去向=预缴托管归集
  - 与 V2 预缴记录/计税结果对接

制度锚定: ID80（审计复杂度从指数降为线性——只存事件流不存中间态）
         / BV-3（freeze 后只读，禁止追加）/ ID91（NCA 双向索引）
"""
from __future__ import annotations

import time
from decimal import Decimal
from typing import Dict, List, Optional

from .v2_prepay_adapter import V2PrepayRecord


class RealTimeTaxLedger:
    """M-8 实时税收账本（事件溯源，ID80 O(n)）。"""

    def __init__(self, ledger_id: str = "TAX-LEDGER-V2"):
        self.ledger_id = ledger_id
        self._event_stream: List[dict] = []
        self._nca_index: Dict[str, str] = {}       # nca_id -> event_id
        self._agent_balances: Dict[str, Decimal] = {}
        self._frozen = False                        # BV-3 只读保护

    def append_event(self, record: V2PrepayRecord) -> str:
        """追加税收事件（不可变写；冻结后拒绝，BV-3）。"""
        if self._frozen:
            raise RuntimeError("Ledger is FROZEN — append prohibited (BV-3)")

        event = {
            "event_id": f"EVT-{len(self._event_stream):08d}",
            "timestamp": time.time(),
            "transaction_id": record.transaction_id,
            "delivery_id": record.delivery_id,
            "tax_amount": str(record.amount),
            "status": record.status,                 # PREPAID / FAIL_CLOSED
            "tax_fact_recorded": record.tax_fact_recorded,
            "data_hash": record.data_hash,
            "signature": record.signature,
            "simulated": record.simulated,
        }
        self._event_stream.append(event)
        self._nca_index[record.transaction_id] = event["event_id"]

        # 主体余额（仅 PREPAID 计入已缴；FAIL_CLOSED 不计）
        if record.status == "PREPAID":
            current = self._agent_balances.get(record.delivery_id, Decimal("0"))
            self._agent_balances[record.delivery_id] = current + record.amount

        return event["event_id"]

    # ---- 查询 ----

    def get_agent_balance(self, agent_id: str) -> Decimal:
        """主体已预缴税收余额（O(1)）。"""
        return self._agent_balances.get(agent_id, Decimal("0"))

    def get_event(self, transaction_id: str) -> Optional[dict]:
        """按交易 ID 反查事件。"""
        event_id = self._nca_index.get(transaction_id)
        if event_id is None:
            return None
        idx = int(event_id.split("-")[1])
        return self._event_stream[idx]

    def get_mou_aggregate(self, start_time: float, end_time: float) -> Decimal:
        """时间段已预缴税收聚合（ID79——ERI/CCI/UPDA 校准输入，完整实现）。"""
        return sum(
            (Decimal(e["tax_amount"]) for e in self._event_stream
             if start_time <= e["timestamp"] <= end_time and e["status"] == "PREPAID"),
            Decimal("0"))

    def freeze(self):
        """BV-3 只读冻结。"""
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    @property
    def event_count(self) -> int:
        return len(self._event_stream)

    @property
    def total_tax_settled(self) -> Decimal:
        """已预缴税收总额（PREPAID 累加）。"""
        return sum(
            (Decimal(e["tax_amount"]) for e in self._event_stream
             if e["status"] == "PREPAID"),
            Decimal("0"))

    @property
    def fail_closed_count(self) -> int:
        """fail-closed 冻结笔数（审计轨迹——纳税事实仍记录）。"""
        return sum(1 for e in self._event_stream if e["status"] == "FAIL_CLOSED")
