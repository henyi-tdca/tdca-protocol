# -*- coding: utf-8 -*-
"""pytest 路径配置：集成测试可同时 import cscp_gateway 与 nsfl_union（跨项目依赖注入）。"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]                      # tdca-cscp/
_D2 = Path(__file__).resolve().parents[2] / "tdca-d2-union"      # tdca-d2-union/
_TM = Path(__file__).resolve().parents[2] / "tdca-translator-market"  # W4 翻译器市场
_WB = Path(__file__).resolve().parents[2] / "tdca-workbuddy"     # P5 Workbuddy

for _p in (_ROOT, _D2, _TM, _WB):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
