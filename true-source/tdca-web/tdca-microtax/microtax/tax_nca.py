# -*- coding: utf-8 -*-
"""M-9 税收 NCA + 自反化合（ID91）。

- 每笔税收事件生成 TaxNCA（制度水印 + 审计轨迹）
- 周期税收报告 NCA 可递归化合（ID91 自反化合——税收的税收）
- 裁决③: 报告税档位默认 0（不新增税率概念）

制度锚定: ID91（自反化合）/ ID56（双协议封印——NCA 不可篡改水印）/ ID92（模拟态标注）
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional

from .v2_prepay_adapter import V2PrepayRecord


@dataclass
class TaxNCA:
    """税收 NCA（嵌套认知资产，ID91 可递归化合）。"""
    nca_id: str
    timestamp: float
    event_type: str
    transaction_id: str
    tax_amount: Decimal
    mou_value: Decimal
    audit_trail: List[dict] = field(default_factory=list)
    nsfl_compliance: bool = True
    constitution_article: str = "16"
    simulated: bool = True                       # ID92 模拟态标注

    def to_watermark(self) -> str:
        """制度水印（ID56 双协议封印语义——不可篡改）。"""
        payload = f"{self.nca_id}|{self.timestamp}|{self.tax_amount}|{self.mou_value}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def add_audit_entry(self, stage: str, result: str, metadata: Optional[dict] = None):
        self.audit_trail.append({
            "stage": stage,
            "result": result,
            "timestamp": time.time(),
            "metadata": metadata or {},
        })

    def to_dict(self) -> dict:
        return {
            "nca_id": self.nca_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "transaction_id": self.transaction_id,
            "tax_amount": str(self.tax_amount),
            "mou_value": str(self.mou_value),
            "watermark": self.to_watermark(),
            "audit_count": len(self.audit_trail),
            "nsfl_compliance": self.nsfl_compliance,
            "simulated": self.simulated,
        }


class TaxNCAFactory:
    """M-9 税收 NCA 工厂（预缴记录 → NCA；周期报告 NCA）。"""

    @staticmethod
    def from_prepay_record(record: V2PrepayRecord) -> TaxNCA:
        """预缴记录 → 税收 NCA。"""
        nca = TaxNCA(
            nca_id=f"TAX-NCA-{record.transaction_id}",
            timestamp=float(record.timestamp),
            event_type="tax_prepay",
            transaction_id=record.transaction_id,
            tax_amount=record.amount,
            mou_value=record.amount,
            nsfl_compliance=record.status == "PREPAID",
            simulated=record.simulated,
        )
        nca.add_audit_entry("PREPAY", record.status,
                            {"delivery_id": record.delivery_id})
        return nca

    @staticmethod
    def periodic_report(period_start: float, period_end: float,
                        total_tax: Decimal, period_id: Optional[str] = None) -> TaxNCA:
        """周期税收报告 NCA（ID91 自反化合——报告 NCA 可参与更高阶配置权调用）。

        裁决③: 报告税默认 0（不新增税率概念）；档位留待 D-010 校准。
        """
        nca = TaxNCA(
            nca_id=f"TAX-REPORT-{period_id or int(time.time())}",
            timestamp=time.time(),
            event_type="periodic_report",
            transaction_id="PERIODIC-REPORT",
            tax_amount=Decimal("0"),          # 裁决③: 报告税 0
            mou_value=total_tax,              # MOU 聚合作为报告锚定
            simulated=True,
        )
        nca.add_audit_entry("PERIOD", f"{period_start}..{period_end}",
                            {"total_tax": str(total_tax)})
        return nca
