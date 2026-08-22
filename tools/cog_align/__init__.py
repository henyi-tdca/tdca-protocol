"""cog_align · 智能体不对称认知对齐评测服务包（DCD-COG-ALIGN-001 M1 服务化）

接缝式新增：复用 tdca-toolchain 基座（cognitive_distance/state/fuzzy），不改核心。
制度锚定: 命题 3.10（不对称性）/ 定义 3.36/3.37 / NIA-MACM PHASE-2 / ID60 / ID8 / ID92
NSFL-Declaration:
  - 不试图消除认知差异（ID60）——只定位差异与对齐难度
  - 计算需真实数据；合成/评测场景输入按 ID92 标注 provenance
  - 禁止伪造认知状态数据
SPDX-License-Identifier: TDCA-Internal
"""
from .engine import (
    CogAlignService,
    PairMeasure,
    MultiSubjectMeasure,
    ConvergenceTrace,
)
from .report import build_pair_report, build_multi_report
from .notary import CogAlignNotary

__all__ = [
    "CogAlignService",
    "PairMeasure",
    "MultiSubjectMeasure",
    "ConvergenceTrace",
    "build_pair_report",
    "build_multi_report",
    "CogAlignNotary",
]
