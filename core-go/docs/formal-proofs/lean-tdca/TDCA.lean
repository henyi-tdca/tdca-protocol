-- Root module for the TDCA library (aggregates submodules).
-- 本工程骨架补齐（M3-b 同期）：外部机验 M1 机验首跑报错 `no such file or directory: TDCA.lean`
-- ——lakefile 的 `@[default_target] lean_lib TDCA` 要求库根模块存在（核证差异回灌）。
-- M3-d 补齐（2026-09-13，缺陷 D-3）：新增 `import TDCA.Induction`
-- ——原版仅 4 个 import，致 `lake build` 默认目标**不覆盖 M3-d 件**（V2 机验暴露；外部执行未擅动、如实登记）。
import TDCA.Basic
import TDCA.MetaInverse
import TDCA.Compose
import TDCA.EpsAdd
import TDCA.Induction
-- M-8 Lean 化（2026-09-14）：新增 `import TDCA.SceneEmergence`
-- ——场景形成机制可机验子集 F-1~F-6（命题 M-8.1~M-8.6）。
import TDCA.SceneEmergence
-- 公理 6 证明器通道（2026-09-14）：新增 `import TDCA.Axiom6`
-- ——四约束形式化（约束 1 / 2 归位自 TDCA.MetaInverse；约束 3 为甲′ 形态，非空前提见该件头注）。
import TDCA.Axiom6
-- 公理 6 · 约束 4 条件形态附录（2026-09-14）：新增 `import TDCA.Axiom6Complexity`
-- ——复杂度以建模参数进入、约束以假设形式给出、结论标 conditional；⛔ 不得读作已从程序推出。
import TDCA.Axiom6Complexity
-- 准入守卫（2026-09-23）：新增 `import TDCA.Admission`
-- ——N-3 制度准入状态机（七态）＋ N-2 信任根分级↔场景密级（fail-closed），共用骨架一次建模双用；
-- 本机机验 exit 0、零 sorry；模型假设与适用范围见件头（A1–A5／B1–B5）。
import TDCA.Admission
-- 失效半径有界性（2026-09-23）：新增 `import TDCA.FailureRadius`
-- ——N-1 信任链分支结构（向下传导、向上隔离；单点失效≠全网重置），零依赖刻画式件；
-- 本机机验 exit 0、零 sorry；模型假设与适用范围见件头（A1–A5）。
import TDCA.FailureRadius
-- 负空间迁移不变量（2026-09-23）：新增 `import TDCA.NegativeSpace`
-- ——N-6 负空间（底线）之修订：底线只增不减、迁移不删除（出处有落）、签批留痕、再修订保持；
-- 本机机验 exit 0、零 sorry；模型假设与适用范围见件头（A1–A6）。
import TDCA.NegativeSpace
