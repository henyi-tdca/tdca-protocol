# -*- coding: utf-8 -*-
"""pytest 配置：将项目根 + 编译器包根加入 sys.path（顶层包导入模式，同 tdca-fos 惯例）。"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))          # .../tdca-ns-runtime
_COMPILER = os.path.join(os.path.dirname(_ROOT), "tdca-nsfl-compiler")  # .../tdca-nsfl-compiler
for p in (_ROOT, _COMPILER):
    if p not in sys.path:
        sys.path.insert(0, p)
