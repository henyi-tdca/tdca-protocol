# SPDX-License-Identifier: Apache-2.0
"""
TDCA-FC-012 C-3 NCA-Reporter
制度锚定: 宪法第1条（可观测性），每 Phase 生成 NCA
Granted-By: TDCA-FC-012-DESIGN-002
NSFL: NCA 必须由 FC-001 生成，禁止前端伪造
"""
from typing import Optional


class NCAReporter:
    """每 Phase 生成 NCA（对接 FC-001）"""

    def __init__(self, nca_generator: Optional[callable] = None):
        self._nca_generator = nca_generator  # FC-001

    def report(self, flow_id: str, phase: str) -> dict:
        if self._nca_generator:
            return self._nca_generator(flow_id, phase)
        return {
            'nca_id': f"NCA-{phase}-{flow_id}",
            'flow_id': flow_id,
            'phase': phase,
            'mock': True,
        }
