/-
  TDCA 形式化证明课题 · 协调原理簇（COORD）· 第二批之二 · COORD-4（分层最优性）
  ============================================================================
  建模方式：独立件、独立命名空间、零依赖（不 import Mathlib）。

  在册表述（照外部四件吸收件与前置对表件，逐字引）：
   COORD-4（分层最优性）：「|Q| 缩减因子」与「结构切换成本」；
   在册批注：现以常数吸收，结论偏粗糙，须独立成文（材料开放问题 2）。
  本件之形态（条件化，前提作显式假设，禁 axiom 藏匿）：
   一 最优层数之存在性：在给定层数上限内，成本函数取最小值（良序 · 构造性）；
   二 切换成本之线性下界：每层固定切换成本，则 k 层之切换成本至少 k · c；
   三 分层收益之判定面：存在层数使总成本不高于基准 ⟹ 分层可行（构造性）。

  模型假设（显式，不得省略）：
   C4-1 成本以 Nat 承载（零依赖简化载体；实数与缩减因子形态另议）；
   C4-2 层数以 Nat 上限 N 界定（有限范围；N 之取值属策略层，不在本件）；
   C4-3 切换成本每层固定为常数 c，累积以线性下界承载；
   C4-4 「最优」＝ 该层数之成本不高于同范围内任何其它层数。

  适用范围：抽象成本骨架层。不主张任何制度层结论；不标「绝对安全」；
  对外表述限「本机机验」；缩减因子与阈值取值属策略层，不在本件。

  机验状态：本机机验（Lean 4.34.0-rc2 · lake build）；非 CI 机验。
  三态终态声明：本件各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项、无占位（sorry）。
-/

namespace TDCA.CoordLayering

/-! ## 一、最优层数之存在性（良序 · 构造性） -/

/-- COORD-4 · 最优层数存在：层数上限 N 内必有一层成本最小 -/
theorem coord4_optimal_exists (cost : Nat → Nat) :
    ∀ N, ∃ k, k ≤ N ∧ ∀ j, j ≤ N → cost k ≤ cost j
  | 0 => ⟨0, Nat.le_refl 0, fun j hj => by
      have hj' : j = 0 := by omega
      subst hj'
      exact Nat.le_refl _⟩
  | N + 1 => by
      obtain ⟨k, hk1, hk2⟩ := coord4_optimal_exists cost N
      by_cases h : cost k ≤ cost (N + 1)
      · refine ⟨k, by omega, fun j hj => ?_⟩
        rcases Nat.lt_or_ge j (N + 1) with hlt | hge
        · exact hk2 j (by omega)
        · have hj' : j = N + 1 := by omega
          subst hj'
          exact h
      · refine ⟨N + 1, Nat.le_refl _, fun j hj => ?_⟩
        rcases Nat.lt_or_ge j (N + 1) with hlt | hge
        · have hjk : cost k ≤ cost j := hk2 j (by omega)
          omega
        · have hj' : j = N + 1 := by omega
          subst hj'
          exact Nat.le_refl _

/-! ## 二、切换成本之线性下界（分层非免费） -/

/-- 各层切换成本之累积（每层固定 c） -/
def switchAccum (c : Nat) : Nat → Nat
  | 0 => 0
  | k + 1 => switchAccum c k + c

/-- COORD-4 · 切换成本之线性下界：k 层之累积至少 k · c -/
theorem coord4_switch_linear (c : Nat) (k : Nat) : k * c ≤ switchAccum c k := by
  induction k with
  | zero => simp [switchAccum]
  | succ m ih =>
      show (m + 1) * c ≤ switchAccum c m + c
      rw [Nat.succ_mul]
      omega

/-! ## 三、分层收益之判定面 -/

/-- COORD-4 · 分层收益之判定面（构造性）：存在层数其总成本不高于基准 ⟹ 分层可行 -/
theorem coord4_layering_beneficial (total : Nat → Nat) (base : Nat) {k : Nat}
    (h : total k ≤ base) : ∃ j, total j ≤ base :=
  ⟨k, h⟩

/-- COORD-4 · 分层不可行（对偶面）：所有层数皆高于基准 ⟹ 分层不可行 -/
theorem coord4_layering_not_beneficial (total : Nat → Nat) (base : Nat)
    (h : ∀ j, base < total j) : ¬ ∃ j, total j ≤ base :=
  fun ⟨j, hj⟩ => absurd hj (Nat.not_le_of_gt (h j))

/-! ## 四、机验基线实例 -/

/-- 基线：恒等成本下最优层数存在（上限 3 内取 0） -/
theorem coord4_example_optimal :
    ∃ k, k ≤ 3 ∧ ∀ j, j ≤ 3 → (fun n : Nat => n) k ≤ (fun n : Nat => n) j :=
  coord4_optimal_exists (fun n : Nat => n) 3

/-- 基线：三层切换成本（每层 2）之线性下界 -/
theorem coord4_example_switch : 3 * 2 ≤ switchAccum 2 3 :=
  coord4_switch_linear 2 3

/-- 基线：分层收益之实例 -/
theorem coord4_example_beneficial :
    ∃ j, (fun n : Nat => n) j ≤ 5 :=
  coord4_layering_beneficial (fun n : Nat => n) 5 (k := 3) (by omega)

end TDCA.CoordLayering
