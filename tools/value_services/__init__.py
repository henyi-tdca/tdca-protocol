"""value_services · TDCA 增值服务包统一入口（cog_align + util_value + merchant_loop 打包）

将 cog_align（认知对齐评测）+ util_value（效用价值评估）+ merchant_loop（商家消费权益循环）
打包为增值服务包，提供统一 CLI 入口与版本信息
（cog_align/ util_value M2 双服务先例 + merchant_loop M1 并入，DCD-MERCHANT-LOOP-001 §四）。

用法:
  python -m value_services cog-align measure --a A --state-a <json> --b B --state-b <json>
  python -m value_services util-value assess --asset <id> --tx <json>
  python -m value_services merchant-loop publish --config <yaml> [--notarize]
  python -m value_services merchant-loop roi-report --benefit-id <id> --merchant-id <id> \
      --budget <n> --audience <n>
  python -m value_services --version
"""
from __future__ import annotations

import sys
from typing import Optional

VERSION = "3.0.0-M1"
SERVICES = {
    "cog-align": "认知对齐评测（不对称认知对齐/场景包/对齐度分档）",
    "util-value": "效用价值评估（U_observed 地板/五阶分层/入表服务）",
    "merchant-loop": "商家消费权益循环（权益发布/核销闭环/ROI 三情景仪表盘）",
}

__all__ = ["VERSION", "SERVICES"]


def main(argv: Optional[list] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("用法: python -m value_services <cog-align|util-value|merchant-loop> <cmd> [args]")
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
    if service == "merchant-loop":
        from merchant_loop.cli import main as merchant_main
        return merchant_main(argv)
    print(f"未知服务: {service}（可选: cog-align / util-value / merchant-loop）")
    return 2


if __name__ == "__main__":
    sys.exit(main())
