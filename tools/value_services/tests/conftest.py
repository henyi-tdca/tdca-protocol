# SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-
"""Test path setup: make the sibling tool package importable."""
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[2]  # tools/
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
