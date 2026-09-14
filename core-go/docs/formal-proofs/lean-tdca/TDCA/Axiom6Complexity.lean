/-!
  TDCA · 公理 6 · 约束 4（复杂度）—— 条件形态附录

  ⚠️ **范围声明**：约束 4 属**工程/实现层**性质，已由 `pkg/enforce/axiom6_verify.go`
     的断言覆盖（Go 通道）；本件**不在证明器主体范围**（主体见 `TDCA.Axiom6` 的约束 1/2/3），
     仅为把约束 4 的**结构形态**录入第二通道（Lean）的**条件附录**。

  ⚠️ **建模参数声明**：本件中的复杂度读数（`t_finv` / `t_verify` / `t_verify_inst` / `t_g` 等 ℕ 参数）
     是**建模参数**——抽象赋值，⛔ **不是**从任何程序/代码推出的量；
     其约束关系（如 `t_finv ≤ t_verify + c`）以**假设**形式给出，⛔ **不得**作为已证结论引用。

  ⚠️ **conditional 标注**：本件全部定理均为 **conditional** —— 结论仅在所列假设
     （建模参数之间的大小关系）成立时成立；假设本身本件不证。

  ⚠️ **边界**：
     · ⛔ 不得把本件读作「复杂度已从程序推出」；
     · ⛔ 不得据此声称「四约束全证」（约束 4 在本通道仅为条件形态附录）；
     · 权威件参照形态：`T(f⁻) = T(Verify) + O(1)` ／ `T(g) = O(1)` ／ `Verify_institution ≥ Verify`
       ／ `C_max = O(16·c(x))`；其中 `C_max = O(n)` 一档为 **SIMULATED 候选**（数据性质：模拟值，
       真实定标受阻于缺真实审计基准数据）—— ⛔ 引用时须保留该数据性质标注，不得暗示已实测。
-/

namespace TDCA.Axiom6Complexity

/-- 约束 4 · 条件形态（f⁻ 对 Verify 的常数开销传递）：
    **假设**（建模参数）：① `t_finv ≤ t_verify + c`（f⁻ 的开销不超过验证开销加常数 `c`）；
    ② `t_verify ≤ t_verify_inst`（制度层验证开销不低于实例验证）。
    **结论（conditional）**：`t_finv ≤ t_verify_inst + c`。
    ⚠️ 本定理仅为两条**假设**之间的算术推论；假设为建模参数，本件不证。 -/
theorem constraint4_verify_bounded (t_finv t_verify t_verify_inst c : Nat)
    (h1 : t_finv ≤ t_verify + c) (h2 : t_verify ≤ t_verify_inst) :
    t_finv ≤ t_verify_inst + c :=
  Nat.le_trans h1 (Nat.add_le_add_right h2 c)

/-- 约束 4 · 条件形态（三角色合并开销上界）：
    **假设**（建模参数）：① `t_finv ≤ t_verify + c`；② `t_verify ≤ t_verify_inst`；
    ③ `t_g ≤ c_g`（g 的开销有常数界 `c_g`——「T(g) = O(1)」的参数化形态）。
    **结论（conditional）**：`t_finv + t_g ≤ t_verify_inst + (c + c_g)`。
    ⚠️ 同前：算术推论；假设为建模参数，本件不证。 -/
theorem constraint4_total_bounded (t_finv t_verify t_verify_inst c t_g c_g : Nat)
    (h1 : t_finv ≤ t_verify + c) (h2 : t_verify ≤ t_verify_inst) (h3 : t_g ≤ c_g) :
    t_finv + t_g ≤ t_verify_inst + (c + c_g) := by
  have hb : t_finv ≤ t_verify_inst + c := constraint4_verify_bounded _ _ _ _ h1 h2
  calc t_finv + t_g ≤ (t_verify_inst + c) + c_g := Nat.add_le_add hb h3
    _ = t_verify_inst + (c + c_g) := by rw [Nat.add_assoc]

end TDCA.Axiom6Complexity
