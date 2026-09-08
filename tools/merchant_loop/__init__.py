"""merchant_loop · 商家消费权益循环增值服务包（DCD-MERCHANT-LOOP-001 M1 工具包）

四模块（DCD §二 功能规格）:
  1. engine    权益函数模板（发布校验/六要素声明/核销闭环/CCA 贡献值记账预留）
  2. notary    核销流水/权益发布 NCA 存证（NCA-MERCHANTLOOP-*，ID92 provenance）
  3. roi       ROI 三情景仪表盘（悲观/中性/乐观——预算平移对照，剔除资产升值因子）
  4. cli       `python -m merchant_loop.cli publish --config <yaml>` + `redeem` + `roi-report`

用法:
  python -m merchant_loop.cli publish --config benefit.yaml [--notarize]
  python -m merchant_loop.cli redeem --benefit benefit.yaml --event event.json [--notarize]
  python -m merchant_loop.cli roi-report --benefit-id B1 --merchant-id M1 --budget 10000 --audience 2000

制度边界（DCD §二）:
  双边消费交易（不进 CLS，T-027）｜ 无池/无杠杆/无升值承诺 ｜ 真实资金流 e-CNY 接入前全模拟态
"""
from .engine import (
    BenefitTemplate,
    RedemptionEvent,
    RedemptionResult,
    MerchantLoopEngine,
    FORBIDDEN_TERMS,
    SIX_ELEMENTS,
    SCENE_TYPES,
)
from .notary import MerchantLoopNotary
from .roi import (
    RoiReport,
    RoiScenarioResult,
    RoiService,
    DEFAULT_SCENARIOS,
)

__all__ = [
    "BenefitTemplate",
    "RedemptionEvent",
    "RedemptionResult",
    "MerchantLoopEngine",
    "FORBIDDEN_TERMS",
    "SIX_ELEMENTS",
    "SCENE_TYPES",
    "MerchantLoopNotary",
    "RoiReport",
    "RoiScenarioResult",
    "RoiService",
    "DEFAULT_SCENARIOS",
]
