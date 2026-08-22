"""value_services · TDCA 增值服务包统一入口（M2 双服务打包）

将 cog_align（认知对齐评测）+ util_value（效用价值评估）打包为增值服务包，
提供统一 CLI 入口与版本信息（M2 双服务打包，DCD-COG-ALIGN-001 §七 + DCD-UTIL-VALUE-001 §七）。

用法:
  python -m value_services cog-align measure --a A --state-a <json> --b B --state-b <json>
  python -m value_services util-value assess --asset <id> --tx <json>
  python -m value_services cog-align scenario --scenario tiering --a A --state-a <json> --b B --state-b <json>
  python -m value_services util-value entry --asset <id> --tx <json> --period 2026-08
  python -m value_services --version
"""
from __future__ import annotations

import sys
from typing import Optional

VERSION = "2.0.0-M2"
SERVICES = {
    "cog-align": "认知对齐评测（不对称认知对齐/场景包/对齐度分档）",
    "util-value": "效用价值评估（U_observed 地板/五阶分层/入表服务）",
}

__all__ = ["VERSION", "SERVICES"]


def main(argv: Optional[list] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("用法: python -m value_services <cog-align|util-value> <cmd> [args]")
        print(f"增值服务包 v{VERSION} ｜ 服务: {', '.join(SERVICES)}")
        return 2
    if argv[0] == "--version":
        print(f"value_services {VERSION}")
        return 0

    service = argv.pop(0)
    if service == "cog-align":
        from cog_align.cli import main as cog_main
        return cog_main(argv)
    if service == "util-value":
        from util_value.cli import main as util_main
        return util_main(argv)
    print(f"未知服务: {service}（可选: cog-align / util-value）")
    return 2


if __name__ == "__main__":
    sys.exit(main())
