# -*- coding: utf-8 -*-
"""DUALCOPY-FIX-001 漂移门：11 组双副本同路径内容比对。

级别：11 组工具链对为 WARN（有差异只报告、不阻断合并；工具上架前须清零，
令面 DUALCOPY-FIX-001 步 2 口径）；第 12 组（tdca-utility-genie 对）为
阻断级（INVSOLVER-README-001 第 3 事）：该组新增同路径漂移一律退出码 1。
口径：仅比较双侧同路径文件内容（字节级）；__pycache__ 不计；
      两侧独有件不在本门范围（属发布位结构事项，另册管理）。
既有历史漂移：先报清单后议——列入 HISTORICAL_EXEMPT 的条目只报告不阻断；
      豁免清单外的新漂移在阻断组即失败。
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

# 阻断组（INVSOLVER-README-001 第 3 事）：新增漂移阻断合并。
BLOCKING_GROUPS = [
    ("tdca-utility-genie", "true-source/tdca-web/tdca-utility-genie"),
]

# 既有历史漂移豁免清单（2026-11-07 实测登记，先报清单后议；
# 清单外新漂移在阻断组即退出码 1）。键为组第一侧内相对路径。
HISTORICAL_EXEMPT = {
    ("tdca-utility-genie", "true-source/tdca-web/tdca-utility-genie"): {
        "README.md",
        "examples/example_merchant_optimization.yaml",
        "examples/example_resource_allocation.yaml",
    },
}


def collect(t: str, m: str):
    out = []
    t_dir = os.path.join(REPO, t)
    m_dir = os.path.join(REPO, m)
    if not os.path.isdir(t_dir) or not os.path.isdir(m_dir):
        return [f"[MISS] 组缺失目录：{t} 或 {m}"]
    for root, _dirs, files in os.walk(t_dir):
        if "__pycache__" in root:
            continue
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), t_dir)
            rel = rel.replace(os.sep, "/")  # 统一正斜杠，豁免清单跨平台可命中
            f_t = os.path.join(t_dir, rel)
            f_m = os.path.join(m_dir, rel)
            if os.path.isfile(f_m) and not filecmp.cmp(f_t, f_m, shallow=False):
                out.append(rel)
    return out


def main() -> int:
    drift = []
    for t, m in GROUPS:
        for rel in collect(t, m):
            drift.append(f"[DRIFT] {t}/{rel} ≠ {m}/{rel}")
    if drift:
        print(f"DUALCOPY_DRIFT WARN：{len(drift)} 处同路径差异（WARN 级不阻断；上架前须清零）")
        for line in drift:
            print(line)
    else:
        print("DUALCOPY_DRIFT CLEAN：11 组同路径差异 0")

    blocked = []
    exempted = []
    for t, m in BLOCKING_GROUPS:
        ex = HISTORICAL_EXEMPT.get((t, m), set())
        for rel in collect(t, m):
            if rel in ex:
                exempted.append(f"[EXEMPT-HIST] {t}/{rel} ≠ {m}/{rel}（历史漂移·清单在案·后议）")
            else:
                blocked.append(f"[DRIFT-BLOCK] {t}/{rel} ≠ {m}/{rel}")
    if exempted:
        print(f"DUALCOPY_DRIFT 历史豁免：{len(exempted)} 处（只报告不阻断，清单后议）")
        for line in exempted:
            print(line)
    if blocked:
        print(f"DUALCOPY_DRIFT BLOCK：阻断组新增漂移 {len(blocked)} 处（退出码 1）")
        for line in blocked:
            print(line)
        return 1
    print("DUALCOPY_DRIFT 阻断组：新增漂移 0（历史豁免另列）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
