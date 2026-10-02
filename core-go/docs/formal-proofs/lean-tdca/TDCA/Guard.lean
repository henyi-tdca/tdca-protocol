/-
  TDCA 形式化证明课题 · 证明总纲命题 M-5（部分性与负空间不可逾越）＋ 开放问题 P-6（熔断可判定）
  ============================================================================
  建模方式：独立件、独立命名空间、零依赖（不 import Mathlib）。
  ⭐ 本件以「定义域守卫」之机验形态承载 M-5 与 P-6 两条：M-5 之**不可逾越**＝
  触发即不在定义域内（**熔断是映射行为，不是事后标注**）；P-6 之**可判定**＝
  给定可判定之 `C₁₆` 与 `trigger`，产出与否为**可判定谓词**，且**fail-closed**。

  模型假设（显式，不得省略）：
   G1 元函数 Φ 为**部分映射**：本件以其机验形态呈现——产出**只对定义域内输入定义**
      （`Phi` 第三参数即守卫之证据），故「触发 ⟹ 无产出」为**类型层面**事实；
   G2 定义域守卫 ＝ `C₁₆ ∧ ¬ NSFL-trigger`（照总纲 §一）；
   G3 `C₁₆` 与 `trigger` 在本件为**谓词**（其判定性由 `DecidablePred` 实例提供）；
   G4 化合 `⊗` 之守卫＝**合取**（合规前置不剥离）——本件给出其机验面。

  适用范围：抽象守卫骨架层。⛔ 不主张任何制度层结论；⛔ 不标「绝对安全」；
  对外表述限「本机机验」；⭐ 真实 `C₁₆` 与 NSFL 触发判据属制度与工程层。

  机验状态：本机机验（Lean 4.34.0-rc2 · lake build）；非 CI 机验。
  三态终态声明：本件各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项、无占位（sorry）。
-/

namespace TDCA.Guard

/-! ## 模型假设 G2：定义域守卫（部分性之来源） -/

/-- 定义域守卫：`C₁₆ ∧ ¬ NSFL-trigger` -/
def InDom (c16 trigger : Nat → Prop) (x : Nat) : Prop :=
  c16 x ∧ ¬ trigger x

/-! ## 模型假设 G1：部分映射之机验形态 -/

/-- 元函数 Φ（部分映射形态）：**仅当**输入在定义域内才有产出 -/
def Phi (c16 trigger : Nat → Prop) (x : Nat) (_h : InDom c16 trigger x) : Nat :=
  x

/-- M-5 · 触发即不在定义域内（守卫之否定面） -/
theorem fuse_excludes_dom (c16 trigger : Nat → Prop) (x : Nat) (ht : trigger x) :
    ¬ InDom c16 trigger x :=
  fun h => h.2 ht

/-- M-5 · **熔断不可逾越**：触发之输入**无法被任何 `C₁₆` 补足**
    —— 守卫不可被"讨好"绕过（合取面） -/
theorem fuse_not_bypassable (c16 trigger : Nat → Prop) (x : Nat) (ht : trigger x) :
    ¬ (c16 x ∧ ¬ trigger x) :=
  fun h => h.2 ht

/-- M-5 · **熔断是映射行为**（非事后标注）：产出存在 ⟹ 输入必未触发 -/
theorem output_implies_not_trigger (c16 trigger : Nat → Prop) (x : Nat)
    (h : InDom c16 trigger x) : ¬ trigger x :=
  h.2

/-! ## 模型假设 G3／开放问题 P-6：熔断之**可判定性** -/

/-- 产出判定（P-6 之机验面）：给定可判定之守卫两件，产出与否**可判定** -/
def decideOutput (c16 trigger : Nat → Prop) [DecidablePred c16] [DecidablePred trigger]
    (x : Nat) : Bool :=
  decide (c16 x ∧ ¬ trigger x)

/-- P-6 · 判定正确性：判 `true` ⟺ 在定义域内 -/
theorem decideOutput_iff (c16 trigger : Nat → Prop) [DecidablePred c16] [DecidablePred trigger]
    (x : Nat) : decideOutput c16 trigger x = true ↔ InDom c16 trigger x := by
  unfold decideOutput InDom
  exact decide_eq_true_iff

/-- P-6 · **fail-closed**：触发即判不可产出（无「告警后放行」） -/
theorem decideOutput_fail_closed (c16 trigger : Nat → Prop) [DecidablePred c16]
    [DecidablePred trigger] (x : Nat) (ht : trigger x) :
    decideOutput c16 trigger x = false := by
  unfold decideOutput
  exact decide_eq_false_iff_not.mpr (fun h => h.2 ht)

/-- P-6 · 判定完备（二值）：判定结果非 `true` 即 `false` -/
theorem decideOutput_decidable (c16 trigger : Nat → Prop) [DecidablePred c16]
    [DecidablePred trigger] (x : Nat) :
    decideOutput c16 trigger x = true ∨ decideOutput c16 trigger x = false :=
  Bool.eq_false_or_eq_true _

/-! ## 模型假设 G4：化合之守卫（合规前置不剥离） -/

/-- 化合之定义域：两侧守卫**合取** -/
def InDomCompose (c1 t1 c2 t2 : Nat → Prop) (x : Nat) : Prop :=
  InDom c1 t1 x ∧ InDom c2 t2 x

/-- M-5 · 化合守卫不弱化：复合在定义域内 ⟹ 每一侧均在定义域内 -/
theorem compose_guard_not_weaker (c1 t1 c2 t2 : Nat → Prop) (x : Nat)
    (h : InDomCompose c1 t1 c2 t2 x) : InDom c1 t1 x ∧ InDom c2 t2 x :=
  h

/-- M-5 · 化合不剥离合规前置：任一侧触发 ⟹ 复合无产出 -/
theorem compose_trigger_blocks (c1 t1 c2 t2 : Nat → Prop) (x : Nat) (ht : t2 x) :
    ¬ InDomCompose c1 t1 c2 t2 x :=
  fun h => h.2.2 ht

/-- 机验基线实例：恒真 `C₁₆`、恒假触发 ⟹ 判定为 `true` -/
theorem guard_example :
    decideOutput (fun _ : Nat => True) (fun _ : Nat => False) 7 = true :=
  (decideOutput_iff (fun _ : Nat => True) (fun _ : Nat => False) 7).mpr
    ⟨trivial, fun h => h⟩

end TDCA.Guard
