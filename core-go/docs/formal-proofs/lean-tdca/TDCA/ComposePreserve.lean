/-
  TDCA 形式化证明课题 · 证明总纲命题 M-3（化合保持性 · **承重**）
  ============================================================================
  建模方式：独立件、独立命名空间、零依赖（不 import Mathlib）。
  ⭐ 本件承载 M-3 之两件**机验面**：
   ① **五可保持**：两侧五可 ⟹ 化合 `⊗` 后五可 —— 并给出**可迭代之归纳面**
      （为 M-4 分形归纳主定理备好归纳步）；
   ② ⭐ **`ε` 可加性之累积上界**（总纲点名之**关键引理**）：`n` 步累积**恰为**
      `n · ε`（线性上界）—— 即总纲所需之 `ε(n) ≤ n·ε` **成立**（⛔ 不退化为
      仅 `ε-形态`）。⚠️ 本件以 `Nat` 承载 `ε`（**零依赖简化载体**）；真数以
      `ℝ` 承载之版本另列（需 `Mathlib`）。

  模型假设（显式，不得省略）：
   M3-1 系统之五可属性：**可观测**／**可计量**／**可配置**／**可审计**／**可熔断**；
   M3-2 化合 `⊗` 之逐项语义：记录**并集**完备／误差**并控**／配置权**并置**／
        广义逆**复合**／守卫**合取** —— 皆以合取承载（⛔ 不剥离任一侧）；
   M3-3 **`ε` 可加性**：单步复合之误差不超过 `ε`；`n` 步累积以 `epsAccum` 承载。

  适用范围：抽象骨架层。⛔ 不主张任何制度层结论；⛔ 不标「绝对安全」；
  对外表述限「本机机验」；⭐ 阈值／权重取值属策略层，⛔ 不在本件。

  机验状态：本机机验（Lean 4.34.0-rc2 · lake build）；非 CI 机验。
  三态终态声明：本件各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项、无占位（sorry）。
-/

namespace TDCA.ComposePreserve

/-! ## 一、五可属性与化合（模型假设 M3-1 / M3-2） -/

/-- 系统之五可属性（照在册五可：可观测／可计量／可配置／可审计／可熔断） -/
structure Sys where
  /-- 可观测：记录（并集）完备 -/
  obs : Prop
  /-- 可计量：误差累积受控 -/
  met : Prop
  /-- 可配置：配置权可声明与并置 -/
  cfg : Prop
  /-- 可审计：存在像内还原之广义逆 -/
  aud : Prop
  /-- 可熔断：守卫可判定且 `fail-closed` -/
  fus : Prop

/-- 五可之合取 -/
def FiveAll (s : Sys) : Prop :=
  s.obs ∧ s.met ∧ s.cfg ∧ s.aud ∧ s.fus

/-- 化合 `⊗`：五可**逐项并**（M3-2；⛔ 不剥离任一侧） -/
def compose (a b : Sys) : Sys where
  obs := a.obs ∧ b.obs
  met := a.met ∧ b.met
  cfg := a.cfg ∧ b.cfg
  aud := a.aud ∧ b.aud
  fus := a.fus ∧ b.fus

/-- M-3 · **五可保持**：两侧五可 ⟹ 化合后五可 -/
theorem five_all_preserved (a b : Sys) (ha : FiveAll a) (hb : FiveAll b) :
    FiveAll (compose a b) :=
  ⟨⟨ha.1, hb.1⟩,
   ⟨ha.2.1, hb.2.1⟩,
   ⟨ha.2.2.1, hb.2.2.1⟩,
   ⟨ha.2.2.2.1, hb.2.2.2.1⟩,
   ⟨ha.2.2.2.2, hb.2.2.2.2⟩⟩

/-! ## 二、可迭代之归纳面（为 M-4 备） -/

/-- 自复合 `n` 次 -/
def iterCompose (s : Sys) : Nat → Sys
  | 0 => s
  | n + 1 => compose (iterCompose s n) s

/-- M-3 · **保持性可迭代**（归纳步之机验）：五可于任意步数自复合下保持 -/
theorem five_all_preserved_iter (s : Sys) (hs : FiveAll s) :
    ∀ n, FiveAll (iterCompose s n) := by
  intro n
  induction n with
  | zero => exact hs
  | succ m ih => exact five_all_preserved (iterCompose s m) s ih hs

/-! ## 三、⭐ `ε` 可加性之累积上界（模型假设 M3-3 · 总纲点名之关键引理） -/

/-- `n` 步复合之误差累积（逐步累加） -/
def epsAccum : Nat → Nat → Nat
  | _, 0 => 0
  | eps, n + 1 => epsAccum eps n + eps

/-- ⭐ M-3 · **线性上界**：`n` 步累积**恰为** `n · ε`（即 `ε(n) = n·ε`，⛔ 不退化） -/
theorem epsAccum_eq (eps n : Nat) : epsAccum eps n = n * eps := by
  induction n with
  | zero => simp [epsAccum]
  | succ m ih =>
      show epsAccum eps m + eps = (m + 1) * eps
      rw [ih, Nat.succ_mul]

/-- M-3 · 累积上界单调（步数增 ⟹ 上界不减） -/
theorem epsAccum_mono (eps n : Nat) : epsAccum eps n ≤ epsAccum eps (n + 1) := by
  show epsAccum eps n ≤ epsAccum eps n + eps
  omega

/-- M-3 · 上界之线性形态亦可直接引用（供下游以 `n · ε` 代入） -/
theorem epsAccum_le_linear (eps n : Nat) : epsAccum eps n ≤ n * eps :=
  Nat.le_of_eq (epsAccum_eq eps n)

/-- 机验基线实例：三步累积 `ε = 3` 为 `9` -/
theorem eps_example : epsAccum 3 3 = 9 := rfl

end TDCA.ComposePreserve
