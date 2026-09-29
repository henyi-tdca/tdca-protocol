# -*- coding: utf-8 -*-
"""
TDCA-NS-RUNTIME-001 · SEA Runtime 级负空间防护 M1（Layer 1 物理叠加层）
======================================================================
Layer 1 四模块（6 周紧急补丁，SEA 最短防护前置）:
  L1-R1  静态负空间清单 V2.0    —— 法律负空间 100%（不可变配置表）
  L1-R2  调用签名黑名单         —— 已知攻击模式 95%+（NCA 审计历史指纹库）
  L1-R3  MOU 预计算拦截器       —— 经济负空间 100%（T(y_t)>0 锚定预计算）
  L1-R4  负空间熔断器 v0.5      —— 运行时异常防护（Blocked 第四态另行论证，见 docs/）

锚定:
  - DCD-NS-RUNTIME-001（已签批立项，M1 Layer 1 独立先行 6 周）
  - TDCA-NS-RUNTIME-001 立项方案（L1-R1~R4 规格 + A-1~6 验收）
  - NSFL-ACCEL-REF-001 §3.1（Layer 1 物理叠加细节，参考稿）
  - TDCA-ID-VERIFY-001（ID93 不引用 / 四符号 / ID89 第四态待论证）
  - tdca-fos/tdca_nsfl/fuse_engine.py（FuseType 5 类，LEGAL alt=∅ 对齐）
  - TDCA-TERMINOLOGY-REGISTRY V1.1（G-1 基线）

纪律（M1 红线）:
  - BV-3: 清单/黑名单/拦截器均只读（不可变配置 + 输出验证）
  - F-4: AI 无权自动修改负空间清单；升级权保留人类
  - MOU 不可降: 每层有 MOU 验证点（L1-R3 即锚定点）
  - 人类签名权: SEA 自我进化人类一票否决（HUF）
  - ID 纪律: ID93 不引用；裸 S 用四符号（S_agent_cog 等）

SPDX-License-Identifier: TDCA-Internal
"""
from .static_list import StaticNegativeSpaceList, StaticListCheckResult, NSListEntry
from .blacklist import CallSignatureBlacklist, BlacklistMatchResult, BlacklistFingerprint
from .mou_precompute import MOUPrecomputeInterceptor, MOUPrecomputeResult, MOUAnchor
from .breaker_v05 import NegativeSpaceBreakerV05, BreakerState, BreakerVerdict
from .runtime import Layer1Runtime, Layer1CheckResult, Layer1Verdict
from .sensor import NSBoundarySensor, SensorVerdict
from .ns_atlas import NSAtlas, AtlasPoint, AtlasQueryResult
from .contract_anchor import NSFLContractAnchor, ContractVerdict
from .nia_macm import NIAMACMIntegrator, NIAResult
from .sandbox_compliance import SandboxCompilePipeline, SandboxCompiledNCA

__all__ = [
    "StaticNegativeSpaceList",
    "StaticListCheckResult",
    "NSListEntry",
    "CallSignatureBlacklist",
    "BlacklistMatchResult",
    "BlacklistFingerprint",
    "MOUPrecomputeInterceptor",
    "MOUPrecomputeResult",
    "MOUAnchor",
    "NegativeSpaceBreakerV05",
    "BreakerState",
    "BreakerVerdict",
    "Layer1Runtime",
    "Layer1CheckResult",
    "Layer1Verdict",
    "NSBoundarySensor",
    "SensorVerdict",
    "NSAtlas",
    "AtlasPoint",
    "AtlasQueryResult",
    "NSFLContractAnchor",
    "ContractVerdict",
    "NIAMACMIntegrator",
    "NIAResult",
    "SandboxCompilePipeline",
    "SandboxCompiledNCA",
]

__version__ = "0.1.0"
