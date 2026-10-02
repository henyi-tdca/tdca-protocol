/-
  TDCA 形式化证明课题 · 协调原理簇（COORD）· 第一批之三 · COORD-5（回议发散定理）
  ============================================================================
  建模方式：独立件、独立命名空间、零依赖（不 import Mathlib）。
  ⭐ 本件取「必要性方向」（构造性）：由「重开无界」推「不存在静默轮」。
  ⚠️ 反方向（「重开有界 ⟹ 存在静默轮」）需经典逻辑（排中律）——本件 ⛔ 不收，
  按「收窄不硬证」另列后续批次，⛔ 不以本件冒充双向等价。
  ⚠️ 期望发散（材料原文以概率 p > 0 表述）需概率论；本件给出其结构面
  （无吸收态 ⇒ 完成轮次无上界），⛔ 不以结构面冒充概率陈述。

  模型假设（显式，不得省略）：
   R1 「重开」建模为轮次谓词 reopen : Nat → Prop（第 k 轮可否重开已决议题）；
   R2 「自 N 起静默」＝ SilentFrom reopen N（第 N 轮及以后不再重开）——
      即停机保证的机验面；
   R3 「重开无界」＝ ReopenUnbounded reopen（任意轮次之后仍存在可重开之轮）——
      即无停机档位的机验面。

  陈述：若执行层可重开已决议题且重开无界（R3），则不存在任何轮次之后
  恒静默（¬ ∃ N, SilentFrom reopen N）——即「已决议」不是吸收态，
  任务完成轮次无上界（与在册 ID84 协作停机定理之必要性方向对应：
  无停机档位 ⟹ 无有限吸收；TDCA 构造在制度面排除该前提 ⟹ 收敛性成立）。

  适用范围：抽象结构骨架层。⛔ 不主张任何制度层结论；⛔ 不标「绝对安全」；
  对外表述限「本机机验」。

  机验状态：本机机验（Lean 4.34.0-rc2 · lake build）；非 CI 机验。
  三态终态声明：本件各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项、无占位（sorry）。
-/

namespace TDCA.CoordReopen

/-- 「自 N 起静默」：第 N 轮及以后不再重开已决议题（＝停机保证之机验面） -/
def SilentFrom (reopen : Nat → Prop) (N : Nat) : Prop :=
  ∀ k, N ≤ k → ¬ reopen k

/-- 「重开无界」：任意轮次之后仍存在可重开之轮（＝无停机档位之机验面） -/
def ReopenUnbounded (reopen : Nat → Prop) : Prop :=
  ∀ n, ∃ k, n ≤ k ∧ reopen k

/-- COORD-5 · 必要性方向（构造性）：重开无界 ⟹ 不存在静默轮
    —— 「已决议」非吸收态，完成轮次无上界 -/
theorem coord5_unbounded_no_silent (reopen : Nat → Prop) (hunb : ReopenUnbounded reopen) :
    ¬ ∃ N, SilentFrom reopen N := by
  intro h
  obtain ⟨N, hN⟩ := h
  obtain ⟨k, hk, hrk⟩ := hunb N
  exact hN k hk hrk

/-- COORD-5 · 直陈面：重开无界 ⟹ 任意给定轮次之后仍可重开 -/
theorem coord5_beyond_any_round (reopen : Nat → Prop) (hunb : ReopenUnbounded reopen)
    (n : Nat) : ∃ k, n ≤ k ∧ reopen k :=
  hunb n

/-- 机验基线实例：恒真重开（每轮皆可重开）⟹ 不存在静默轮 -/
theorem coord5_example : ¬ ∃ N, SilentFrom (fun _ : Nat => True) N :=
  coord5_unbounded_no_silent (fun _ : Nat => True) (fun n => ⟨n, Nat.le_refl n, trivial⟩)

end TDCA.CoordReopen
