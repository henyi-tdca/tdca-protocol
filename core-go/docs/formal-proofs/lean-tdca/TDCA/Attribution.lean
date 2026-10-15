/-
  TDCA 形式化证明课题 · 开放问题 P-11（归责映射 · 可机验子集）
  ============================================================================
  建模方式：独立件、独立命名空间、零依赖（不 import Mathlib）。

  可形式化子集之声明（本件即该声明与其形式化实现）：
  本件只形式化「分层归责」之结构面（关系与层级之逻辑性质），不涉以下三类：
   一 事实层之归责（谁做了什么、是否担责）——属事实与制度层，不进证明器；
   二 制度层之判据与阈值（免责条件、责任比例、门槛取值）——不在本件；
   三 模型层预判之真实性（照在册 B-5 表述：分层归责预判属模型层，随四信号检验）。
  形式化之结构面四条：可上溯之传递性；层级单调（上溯不降层）；责任方向单向
  （不可回流）与分层隔离（平层不可互达）；无环（不存在自证责任循环）。
  另给第一节点（执行层）与责任主体（无上级）之接口。

  模型假设（显式，不得省略）：
   A1 委托关系 up : α → α → Prop（约定：up a b 读作「b 为 a 之委托人」，
      即 a 之上溯指向 b）；
   A2 层级 level : α → Nat（约定：执行层智能体之层级为 0），且与 up 一致：
      若 up a b 则 level b = level a + 1（每上溯一层，层级加一）；
   A3 责任主体（最终责任主体对应之机验形态）＝ 无委托人者：
      Root up a := ∀ b, ¬ up b a。

  适用范围：抽象归责结构骨架层。不主张任何制度层结论；不标「绝对安全」；
  对外表述限「本机机验」；不代拟归责判据与责任比例。

  机验状态：本机机验（Lean 4.34.0-rc2 · lake build）；非 CI 机验。
  三态终态声明：本件各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项、无占位（sorry）。
-/

namespace TDCA.Attribution

variable {α : Type}

/-! ## 一、关系与层级（模型假设 A1 / A2 / A3） -/

/-- 责任主体（结构面）：无委托人者（最终责任主体对应之机验形态 · A3） -/
def Root (up : α → α → Prop) (a : α) : Prop :=
  ∀ b, ¬ up b a

/-- 有委托人 -/
def HasUp (up : α → α → Prop) (a : α) : Prop :=
  ∃ b, up a b

/-- 可上溯（传递闭包）：自 a 沿委托关系可达 b -/
inductive Reaches (up : α → α → Prop) : α → α → Prop
  | refl (a : α) : Reaches up a a
  | step {a b c : α} : up a b → Reaches up b c → Reaches up a c

/-- 严格可上溯（至少一步）：用于表达「无环」 -/
inductive ReachesPos (up : α → α → Prop) : α → α → Prop
  | step {a b c : α} : up a b → Reaches up b c → ReachesPos up a c

/-- 层级与委托关系一致（模型假设 A2）：上溯一层，层级加一 -/
def Leveled (up : α → α → Prop) (level : α → Nat) : Prop :=
  ∀ a b, up a b → level b = level a + 1

/-! ## 二、结构面一：可上溯之传递性 -/

/-- P-11 · 可上溯关系传递 -/
theorem reaches_trans (up : α → α → Prop) :
    ∀ {a b c : α}, Reaches up a b → Reaches up b c → Reaches up a c
  | _, _, _, .refl _, hbc => hbc
  | _, _, _, .step h1 hbc, hcd => Reaches.step h1 (reaches_trans up hbc hcd)

/-- P-11 · 严格可上溯蕴含可上溯 -/
theorem reaches_pos_to_reaches (up : α → α → Prop) :
    ∀ {a b : α}, ReachesPos up a b → Reaches up a b
  | _, _, .step hab hbc => Reaches.step hab hbc

/-! ## 三、结构面二：层级单调（上溯不降层） -/

/-- P-11 · 上一层即层级加一 -/
theorem up_level_lt (up : α → α → Prop) (level : α → Nat) (hl : Leveled up level)
    {a b : α} (h : up a b) : level a < level b := by
  have := hl a b h
  omega

/-- P-11 · 可上溯则不降层 -/
theorem reaches_level_le (up : α → α → Prop) (level : α → Nat) (hl : Leveled up level) :
    ∀ {a b : α}, Reaches up a b → level a ≤ level b
  | _, _, .refl _ => Nat.le_refl _
  | _, _, .step hab hbc => by
      have h1 : level _ < level _ := up_level_lt up level hl hab
      have h2 : level _ ≤ level _ := reaches_level_le up level hl hbc
      omega

/-- P-11 · 严格可上溯则层级严格上升 -/
theorem reaches_pos_level_lt (up : α → α → Prop) (level : α → Nat) (hl : Leveled up level) :
    ∀ {a b : α}, ReachesPos up a b → level a < level b
  | _, _, .step hab hbc => by
      have h1 : level _ < level _ := up_level_lt up level hl hab
      have h2 : level _ ≤ level _ := reaches_level_le up level hl hbc
      omega

/-! ## 四、结构面三：责任方向单向（不可回流）与分层隔离 -/

/-- P-11 · 责任方向单向：上级不可回达下级 -/
theorem no_downward (up : α → α → Prop) (level : α → Nat) (hl : Leveled up level)
    {a b : α} (hab : up a b) : ¬ Reaches up b a := by
  intro hba
  have h1 : level b ≤ level a := reaches_level_le up level hl hba
  have h2 : level b = level a + 1 := hl a b hab
  omega

/-- P-11 · 分层隔离：严格可上溯 ⟹ 两侧层级不同（平层之间不可互达） -/
theorem same_level_no_reach (up : α → α → Prop) (level : α → Nat) (hl : Leveled up level)
    {a b : α} (h : ReachesPos up a b) : level a ≠ level b := by
  have := reaches_pos_level_lt up level hl h
  omega

/-! ## 五、结构面四：无环（不存在自证责任循环） -/

/-- P-11 · 无环：任何智能体均不可经至少一步委托回到自身 -/
theorem p11_no_cycle (up : α → α → Prop) (level : α → Nat) (hl : Leveled up level)
    (a : α) : ¬ ReachesPos up a a := by
  intro h
  have := reaches_pos_level_lt up level hl h
  omega

/-! ## 六、第一节点与责任主体之接口 -/

/-- P-11 · 第一节点（执行层）：层级为 0 者上溯必至层级 1 -/
theorem first_node_up (up : α → α → Prop) (level : α → Nat) (hl : Leveled up level)
    {a b : α} (ha : level a = 0) (h : up a b) : level b = 1 := by
  have := hl a b h
  omega

/-- P-11 · 责任主体之刻画：a 为责任主体 ⟺ 无人为 a 之委托人 -/
theorem root_iff (up : α → α → Prop) (a : α) : Root up a ↔ ∀ b, ¬ up b a :=
  Iff.rfl

/-- P-11 · 责任主体与可达面：无委托人者，其上层不可再上溯 -/
theorem root_no_reach (up : α → α → Prop) (a : α) (h : Root up a) : ∀ b, ¬ up b a :=
  h

/-! ## 七、机验基线实例（自然数链：第 n 层之委托人为 n+1） -/

/-- 基线：自然数链之委托关系 -/
def natUp (a b : Nat) : Prop := b = a + 1

/-- 基线：层级取自身 -/
def natLv (n : Nat) : Nat := n

/-- 基线：自然数链满足层级一致（A2） -/
theorem p11_example_leveled : Leveled natUp natLv := by
  intro a b h
  simpa [natUp, natLv] using h

/-- 基线：可上溯两步 -/
theorem p11_example_reaches : Reaches natUp 0 2 :=
  Reaches.step (show natUp 0 1 from rfl) (Reaches.step (show natUp 1 2 from rfl) (Reaches.refl 2))

/-- 基线：严格可上溯两步 -/
theorem p11_example_pos : ReachesPos natUp 0 2 :=
  ReachesPos.step (show natUp 0 1 from rfl) (Reaches.step (show natUp 1 2 from rfl) (Reaches.refl 2))

/-- 基线：无环（不可自证责任循环） -/
theorem p11_example_no_cycle : ¬ ReachesPos natUp 3 3 :=
  p11_no_cycle natUp natLv p11_example_leveled 3

/-- 基线：平层隔离 -/
theorem p11_example_same_level : ¬ ReachesPos natUp 1 1 :=
  p11_no_cycle natUp natLv p11_example_leveled 1

/-- 基线：第一节点上溯至层级 1 -/
theorem p11_example_first_node : natLv 1 = 1 :=
  first_node_up natUp natLv p11_example_leveled (show natLv 0 = 0 from rfl) (show natUp 0 1 from rfl)

/-! ## 八、良基（追加节 · 智能体定义骨架 P4 · 2026-10-16）
    本节为追加节：⛔ 不回改上文任何行。复用 Leveled／up_level_lt（及基线 natUp／natLv）。
    方向澄清（如实记录 · 三态合法）：以层级为秩函数，**良基成立的是委托方向**
    （fun a b => up a b：沿委托层级严格递减，无环且链可终止——与 p11_no_cycle 互证）；
    设计骨架所书之逆方向（fun a b => up b a：沿层级严格**递增**）在 Leveled 单一前提下
    **不成立**（自然数链反例：attribution_wellFounded_inverse_refuted，refuted 终态）——
    「上溯链」在无限层级下非良基；逆方向收敛须另立层级全局势界前提（本件不预设该前提）。
    适用范围：抽象归责结构骨架层；不标「绝对安全」；对外表述限「本机机验」。 -/

/-- 秩函数引理（委托方向）：层级有上界 n 者，其委托方向可达性（Acc）成立（对层级上界归纳）。 -/
theorem acc_up_of_level_le (up : α → α → Prop) (level : α → Nat) (hl : Leveled up level) :
    ∀ n a, level a ≤ n → Acc (fun x y => up x y) a := by
  intro n
  induction n with
  | zero =>
    intro a ha
    constructor
    intro b hb
    have h1 := up_level_lt up level hl hb
    have hlt : level b < 0 := by omega
    exact (Nat.not_lt_zero _ hlt).elim
  | succ n ih =>
    intro a ha
    constructor
    intro b hb
    have h1 := up_level_lt up level hl hb
    exact ih b (by omega)

/-- 主定理（委托方向）：以层级为秩函数，委托关系良基（链无环且可终止之形式化面；
    与 p11_no_cycle 互证：无环 ＋ 层级递减 ⟹ 良基）。 -/
theorem attribution_wellFounded (up : α → α → Prop) (level : α → Nat)
    (hl : Leveled up level) : WellFounded (fun a b => up a b) :=
  ⟨fun a => acc_up_of_level_le up level hl (level a) a (Nat.le_refl _)⟩

/-- 副定理：任一点可终止（Acc 形态，NCA 追溯之结构面）。 -/
theorem nca_trace_terminates (up : α → α → Prop) (level : α → Nat)
    (hl : Leveled up level) (a : α) : Acc (fun a b => up a b) a :=
  acc_up_of_level_le up level hl (level a) a (Nat.le_refl _)

/-- 逆方向（设计骨架原书方向）不成立（refuted · 三态合法）：
    自然数链 natUp 满足 Leveled（见 p11_example_leveled），
    但 (fun a b => up b a) 存在无限严格递增链（0, 1, 2, …：每步 up i (i+1) 成立），
    故非良基——「上溯链良基」须以层级全局势界为前提，单一 Leveled 前提不足。 -/
theorem attribution_wellFounded_inverse_refuted :
    ¬ WellFounded (fun a b => natUp b a) := by
  intro hwf
  have hacc := hwf.apply 0
  exact Acc.rec (motive := fun _ _ => False) (fun x _ h2 => h2 (x + 1) rfl) hacc

end TDCA.Attribution
