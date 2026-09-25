# -*- coding: utf-8 -*-
"""冷启动缔约滚动任务 · 生产驱动 (GSEQ-0547)
=========================================================
复用 v3 M1 机制(零新核心逻辑): 直接驱动 run_coldstart_threephase.main()
全链路(扫描→评估→准入→沙盒→生产)。仅做 sys.path 校正(修复 docs/ 层级导致的
相对路径错位), 不改动任何核心逻辑。

护栏(由运行环境/操作者施加, 详见 GSEQ-0547 指令):
  预算 ¥100 余额内(超限即停+报告) | ≤2 条/周/目标 | 拒绝零容忍转向 |
  mixed 口径 | 凭证零落盘 | NCA 走 generate_nca(max+1, GSEQ-0551) | NSFL 先于一切。

周期报告: 落 COLDSTART-EXPERIMENT-REPORT.md, 并入 obs-daily 08:07 简报(缔约结果段)。
"""
import os
import sys
from pathlib import Path

# 仓库根：TDCA_REPO_ROOT 覆盖优先；默认按本文件位置 parents[3] 探测（coldstart→cognitive-compiler→docs→根）
REPO = Path(os.environ["TDCA_REPO_ROOT"]).expanduser().resolve() if os.environ.get("TDCA_REPO_ROOT") else Path(__file__).resolve().parents[3]
if not (REPO / "docs" / "cognitive-compiler").is_dir():
    raise SystemExit("[FAIL] 仓库根探测失败: %s（可用 TDCA_REPO_ROOT 覆盖）——不静默空跑" % REPO)
_CC = os.path.join(REPO, "docs", "cognitive-compiler")
_SIM = os.path.join(_CC, "simulations", "multilateral_search_match")

for p in (_CC, _SIM, os.path.join(REPO, "config"), os.path.join(REPO, "nca-generator")):
    if p not in sys.path:
        sys.path.insert(0, p)

import run_coldstart_threephase as C


if __name__ == "__main__":
    C.main()
