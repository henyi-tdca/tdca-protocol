/-
  TDCA 形式化证明课题 · 双锚一致性 · N-5（格式锚 ＋ 效用锚）
  ============================================================================
  建模方式：独立件、独立命名空间。双锚以内核可检结构承载——格式锚＝Bool 通过位，
  效用锚＝（声明值， 下限）对、锚定 ⟺ 下限 ≤ 声明；分配效力以双锚合取定义，
  四判据各自落为内核可检定理。结构层结论判 proved；真实效用接口现为 SIMULATED，
  接口层结论一律以 RealIfaceSpec 假设显式承载、判 conditional——两层如实分列。

  模型假设（显式，不得省略）：
   A1 双锚刻画：格式锚 FormatAnchor.passed（内核可检 Bool，过 ⟺ passed = true）；
     效用锚 UtilityAnchor（declared 声明值／floor 下限），锚定 ⟺ floor ≤ declared
     （Nat 序事实内核可判，无证据声明不能冒充锚定）；
   A2 下限取值：stdFloor := 1（正效用要求：零/负声明不得锚定）；「不可伪造」之抽象
     ＝锚定判定必须内核可检地满足 floor ≤ declared，不得取无证据之断言形态；
   A3 分配效力定义（判据①的口径）：allocatable ⟺ 格式锚过 ∧ 效用锚定；
     「可连」connectable ⟺ 格式锚过——二者为不同谓词，不得互推（判据②④）；
   A4 双锚独立性以见证态机验：formatOnly（格式过、效用未定）与 utilityOnly
     （效用锚定、格式未过）两态各自存在且均不可分配；
   A5 真实效用接口为 SIMULATED（模拟态显式标注）：接口层结论（real_iface_conditional）
     以忠实性假设 spec 为前提，判 conditional；结构层判 proved。不得以结构证明
     冒充接口实况。

  适用范围：工程哲学 §2.4「制度锚点必须双锚定：既锚定格式（能不能协作），
  又锚定价值（协作产生多少效用、归谁分配）」之可机验抽象骨架。
  真实锚定之密码学/计量机制属工程层，不在本件形式化范围。

  机验状态：本机已机验（Lean 4.34.0-rc2，lake build 0 error）；非 CI 机验。
  三态终态声明（分层分列）：
   · 结构层——本节各定理均为内核可检完整证明（proved，以显式假设为前提）；
   · 接口层——real_iface_conditional 为假设下之条件迁移定理，其前提（真实接口
     之忠实性）对 SIMULATED 接口不可核，故接口层判 conditional；
   无 refuted。⛔ 不标「绝对安全」；对外表述限「本机机验」。

  依赖纪律：本件零依赖（不 import Mathlib，亦不引用其它 TDCA 件）——
  双锚骨架只需 Bool/Nat 内核可判事实，同时隔离上游弃用告警面；
  如后续扩充需 Mathlib 引理，另件处理。
-/

namespace TDCA.DualAnchor

/-! ## 载体结构（模型假设 A1 / A2 / A5） -/

/-- 格式锚：能不能协作（内核可检通过位） -/
structure FormatAnchor where
  passed : Bool

/-- 效用锚：协作产生多少效用、归谁分配（声明值＋不可伪造下限） -/
structure UtilityAnchor where
  declared : Nat
  floor : Nat

/-- 效用锚外部接口现状：SIMULATED（模拟态显式标注，模型假设 A5） -/
def utilityIfaceStatus : String := "SIMULATED"

/-- 下限机制常数（模型假设 A2）：正效用要求，stdFloor = 1 -/
def stdFloor : Nat := 1

/-- 双锚状态 -/
structure DualState where
  fmt : FormatAnchor
  utl : UtilityAnchor

/-- 格式锚过（判据②③「可连」之定义） -/
def formatOk (f : FormatAnchor) : Prop := f.passed = true

/-- 效用锚已定（模型假设 A1：下限 ≤ 声明，内核可判） -/
def utilityAnchored (u : UtilityAnchor) : Prop := u.floor ≤ u.declared

/-- 可连：格式锚过（判据②） -/
def connectable (s : DualState) : Prop := formatOk s.fmt

/-- 可分配：分配效力成立 ⟺ 双锚齐备（判据①的口径，模型假设 A3） -/
def allocatable (s : DualState) : Prop := formatOk s.fmt ∧ utilityAnchored s.utl

/-! ## 见证态（判据②④：可连不可分 / 双锚独立性） -/

/-- 格式过、效用未定（声明 0 低于下限 1）：可连不可分之见证态 -/
def formatOnly : DualState := ⟨⟨true⟩, ⟨0, stdFloor⟩⟩

/-- 效用锚定（声明 2 ≥ 下限 1）、格式未过：独立性之另一见证态 -/
def utilityOnly : DualState := ⟨⟨false⟩, ⟨2, stdFloor⟩⟩

/-! ## N-5 · 四条判据（机验面，结构层 · proved） -/

/-- 判据① 双锚齐备 ⟺ 可分配：产生分配效力 ⟹ 格式锚通过 ∧ 效用锚已定 -/
theorem alloc_requires_both (s : DualState) :
    allocatable s → formatOk s.fmt ∧ utilityAnchored s.utl := id

/-- 判据①′ 逆：双锚齐备 ⟹ 可分配（合取方向） -/
theorem alloc_of_both (s : DualState) :
    formatOk s.fmt → utilityAnchored s.utl → allocatable s := And.intro

/-- 判据①″ 逆否：缺一即不可分 -/
theorem not_alloc_of_missing (s : DualState)
    (h : ¬ formatOk s.fmt ∨ ¬ utilityAnchored s.utl) : ¬ allocatable s :=
  fun ha => h.elim (fun nf => nf ha.1) (fun nu => nu ha.2)

/-- 判据② 可连不可分（分离性）：格式锚过而效用锚未定 ⟹ 连接可成立、分配效力不成立 -/
theorem connect_but_not_alloc (s : DualState)
    (hc : connectable s) (hu : ¬ utilityAnchored s.utl) :
    connectable s ∧ ¬ allocatable s :=
  ⟨hc, fun ⟨_, hu'⟩ => hu hu'⟩

/-- 判据②′ 见证：formatOnly 态可连（连接可成立） -/
theorem formatOnly_connectable : connectable formatOnly := rfl

/-- 判据②″ 见证：formatOnly 态效用锚未定（0 < 1 之下限校验不通过） -/
theorem formatOnly_not_anchored : ¬ utilityAnchored formatOnly.utl :=
  fun h => Nat.not_succ_le_zero 0 h

/-- 判据②‴ 见证：formatOnly 态不可分配 -/
theorem formatOnly_not_allocatable : ¬ allocatable formatOnly :=
  fun ⟨_, hu⟩ => formatOnly_not_anchored hu

/-- 判据③ 效用锚之硬下限：锚定 ⟹ 声明不低于下限（内核可检，无证据声明不能冒充锚定） -/
theorem floor_le_of_anchored (u : UtilityAnchor) :
    utilityAnchored u → u.floor ≤ u.declared := id

/-- 判据③′ 硬下限之阻断力：声明为 0 而限为正者不得锚定 -/
theorem zero_decl_not_anchored (u : UtilityAnchor)
    (hd : u.declared = 0) (hf : 0 < u.floor) : ¬ utilityAnchored u := by
  intro h
  unfold utilityAnchored at h
  rw [hd] at h
  omega

/-- 判据④ 双锚独立性（其一）：「能连」推不出「能分」（formatOnly 为反例见证） -/
theorem connect_not_sufficient :
    ¬ ∀ s : DualState, connectable s → allocatable s :=
  fun h => formatOnly_not_allocatable (h _ formatOnly_connectable)

/-- 判据④′ 双锚独立性（其二）：效用锚定推不出可分配（utilityOnly 为反例见证） -/
theorem utilityOnly_anchored : utilityAnchored utilityOnly.utl := Nat.le_succ 1

theorem utilityOnly_not_connectable : ¬ connectable utilityOnly :=
  fun h => by cases h

theorem utilityOnly_not_allocatable : ¬ allocatable utilityOnly :=
  fun ⟨hf, _⟩ => utilityOnly_not_connectable hf

theorem anchor_not_sufficient :
    ¬ ∀ s : DualState, utilityAnchored s.utl → allocatable s :=
  fun h => utilityOnly_not_allocatable (h _ utilityOnly_anchored)

/-! ## 接口层（模型假设 A5：SIMULATED，conditional） -/

/-- 真实效用接口之假设规格：接口对「效用锚已定」之判定 anchored 须忠实于
    下限校验（anchored u ⟹ floor ≤ declared）。SIMULATED 现状下此忠实性
    不可核——本结构之全部结论判 conditional（不得以结构证明冒充接口实况） -/
structure RealIfaceSpec where
  anchored : UtilityAnchor → Prop
  faithful : ∀ u, anchored u → u.floor ≤ u.declared

/-- 接口层（conditional）：在忠实性假设 spec 下，接口判「双锚齐备」⟹
    格式锚过 ∧ 声明不低于下限——结构层结论向真实接口之条件迁移 -/
theorem real_iface_conditional (spec : RealIfaceSpec) (s : DualState)
    (hfmt : formatOk s.fmt) (hif : spec.anchored s.utl) :
    formatOk s.fmt ∧ s.utl.floor ≤ s.utl.declared :=
  ⟨hfmt, spec.faithful s.utl hif⟩

end TDCA.DualAnchor
