"""MOU 税收锚定记账（模拟态 · ID92）。

静默挂载 = 经许可（MIT）零触碰对方仓；按 CATEGORY.md 约定
以 15% 分润模拟态记账反哺原项目方（NCA 确权，非法币承诺，无现金流）。
MOU = 进项 + 出项税收总和；本包仅记「应付上游分润（模拟态）」出项侧，
无真实现金流。
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

    def __init__(self, tax_rate: float = 0.15):
        self._records: List[MouRecord] = []
        self._cumulative = 0.0
        self.tax_rate = tax_rate  # 上游分润率（模拟态）

    def record_profit_share(self, base_utility: float, note: str = "") -> MouRecord:
        """记一笔模拟态应付上游分润（出项）。无现金流。"""
        tax_out = round(base_utility * self.tax_rate, 6)
        rec = MouRecord(
            mou_id=f"MOU-{uuid.uuid4().hex[:8].upper()}",
            tax_in=0.0,
            tax_out=tax_out,
            total=round(tax_out, 6),
            note=note,
        )
        self._records.append(rec)
        self._cumulative += rec.total
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
            "tax_rate": self.tax_rate,
            "note": "ID92 模拟态：15% 上游分润 NCA 记账，无真实现金流",
        }
