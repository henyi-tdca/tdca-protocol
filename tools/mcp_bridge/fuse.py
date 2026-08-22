# FC-ID: DCD-MCP-BRIDGE-001 | 模块 2 NSFL 熔断预检（复用 enforce_entry R10 单一事实源）
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from enforce_entry import scan_nsfl_text  # noqa: E402  单一事实源：禁词表 + 行级否定豁免


def precheck(arguments: dict, fuse_log: Path) -> tuple:
    """调用参数过 NSFL 负空间扫描。
    返回 (放行?, 命中清单)。命中 → 落熔断日志（绝不静默通过）。
    """
    import json
    text = json.dumps(arguments, ensure_ascii=False)
    hits = scan_nsfl_text(text)
    if hits:
        fuse_log.parent.mkdir(parents=True, exist_ok=True)
        with fuse_log.open("a", encoding="utf-8") as f:
            f.write(f"[SIMULATED] {datetime.now(timezone.utc).isoformat()} | "
                    f"mcp-bridge 熔断 | 命中 {hits} | 参数摘要 {text[:80]}\n")
        return False, hits
    return True, []
