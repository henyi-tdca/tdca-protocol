# -*- coding: utf-8 -*-
"""使测试可从仓库根目录直跑：python -m pytest nca-generator/（含 config/ 依赖路径）"""
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here))
sys.path.insert(0, str(_here.parent / "config"))
