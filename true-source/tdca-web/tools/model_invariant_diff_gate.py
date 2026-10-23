# -*- coding: utf-8 -*-
"""
L1SI167-MODEL-INVARIANT-CI-001 乙档强制门禁 · PR 改动面静态检查。

用法（CI 批次或本地）：
    python tools/model_invariant_diff_gate.py <changed_file> [more ...]

退出码：
    0 — 未触发：判定路径无模型客户端调用（打印「前置守卫·未触发」）
    1 — 触发乙档：某 PR 使判定路径引入模型参与 ⟹ 该 PR 升强制门禁
       （须同卡双模型五字段三次一致，未过 ⛔ 合并）

判据（CI 令 §三）：改动文件若在判定路径模块清单内、且出现模型客户端
标记 ⟹ 触发。清单与标记与 tests/test_model_invariant_guard.py 同源维护。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import sys
from pathlib import Path

JUDGMENT_MODULES = {
    "api_v1.py",
    "agent_channel_ops.py",
    "agent_channel_deposit_ops.py",
}
MODEL_CLIENT_MARKERS = [
    "openai", "anthropic", "dashscope", "litellm",
    "openrouter", "zhipuai", "moonshot", "ollama",
]


def main(argv: list[str]) -> int:
    hits: list[str] = []
    for arg in argv[1:]:
        p = Path(arg)
        if p.name not in JUDGMENT_MODULES or not p.exists():
            continue
        low = p.read_text(encoding="utf-8", errors="replace").lower()
        for m in MODEL_CLIENT_MARKERS:
            if m in low:
                hits.append(f"{p.name}: 模型客户端标记 `{m}`")
    if hits:
        print("⛔ 乙档门禁触发：判定路径引入模型参与，该 PR 升强制门禁"
              "（同卡双模型五字段三次一致，未过 ⛔ 合并）")
        for h in hits:
            print(" -", h)
        return 1
    print("前置守卫·未触发：判定路径无模型客户端调用（改动面："
          + (", ".join(argv[1:]) or "（空）") + "）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
