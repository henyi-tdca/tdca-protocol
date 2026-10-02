/-
  TDCA 形式化证明课题 · 开放问题 P-5（命题 3.10 认知距离不对称）· 机验面
  ============================================================================
  建模方式：独立件、独立命名空间、零依赖（不 import Mathlib）。

  在册陈述（逐字引）：
    定义 3.36：d_cognitive(a,b) = inf{ Length(γ) | γ 为连接 a,b 的认知路径 }；
    命题 3.10：d_cognitive(a,b) ≠ d_cognitive(b,a)（认知距离不对称）。
    出处：数学基础白皮书修订本（定义 3.36／3.37 与命题 3.10）；在册实现
    为工作区 tdca-protocol-tools-release 下 tdca_cognitive_distance.py。

  本件之机验面（显式声明，不得省略）：
   一 本件以「可达性」（有向路径之存在）承载命题 3.10 之不对称面：
      认知路径在册为有向，故「a 可达 b 而 b 不可达 a」即距离不对称之结构根因
      （不可达侧无有限距离）；
   二 距离取值面（下确界／最短长度之数值）与定义 3.37 之实数形态
      （Difficulty_align = exp(-d)）需实数与完备性工具，属另件另议；
   三 本件给出不对称之充分条件（构造性：单向边 ＋ 反向不可达）与必要条件
      （对称认知结构下不存在不对称）。

  模型假设（显式，不得省略）：
   D1 认知路径为有向：E : α → α → Prop（边 a b 表示自 a 至 b 一步认知可达）；
   D2 可达 ＝ 存在有向路径（自反传递闭包 Reach）；
   D3 对称认知结构：Symm E := 每条边均双向；
   D4 不对称之判定面取可达性不对称（D2 之否定侧）。

  适用范围：抽象认知图骨架层。不主张任何制度层结论；不标「绝对安全」；
  对外表述限「本机机验」；不涉任何真实认知度量数据。

  机验状态：本机机验（Lean 4.34.0-rc2 · lake build）；非 CI 机验。
  三态终态声明：本件各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项、无占位（sorry）。
-/

namespace TDCA.CogDist

variable {α : Type}

/-! ## 一、定义（模型假设 D1–D3） -/

/-- 可达（模型假设 D2）：存在有向认知路径（自反传递闭包） -/
inductive Reach (E : α → α → Prop) : α → α → Prop
  | refl (a : α) : Reach E a a
  | tail {a b c : α} : E a b → Reach E b c → Reach E a c

/-- 对称认知结构（模型假设 D3）：每条边均双向 -/
def Symm (E : α → α → Prop) : Prop :=
  ∀ a b, E a b → E b a

/-! ## 二、可达之基本性质 -/

/-- 可达关系传递 -/
theorem reach_trans (E : α → α → Prop) :
    ∀ {a b c : α}, Reach E a b → Reach E b c → Reach E a c
  | _, _, _, .refl _, hbc => hbc
  | _, _, _, .tail e hbc, hcd => Reach.tail e (reach_trans E hbc hcd)

/-- 一条边即一步可达 -/
theorem reach_of_edge (E : α → α → Prop) {a b : α} (h : E a b) : Reach E a b :=
  Reach.tail h (Reach.refl b)

/-! ## 三、P-5 · 必要面（对称结构下不存在不对称） -/

/-- P-5 · 对称认知结构 ⟹ 可达对称 -/
theorem reach_sym_of_symm (E : α → α → Prop) (hs : Symm E) :
    ∀ {a b : α}, Reach E a b → Reach E b a
  | _, _, .refl a => Reach.refl a
  | a, _, .tail (b := x) e rest =>
      reach_trans E (reach_sym_of_symm E hs rest) (Reach.tail (hs a x e) (Reach.refl a))

/-- P-5 · 必要面：对称认知结构下，不存在「单向可达」之不对称 -/
theorem p5_no_asym_in_symm (E : α → α → Prop) (hs : Symm E) {a b : α}
    (h : Reach E a b ∧ ¬ Reach E b a) : False :=
  h.2 (reach_sym_of_symm E hs h.1)

/-- P-5 · 必要面（等价形式）：对称结构 ⟹ 双向可达等价 -/
theorem p5_reach_iff_of_symm (E : α → α → Prop) (hs : Symm E) (a b : α) :
    Reach E a b ↔ Reach E b a :=
  ⟨fun h => reach_sym_of_symm E hs h, fun h => reach_sym_of_symm E hs h⟩

/-! ## 四、P-5 · 充分面（构造性：单向边 ＋ 反向不可达 ⟹ 不对称） -/

/-- P-5 · 充分面（构造性）：存在边 a 至 b 且 b 不可达 a ⟹ 可达性不对称
    —— 命题 3.10 之结构根因（不可达侧无有限距离） -/
theorem p5_asym_of_oneway (E : α → α → Prop) {a b : α} (h : E a b) (hno : ¬ Reach E b a) :
    Reach E a b ∧ ¬ Reach E b a :=
  ⟨reach_of_edge E h, hno⟩

/-- P-5 · 不对称之传递：a 单通至 b 且 b 单通至 c ⟹ a 单通至 c -/
theorem p5_asym_trans (E : α → α → Prop) {a b c : α}
    (h1 : Reach E a b ∧ ¬ Reach E b a) (h2 : Reach E b c ∧ ¬ Reach E c b) :
    Reach E a c ∧ ¬ Reach E c a :=
  ⟨reach_trans E h1.1 h2.1, fun h => h2.2 (reach_trans E h h1.1)⟩

/-! ## 五、机验基线实例 -/

/-- 基线：有向链（第 n 步指向 n+1） -/
def chainE (a b : Nat) : Prop := b = a + 1

/-- 基线：对称图（相邻双向） -/
def symE (a b : Nat) : Prop := b = a + 1 ∨ a = b + 1

/-- 基线：有向链上可达者必不降（每步加一） -/
theorem chainE_reach_le : ∀ {a b : Nat}, Reach chainE a b → a ≤ b
  | _, _, .refl _ => Nat.le_refl _
  | a, c, .tail (b := x) e rest => by
      have hx : x = a + 1 := e
      have ih : x ≤ c := chainE_reach_le rest
      omega

/-- 基线：有向链上不对称之实例（0 可达 2，而 2 不可达 0） -/
theorem p5_example_asym : Reach chainE 0 2 ∧ ¬ Reach chainE 2 0 := by
  refine ⟨?_, ?_⟩
  · exact Reach.tail (show chainE 0 1 from rfl) (Reach.tail (show chainE 1 2 from rfl) (Reach.refl 2))
  · intro h
    have ih : 2 ≤ 0 := chainE_reach_le h
    omega

/-- 基线：对称图之对称性 -/
theorem symE_symm : Symm symE := by
  intro a b h
  rcases h with h | h
  · exact Or.inr h
  · exact Or.inl h

/-- 基线：对称图双向可达 -/
theorem p5_example_symm_reach : Reach symE 0 1 ∧ Reach symE 1 0 :=
  ⟨reach_of_edge symE (show symE 0 1 from Or.inl rfl),
   reach_of_edge symE (show symE 1 0 from Or.inr rfl)⟩

/-- 基线：对称图下不存在不对称（与有向链实例对照） -/
theorem p5_example_no_asym (h : Reach symE 0 1 ∧ ¬ Reach symE 1 0) : False :=
  p5_no_asym_in_symm symE symE_symm h

end TDCA.CogDist
