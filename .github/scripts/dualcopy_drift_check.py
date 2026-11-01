# -*- coding: utf-8 -*-
"""DUALCOPY-FIX-001 漂移门：11 组双副本同路径内容比对。

级别：WARN（有差异只报告、不阻断合并）；但工具上架前须清零（令面步 2 口径）。
口径：仅比较双侧同路径文件内容（字节级）；__pycache__ 不计；
      tools/ 侧独有件与主线侧独有件不在本门范围（属发布位结构事项，另册管理）。
退出码恒 0（WARN 级）。
"""
import filecmp
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GROUPS = [
    ("tools/cog_align", "tdca-toolchain/cog_align"),
    ("tools/cypress_pool", "tdca-toolchain/cypress_pool"),
    ("tools/flow-orchestrator", "tdca-flow-orchestrator"),
    ("tools/maka_nca", "tdca-toolchain/maka_nca"),
    ("tools/merchant_loop", "tdca-toolchain/merchant_loop"),
    ("tools/paperclip_nca", "tdca-toolchain/paperclip_nca"),
    ("tools/pi_nca", "tdca-toolchain/pi_nca"),
    ("tools/util_value", "tdca-toolchain/util_value"),
    ("tools/value_services", "tdca-toolchain/value_services"),
    ("tools/thingsboard_pool", "tdca-toolchain/thingsboard_pool"),
    ("tools/dca_sandbox", "tdca-toolchain/dca_sandbox"),
]


def main() -> int:
    drift = []
    for t, m in GROUPS:
        t_dir = os.path.join(REPO, t)
        m_dir = os.path.join(REPO, m)
        if not os.path.isdir(t_dir) or not os.path.isdir(m_dir):
            drift.append(f"[MISS] 组缺失目录：{t} 或 {m}")
            continue
        for root, _dirs, files in os.walk(t_dir):
            if "__pycache__" in root:
                continue
            for fn in files:
                rel = os.path.relpath(os.path.join(root, fn), t_dir)
                f_t = os.path.join(t_dir, rel)
                f_m = os.path.join(m_dir, rel)
                if os.path.isfile(f_m) and not filecmp.cmp(f_t, f_m, shallow=False):
                    drift.append(f"[DRIFT] {t}/{rel} ≠ {m}/{rel}")
    if drift:
        print(f"DUALCOPY_DRIFT WARN：{len(drift)} 处同路径差异（WARN 级不阻断；上架前须清零）")
        for line in drift:
            print(line)
    else:
        print("DUALCOPY_DRIFT CLEAN：11 组同路径差异 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
