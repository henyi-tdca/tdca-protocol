/-
  TDCA 形式化证明课题 · M1 · 类型骨架（Basic）
  ============================================================================
  归属：本课题（M1）
  状态：本机已机验（2026-09-22，Lean 4.34.0-rc2）——lake build 0 error、逐件 exit 0、零 sorry；**非 CI 机验**，不得称「已证明」
        首次机验须由 CI（lake env lean）或外部通道执行；**不得**声称已证明。

  模型假设（**显式，不得省略**）：
   · 制度函数以「全函数 + Option 输出」建模**部分性**——`none` 表未定义/熔断
     （对齐 M-5 的守卫写法：守卫不通过即不在定义域，产出以 `none` 表示）；
   · **确定性**：同输入同输出——Lean 中即 `f` 为函数（同值同像）；
   · **记录完备性 / 重算可行性**：抽象为「`Verify` 能重算 `f x` 并比对」，
     即 `Verify` 只依赖 `f` 与 `x`（不外求信息）；
   · D / R 为任意类型；`R` 需 `DecidableEq`（比对可判定）。
   · **不标「绝对安全」**：本骨架刻画「重算比对」的完备/可靠与广义逆的代数性质，
     不含对真实制度行为的强断言；外部接口与真实数据皆为模型外因素。
-/
import Mathlib.Data.Real.Basic

namespace TDCA.MetaInverse

/-- 制度函数（抽象层）：`D → Option R`；`none` 表示未定义 / 熔断（部分性） -/
abbrev InstFun (D R : Type) := D → Option R

/-- 审计验证器（**重算比对**形态）：
    给定记录 `y` 与输入 `x`，重算 `f x` 并与 `y` 比对；未定义则直接拒绝。 -/
def Verify {D R : Type} [DecidableEq R] (f : D → Option R) (y : R) (x : D) : Bool :=
  match f x with
  | some y' => decide (y' = y)
  | none => false

/-- 右逆（还原函数）骨架：`R → D` 的截面选择（像集外取值由调用方另定） -/
abbrev RightInv (D R : Type) := R → D

end TDCA.MetaInverse
