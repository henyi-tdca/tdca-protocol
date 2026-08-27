"""MOU 税收锚定记账（ID79，模拟态 ID92）。

MOU = 进项 + 出项税收总和；无真实现金流，NCA 记账为主（法币通道就绪后凭账本转实际结算）。
"""

from dataclasses import dataclass, field
from typing import Dict, List
import uuid


@dataclass
class MouRecord:
    mou_id: str
    tax_in: float
    tax_out: float
    total: float
    simulated: bool = True
    note: str = ""


class MouLedger:
    """MOU 记账本（模拟态）。"""

    def __init__(self):
        self._records: List[MouRecord] = []
        self._cumulative = 0.0

    def record(self, tax_in: float, tax_out: float, note: str = "") -> MouRecord:
        total = round(tax_in + tax_out, 6)
        rec = MouRecord(
            mou_id=f"MOU-{uuid.uuid4().hex[:8].upper()}",
            tax_in=tax_in, tax_out=tax_out, total=total, note=note,
        )
        self._records.append(rec)
        self._cumulative += total
        return rec

    @property
    def cumulative(self) -> float:
        return round(self._cumulative, 6)

    @property
    def count(self) -> int:
        return len(self._records)

    def snapshot(self) -> Dict:
        return {
            "cumulative_mou": self.cumulative,
            "records": self.count,
            "simulated": True,
            "note": "ID92 模拟态：NCA 记账，无真实现金流",
        }
