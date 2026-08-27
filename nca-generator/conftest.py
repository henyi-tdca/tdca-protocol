# -*- coding: utf-8 -*-
"""使测试可从仓库根目录直跑：python -m pytest nca-generator/"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
