"""pi_nca · Pi 化合内化包（DCD-PI-COMPOUND-001 M1，MIT 层）

M1a: agent 构建协议 → TDCA 制度编译（Compile 非蒸馏）
M1b: 构建轨迹 → NCA 存证
Fair Source 管控: 化合仅限 MIT 层（许可证边界即化合边界）
SPDX-License-Identifier: TDCA-Internal
"""
from .compiler import (
    PiCompiler,
    CompiledStep,
    FairSourceGuard,
    MIT_LAYER,
    FAIR_SOURCE_LAYER,
)

__all__ = ["PiCompiler", "CompiledStep", "FairSourceGuard", "MIT_LAYER", "FAIR_SOURCE_LAYER"]
