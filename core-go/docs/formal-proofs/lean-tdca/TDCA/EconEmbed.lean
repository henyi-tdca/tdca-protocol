/-
  TDCA 形式化线第三批 · PRP-ECON-EMBED（拟名 · ⛔ 不沿用 ECON-001）· 成本正定性 · 条件化子集
  ============================================================================
  件性质：智库研究 → 机验载体件（新增，只增不改；⛔ 不改任何既有模块）
  归属：形式化线第三批 序 P1-2；程序依据 TDCA-STD-INSTITUTION-PROMOTION-001 步②/③
  ⛔ 对外表述限「本机机验」（⛔ 非 CI 机验）；⛔ 不得称「已证明／绝对安全」
  ⚠️ 性质如实（要紧）：本件所证 ⛔ 非「生成必有成本」，而是**条件化命题** ——
     「⭐ 给定满足正性公理的离散成本模型，含擦除操作之会话成本严格为正」；
     ⛔ 不得对外表述为「已证无免费生成」（⭐ 照审查件 `TDCA-REVIEW-FORMAL-PRP-BATCH3-001` §三.1）

  机验目标（L1 子集）：
   E-1（条件化主命题）：正性公理 ＋ 擦除计数 ≥ 1 ⟹ 会话成本 > 0
   E-2（零成本刻画之弱形态）：成本 = 0 ⟹ 擦除计数 = 0（纯只读会话）
   E-3（具体实例 · 可判定自检）：含 `erase` 之样本会话擦除计数 = 1；纯读会话 = 0

  模型假设（显式，不得省略）：
   M1 会话 = 操作列表，操作集 {read, write, erase}（离散、有限、可判定）
   M2 擦除计数 `eraseCount`：按出现次数计（结构归纳）
   M3 成本模型 `cost : Session → ℕ`；⭐ **正性公理 AX-PHY-1（离散形态）**：
      ∃ `λ : ℕ`，`λ ≥ 1` 且 `∀ s, λ * eraseCount s ≤ cost s`
      —— ⚠️ ⭐ **该公理为经验／物理前提，⛔ 不进 Lean 作为定理**，仅作**显式假设**（条件化隔离）
   M4 ⚠️ 本 L1 件以 **`ℕ`** 建模成本（离散、可判定）；⭐ 提案之 **`ℚ` 形态**（`cost : Session → ℚ`
      ＋ `λ : ℚ`，`hλ : λ > 0`）⭐ **属 L2 另件**，⛔ 不在本件范围内（收窄不硬证）
   M5 本件不作制度主张；「无免费生成」之制度含义归制度层与 ECON-EMBED 研究件

  数据性质：形式化（确定性、无随机量、无外部数据）
  依赖纪律：本件零依赖（不 import Mathlib，亦不引用其它 TDCA 件）
-/

namespace TDCA.EconEmbed

/-! ## 载体结构（模型假设 M1 / M2） -/

/-- 会话操作（模型假设 M1） -/
inductive Op : Type
  | read | write | erase
  deriving DecidableEq, Repr

/-- 会话：操作列表（模型假设 M1） -/
abbrev Session := List Op

/-- 擦除计数：`erase` 之出现次数（模型假设 M2） -/
def eraseCount : Session → Nat
  | [] => 0
  | Op.erase :: t => eraseCount t + 1
  | _ :: t => eraseCount t

/-! ## E-1 条件化主命题（正性公理 ⇒ 含擦除会话成本为正） -/

theorem cost_pos_of_erase {cost : Session → Nat} {lam : Nat} (hlam : 0 < lam)
    (hax : ∀ s : Session, lam * eraseCount s ≤ cost s) {s : Session}
    (hs : 1 ≤ eraseCount s) : 0 < cost s := by
  have hs' : 0 < eraseCount s := Nat.lt_of_lt_of_le Nat.zero_lt_one hs
  have h2 : 0 < lam * eraseCount s := Nat.mul_pos hlam hs'
  exact Nat.lt_of_lt_of_le h2 (hax s)

/-! ## E-2 零成本刻画（弱形态：成本为零 ⇒ 无擦除） -/

theorem erase_zero_of_cost_zero {cost : Session → Nat} {lam : Nat} (hlam : 0 < lam)
    (hax : ∀ s : Session, lam * eraseCount s ≤ cost s) {s : Session}
    (hz : cost s = 0) : eraseCount s = 0 := by
  rcases Nat.eq_zero_or_pos (eraseCount s) with h | h
  · exact h
  · have hc : 0 < cost s := cost_pos_of_erase hlam hax h
    rw [hz] at hc
    exact absurd hc (Nat.lt_irrefl 0)

/-! ## E-3 具体实例（可判定自检） -/

example : eraseCount [Op.read, Op.erase, Op.write] = 1 := by decide

example : eraseCount [Op.read, Op.write] = 0 := by decide

example : eraseCount ([] : Session) = 0 := by decide

/-- E-3′ 条件化实例：λ = 1、成本恒等于擦除计数时，含擦除会话成本为正 -/
example : 0 < (1 : Nat) * eraseCount [Op.erase] := by decide

end TDCA.EconEmbed