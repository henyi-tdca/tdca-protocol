# SPDX-License-Identifier: Apache-2.0
"""
TDCA-FC-012 C-3 MOU-Closer
制度锚定: 宪法第3条（自证清白）+ ID79（MOU 税收锚定）+ ID70（CBDC 唯一性）
Granted-By: TDCA-FC-012-DESIGN-002
NSFL: MOU 必须基于真实税收数据，Tax_in + Tax_out > 0
"""
from typing import Optional


class MOUCloser:
    """全流程 MOU 闭环验证（P8 交付）"""

    def __init__(self, mou_recorder: Optional[callable] = None):
        self._mou_recorder = mou_recorder  # FC-003A

    def close(self, flow_id: str, tax_in: float, tax_out: float) -> dict:
        mou_total = tax_in + tax_out
        if mou_total <= 0:
            raise ValueError(
                f"[NSFL-TRIGGER] MOU 未闭环: {flow_id} Tax_in({tax_in}) + Tax_out({tax_out}) = {mou_total}"
            )
        if self._mou_recorder:
            self._mou_recorder(flow_id, tax_in, tax_out)
        return {
            'flow_id': flow_id,
            'tax_in': tax_in,
            'tax_out': tax_out,
            'mou_total': mou_total,
            'closed': True,
        }
