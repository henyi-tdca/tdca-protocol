# -*- coding: utf-8 -*-
"""pytest 配置：将项目根 + Runtime 包根加入 sys.path（顶层包导入模式，同 tdca-fos 惯例）。"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))          # .../tdca-nsfl-compiler
_RUNTIME = os.path.join(os.path.dirname(_ROOT), "tdca-ns-runtime")  # .../tdca-ns-runtime
for p in (_ROOT, _RUNTIME):
    if p not in sys.path:
        sys.path.insert(0, p)
