"""tdca-cls · 闭环结算引擎（R-CLS-5 E-1 原型）

CLS 结算引擎：GIM-OnCycle（R-CLS-3）+ RTN 净额（R-CLS-2）+ DPI 状态机（R-CLS-1）+ DVP 模拟（T-035）
铁律: CLS 算法 FROZEN 不变（R-CLS-1/2/3/4 M4 ACCEPT）；MICROTAX 只读复用（适配器层 E-2 接入）
"""
__version__ = "0.1.0"
