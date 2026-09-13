-- TDCA 形式化证明课题 · M1 Lean 工程
-- 状态：SKELETON——**本工程无 Lean 工具链（lean/lake/elan 均不可用），全部内容未经机器验证**
-- 工具链：lean-toolchain = leanprover/lean4:v4.34.0-rc2（与本目录 lean-toolchain 文件一致）
-- 依赖：Mathlib（与既有形式化先例一致的库面）
import Lake
open Lake DSL

package «tdca-formal» where
  -- M1 目标：M-0 / M-1 / M-2 的形式化（见 TDCA/MetaInverse.lean）
  -- 版本锁定与依赖镜像待与 CI 统一（挂账，见 README「机验状态」）

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git"

@[default_target]
lean_lib TDCA where
  roots := #[`TDCA]
