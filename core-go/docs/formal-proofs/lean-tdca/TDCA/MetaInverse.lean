/-
  TDCA 形式化证明课题 · M1 · M-0 / M-1 / M-2
  ============================================================================
  归属：本课题（M1）｜ 对应：输入件《形式化证明总纲》§二 命题体系
  状态：SKELETON——**未经机器验证**（本工程无 Lean 工具链）
        · 本文件证明体为**尝试**，任一行可能因 Lean/Mathlib 版本差异需微调；
        · 若某处不通过，**必须显式留 `sorry`** 并登记义务（**不得**伪造通过，例外程序）；
        · **禁止**在 README/存证中声称「sorry = 0」或「已证明」（除 CI 实测）。

  与既有先例（TDCA-CORE-GO-AXIOM6-001 / AXIOM6-PROOF）的关系：
    · 本骨架是公理 6「f / f⁻ / g」三角色的**抽象层重申**（f = InstFun、f⁻ = Verify、g = RightInv）；
    · 本骨架**不重复**既有 Go 断言（9 项 PASS）与框架级证明（定理 E.1~E.4）；
      其增量在于**独立的第二通道**（Lean）与**可机验的泛化陈述**。
-/
import Mathlib.Data.Real.Basic
import TDCA.Basic

namespace TDCA.MetaInverse

variable {D R : Type} [DecidableEq R]

/-! ## M-0 · 基例可审计性（`Verify` 完备性） -/

/-- **M-0**：若 `f x = some y`，则 `Verify f y x = true`。
    证明要点：`Verify` 重算 `f x` 得 `some y`，比对 `decide (y = y)` 恒真。 -/
theorem M0_verify_complete (f : D → Option R) (x : D) (y : R) (h : f x = some y) :
    Verify f y x = true := by
  simp [Verify, h]

/-! ## M-1 · 可靠性（`Verify` 通过 ⟹ 输出正确） -/

/-- **M-1**：`Verify f y x = true` ⟹ `f x = some y`。
    证明要点：分 `f x` 为 `none` / `some y'` 两支；`none` 支矛盾，`some` 支由 `decide` 真得 `y' = y`。 -/
theorem M1_verify_sound (f : D → Option R) (y : R) (x : D)
    (h : Verify f y x = true) : f x = some y := by
  cases hx : f x with
  | none => simp [Verify, hx] at h
  | some y' =>
      simp only [Verify, hx] at h
      have hy : y' = y := of_decide_eq_true h
      rw [hy]

/-! ## M-2 · 反射广义逆存在（两条正则性公理） -/

/-- **M-2**（构造性）：给定截面选择 `g`（在像集上满足还原），
    则反射广义逆的两条正则性公理成立：
      (i)  `∀ x y, f x = some y → f (g y) = some y`（对应 `Φ₀ G₀ Φ₀ = Φ₀`）
      (ii) `∀ y, (∃ x, f x = some y) → f (g y) = some y`（对应 `G₀ Φ₀ G₀ = G₀` 的像内形态）
    证明要点：均由 `hg` 直接给出；(ii) 由 (i) 消解存在量词。 -/
theorem M2_reflexive_inverse (f : D → Option R) (g : R → D)
    (hg : ∀ y x, f x = some y → f (g y) = some y) :
    (∀ x y, f x = some y → f (g y) = some y) ∧
    (∀ y, (∃ x, f x = some y) → f (g y) = some y) := by
  constructor
  · intro x y h
    exact hg y x h
  · intro y hx
    rcases hx with ⟨x, hx⟩
    exact hg y x hx

/-! ## 证伪尝试（**红队面**，本文件的自我削弱项） -/

/-- **非单射情形下「右逆存在但左逆不存在」**：
    给出反例构造——`x₁ ≠ x₂` 映到同一 `y`，则不存在左逆 `l`（`l ∘ f = id`）。
    意义：**M-2 只主张右逆**（公理 6 口径「右逆非左逆」），本定理把该边界**证在文件内**。 -/
theorem M2_no_left_inverse_when_non_injective
    (f : D → Option R) (x₁ x₂ : D) (y : R)
    (h₁ : f x₁ = some y) (h₂ : f x₂ = some y) (hne : x₁ ≠ x₂) :
    ¬ ∃ l : R → D, ∀ x z, f x = some z → l z = x := by
  intro ⟨l, hl⟩
  have hx1 : l y = x₁ := hl x₁ y h₁
  have hx2 : l y = x₂ := hl x₂ y h₂
  exact hne (hx1.symm.trans hx2)

end TDCA.MetaInverse

/-
  ────────────────────────────────────────────────────────────────────────────
  **证明义务清单（sorry 清零 checklist）** —— 首次机验前不得勾销：
   [1] `M0_verify_complete`：`simp [Verify, h]` 是否在目标 Mathlib 版本下直接关闭
       （备选：`rw [Verify, h]; simp` 或 `decide_eq_true_eq` 显式装配）；
   [2] `M1_verify_sound`：`cases hx : f x` + `simp only [Verify, hx] at h` 的消解写法
       是否成立（备选：`split at h` + `of_decide_eq_true`）；
   [3] `M2_no_left_inverse_when_non_injective`：`hl` 的返回形态与本文件的简化陈述是否一致
       （若需完整左逆定义含 `f (l z) = some z`，则加合取并调整结尾）；
   [4] 全部定理**均未机验**；`lake env lean` 与 `sorry` 计数为 CI 侧职责。
  ⚠️ 三态原则：若某条经机验为**不成立**，则**改述为 conditional 或输出反例**——
      **失败亦为合法终态**，不得伪造通过。
-/
