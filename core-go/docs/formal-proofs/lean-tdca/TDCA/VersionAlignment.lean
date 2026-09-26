/-
  TDCA 形式化证明课题 · 版本对齐 fail-closed · N-4（制度版本 ＋ 检查器版本）
  ============================================================================
  建模方式：独立件、独立命名空间。制度版本／检查器版本以 ℕ 承载；「失配」为可计算
  判据（decide 形态）；发布门＝版本门 ∧ 工件断言门之单一合取（与「对内先工件、后制度」
  同一 fail-closed 根）；版本门对缺信息（none）直接给 false。结构层判 proved；
  真实 CI 接线层以 RealGateSpec 假设承载、判 conditional。

  模型假设（显式，不得省略）：
   A1 版本刻画：制度版本 instVer 与检查器版本 chkVer 均为 ℕ，可比、可判等；
   A2 失配判据（判据②）：mismatch? i c ⟺ i ≠ c，decide 形态、内核可计算
     （demo_mismatch_computable 给出 1 ≠ 2 之可算实证）；
   A3 版本门（判据①④）：versionGate 仅对 (some i, some c) 给 decide (i = c)，
     任一为 none 即 false——「不确定 ⟹ 拒绝」，无默认放行分支（fail-closed）；
   A4 发布门（判据③「同一根」）：releaseGate ＝版本门 ∧ 工件断言门之合取；
     工件未过断言即被拒，即须回改制度边界后再发——与版本失配同根同向；
   A5 真实 CI 接线为工程层：结构层结论判 proved；接口层（RealGateSpec 忠实性）
     判 conditional（SIMULATED 现状下不可核，不得以结构证明冒充接口实况）。

  适用范围：GSEQ-2551 第 2 节 N-4 行（演化同步判据；与「对内先工件、后制度」
  原则同一根）之可机验抽象骨架。工程锚点：ID85（法规基座缺失即拒绝决策、不静默降级）、
  ID31（缺失即异常、异常即阻断）、CI 侧既有 fail-closed 实践。
  真实版本比对之密码学绑定、CI 接线属工程层，不在本件形式化范围。

  机验状态：本机已机验（2026-09-23，Lean 4.34.0-rc2，lake build 0 error）；非 CI 机验。
  三态终态声明（分层分列）：
   · 结构层——本节各定理均为内核可检完整证明（proved）；
   · 接口层——real_gate_conditional 为忠实性假设下之条件定理，判 conditional；
   无 refuted。⛔ 不标「绝对安全」；对外表述限「本机机验」。

  依赖纪律：本件零依赖（不 import Mathlib，亦不引用其它 TDCA 件）——
  版本对齐骨架只需 Nat 可判等事实，同时隔离上游弃用告警面；
  如后续扩充需 Mathlib 引理，另件处理。
-/

namespace TDCA.VersionAlignment

/-! ## 载体与判定（模型假设 A1–A4） -/

/-- 失配判据（判据②：可计算，decide 形态） -/
def mismatch? (i c : Nat) : Bool := decide (i ≠ c)

/-- 版本门（判据①③④：fail-closed；缺信息 ⟹ false） -/
def versionGate : Option Nat → Option Nat → Bool
  | some i, some c => decide (i = c)
  | _, _ => false

/-- 发布门＝版本门 ∧ 工件断言门（判据③「同一根」：单一合取门，两闸同向） -/
def releaseGate (vOk aOk : Bool) : Bool := vOk && aOk

/-! ## N-4 · 四条判据（机验面，结构层 · proved） -/

/-- 判据① 失配 ⟹ 拒绝：版本不一致时发布须被拒 -/
theorem deny_on_mismatch (i c : Nat) (h : i ≠ c) :
    versionGate (some i) (some c) = false := by
  simp [versionGate, h]

/-- 判据①′ 方向不可反转（fail-closed 实证）：失配态下门不可开 -/
theorem no_fail_open (i c : Nat) (h : i ≠ c) :
    versionGate (some i) (some c) ≠ true := by
  rw [deny_on_mismatch i c h]
  intro hc
  cases hc

/-- 判据①″ 逆方向（拒绝不冒充对齐）：门过 ⟹ 两版本齐备且相等 -/
theorem gate_true_implies_match (vi ci : Option Nat)
    (hg : versionGate vi ci = true) :
    ∃ i c, vi = some i ∧ ci = some c ∧ i = c := by
  cases vi with
  | none => simp only [versionGate] at hg; cases hg
  | some i =>
    cases ci with
    | none => simp only [versionGate] at hg; cases hg
    | some c =>
      refine ⟨i, c, rfl, rfl, ?_⟩
      simp only [versionGate] at hg
      exact of_decide_eq_true hg

/-- 判据② 失配须可判：失配判据之真值 ⟺ 版本不等（内核可判，计算实证见下） -/
theorem mismatch?_true_iff (i c : Nat) : mismatch? i c = true ↔ i ≠ c := by
  simp [mismatch?]

/-- 判据②′ 可算实证：1 ≠ 2 之失配判据归约为 true（rfl 机验） -/
theorem demo_mismatch_computable : mismatch? 1 2 = true := rfl

/-- 判据④ 不确定 ⟹ 拒绝（左缺）：制度版本未知即拒 -/
theorem deny_none_left (ci : Option Nat) : versionGate none ci = false := rfl

/-- 判据④′ 不确定 ⟹ 拒绝（右缺）：检查器版本未知即拒 -/
theorem deny_none_right (vi : Option Nat) : versionGate vi none = false := by
  cases vi <;> rfl

/-- 判据③ 同一根（工件闸）：工件未过断言 ⟹ 发布被拒（无论版本是否对齐） -/
theorem artifacts_fail_blocks (vOk : Bool) : releaseGate vOk false = false := by
  cases vOk <;> rfl

/-- 判据③′ 发布须双闸同过：发布门过 ⟹ 版本门过 ∧ 工件门过 -/
theorem release_requires_both (vOk aOk : Bool) (h : releaseGate vOk aOk = true) :
    vOk = true ∧ aOk = true := by
  cases vOk <;> cases aOk <;> simp_all [releaseGate]

/-! ## 接口层（模型假设 A5：真实 CI 接线，conditional） -/

/-- 真实发布门接线之假设规格：门之通过须忠实于版本相等
    （SIMULATED 现状下此忠实性不可核——本结构之结论判 conditional） -/
structure RealGateSpec where
  gate : Nat → Nat → Bool
  faithful : ∀ i c, gate i c = true → i = c

/-- 接口层（conditional）：在忠实性假设下，失配 ⟹ 真实门拒绝 -/
theorem real_gate_conditional (spec : RealGateSpec) (i c : Nat)
    (h : i ≠ c) : spec.gate i c = false := by
  by_cases hg : spec.gate i c = true
  · exact (h (spec.faithful i c hg)).elim
  · exact Bool.eq_false_iff.2 hg

end TDCA.VersionAlignment
