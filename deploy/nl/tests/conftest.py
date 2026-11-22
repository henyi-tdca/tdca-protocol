# -*- coding: utf-8 -*-
"""CIFIX-001（L1SI226）测试装置：nl_service 之 enforce_entry 单一事实源在仓内
`tools/enforce_entry.py`（与 tools/mcp_bridge/fuse.py 同一引用面，注释见
nl_service.py L27「NSFL 单一事实源（与 mcp 桥同一文件）」）。

pytest 只把 tests/ 所在目录及其祖先 conftest 目录加入 sys.path，`tools/` 不在
其列 ⟹ 收集期 `from enforce_entry import scan_nsfl_text` 即 ModuleNotFound。
本装置按**仓库相对定位**（⛔硬编码绝对路径）把 `<repo>/tools` 加入 sys.path，
纯导入路径修复：不改被测代码语义、不改断言、不 skip。
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_TOOLS = Path(__file__).resolve().parents[3] / "tools"

if _REPO_TOOLS.is_dir():
    sys.path.insert(0, str(_REPO_TOOLS))
