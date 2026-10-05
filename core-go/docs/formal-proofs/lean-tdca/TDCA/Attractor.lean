/-
  TDCA 形式化线第三批 · PRP-ATT-001（拟名 INST-ATTRACTOR）· 制度吸引子 · 离散收窄版
  ============================================================================
  件性质：智库研究 → 机验载体件（新增，只增不改；⛔ 不改任何既有模块）
  归属：形式化线第三批 序 P2-1；程序依据 TDCA-STD-INSTITUTION-PROMOTION-001 步②/③
  ⛔ 对外表述限「本机机验」（⛔ 非 CI 机验）；⛔ 不得称「已证明／绝对安全」
  ⚠️ 性质如实（要紧）：本件所证 ⛔ 非「实数域上之压缩映射不动点定理（Banach）」，
     而是**条件化之离散收窄版**：「给定『压缩前提（H2 离散形态）＋ 不动点存在前提（H1 离散形态）』
     之自然数承载系统，其吸引子存在唯一、全局收敛、且有步数界与偏差不增面」；
     ⛔ 不得对外表述为「已证一般压缩映射定理」

  机验目标（离散收窄子集 · ⛔ 不外推）：
   AT-1 存在唯一 ＋ 全局收敛：压缩前提 ⟹ 吸引子（0）存在唯一，且自任意态有限步到达
   AT-2 ε-摄动界（离散形态）：附加「非扩张」前提 ⟹ 迭代不放大初始偏差
   AT-3 替换成本（步数）之下界与上界：非零态不可 0 步到达；自 x 出发之步数 ≤ x
   AT-4 收敛速率界：自 x 出发，迭代至多 x 步到达吸引子（与 AT-3 同源）

  模型假设（显式，不得省略）：
   A1（不动点存在前提 · H1 之离散形态）：`step 0 = 0`
   A2（压缩前提 · H2 之离散形态）：∀ x ≠ 0，`step x + 1 ≤ x`（每步至少缩减 1）
   A3（非扩张前提 · 仅 AT-2 用）：`Within x y d → Within (step x) (step y) d`
   A4 ⚠️ 连续／实数形态（q < 1 之实数压缩率、`ε/(1-q)` 界、Banach 定理）⛔ **不在本件**；
      属另件另议（须实数与完备性工具）；本件 ⛔ 不冒充该情形已证
   A5 本件不作制度主张；「吸引子」之制度含义归制度层与研究件

  数据性质：形式化（确定性、无随机量、无外部数据）
  依赖纪律：本件零依赖（不 import Mathlib，亦不引用其它 TDCA 件）
  机验状态：本机机验；⛔ 非 CI 机验
-/

namespace TDCA.Attractor

/-! ## 一、载体与假设（模型假设 A1 / A2 / A3） -/

/-- 偏差包含（不含减法之离散形态）：`y ≤ x + d ∧ x ≤ y + d` -/
def Within (x y d : Nat) : Prop := y ≤ x + d ∧ x ≤ y + d

/-- A1（不动点存在前提 · H1 之离散形态）：零为不动点 -/
def FixZero (step : Nat → Nat) : Prop := step 0 = 0

/-- A2（压缩前提 · H2 之离散形态）：非零态每步至少缩减 1 -/
def Contract1 (step : Nat → Nat) : Prop := ∀ x, x ≠ 0 → step x + 1 ≤ x

/-- 系统前提之合取（离散收窄版） -/
def IsAttractorSys (step : Nat → Nat) : Prop := FixZero step ∧ Contract1 step

/-- A3（非扩张前提 · 仅 AT-2 用）：偏差不被单步放大 -/
def NonExpand (step : Nat → Nat) : Prop :=
  ∀ x y d, Within x y d → Within (step x) (step y) d

/-! ## 二、迭代 -/

/-- 迭代 `n` 次 -/
def iterN (step : Nat → Nat) : Nat → Nat → Nat
  | 0, x => x
  | n + 1, x => iterN step n (step x)

/-! ## 三、AT-1（存在唯一 ＋ 全局收敛） -/

/-- AT-1a 迭代单调不增（压缩前提） -/
theorem att_iter_le (step : Nat → Nat) (h : IsAttractorSys step) :
    ∀ n x, iterN step n x ≤ x := by
  unfold IsAttractorSys FixZero Contract1 at h
  obtain ⟨h0, hc⟩ := h
  intro n
  induction n with
  | zero => intro x; simp [iterN]
  | succ k ih =>
      intro x
      show iterN step k (step x) ≤ x
      have h1 : iterN step k (step x) ≤ step x := ih (step x)
      have h2 : step x ≤ x := by
        rcases Nat.eq_zero_or_pos x with hxz | hxp
        · subst hxz; simp [h0]
        · have hc' := hc x (by omega)
          omega
      omega

/-- AT-4（收敛速率界）＋ AT-3 上界：自 `x` 出发至多 `x` 步到达吸引子 -/
theorem att_reaches (step : Nat → Nat) (h : IsAttractorSys step) :
    ∀ x, ∃ k, k ≤ x ∧ iterN step k x = 0 := by
  unfold IsAttractorSys FixZero Contract1 at h
  obtain ⟨h0, hc⟩ := h
  intro x
  induction x using Nat.strongRecOn with
  | ind x ih =>
      rcases Nat.eq_zero_or_pos x with hxz | hxp
      · subst hxz
        exact ⟨0, Nat.le_refl 0, rfl⟩
      · have hlt : step x < x := by
          have hc' := hc x (by omega)
          omega
        obtain ⟨k, hk1, hk2⟩ := ih (step x) hlt
        refine ⟨k + 1, by omega, ?_⟩
        show iterN step k (step x) = 0
        exact hk2

/-- AT-1b 吸引子唯一：不动点只能是零 -/
theorem att_unique (step : Nat → Nat) (h : IsAttractorSys step) :
    ∀ x, step x = x → x = 0 := by
  unfold IsAttractorSys FixZero Contract1 at h
  obtain ⟨_h0, hc⟩ := h
  intro x hx
  rcases Nat.eq_zero_or_pos x with hxz | hxp
  · exact hxz
  · have hc' := hc x (by omega)
    rw [hx] at hc'
    omega

/-- AT-1 合成：存在唯一吸引子 ＋ 全局收敛 -/
theorem att_attractor (step : Nat → Nat) (h : IsAttractorSys step) (x : Nat) :
    (∃ k, k ≤ x ∧ iterN step k x = 0) ∧ (∀ y, step y = y → y = 0) :=
  ⟨att_reaches step h x, att_unique step h⟩

/-- AT-3 下界：非零态不可 0 步到达吸引子 -/
theorem att_zero_steps_not_attracted {step : Nat → Nat} {x : Nat} (hx : x ≠ 0) :
    iterN step 0 x ≠ 0 := by
  simpa [iterN] using hx

/-! ## 四、AT-2（ε-摄动界 · 离散形态） -/

/-- AT-2：非扩张前提下，迭代 `n` 步不放大初始偏差 -/
theorem att_perturb (step : Nat → Nat) (hne : NonExpand step) :
    ∀ n x y d, Within x y d → Within (iterN step n x) (iterN step n y) d := by
  intro n
  induction n with
  | zero => intro x y d hw; simpa [iterN] using hw
  | succ k ih =>
      intro x y d hw
      exact ih (step x) (step y) d (hne x y d hw)

/-- AT-2′ 常形态（供引用） -/
theorem att_perturb_bound (step : Nat → Nat) (hne : NonExpand step) {x y d : Nat}
    (hw : Within x y d) (n : Nat) : Within (iterN step n x) (iterN step n y) d :=
  att_perturb step hne n x y d hw

/-! ## 五、机验基线实例 -/

/-- 基线 1：常零算子满足系统前提（退化吸引子） -/
theorem att_example_const_zero_sys : IsAttractorSys (fun _ => 0) := by
  constructor
  · rfl
  · intro x hx
    show (0 : Nat) + 1 ≤ x
    omega

/-- 基线 2：常零算子为非扩张 -/
theorem att_example_const_zero_nonexpand : NonExpand (fun _ => 0) := by
  intro x y d _hw
  refine ⟨?_, ?_⟩ <;> simp

/-- 基线 3：前驱算子满足系统前提（每步缩减恰 1） -/
theorem att_example_pred_sys : IsAttractorSys Nat.pred := by
  constructor
  · rfl
  · intro x hx
    cases x with
    | zero => exact absurd rfl hx
    | succ y => simp [Nat.pred]

/-- 基线 4：自 5 出发至多 5 步到达吸引子 -/
theorem att_example_pred_conv : ∃ k, k ≤ 5 ∧ iterN Nat.pred k 5 = 0 :=
  att_reaches Nat.pred att_example_pred_sys 5

/-- 基线 5：常零算子之摄动不增（AT-2 实例） -/
theorem att_example_const_zero_perturb (x y d n : Nat) (hw : Within x y d) :
    Within (iterN (fun _ => 0) n x) (iterN (fun _ => 0) n y) d :=
  att_perturb (fun _ => 0) att_example_const_zero_nonexpand n x y d hw

end TDCA.Attractor
