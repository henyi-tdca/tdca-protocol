import TDCA.Basic
import TDCA.MetaInverse
import Mathlib.Data.Fintype.Basic          -- 新增（裁定 ③ 允许）

/-!
  TDCA · 公理 6 实例化（证明器通道）—— 四约束
  ⚠️ 本件为第二通道，⛔ 不替代 Go 实现与测试。
  ⚠️ 约束 1/2 归位自 TDCA.MetaInverse；约束 3 为本件新证（甲′ 形态）；约束 4 见 Axiom6Complexity.lean（条件形态附录）。
  ⛔ 不得表述为「四约束全证」。

  ⚠️ 约束 3 之非空前提（甲′ · 治理裁定 2026-09-14）：
     · 原定稿（仅 [DecidableEq R] [Fintype D]）在 D = Empty 时不成立（不存在任何函数 g : R → D；反例已机验，见 GSEQ-1615）。
     · 甲′ 增补 [Inhabited D]（数据版；⚠️ Nonempty D〔Prop 版〕不够）。
     · 依据：权威件 §1.1 的 X（AgentCard 集合）实际非空 ⟹ [Inhabited D] 系对工程前提的显式化，⛔ 非削弱结论；
       与 L3-c（取甲·可枚举代表元）一致。
-/

namespace TDCA.Axiom6

variable {D R : Type}

/-- 公理 6 · 约束 1（验证完备性）。归位自 TDCA.MetaInverse.M0_verify_complete。 -/
theorem constraint1_completeness [DecidableEq R] (f : D → Option R) (x : D) (y : R)
    (h : f x = some y) : TDCA.MetaInverse.Verify f y x = true :=
  TDCA.MetaInverse.M0_verify_complete f x y h

/-- 公理 6 · 约束 2（验证可靠性）。归位自 TDCA.MetaInverse.M1_verify_sound。 -/
theorem constraint2_soundness [DecidableEq R] (f : D → Option R) (y : R) (x : D)
    (h : TDCA.MetaInverse.Verify f y x = true) : f x = some y :=
  TDCA.MetaInverse.M1_verify_sound f y x h

/-- 公理 6 · 约束 3（可还原性 · 甲′）：像点存在还原见证。
    ⚠️ 三实例前提：[DecidableEq R] + [Fintype D] + [Inhabited D]（甲′ 增补）。
    ⚠️ 依 L3-c（取甲·可枚举代表元）：⛔ 不得显式引入 Classical.choice/良序化；
       可枚举构造内部传递继承 Classical.choice 不视为显式引入（治理裁定 2026-09-14）。
    ⚠️ #print axioms 预期 [propext, Classical.choice, Quot.sound] —— 须如实标注为内部继承。 -/
theorem constraint3_right_inverse [DecidableEq R] [Fintype D] [Inhabited D]
    (f : D → Option R) :
    ∃ g : R → D, ∀ y, (∃ x, f x = some y) → f (g y) = some y := by
  refine ⟨fun y => (Finset.univ.toList.find? (fun x => decide (f x = some y))).getD default, ?_⟩
  intro y hy
  show f ((Finset.univ.toList.find? (fun x => decide (f x = some y))).getD default) = some y
  rcases hy with ⟨x, hx⟩
  have hxin : x ∈ Finset.univ.toList := Finset.mem_toList.mpr (Finset.mem_univ x)
  have hdec : decide (f x = some y) = true := by
    rw [decide_eq_true_eq]; exact hx
  have hsome : (Finset.univ.toList.find? (fun x => decide (f x = some y))).isSome := by
    rw [List.find?_isSome]
    exact ⟨x, hxin, hdec⟩
  obtain ⟨a, ha⟩ := Option.isSome_iff_exists.mp hsome
  have hpa := List.find?_some ha
  have hay : f a = some y := of_decide_eq_true hpa
  rw [ha]
  exact hay

end TDCA.Axiom6
