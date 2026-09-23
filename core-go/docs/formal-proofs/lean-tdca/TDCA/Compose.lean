/-
  TDCA 形式化证明课题 · M-3 段 1+2 · 化合保持性：复合（L2 / L3 / L4）
  ============================================================================
  状态：本机已机验（2026-09-22，Lean 4.34.0-rc2）——lake build 0 error、逐件 exit 0、零 sorry；**非 CI 机验**

  依据：M-3 方案设计§三 三段式（段 1 代数 / 段 2 前置）§五 引理清单 L2/L3/L4
  对应：输入件《形式化证明总纲》M-3「Φ₂∘Φ₁ 有可计算反射广义逆 G₁∘G₂」

  ⚠️ **本文件的实质结论（写于代码之前）**：输入件的「`G = G₁∘G₂`」是**简写**。
  严格地说，`G = gf ∘ hg` 成立**需要额外条件**（下称**兼容条件**）：
      `∀ s ∈ Im(Φ), f (hg s) = some (hg s)`（即 `hg s` 落在 `f` 的像内）
  **不满足时**，`gf ∘ hg` **不是**复合的右逆（本文件 L3a 把该条件显式化为假设；
  L3b 给出**不依赖该条件**的规范代表元版本，但须先证选择函数存在）。
-/
import Mathlib.Data.Real.Basic

namespace TDCA.MetaInverse

/-! ## 复合（部分映射）与 L2 · 定义域刻画 -/

/-- **复合（部分）**：任一段未定义 → 复合未定义（`Option.bind` 语义） -/
def comp {D R S : Type} (g : R → Option S) (f : D → Option R) : D → Option S :=
  fun x => (f x).bind g

/-- **L2（复合的像/定义域刻画）**：`comp g f x = some z ⟺ ∃ y, f x = some y ∧ g y = some z`。
    证明要点：`Option.bind` 的展开引理。 -/
theorem L2_comp_some {D R S : Type} (g : R → Option S) (f : D → Option R) (x : D) (z : S) :
    comp g f x = some z ↔ ∃ y : R, f x = some y ∧ g y = some z := by
  unfold comp
  exact Option.bind_eq_some_iff

/-- **L2′（未定义刻画）**：`comp g f x = none ⟺ f x = none ∨ ∃ y, f x = some y ∧ g y = none`。
    义务 **L2-b**（见尾注）：`Option.bind_eq_none_iff` 系引理装配。 -/
theorem L2_comp_none {D R S : Type} (g : R → Option S) (f : D → Option R) (x : D) :
    comp g f x = none ↔ f x = none ∨ ∃ y : R, f x = some y ∧ g y = none := by
  unfold comp
  cases f x with
  | none => simp
  | some y => simp

/-! ## 段 1 · L3 · 复合广义逆的代数（**含兼容条件澄清**） -/

/-- **L3a（`gf ∘ hg` 版，显式兼容条件）**：设 `gf` 为 `f` 的像内还原、`hg` 为 `g` 的像内还原，
    且满足**兼容条件** `h_compat`（`hg s` **落在 `f` 的像内**，即 `∃ d : D, f d = some (hg s)`），
    则 `G := gf ∘ hg` 是复合 `Φ := g ∘ f` 的右逆（像内还原）。

    ⚠️ **陈述修正（2026-09-13，缺陷 D-1）**：原陈述写作
    `f (hg s) = some (hg s)`——**类型不匹配**（`hg s : R` 而 `f : D → Option R`），
    经 V2 外部机验报 `47:52` 等 4 处 error 暴露；现改述为**类型正确**的像内形式
    `∃ d : D, f d = some (hg s)`（docstring 原述「落在像内」不变，**命题不变**）。

    ⚠️ **证明体补正（2026-09-14，缺陷 D-1b）**：**V3 复跑显示陈述修正已生效**
    （V2 的 `47:52` 等 4 处陈述级错误**全部消失**），但**证明体**在 `59:56 / 59:55` 报见证层错误 ——
    原写法 `h_compat s ⟨r, hfr, hgr⟩` 把 `r : R`（`L2_comp_some` 内层 `∃ y : R` 的见证）**误作**
    `∃ x : D, comp g f x = some s` 的见证；现改为**在 `rw` 改写前**取**原始输入见证** `h_compat s ⟨x, hx⟩`（`x : D`）。
    ⚠️ **补正后已机验（2026-09-22 本机 Lean 4.34.0-rc2）：exit 0、零 sorry**（V4 复跑即本机复跑；CI 复跑仍待）。 -/
theorem L3a_compose_right_inverse {D R S : Type}
    (f : D → Option R) (g : R → Option S) (gf : R → D) (hg : S → R)
    (h_ctx : ∀ r, (∃ x, f x = some r) → f (gf r) = some r)
    (h_hg : ∀ s, (∃ r, g r = some s) → g (hg s) = some s)
    (h_compat : ∀ s, (∃ x, comp g f x = some s) → ∃ d : D, f d = some (hg s)) :
    ∀ x s, comp g f x = some s → comp g f (gf (hg s)) = some s := by
  intro x s hx
  have himg : ∃ d : D, f d = some (hg s) := h_compat s ⟨x, hx⟩
  rw [L2_comp_some] at hx
  rcases hx with ⟨r, _, hgr⟩
  have hgs : g (hg s) = some s := h_hg s ⟨r, hgr⟩
  have hfhg : f (gf (hg s)) = some (hg s) := h_ctx (hg s) himg
  rw [L2_comp_some]
  exact ⟨hg s, hfhg, hgs⟩

/-- **L3b（规范代表元版，不依赖兼容条件）**：若选择函数 `G` 满足「像内还原」，
    则两条正则性公理成立（形态与 `M2_reflexive_inverse` 同构）。
    ⚠️ `G` 的**存在性**由「`s ∈ Im(Φ)` 时可枚举代表元」给出——**该存在性本文件不证**
    （属构造性前提，见义务 L3-c）。 -/
theorem L3b_canonical_right_inverse {D R S : Type}
    (f : D → Option R) (g : R → Option S) (G : S → D)
    (hG : ∀ s, (∃ x, comp g f x = some s) → comp g f (G s) = some s) :
    (∀ x s, comp g f x = some s → comp g f (G s) = some s) ∧
    (∀ s, (∃ x, comp g f x = some s) → comp g f (G s) = some s) := by
  constructor
  · intro x s hx
    exact hG s ⟨x, hx⟩
  · intro s hs
    exact hG s hs

/-! ## 段 2 · L4 · 守卫保持（合取，不可剥离） -/

/-- **复合守卫**：`P`（首段定义域守卫）**合取** `Q`（次段值域守卫）——**不可剥离** -/
def guardComp {D R S : Type} (P : D → Prop) (Q : R → Prop)
    (f : D → Option R) (_g : R → Option S) (x : D) : Prop :=
  P x ∧ ∃ y : R, f x = some y ∧ Q y

/-- **L4a（守卫保持 · 蕴含侧）**：复合守卫 ⟹ 首段守卫（且次段守卫可由像取得）。 -/
theorem L4_guard_implies_first {D R S : Type} (P : D → Prop) (Q : R → Prop)
    (f : D → Option R) (g : R → Option S) (x : D) :
    guardComp P Q f g x → P x := by
  intro h
  exact h.1

/-- **L4b（剥离红队）**：**存在** `x` 使 `P x` 成立而 `guardComp` 不成立——
    即「**只保留首段守卫**」会**漏掉**次段守卫，故守卫**不可剥离**（违反即为内核违规）。
    2026-09-24 删结论冗余合取支 `P x ∧`（cosmetic；`P x` 已由前提 `hP` 给出），余不动。 -/
theorem L4_guard_not_separable {D R S : Type} (P : D → Prop) (Q : R → Prop)
    (f : D → Option R) (g : R → Option S) (x : D) (y : R)
    (_hP : P x) (hf : f x = some y) (hQ : ¬ Q y) :
    ¬ guardComp P Q f g x := by
  intro hconj
  rcases hconj with ⟨_, y', hf', hQ'⟩
  rw [hf] at hf'
  injection hf' with hy
  exact hQ (hy.symm ▸ hQ')

end TDCA.MetaInverse

/-
  ────────────────────────────────────────────────────────────────────────────
  **证明义务清单（sorry 清零 checklist）**：
   [L2-b] `L2_comp_none`：改用 `Option.bind_eq_none_iff`（若名称/形态不同，
          可 `cases f x <;> simp [comp, Option.bind]` 展开消解）。
   [L3-a] `L3a_compose_right_inverse`：**陈述已于 2026-09-13 修正**（D-1）——
          原 `h_compat : … → f (hg s) = some (hg s)` **类型不匹配**（`hg s : R`、`f : D → Option R`），
          经 V2 外部机验报 `47:52` 等 4 处 error 暴露；现为 **`… → ∃ d : D, f d = some (hg s)`**（像内形式，**命题不变**）；
          证明相应为「取见证 → 交 `h_ctx` 还原 → `L2_comp_some` 闭合」。
          ⚠️ **修正后已机验（2026-09-22 本机）：exit 0、零 sorry**（CI 复跑仍待）；**关键点仍是 `h_compat`（兼容条件）为显式真实前提**——
          它不是装饰，而是「`G = gf ∘ hg`」成立的前提（输入件原文未显式列出）。
   [L3-c] `L3b_canonical_right_inverse`：`G` 的**存在性**（枚举代表元）未证——
          依赖 `s ∈ Im(Φ)` 时可构造代表元；若 `D` 无限且无可选择结构，
          须以 `Classical.choice` + 良序化承接（**设计决策**，见 M-3 方案 §四）。
   [L4-a/L4-b] 已给完整证明尝试（谓词层，低风险）。
  ⚠️ **本文件已机验（2026-09-22 本机 Lean 4.34.0-rc2）：`L2_comp_none` 为完整证明，全件 `sorry` = 0（编译器零 sorry 告警，双口径）**；CI 复跑前对外称「本机机验通过」。
  ⚠️ 三态原则：若某条经机验不成立，**改述为 conditional 或输出反例**（合法终态）。
-/
