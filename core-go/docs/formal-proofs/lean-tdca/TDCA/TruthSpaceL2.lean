/-
  TDCA 形式化线第三批 · PRP-TRI-001 · 三空间真值之代数结构 · L2 子集
  （样本代数构成海廷代数 · 逐式穷举）
  ============================================================================
  件性质：智库研究 → 机验载体件（新增，只增不改；⛔ 不改任何既有模块）
  归属：形式化线第三批 序 P2-2；程序依据 TDCA-STD-INSTITUTION-PROMOTION-001 步②/③
  ⛔ 对外表述限「本机机验」（⛔ 非 CI 机验）；⛔ 不得称「已证明／绝对安全」
  ⚠️ 性质如实（要紧）：本件所证 ⛔ 非「任意三空间真值域皆构成海廷代数」，
     而是**条件化之有限样本代数判定**：「给定模型假设 M1–M3 之四点链样本代数，
     其（meet／join／相对伪补）逐式满足海廷代数公理」—— ⛔ 不得外推为一般定理

  机验目标（L2 子集 · 逐式穷举 · ⛔ 不外推）：
   L2-1 格公理：meet／join 之交换、结合、幂等、吸收（四条 × 二算子）
   L2-2 有界与非退化：⊥ 为 meet 之零元、⊤ 为 join 之幺元；⊥ ≠ ⊤
   L2-3 分配律：meet 对 join 分配、join 对 meet 分配（格分配 ⟹ 分配格）
   L2-4 海廷伴随（相对伪补）：`meet a c ≤ b ↔ c ≤ (a ⇒ b)`（逐式穷举）
   L2-5 伪补一致：`compl a = (a ⇒ ⊥)`；且排中律**非普遍**成立（与 L1 之 T-3／T-4 同向）

  模型假设（显式，不得省略）：
   M1 真值域 = 四点链 ⊥ < und < neg < ⊤（有限、可判定；⛔ 非完整海廷代数主张）
   M2 分类：Pos := ⊤ · Neg := neg · Und := und；⊥ 为逻辑锚（不属三空间）
   M3 运算：meet = 取下界（合取）· join = 取上界（析取）· compl = 伪补（a ⇒ ⊥）
      · `⇒`（相对伪补）＝ `if a ≤ b then ⊤ else b`（链上之海廷蕴含，照极大性定义）
   M4 ⚠️ 本件以**有限穷举**（`cases` 逐支判定）判定逐式；⭐ 一般三空间真值域（非链／非有限）⛔ **不在本件**
   M5 ⛔ 本件不作制度主张；语义面与制度层「负空间三不可」之对接归解释文件与制度层
   M6 本件为 L2 之**独立载体**（⭐ 照「零依赖」纪律：⛔ 不 import Mathlib、⛔ 不引用其它 TDCA 件，
      故与 L1 件**不共享模块**，重复其载体定义）；⚠️ 零依赖下**无 `Fintype`** ⟹ 逐式判定
      以 `cases` 穷举（⛔ 不用 `decide` 处理量词）

  数据性质：形式化（确定性、无随机量、无外部数据）
  依赖纪律：本件零依赖（不 import Mathlib，亦不引用其它 TDCA 件）
  机验状态：本机机验；⛔ 非 CI 机验
-/

namespace TDCA.TruthSpaceL2

/-! ## 一、载体（模型假设 M1 / M2） -/

/-- 真值域：四点链 `⊥ < und < neg < ⊤`（模型假设 M1） -/
inductive TV : Type
  | bot | und | neg | pos
  deriving DecidableEq, Repr

open TV

/-- 层级序：`⊥ ↦ 0`、`und ↦ 1`、`neg ↦ 2`、`⊤ ↦ 3`（模型假设 M1） -/
def rank : TV → Nat
  | bot => 0
  | und => 1
  | neg => 2
  | pos => 3

/-- 序关系（`a ≤ b`）（模型假设 M1） -/
def Le (a b : TV) : Prop := rank a ≤ rank b

instance : DecidableRel Le := fun a b => Nat.decLe (rank a) (rank b)

/-! ## 二、运算（模型假设 M3） -/

/-- 合取：取下界 -/
def meet : TV → TV → TV
  | .bot, _ => .bot
  | _, .bot => .bot
  | .und, _ => .und
  | _, .und => .und
  | .neg, _ => .neg
  | _, .neg => .neg
  | .pos, .pos => .pos

/-- 析取：取上界 -/
def join : TV → TV → TV
  | .pos, _ => .pos
  | _, .pos => .pos
  | .neg, _ => .neg
  | _, .neg => .neg
  | .und, _ => .und
  | _, .und => .und
  | .bot, .bot => .bot

/-- 伪补（`a ⇒ ⊥`，即 L1 之 `compl`） -/
def compl : TV → TV
  | .bot => .pos
  | .und => .bot
  | .neg => .bot
  | .pos => .bot

/-- 相对伪补（海廷蕴含）`a ⇒ b` ＝ 满足 `a ∧ c ≤ b` 之极大 `c`（链上取其值） -/
def impl (a b : TV) : TV := if Le a b then pos else b

/-! ## 三、L2-1 格公理（逐式穷举） -/

theorem meet_comm (a b : TV) : meet a b = meet b a := by
  cases a <;> cases b <;> decide

theorem meet_assoc (a b c : TV) : meet (meet a b) c = meet a (meet b c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem meet_idem (a : TV) : meet a a = a := by
  cases a <;> decide

theorem join_comm (a b : TV) : join a b = join b a := by
  cases a <;> cases b <;> decide

theorem join_assoc (a b c : TV) : join (join a b) c = join a (join b c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem join_idem (a : TV) : join a a = a := by
  cases a <;> decide

theorem meet_absorbs_join (a b : TV) : meet a (join a b) = a := by
  cases a <;> cases b <;> decide

theorem join_absorbs_meet (a b : TV) : join a (meet a b) = a := by
  cases a <;> cases b <;> decide

/-! ## 四、L2-2 有界与非退化 -/

theorem bot_meet (a : TV) : meet bot a = bot := by
  cases a <;> decide

theorem top_join (a : TV) : join pos a = pos := by
  cases a <;> decide

theorem bot_ne_top : (bot : TV) ≠ pos := by decide

/-! ## 五、L2-3 分配律 -/

theorem meet_distrib_join (a b c : TV) : meet a (join b c) = join (meet a b) (meet a c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem join_distrib_meet (a b c : TV) : join a (meet b c) = meet (join a b) (join a c) := by
  cases a <;> cases b <;> cases c <;> decide

/-! ## 六、L2-4 海廷伴随（相对伪补之刻划） -/

/-- 海廷伴随：`a ∧ c ≤ b ↔ c ≤ (a ⇒ b)`（逐式穷举） -/
theorem heyting_adjunction (a b c : TV) : Le (meet a c) b ↔ Le c (impl a b) := by
  cases a <;> cases b <;> cases c <;> decide

theorem impl_refl (a : TV) : impl a a = pos := by
  cases a <;> decide

/-- 伪补之基本性质：`a ∧ (a ⇒ ⊥) ≤ ⊥` -/
theorem impl_bot_meet_le (a : TV) : Le (meet a (impl a bot)) bot := by
  cases a <;> decide

/-! ## 七、L2-5 伪补一致与排中非普遍 -/

/-- 伪补一致：`compl a = (a ⇒ ⊥)` -/
theorem compl_eq_impl_bot (a : TV) : compl a = impl a bot := by
  cases a <;> decide

/-- 排中律**非普遍**成立（反例：负空间元；与 L1 之 T-3／T-4 同向） -/
theorem excluded_middle_not_universal : ¬ (∀ a : TV, join a (compl a) = pos) := by
  intro h
  exact absurd (h neg) (by decide)

/-! ## 八、机验基线实例（可判定自检） -/

example : meet und neg = und := by decide

example : join und (compl und) = und := by decide

example : impl neg bot = bot := by decide

example : impl bot und = pos := by decide

end TDCA.TruthSpaceL2
