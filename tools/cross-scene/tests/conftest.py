# SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-
"""W3 测试路径配置：跨项目依赖（nsfl_union D-2 引擎联调）。"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]                      # tdca-cross-scene/
_D2 = Path(__file__).resolve().parents[2] / "tdca-d2-union"      # tdca-d2-union/

for _p in (_ROOT, _D2):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
