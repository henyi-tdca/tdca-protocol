/-
  TDCA 形式化证明课题 · 失效半径有界性 · N-1（信任链分支结构）
  ============================================================================
  建模方式：独立件、独立命名空间。信任链建模为「分支的有限集合」，失效建模为
  「分支内某位置的失效事件（带失效时点序号）」，受影响性与记录存活性按
  （分支 × 位置 × 序号）三轴切片定义——四条判据各自落为内核可检的刻画式定理。

  模型假设（显式，不得省略）：
   A1 信任链＝分支的有限集合；分支＝同一物理锚点下的节点线性序列；
     「向下传导方向」＝分支内位置序号增大方向；
   A2 失效事件 f 携带：所在分支（含「该分支 ∈ 链」的在链证据）、分支内位置 f.pos、
     失效时点序号 f.seq（沿记录签发轴单调）；失效点必在链上，无「链外失效」；
   A3 受影响谓词 affected 定义即刻画：节点（br, p）受 f 影响 ⟺ br = f.br 且 f.pos ≤ p
     （同分支、不早于失效位置）——向下传导、向上隔离皆为定义层面的事实；
   A4 记录存活谓词 survives 定义即刻画：r 于失效后仍可追溯 ⟺ 非（r 受影响 且 r.seq ≥ f.seq）
     ——失效只按「受影响集 × 时点」切片其后，不回溯撤销；
   A5 不建模跨分支共享状态／跨分支依赖；若真实部署存在共享状态（如全局计数器），
     单点失效的影响面超出本件刻画，不得援引本件结论覆盖之。

  适用范围：工程哲学 §2.3「向下传导、向上隔离；一次物理锚点失效是一个设备出局，
  不是全网重置」的可机验抽象骨架。真实平台的密钥轮换、锚点重锚等动态属工程层，
  不在本件形式化范围。

  机验状态：本机已机验（Lean 4.34.0-rc2，lake build 0 error）；非 CI 机验。
  三态终态声明：本节各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项。⛔ 不标「绝对安全」；对外表述限「本机机验」。

  依赖纪律：本件零依赖（不 import Mathlib，亦不引用其它 TDCA 件）——
  失效半径骨架只需 Nat 序事实，同时隔离上游弃用告警面；
  如后续扩充需 Mathlib 引理，另件处理。
-/

namespace TDCA.FailureRadius

/-! ## 载体结构（模型假设 A1 / A2） -/

/-- 链上节点：裸序号，无身份语义 -/
structure ChainNode where
  id : Nat

/-- 分支：同一物理锚点下的节点线性序列（位置＝序列内下标） -/
structure Branch where
  nodes : List ChainNode

/-- 信任链：分支的有限集合（＝全网） -/
structure TrustChain where
  branches : List Branch

/-- 失效事件（模型假设 A2：带在链证据，失效点必在链上） -/
structure Failure (c : TrustChain) where
  br  : Branch
  mem : br ∈ c.branches
  pos : Nat
  seq : Nat

/-- 链上记录：签发位置（分支 × 下标）＋签发序号（时间轴） -/
structure Record where
  branch : Branch
  pos    : Nat
  seq    : Nat

/-! ## N-1 · 四条判据（机验面） -/

/-- 受影响谓词（判据①③的机验面，模型假设 A3）：
    节点（br, p）受失效 f 影响 ⟺ 同分支 且 位置不早于失效位置（向下传导；向上隔离） -/
def affected (f : Failure c) (br : Branch) (p : Nat) : Prop :=
  br = f.br ∧ f.pos ≤ p

/-- 「全网重置」的机验面（判据②的否定对象）：受影响集＝全集（每个分支每个位置均受影响） -/
def globalReset (c : TrustChain) (f : Failure c) : Prop :=
  ∀ br ∈ c.branches, ∀ p : Nat, affected f br p

/-- 判据① 分支隔离：受影响集 ⊆ 失效所在分支（受影响 ⟹ 同分支） -/
theorem isolation (f : Failure c) (br : Branch) (p : Nat)
    (h : affected f br p) : br = f.br :=
  h.1

/-- 判据①′ 跨分支免疫：链上其它分支的任意位置均不受影响 -/
theorem cross_branch_immune (c : TrustChain) (f : Failure c)
    (br : Branch) (_hmem : br ∈ c.branches) (hne : br ≠ f.br) (p : Nat) :
    ¬ affected f br p :=
  fun h => hne h.1

/-- 判据② 不全局重置：单点失效（失效点在链上）且链上存在其它分支 ⟹
    存在不受影响的（分支 × 位置）——受影响集 ⊊ 全集，「全网重置」不成立 -/
theorem no_global_reset (c : TrustChain) (f : Failure c)
    (other : Branch) (hmem : other ∈ c.branches) (hne : other ≠ f.br) :
    ¬ globalReset c f :=
  fun h => hne (h other hmem 0).1

/-- 判据③（向下传导）：失效位置之下（含失效点）确实受影响——受影响集非空切片 -/
theorem downward_reaches (f : Failure c) (p : Nat) (h : f.pos ≤ p) :
    affected f f.br p :=
  ⟨rfl, h⟩

/-- 判据③（向上隔离）：失效位置之上的同分支位置不受影响——上层失效不改变下层既有记录 -/
theorem upward_isolated (f : Failure c) (p : Nat) (h : p < f.pos) :
    ¬ affected f f.br p :=
  fun ⟨_, h2⟩ => Nat.not_le_of_gt h h2

/-- 记录存活谓词（判据④的机验面，模型假设 A4）：
    r 于失效后仍可追溯 ⟺ 非（r 位于受影响位置 且 签发序号不早于失效时点）——
    失效只切片其后，不回溯撤销 -/
def survives (c : TrustChain) (f : Failure c) (r : Record) : Prop :=
  ¬ (affected f r.branch r.pos ∧ f.seq ≤ r.seq)

/-- 判据④＋③＋①的合取刻画：存活 ⟺ 非（受影响 × 时点之后）——
    「受影响集」与「失效时点」的联合刻画，与定义一致（Iff.rfl 内核可检） -/
theorem survives_iff (c : TrustChain) (f : Failure c) (r : Record) :
    survives c f r ↔ ¬ (affected f r.branch r.pos ∧ f.seq ≤ r.seq) :=
  Iff.rfl

/-- 判据④ 既有记录不失效：失效时点之前签发的记录恒可追溯（不受分支影响） -/
theorem prior_records_survive (c : TrustChain) (f : Failure c) (r : Record)
    (h : r.seq < f.seq) : survives c f r :=
  fun ⟨_, h2⟩ => Nat.not_le_of_gt h h2

/-- 判据④′ 跨分支记录不失效：非失效分支的记录无论签发时点均可追溯 -/
theorem cross_branch_records_survive (c : TrustChain) (f : Failure c) (r : Record)
    (h : r.branch ≠ f.br) : survives c f r :=
  fun ⟨ha, _⟩ => h ha.1

/-- 切片一致性（刻画的对偶面）：位于受影响位置且签发于失效时点之后的记录
    按判定不可追溯——被切除的恰好是「受影响集 × 时点之后」这一切片，不多不少 -/
theorem affected_forward_dropped (c : TrustChain) (f : Failure c) (r : Record)
    (ha : affected f r.branch r.pos) (hs : f.seq ≤ r.seq) :
    ¬ survives c f r :=
  fun h => h ⟨ha, hs⟩

end TDCA.FailureRadius
