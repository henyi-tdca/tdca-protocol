/-
  TDCA 形式化证明课题 · 准入守卫 · N-3（制度准入状态机）＋ N-2（信任根分级 ↔ 场景密级）
  ============================================================================
  建模方式：N-3 与 N-2 同属「准入守卫」，共用本骨架一次建模双用（两节各自独立交付/核证）。

  模型假设（显式，不得省略）：
   A1（N-3）态只记载体合法性，不含「它是谁」语义——AdmState 为裸枚举、无身份载荷；
   A2（N-3）「已认证（certified）」⟺ 已通过准入编译（编译通过证据 CompilePass.pass = true），
     不存在「已认证但未编译」的态或迁移；
   A3（N-3）迁移由 AdmTrans 归纳定义封闭列出——未列出的迁移即非法（非法性由刻画定理机验给出）；
   A4（N-3）熔断（fused）为终态；回出条件＝重新走注册流程（不在本机状态机内，属治理动作）；
   B1（N-2）信任根四级（degraded/temporary/standard/high）与场景密级（0=普通…3=机密）
     均为全序离散梯级，以 ℕ 承载；
   B2（N-2）tierLevel 只表信任强度、不表身份（同 A1 纪律）；
   B3（N-2）所需层级映射 requiredLevel : 密级 → 所需层级为单调不减；本件取恒等实现，
     任何单调实现可替换（定理只依赖单调性，不依赖恒等形态）；
   B4（N-2）接入判定 admit 为 fail-closed：层级不达标即拒，无「告警后放行」分支；
   B5（N-2）判定只依赖（密级， 根层级）两参，不含身份/历史维度。

  适用范围：协议层准入守卫的抽象骨架；真实平台的身份续期、密钥轮换等动态属工程层，
  不在本件形式化范围（不得以本件结论覆盖之）。

  机验状态：本机已机验（2026-09-23，Lean 4.34.0-rc2，lake build 0 error）；非 CI 机验。
  三态终态声明：本节各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项。⛔ 不标「绝对安全」；对外表述限「本机机验」。

  依赖纪律：本件不 import Mathlib（零上游依赖）——准入守卫骨架无需 Mathlib 引理，
  同时隔离上游弃用告警面；如后续扩充需 Mathlib 引理，另件处理。
-/

namespace TDCA.Admission

/-! ## N-3 · 制度准入状态机（七态，判据①–④） -/

/-- 七态：未注册 / 已注册 / 已认证 / 活跃 / 降级 / 暂停 / 熔断。
    裸枚举、无身份载荷（模型假设 A1） -/
inductive AdmState
  | unregistered | registered | certified | active | degraded | suspended | fused
  deriving DecidableEq, Repr

/-- 准入编译通过证据（模型假设 A2 载体：pass 为内核可检布尔，certified 必经此证） -/
structure CompilePass where
  pass : Bool

/-- 迁移关系（模型假设 A3：封闭列出，未列出者非法）。
    Type 承载：迁移为带证据的一等对象——编译通过证据可机验提取（判据④） -/
inductive AdmTrans : AdmState → AdmState → Type
  | reg        : AdmTrans .unregistered .registered
  | certify    (ok : CompilePass) (hg : ok.pass = true) : AdmTrans .registered .certified
  | activate   : AdmTrans .certified .active
  | degrade    : AdmTrans .active .degraded
  | restore    : AdmTrans .degraded .active
  | suspend    : AdmTrans .active .suspended
  | resume     : AdmTrans .suspended .active
  | fuseAct    : AdmTrans .active .fused
  | fuseDeg    : AdmTrans .degraded .fused
  | fuseSus    : AdmTrans .suspended .fused

/-- 合法后继的判定性刻画（判据②「无非法迁移」的机验面） -/
def AdmSucc : AdmState → AdmState → Bool
  | .unregistered, .registered => true
  | .registered,   .certified  => true
  | .certified,    .active     => true
  | .active,       .degraded   => true
  | .degraded,     .active     => true
  | .active,       .suspended  => true
  | .suspended,    .active     => true
  | .active,       .fused      => true
  | .degraded,     .fused      => true
  | .suspended,    .fused      => true
  | _,             _           => false

/-- 判据②（安全）：迁移合法 ⟺ 判定后继为真——非法迁移全体被排除（刻画定理） -/
theorem AdmTrans_iff_AdmSucc (s t : AdmState) : Nonempty (AdmTrans s t) ↔ AdmSucc s t = true := by
  constructor
  · rintro ⟨h⟩
    cases h <;> rfl
  · intro h
    apply Nonempty.intro
    cases s <;> cases t <;> simp [AdmSucc] at h ⊢
    <;> first
      | exact AdmTrans.reg
      | exact (AdmTrans.certify ⟨true⟩ rfl)
      | exact AdmTrans.activate
      | exact AdmTrans.degrade
      | exact AdmTrans.restore
      | exact AdmTrans.suspend
      | exact AdmTrans.resume
      | exact AdmTrans.fuseAct
      | exact AdmTrans.fuseDeg
      | exact AdmTrans.fuseSus

/-- 判据②（安全）实例：非法迁移拒证——未经注册的直达活跃不存在 -/
theorem not_trans_unregistered_active : ¬ Nonempty (AdmTrans .unregistered .active) :=
  fun h => absurd ((AdmTrans_iff_AdmSucc _ _).mp h) (by decide)

/-- 判据①（完备）：任一非熔断态至少一条出边 -/
theorem AdmTrans_complete (s : AdmState) (hf : s ≠ .fused) : ∃ t, Nonempty (AdmTrans s t) := by
  cases s
  case unregistered => exact ⟨_, ⟨.reg⟩⟩
  case registered   => exact ⟨_, ⟨.certify ⟨true⟩ rfl⟩⟩
  case certified    => exact ⟨_, ⟨.activate⟩⟩
  case active       => exact ⟨_, ⟨.degrade⟩⟩
  case degraded     => exact ⟨_, ⟨.restore⟩⟩
  case suspended    => exact ⟨_, ⟨.resume⟩⟩
  case fused        => exact absurd rfl hf

/-- 判据①（完备）：熔断为终态——无出边；回出条件＝重走注册流程（假设 A4，治理动作） -/
theorem fused_terminal (s : AdmState) : ¬ Nonempty (AdmTrans .fused s) := by
  rintro ⟨h⟩
  cases h

/-- 判据②（安全）：降级态出边仅 {活跃, 熔断}——不得借降级绕过熔断 -/
theorem degraded_out_only (t : AdmState) (h : AdmTrans .degraded t) :
    t = .active ∨ t = .fused := by
  cases h
  · exact Or.inl rfl
  · exact Or.inr rfl

/-- 判据②（安全）：暂停态出边仅 {活跃, 熔断}——同上 -/
theorem suspended_out_only (t : AdmState) (h : AdmTrans .suspended t) :
    t = .active ∨ t = .fused := by
  cases h
  · exact Or.inl rfl
  · exact Or.inr rfl

/-- 迁移附载的编译通过证据提取（无编译证迁移附载 none） -/
def transCompilePass : ∀ {s t}, AdmTrans s t → Option CompilePass
  | _, _, .certify ok _ => some ok
  | _, _, _             => none

/-- 判据④（一致性）：凡入 certified 之迁移，附载编译通过证据且 pass = true——
    不存在「已认证但未编译」的旁路（假设 A2 的机验不变式） -/
theorem certified_requires_compile (s : AdmState) (h : AdmTrans s .certified) :
    ∃ ok, transCompilePass h = some ok ∧ ok.pass = true := by
  cases h with
  | certify ok hg => exact ⟨ok, rfl, hg⟩

/-! ## N-2 · 信任根分级 ↔ 场景密级（fail-closed，判据①–④） -/

/-- 信任根四级（模型假设 B1/B2：层级只表信任强度） -/
inductive RootTier
  | degraded | temporary | standard | high
  deriving DecidableEq, Repr

/-- 层级梯级映射（B1） -/
def tierLevel : RootTier → Nat
  | .degraded  => 0
  | .temporary => 1
  | .standard  => 2
  | .high      => 3

/-- 场景密级（B1：0=普通 … 3=机密），以 ℕ 承载（abbrev：保持 ℕ 全部序/算术实例可见） -/
abbrev Clearance : Type := Nat

/-- 所需层级映射（B3：单调不减；恒等实现，任何单调实现可替换） -/
def requiredLevel : Clearance → Nat := id

/-- 判据①（N-2）：密级 → 所需层级为单调不减映射 -/
theorem requiredLevel_mono (a b : Clearance) (h : a ≤ b) : requiredLevel a ≤ requiredLevel b := h

/-- fail-closed 接入判定（B4：不达标即拒，无「告警后放行」分支） -/
def admit (c : Clearance) (r : RootTier) : Bool :=
  decide (requiredLevel c ≤ tierLevel r)

/-- 判定刻画：放行 ⟺ 层级达标（判据③「校验失败即拒」的机验面） -/
theorem admit_iff (c : Clearance) (r : RootTier) :
    admit c r = true ↔ requiredLevel c ≤ tierLevel r := by
  unfold admit
  exact decide_eq_true_iff

/-- 判据③（N-2）：校验失败即拒（非告警后放行） -/
theorem admit_reject (c : Clearance) (r : RootTier)
    (h : ¬ requiredLevel c ≤ tierLevel r) : admit c r = false := by
  unfold admit
  match h' : decide (requiredLevel c ≤ tierLevel r) with
  | true => exact absurd (of_decide_eq_true h') h
  | false => rfl

/-- 判据②（N-2）：高密级 × 低层级根 ⟹ 拒绝接入（不得降级放行） -/
theorem admit_reject_high_low (c : Clearance) (r : RootTier)
    (h : requiredLevel c > tierLevel r) : admit c r = false := by
  apply admit_reject
  omega

/-- 判据④（N-2）前半：普通场景可用降级根（0 ≤ 0 放行，实例为 rfl 可机检） -/
theorem admit_normal_with_degraded : admit 0 .degraded = true := rfl

/-- 判据④（N-2）后半：放行集对**密级向下封闭**——高档放行 ⟹ 低档必放行；
    逆方向不成立（低档放行不蕴含高档放行，恰由 admit_reject_high_low 拒证）。
    与拒证定理合观 ⟹ 低层级根不得使高密级通过 -/
theorem admit_downward_closed (c c' : Clearance) (r : RootTier)
    (hcc : c ≤ c') (hp : admit c' r = true) : admit c r = true :=
  (admit_iff c r).mpr (Nat.le_trans (requiredLevel_mono c c' hcc) ((admit_iff c' r).mp hp))

/-- 判定实例（机检）：机密 × 降级根 ⟹ 拒绝（3 ≰ 0） -/
theorem admit_secret_degraded_rejected : admit 3 .degraded = false := rfl

end TDCA.Admission
