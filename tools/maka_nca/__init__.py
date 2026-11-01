"""maka_nca · Maka 化合内化包（DCD-MAKA-COMPOUND-001 M1）

M1a: Event Log → NCA 转换器 + 审计链（append-only 保持）
M1b: UtilityGenie 正和验证插件
M1c: 端到端（示例 Event Log → NCA 上链演示，CLI）

制度锚定: ID91（自反化合）/ 宪法 C02（正和聚合）/ ID84（停机制定理）/ BIDIR-001
SPDX-License-Identifier: TDCA-Internal
"""
from .converter import (
    MakaNcaConverter,
    NcaRecord,
    EVENT_TYPES,
    EVENT_TO_OP_TYPE,
)
from .validator import PositiveSumValidator, PositiveSumVerdict

__all__ = [
    "MakaNcaConverter",
    "NcaRecord",
    "EVENT_TYPES",
    "EVENT_TO_OP_TYPE",
    "PositiveSumValidator",
    "PositiveSumVerdict",
]
