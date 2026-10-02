/-
  TDCA 形式化证明课题 · 协调原理簇（COORD）· 第二批之一 · COORD-3（协调天花板）
  ============================================================================
  建模方式：独立件、独立命名空间、零依赖（不 import Mathlib）。

  在册表述（照外部四件吸收件与前置对表件，逐字引）：
   COORD-3（协调天花板）：由条件 H1 与 H2 得 P′(1) > 0 与 P′(∞) < 0；
   在册批注：充分性须显式；离散版 H3 为开放问题（材料自认）。
  本件之形态（条件化，前提作显式假设，禁 axiom 藏匿）：
   H1 取「每步严格递增」（增益为正）；H2 取凹性（增益递减）；
   结论面三条：起点增益为正；天花板（某处增益非正 ⟹ 此后不再上升）；
   增益恒正 ⟹ 无天花板。
  离散版 H3（何时增益必转为非正）为开放问题 —— 本件不涉（材料自认）。

  模型假设（显式，不得省略）：
   C3-1 协调增益以 P : Nat → Nat 承载（零依赖简化载体；实数与导数形态另议）；
   C3-2 H1：每步严格递增（增益为正）；
   C3-3 H2：凹性（增益递减）——以 P n + P (n+2) ≤ 2 * P (n+1) 承载；
   C3-4 天花板判定面取「相邻差非正」。

  适用范围：抽象序列骨架层。不主张任何制度层结论；不标「绝对安全」；
  对外表述限「本机机验」；阈值与规模取值属策略层，不在本件。

  机验状态：本机机验（Lean 4.34.0-rc2 · lake build）；非 CI 机验。
  三态终态声明：本件各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项、无占位（sorry）。
-/

namespace TDCA.CoordCeiling

/-- H1 之严格递增形态（每步增益为正） -/
def StrictMono (P : Nat → Nat) : Prop :=
  ∀ n, P n < P (n + 1)

/-- H2 之凹性形态（增益递减） -/
def Concave (P : Nat → Nat) : Prop :=
  ∀ n, P n + P (n + 2) ≤ 2 * P (n + 1)

/-! ## 一、起点增益为正（充分性之显式面） -/

/-- COORD-3 · 起点增益为正：H1 ⟹ P(1) > P(0) -/
theorem coord3_start_positive (P : Nat → Nat) (h1 : StrictMono P) : P 0 < P 1 :=
  h1 0

/-! ## 二、天花板（协调上限） -/

/-- COORD-3 · 天花板之单步面：凹性 ＋ 某处增益非正 ⟹ 下一步增益仍非正 -/
theorem coord3_ceiling_step (P : Nat → Nat) (hc : Concave P) {m : Nat} (h : P (m + 1) ≤ P m) :
    P (m + 2) ≤ P (m + 1) := by
  have hm := hc m
  omega

/-- COORD-3 · 天花板之步进面（任意步数）：凹性 ＋ 某处增益非正 ⟹ 该处起 k 步后仍非正 -/
theorem coord3_ceiling_aux (P : Nat → Nat) (hc : Concave P) (n : Nat) (h : P (n + 1) ≤ P n) :
    ∀ k, P (n + k + 1) ≤ P (n + k) := by
  intro k
  induction k with
  | zero => simpa using h
  | succ j ih =>
      have h2 : P (n + j + 2) ≤ P (n + j + 1) := coord3_ceiling_step P hc (m := n + j) ih
      have hidx1 : n + (j + 1) = n + j + 1 := by omega
      have hidx2 : n + j + 1 + 1 = n + j + 2 := by omega
      rw [hidx1, hidx2]
      exact h2

/-- COORD-3 · 天花板：凹性 ＋ 某处增益非正 ⟹ 此后增益恒非正 -/
theorem coord3_ceiling (P : Nat → Nat) (hc : Concave P) {n : Nat} (h : P (n + 1) ≤ P n)
    {m : Nat} (hm : n ≤ m) : P (m + 1) ≤ P m := by
  obtain ⟨k, rfl⟩ := Nat.le.dest hm
  exact coord3_ceiling_aux P hc n h k

/-! ## 三、无天花板（严格递增之面） -/

/-- COORD-3 · 无天花板：H1 ⟹ 任意处增益不为非正 -/
theorem coord3_no_ceiling (P : Nat → Nat) (h1 : StrictMono P) (n : Nat) : ¬ (P (n + 1) ≤ P n) :=
  fun h => absurd h (Nat.not_le_of_gt (h1 n))

/-- COORD-3 · 分界面：H1 与「无天花板」等价面 -/
theorem coord3_dichotomy (P : Nat → Nat) (h1 : StrictMono P) :
    (∀ n, P n < P (n + 1)) ∧ (∀ n, ¬ (P (n + 1) ≤ P n)) :=
  ⟨h1, fun n => coord3_no_ceiling P h1 n⟩

/-! ## 四、机验基线实例 -/

/-- 基线：常数序列（增益恒零）自任意处不再上升 -/
theorem coord3_example_const :
    ∀ m, (fun _ : Nat => 7) (m + 1) ≤ (fun _ : Nat => 7) m :=
  fun _ => Nat.le_refl 7

/-- 基线：严格递增序列（P n = n）无天花板 -/
theorem coord3_example_strict : ¬ ((fun n : Nat => n) 3 ≤ (fun n : Nat => n) 2) :=
  coord3_no_ceiling (fun n : Nat => n) (fun n => Nat.lt_succ_self n) 2

/-- 基线：凹性之实例（线性序列为凹） -/
theorem coord3_example_concave : Concave (fun n : Nat => n) := by
  intro n
  show n + (n + 2) ≤ 2 * (n + 1)
  omega

end TDCA.CoordCeiling
