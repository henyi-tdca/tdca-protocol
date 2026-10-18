"""dca_sandbox · DCA-重塑版 SEA 沙盒模拟器（DCD-DCA-SANDBOX-001 M1 装配）

装配 merchant_loop M1（FROZEN 只装配不改写）+ 模拟参数 → 周推进日清模拟。
对齐 SBX-OPS 状态机语义：Phase0(准入) → P0(实验) → P1(评估) → Exit(出盒)/Closed。

用法:
  python -m dca_sandbox.cli run --weeks 13 --seed 20260908 [--notarize]

纪律: 全 SIMULATED（ID92）；0 真实资金流；0 配置权真实调用；红线审计（违例→BLOCKED）。
"""
from .engine import (
    DcaSandboxSimulation,
    MerchantConfig,
    WeeklyResult,
    SandboxRunResult,
    WEEK_RUN,
    NUCLEAR_RATE_TARGET,
    NUCLEAR_RATE_CONSEC_WEEKS,
    CCA_RESPONSE_TARGET,
    ACTIVATION_THRESHOLD,
    ST_PHASE0,
    ST_P0,
    ST_P1,
    ST_EXIT,
    ST_CLOSED,
)

__all__ = [
    "DcaSandboxSimulation",
    "MerchantConfig",
    "WeeklyResult",
    "SandboxRunResult",
    "WEEK_RUN",
    "NUCLEAR_RATE_TARGET",
    "NUCLEAR_RATE_CONSEC_WEEKS",
    "CCA_RESPONSE_TARGET",
    "ACTIVATION_THRESHOLD",
    "ST_PHASE0",
    "ST_P0",
    "ST_P1",
    "ST_EXIT",
    "ST_CLOSED",
]
