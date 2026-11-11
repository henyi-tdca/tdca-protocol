-- TDCA 形式化证明课题 · M1 Lean 工程
-- 状态：本机已机验（2026-09-22，Lean 4.34.0-rc2 / Lake 5.0.0-src，lake build EXIT=0、919 jobs、0 error）——**非 CI 机验**，对外仍不得称「已证明」（表述与机验纪律）
-- 工具链：lean-toolchain = leanprover/lean4:v4.34.0-rc2（与本目录 lean-toolchain 文件一致）
-- 依赖：Mathlib（与既有形式化先例一致的库面）
-- L1SI211-EXTERNAL-FIX-001 B：锁 revision（2026-09-22 机验同 rev，与 lean-toolchain
-- leanprover/lean4:v4.34.0-rc2 对齐；lake-manifest.json 同值可互核）——⛔ 悬空引 HEAD，
-- 保证 CI 形式化闸门跨环境可复现。
import Lake
open Lake DSL

package «tdca-formal» where
  -- M1 目标：M-0 / M-1 / M-2 的形式化（见 TDCA/MetaInverse.lean）
  -- 版本锁定与依赖镜像待与 CI 统一（挂账，见 README「机验状态」）

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "f508fa49b941037007135bdea650664f7aeb38cf"

@[default_target]
lean_lib TDCA where
  roots := #[`TDCA]
