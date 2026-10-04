/-
  TDCA 形式化线第三批 · PRP-TRI-001（拟名 TRUTHSPACE-HEYTING）· 三空间真值之代数结构 · L1 子集
  ============================================================================
  件性质：智库研究 → 机验载体件（新增，只增不改；⛔ 不改任何既有模块）
  归属：形式化线第三批 序 P1-1；程序依据 TDCA-STD-INSTITUTION-PROMOTION-001 步②/③
  ⛔ 对外表述限「本机机验」（⛔ 非 CI 机验）；⛔ 不得称「已证明／绝对安全」

  机验目标（L1 · 只此四条，⛔ 不外推）：
   T-1 三空间互斥：Pos / Neg / Und 两两不可同时成立
   T-2 正空间合取封闭：Pos x → Pos y → Pos (meet x y)
   T-3 负空间无补（排中失效）：IsNeg x → join x (compl x) ≠ ⊤
   T-4 未裁决无补（增益 · 如实登记）：IsUnd x → join x (compl x) ≠ ⊤
  辅证（对照）：
   A-1 正空间排中成立：IsPos x → join x (compl x) = ⊤
   A-2 三分类穷尽（或为逻辑锚 ⊥）
   A-3 排中律非普遍成立（反例：负空间元）

  模型假设（显式，不得省略）：
   M1 真值域 = 四点链 ⊥ < und < neg < ⊤（有限、可判定；⛔ 非完整海廷代数主张）
   M2 三空间分类：Pos := ⊤（成立/可证）· Neg := neg · Und := und；⊥ 为逻辑锚（不属三空间）
   M3 运算：meet = 取下界（合取）· join = 取上界（析取）· compl = 伪补（a → ⊥）
   M4 本件只机验上述条文；完整海廷代数结构（公理表逐式穷举）归 L2 另件，⛔ 不在本件范围内
   M5 语义面与制度层「负空间三不可」之对接归解释文件与制度层，本件不作制度主张

  数据性质：形式化（确定性、无随机量、无外部数据）
  依赖纪律：本件零依赖（不 import Mathlib，亦不引用其它 TDCA 件）
-/

namespace TDCA.TruthSpace

/-! ## 载体结构（模型假设 M1 / M2） -/

/-- 真值域：四点链 `⊥ < und < neg < ⊤`（模型假设 M1） -/
inductive TV : Type
  | bot | und | neg | pos
  deriving DecidableEq, Repr

open TV

/-- 三空间分类：正空间（成立／可证）（模型假设 M2） -/
def IsPos (x : TV) : Prop := x = pos

/-- 三空间分类：负空间（不可算计）（模型假设 M2） -/
def IsNeg (x : TV) : Prop := x = neg

/-- 三空间分类：未裁决（模型假设 M2） -/
def IsUnd (x : TV) : Prop := x = und

/-! ## 运算（模型假设 M3） -/

/-- 合取：取下界 -/
def meet : TV → TV → TV
  | .bot, _ => .bot
  | _, .bot => .bot
  | .und, _ => .und
  | _, .und => .und
  | .neg, _ => .neg
  | _, .neg => .neg
  | .pos, .pos => .pos

/-- 析取：取上界 -/
def join : TV → TV → TV
  | .pos, _ => .pos
  | _, .pos => .pos
  | .neg, _ => .neg
  | _, .neg => .neg
  | .und, _ => .und
  | _, .und => .und
  | .bot, .bot => .bot

/-- 伪补（`a → ⊥`） -/
def compl : TV → TV
  | .bot => .pos
  | .und => .bot
  | .neg => .bot
  | .pos => .bot

/-! ## T-1 三空间互斥 -/

theorem tri_mutex_pos_neg (x : TV) : ¬ (IsPos x ∧ IsNeg x) := by
  unfold IsPos IsNeg
  cases x <;> decide

theorem tri_mutex_neg_und (x : TV) : ¬ (IsNeg x ∧ IsUnd x) := by
  unfold IsNeg IsUnd
  cases x <;> decide

theorem tri_mutex_pos_und (x : TV) : ¬ (IsPos x ∧ IsUnd x) := by
  unfold IsPos IsUnd
  cases x <;> decide

/-! ## T-2 正空间合取封闭 -/

theorem pos_meet_closed {x y : TV} (hx : IsPos x) (hy : IsPos y) : IsPos (meet x y) := by
  unfold IsPos at hx hy ⊢
  rw [hx, hy]
  rfl

/-! ## T-3 负空间无补（排中律在负空间元素上失效） -/

theorem neg_excluded_middle_fails {x : TV} (hx : IsNeg x) : join x (compl x) ≠ pos := by
  unfold IsNeg at hx
  rw [hx]
  decide

/-! ## T-4 未裁决无补（增益 · 如实登记） -/

theorem und_excluded_middle_fails {x : TV} (hx : IsUnd x) : join x (compl x) ≠ pos := by
  unfold IsUnd at hx
  rw [hx]
  decide

/-! ## 辅证（对照） -/

/-- A-1 正空间排中成立（与 T-3／T-4 对照） -/
theorem pos_excluded_middle_holds {x : TV} (hx : IsPos x) : join x (compl x) = pos := by
  unfold IsPos at hx
  rw [hx]
  rfl

/-- A-2 三分类穷尽（或为逻辑锚 ⊥） -/
theorem tri_exhaustive_or_anchor (x : TV) : x = bot ∨ IsPos x ∨ IsNeg x ∨ IsUnd x := by
  unfold IsPos IsNeg IsUnd
  cases x <;> simp

/-- A-3 排中律非普遍成立（反例：负空间元） -/
theorem excluded_middle_not_universal : ¬ (∀ x : TV, join x (compl x) = pos) := by
  intro h
  exact absurd (h neg) (by decide)

/-! ## 自检断言（供本机／CI 复核用） -/

example : meet pos neg = neg := by decide

example : join und (compl und) = und := by decide

end TDCA.TruthSpace