/-
  TDCA 形式化线 · F-3「场景 ＝ 元函数与解释项之分形嵌套」· 收窄版（L1 子集）
  ⚠️ 性质如实：本件所证 ⛔ 非「场景分形嵌套之一般定理」，而是条件化之收窄版：
     取「解释项 ＋ 单一子场景」之二元嵌套（F1）、以层数作「有限层」之显式判据（F2）、
     以生成器＝加一层（F3）之承载系统；其层数在生成下严格增一、迭代 k 次恰增 k、越级关系传递。
     ⛔ 不得对外表述为「已证场景分形嵌套定理」。
  ⚠️ 前置如实：上游「元函数与解释项分层律」规范送审件未落定 ⟹ 本件走收窄版，
     ⛔ 不进内核作定理、⛔ 不加前提外之主张。
  机验目标：FS-1 生成器改层 / FS-2 迭代累积 / FS-3 嵌套严格增 / FS-4 越级传递
  模型假设（显式，不得省略）：F1 二元嵌套 / F2 层数作有限层判据 / F3 生成器加一层 /
     F4 待定项（嵌套深度有无界、分形互斥完备、边界与元函数选取唯一性）⛔ 不在本件、归数学裁定 /
     F5 本件不作制度主张
  数据性质：形式化（确定性、无随机量、无外部数据）
  依赖纪律：本件零依赖（不 import Mathlib，亦不引用其它 TDCA 件）
  机验状态：本机机验；⛔ 非 CI 机验
-/

namespace TDCA.FractalScene

inductive Item where
  | mk (n : Nat) : Item
  deriving DecidableEq, Repr

inductive Scene where
  | leaf (i : Item) : Scene
  | nest (i : Item) (s : Scene) : Scene
  deriving DecidableEq, Repr

def level : Scene → Nat
  | .leaf _ => 0
  | .nest _ s => level s + 1

def gen (i : Item) (s : Scene) : Scene := Scene.nest i s

theorem gen_level_add_one (i : Item) (s : Scene) : level (gen i s) = level s + 1 := rfl

def genN (i : Item) : Nat → Scene → Scene
  | 0, s => s
  | k + 1, s => genN i k (gen i s)

theorem genN_level (i : Item) (k : Nat) (s : Scene) :
    level (genN i k s) = level s + k := by
  induction k generalizing s with
  | zero => rfl
  | succ k ih =>
    show level (genN i k (gen i s)) = level s + (k + 1)
    rw [ih, gen_level_add_one, Nat.add_assoc, Nat.add_comm 1 k]

theorem nest_level_gt (i : Item) (s : Scene) : level s < level (Scene.nest i s) :=
  Nat.lt_succ_self (level s)

inductive Below : Scene → Scene → Prop where
  | refl (s : Scene) : Below s s
  | step {s t : Scene} (i : Item) : Below s t → Below s (Scene.nest i t)

theorem below_trans {a b c : Scene} (h1 : Below a b) (h2 : Below b c) : Below a c := by
  induction h2 with
  | refl => exact h1
  | step i _ ih => exact Below.step i ih

end TDCA.FractalScene
