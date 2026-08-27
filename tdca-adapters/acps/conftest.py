# -*- coding: utf-8 -*-
"""使 tests 可从仓库根目录直接运行：python -m pytest tdca-adapters/acps/tests/"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
