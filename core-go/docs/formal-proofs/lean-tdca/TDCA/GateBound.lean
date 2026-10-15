/-
  TDCA 形式化证明课题 · 智能体定义骨架 P3 · 闸门有界误差（GateBound）
  ============================================================================
  施工：四条形式化陈述骨架 · P3（交办令 TDCA-HANDOFF-FORMAL-AGENT-DEFINITION-001）
  状态：本机机验（2026-10-16，Lean 4.34.0-rc2）——exit 0、零 sorry；**非 CI 机验**，
        对外不得称「已证明」（表述与机验纪律，与在册各件同）。

  建模方式：与在册 ε-可加性模块（TDCA.EpsAdd）同法——**建模假设与数学引理在类型层分离**：
  GateModel 之三组不等式前提（hpos／hgl／hle1／hmax）为**显式建模假设字段**（⛔ 非数学结论）；
  数学部分（可机验）＝主定理 gate_bounded（收缩归纳）＋对照引理 no_gate_accumulates（线性累积归纳）。

  模型假设（显式，不得省略）：
   A1 闸门强度 g : ℕ → ℝ 一致有下界 g_min > 0 且每步 g k ≤ 1（收缩因子 1 − g k ∈ [0, 1−g_min]）；
   A2 每步扰动 eps : ℕ → ℝ 一致有上界 |eps k| ≤ eps_max（L-ε 同口径，建模假设非定理）；
   A3 初值 e0 显式入模（⛔ 不得省略）：主定理之界含初值项 max |e0| (eps_max / g_min)；
   A4 ℝ 承载（与在册 Mathlib 先例一致；离散 ℕ 收窄版另件，本件不冒充离散结论）。
  适用范围：抽象闸门-误差骨架层。不主张任何制度层结论；不标「绝对安全」；
  对外表述限「本机机验」。⛔ 本件不含任何性能／物理主张。

  三态终态声明：本件两条定理均为内核可检完整证明（proved，以显式假设为前提）；
  对照引理备注：无闸门实例（g ≡ 0）与 A1（g_min > 0）在 GateModel 字段下不相容——
  该引理按设计骨架以归纳直证（不假道矛盾），其内容即无闸门递推 e(k+1) = e k + eps k 之线性累积口径，
  与在册 EpsAdd 之 ε(n) ≤ n·ε 同形；其前提组之不相容性如实注明（refuted 载体下的条件对照）。
-/

import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Ring

namespace TDCA.GateBound

/-- 闸门模型（建模假设 A1–A3：三组不等式前提为显式字段，⛔ 非数学结论）。 -/
structure GateModel where
  /-- 闸门强度（建模参数） -/
  g       : ℕ → ℝ
  /-- 闸门强度一致下界（建模假设 A1） -/
  g_min   : ℝ
  /-- 建模假设：0 < g_min -/
  hpos    : 0 < g_min
  /-- 建模假设：∀ k, g_min ≤ g k -/
  hgl     : ∀ k, g_min ≤ g k
  /-- 建模假设：∀ k, g k ≤ 1（收缩因子非负） -/
  hle1    : ∀ k, g k ≤ 1
  /-- 每步扰动（建模参数） -/
  eps     : ℕ → ℝ
  /-- 每步扰动一致上界（建模假设 A2） -/
  eps_max : ℝ
  /-- 建模假设：∀ k, |eps k| ≤ eps_max（即 L-ε 口径） -/
  hmax    : ∀ k, |eps k| ≤ eps_max
  /-- 初值（建模参数 A3：⛔ 显式入模，不得省略） -/
  e0      : ℝ

/-- 单步更新：e(k+1) = (1 − g k) · e k + eps k（与提案骨架符号一致）。 -/
def e (M : GateModel) : ℕ → ℝ
  | 0     => M.e0
  | k + 1 => (1 - M.g k) * e M k + M.eps k

/-- 主定理：有闸门 ⟹ 误差一致有界（与步数无关；含初值项 max |e0| (eps_max / g_min)）。 -/
theorem gate_bounded (M : GateModel) (k : ℕ) :
    |e M k| ≤ max |M.e0| (M.eps_max / M.g_min) := by
  induction k with
  | zero =>
    calc |e M 0| = |M.e0| := rfl
      _ ≤ max |M.e0| (M.eps_max / M.g_min) := le_max_left _ _
  | succ k ih =>
    have hMnn : (0:ℝ) ≤ max |M.e0| (M.eps_max / M.g_min) :=
      le_trans (abs_nonneg M.e0) (le_max_left |M.e0| (M.eps_max / M.g_min))
    have hgk : (0:ℝ) ≤ 1 - M.g k := sub_nonneg.mpr (M.hle1 k)
    have hgmM : M.eps_max ≤ M.g k * max |M.e0| (M.eps_max / M.g_min) := by
      have hdiv := (div_le_iff₀ M.hpos).mp
        (le_max_right |M.e0| (M.eps_max / M.g_min))
      have h1' : max |M.e0| (M.eps_max / M.g_min) * M.g_min
               ≤ max |M.e0| (M.eps_max / M.g_min) * M.g k :=
        mul_le_mul_of_nonneg_left (M.hgl k) hMnn
      calc M.eps_max ≤ max |M.e0| (M.eps_max / M.g_min) * M.g_min := hdiv
        _ ≤ max |M.e0| (M.eps_max / M.g_min) * M.g k := h1'
        _ = M.g k * max |M.e0| (M.eps_max / M.g_min) := mul_comm _ _
    have h2 : (1 - M.g k) * max |M.e0| (M.eps_max / M.g_min) + M.eps_max
            ≤ max |M.e0| (M.eps_max / M.g_min) := by
      have h3 : (1 - M.g k) * max |M.e0| (M.eps_max / M.g_min)
              + M.g k * max |M.e0| (M.eps_max / M.g_min)
              = max |M.e0| (M.eps_max / M.g_min) := by ring
      calc (1 - M.g k) * max |M.e0| (M.eps_max / M.g_min) + M.eps_max
          ≤ (1 - M.g k) * max |M.e0| (M.eps_max / M.g_min)
            + M.g k * max |M.e0| (M.eps_max / M.g_min) :=
            add_le_add_right hgmM _
        _ = max |M.e0| (M.eps_max / M.g_min) := h3
    calc |e M (k + 1)| = |(1 - M.g k) * e M k + M.eps k| := rfl
      _ ≤ |(1 - M.g k) * e M k| + |M.eps k| := abs_add_le _ _
      _ = |1 - M.g k| * |e M k| + |M.eps k| := by rw [abs_mul]
      _ = (1 - M.g k) * |e M k| + |M.eps k| := by rw [abs_of_nonneg hgk]
      _ ≤ (1 - M.g k) * max |M.e0| (M.eps_max / M.g_min) + M.eps_max :=
          add_le_add (mul_le_mul_of_nonneg_left ih hgk) (M.hmax k)
      _ ≤ max |M.e0| (M.eps_max / M.g_min) := h2

/-- 对照引理：无闸门（g ≡ 0）⟹ 线性累积 |e n| ≤ |e0| + n · eps_max（接在册 EpsAdd 线性口径）。
    如实注明：无闸门与 GateModel 之 A1（g_min > 0 ∧ g_min ≤ g k）不相容——
    本引理按设计骨架以归纳直证（不假道矛盾），其前提组之不相容性即「无闸门须另立模型」之形式化记录。 -/
theorem no_gate_accumulates (M : GateModel) (hg : ∀ k, M.g k = 0) (n : ℕ) :
    |e M n| ≤ |M.e0| + n * M.eps_max := by
  induction n with
  | zero =>
    calc |e M 0| = |M.e0| := rfl
      _ ≤ |M.e0| + (0:ℕ) * M.eps_max := by simp
  | succ n ih =>
    have hrw : (1 - M.g n) * e M n + M.eps n = e M n + M.eps n := by
      rw [hg n]; ring
    calc |e M (n + 1)| = |(1 - M.g n) * e M n + M.eps n| := rfl
      _ = |e M n + M.eps n| := by rw [hrw]
      _ ≤ |e M n| + |M.eps n| := abs_add_le _ _
      _ ≤ (|M.e0| + n * M.eps_max) + M.eps_max := add_le_add ih (M.hmax n)
      _ = |M.e0| + (n + 1:ℕ) * M.eps_max := by
          rw [Nat.cast_add, Nat.cast_one]; ring

end TDCA.GateBound
