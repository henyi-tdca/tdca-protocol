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
