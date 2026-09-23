/-
  TDCA 形式化证明课题 · 负空间（底线）之修订 · N-6（迁移不变量）
  ============================================================================
  建模方式：独立件、独立命名空间。三域（负空间登记簿／场景约束／正空间规则）以
  State 承载；「合法修订」以归纳关系 Rev 封闭列出（addNeg／toScene／toPositive），
  迁移以「同 id 换状态标记＋目标域挂接」刻画；四判据各自落为内核可检定理。

  模型假设（显式，不得省略）：
   A1 三域刻画：State ＝ neg（负空间登记簿：条目＋状态 inForce／relocatedTo d）
     ＋ sc（场景约束）＋ pr（正空间规则）；条目＝裸 Nat id，无身份语义；
   A2 「底线只增不减」按制度内容全集口径形式化：baseline ＝ neg 之条目投影 ∪ sc ∪ pr；
     负空间登记簿因迁移以「同 id 换状态标记」保留条目（登记留痕，对应「留下判例存证」），
     故负空间 id 集合字面不减、全集亦不减——不存在「删除至消失」的合法修订；
   A3 合法修订封闭列出：addNeg（登记新条目）／toScene／toPositive（迁移，要求源条目
     在负空间为 inForce）；未列出者非法；迁移构造子同时要求人类签批证据
     （approved = true）与判例编号在案（precedent > 0）；
   A4 签批权归属不进入本件——Approval 仅为内核可检证据载体（Bool ＋ 判例号），
     「谁有权签批」属治理层，不在本件范围；
   A5 不建模时间与并发：修订为全序单步；再修订以 Revs 闭包（nil/cons）承载；
   A6 不假设条目 id 唯一（登记簿为列表，允许重复登记；定理不依赖唯一性）。

  适用范围：制度哲学 §5.2「重新分类而非删除……底线只增不减，但条目可以换位置」
  之可机验抽象骨架。签批流程、判例治理属制度层，不在本件形式化范围。

  机验状态：本机已机验（Lean 4.34.0-rc2，lake build 0 error）；非 CI 机验。
  三态终态声明：本节各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项。⛔ 不标「绝对安全」；对外表述限「本机机验」。

  依赖纪律：本件零依赖（不 import Mathlib，亦不引用其它 TDCA 件）——
  迁移骨架只需 List 归纳与 Nat 序事实，同时隔离上游弃用告警面；
  如后续扩充需 Mathlib 引理，另件处理。
-/

namespace TDCA.NegativeSpace

/-! ## 载体结构（模型假设 A1 / A3 / A4） -/

/-- 条目：裸 id，无身份语义（模型假设 A1） -/
structure Entry where
  id : Nat
  deriving DecidableEq, Repr

/-- 迁移目标域：场景约束 或 正空间规则（判据②「出处有落」的落点类型） -/
inductive Dest
  | scene | positive
  deriving DecidableEq, Repr

/-- 负空间条目的登记状态：在档 ／ 已迁移至某目标域（登记留痕，模型假设 A2） -/
inductive NStatus
  | inForce
  | relocatedTo : Dest → NStatus
  deriving DecidableEq, Repr

/-- 负空间登记项：条目＋登记状态 -/
structure NegItem where
  entry : Entry
  status : NStatus
  deriving DecidableEq, Repr

/-- 人类签批＋判例存证之证据载体（模型假设 A4：签批权归属不入件） -/
structure Approval where
  approved : Bool
  precedent : Nat

/-- 三域状态（模型假设 A1） -/
structure State where
  neg : List NegItem
  sc  : List Entry
  pr  : List Entry

/-- 目标域对应的清单（判据②的「落」） -/
def destOf : Dest → State → List Entry
  | .scene, s => s.sc
  | .positive, s => s.pr

/-- 移除首个指定条目之登记项（迁移时置换旧登记项用；保留其余登记） -/
def removeItem (e : Entry) : List NegItem → List NegItem
  | [] => []
  | it :: rest => if it.entry = e then rest else it :: removeItem e rest

/-- 制度内容全集（「底线」，模型假设 A2 的口径）：负空间登记条目投影 ∪ sc ∪ pr -/
def baseline (s : State) : List Entry :=
  s.neg.map NegItem.entry ++ s.sc ++ s.pr

/-- 登记簿良态（判据②在再修订下的保持载体）：凡登记为「已迁移至 d」的条目，
    其 id 必落在目标域 d 的清单内——出处有落，不落入无主 -/
def Invariant (s : State) : Prop :=
  ∀ item ∈ s.neg, ∀ d, item.status = .relocatedTo d → item.entry ∈ destOf d s

/-! ## 合法修订（模型假设 A3：封闭列出，未列出者非法） -/

/-- 合法修订关系：登记新条目 ／ 迁移至场景约束 ／ 迁移至正空间规则。
    迁移三要件：源条目在档（inForce）、人类签批（approved = true）、判例在案（precedent > 0） -/
inductive Rev : State → State → Type
  | addNeg (e : Entry) :
      Rev s ⟨{ entry := e, status := .inForce } :: s.neg, s.sc, s.pr⟩
  | toScene (e : Entry) (_h : { entry := e, status := .inForce } ∈ s.neg)
      (ap : Approval) (hg : ap.approved = true) (hp : 0 < ap.precedent) :
      Rev s ⟨{ entry := e, status := .relocatedTo .scene } :: removeItem e s.neg,
             e :: s.sc, s.pr⟩
  | toPositive (e : Entry) (_h : { entry := e, status := .inForce } ∈ s.neg)
      (ap : Approval) (hg : ap.approved = true) (hp : 0 < ap.precedent) :
      Rev s ⟨{ entry := e, status := .relocatedTo .positive } :: removeItem e s.neg,
             s.sc, e :: s.pr⟩

/-- 再修订闭包（模型假设 A5：全序多步） -/
inductive Revs : State → State → Type
  | nil : Revs s s
  | cons : Rev s s' → Revs s' s'' → Revs s s''

/-! ## 辅助引理（baseline 成员构造与 removeItem 两条：不误伤、不增生） -/

/-- 由负空间登记投影进入底线全集 -/
theorem mem_baseline_of_mem_neg {s : State} {x : Entry}
    (h : x ∈ s.neg.map NegItem.entry) : x ∈ baseline s :=
  List.mem_append.2 (Or.inl (List.mem_append.2 (Or.inl h)))

/-- 由场景约束进入底线全集 -/
theorem mem_baseline_of_mem_sc {s : State} {x : Entry}
    (h : x ∈ s.sc) : x ∈ baseline s := by
  rw [baseline]
  exact List.mem_append.2 (Or.inl (List.mem_append.2 (Or.inr h)))

/-- 由正空间规则进入底线全集 -/
theorem mem_baseline_of_mem_pr {s : State} {x : Entry}
    (h : x ∈ s.pr) : x ∈ baseline s := by
  rw [baseline]
  exact List.mem_append.2 (Or.inr h)

/-- 不误伤：entry 不同的登记项在移除后仍在 -/
theorem mem_removeItem_of_ne {e : Entry} {y : NegItem} {l : List NegItem}
    (hne : y.entry ≠ e) (h : y ∈ l) : y ∈ removeItem e l := by
  induction l with
  | nil => exact (List.not_mem_nil h).elim
  | cons it rest ih =>
    by_cases hit : it.entry = e
    · simp [removeItem, hit]
      rcases (List.mem_cons.1 h) with hy | hy
      · exact (hne (hy ▸ hit)).elim
      · exact hy
    · simp [removeItem, hit]
      rcases (List.mem_cons.1 h) with hy | hy
      · exact Or.inl hy
      · exact Or.inr (ih hy)

/-- 不增生：移除结果 ⊆ 原登记簿 -/
theorem mem_of_mem_removeItem {e : Entry} {y : NegItem} {l : List NegItem}
    (h : y ∈ removeItem e l) : y ∈ l := by
  induction l with
  | nil => exact (List.not_mem_nil h).elim
  | cons it rest ih =>
    by_cases hit : it.entry = e
    · simp [removeItem, hit] at h
      exact List.mem_cons.2 (Or.inr h)
    · simp [removeItem, hit] at h
      rcases h with hy | hy
      · exact List.mem_cons.2 (Or.inl hy)
      · exact List.mem_cons.2 (Or.inr (ih hy))

/-! ## N-6 · 四条判据（机验面） -/

/-- 判据① 底线单调不减：任何合法修订后，制度内容集合（含负空间登记）不减——
    原任一条目在新状态三域之一中仍可寻得，不存在「删除至消失」的合法迁移 -/
theorem baseline_mono (r : Rev s s') (x : Entry) (h : x ∈ baseline s) : x ∈ baseline s' := by
  rw [baseline, List.mem_append, List.mem_append] at h
  rcases h with (hn | hsc) | hpr
  · cases r with
    | addNeg e =>
      exact mem_baseline_of_mem_neg (List.mem_cons_of_mem _ hn)
    | toScene e _h _ap _hg _hp =>
      rw [List.mem_map] at hn
      rcases hn with ⟨y, hy, hyx⟩
      subst hyx
      by_cases hxy : y.entry = e
      · subst hxy
        exact mem_baseline_of_mem_neg (List.mem_cons.2 (Or.inl rfl))
      · exact mem_baseline_of_mem_neg (List.mem_cons_of_mem _
          (List.mem_map.2 ⟨y, mem_removeItem_of_ne hxy hy, rfl⟩))
    | toPositive e _h _ap _hg _hp =>
      rw [List.mem_map] at hn
      rcases hn with ⟨y, hy, hyx⟩
      subst hyx
      by_cases hxy : y.entry = e
      · subst hxy
        exact mem_baseline_of_mem_neg (List.mem_cons.2 (Or.inl rfl))
      · exact mem_baseline_of_mem_neg (List.mem_cons_of_mem _
          (List.mem_map.2 ⟨y, mem_removeItem_of_ne hxy hy, rfl⟩))
  · cases r with
    | addNeg _e =>
      exact mem_baseline_of_mem_sc hsc
    | toScene e _h _ap _hg _hp =>
      exact mem_baseline_of_mem_sc (List.mem_cons_of_mem e hsc)
    | toPositive _e _h _ap _hg _hp =>
      exact mem_baseline_of_mem_sc hsc
  · cases r with
    | addNeg _e =>
      exact mem_baseline_of_mem_pr hpr
    | toScene _e _h _ap _hg _hp =>
      exact mem_baseline_of_mem_pr hpr
    | toPositive e _h _ap _hg _hp =>
      exact mem_baseline_of_mem_pr (List.mem_cons_of_mem e hpr)

/-- 判据② 迁移不删除／出处有落：新登记为「已迁移至 d」的登记项（本次修订新产生），
    其条目必落在目标域 d 的清单内——不凭空消失、不落入无主 -/
theorem relocate_lands (r : Rev s s') (item : NegItem) (d : Dest)
    (hm : item ∈ s'.neg) (hr : item.status = .relocatedTo d)
    (hfresh : item ∉ s.neg) :
    item.entry ∈ destOf d s' := by
  cases r with
  | addNeg e =>
    rw [List.mem_cons] at hm
    rcases hm with rfl | ho
    · cases hr
    · exact (hfresh ho).elim
  | toScene e _h _ap _hg _hp =>
    rw [List.mem_cons] at hm
    rcases hm with rfl | ho
    · cases hr
      exact List.mem_cons_self
    · exact (hfresh (mem_of_mem_removeItem ho)).elim
  | toPositive e _h _ap _hg _hp =>
    rw [List.mem_cons] at hm
    rcases hm with rfl | ho
    · cases hr
      exact List.mem_cons_self
    · exact (hfresh (mem_of_mem_removeItem ho)).elim

/-- 判据③ 迁移须签批留痕：任何「本次修订新产生的已迁移登记项」之修订，
    必携带人类签批证据（approved = true）与判例编号（> 0） -/
theorem migrate_signed (r : Rev s s') (item : NegItem) (d : Dest)
    (hm : item ∈ s'.neg) (_hr : item.status = .relocatedTo d)
    (hfresh : item ∉ s.neg) :
    ∃ ap : Approval, ap.approved = true ∧ 0 < ap.precedent := by
  cases r with
  | addNeg e =>
    rw [List.mem_cons] at hm
    rcases hm with rfl | ho
    · cases _hr
    · exact (hfresh ho).elim
  | toScene e _h ap hg hp =>
    rw [List.mem_cons] at hm
    rcases hm with rfl | ho
    · exact ⟨ap, hg, hp⟩
    · exact (hfresh (mem_of_mem_removeItem ho)).elim
  | toPositive e _h ap hg hp =>
    rw [List.mem_cons] at hm
    rcases hm with rfl | ho
    · exact ⟨ap, hg, hp⟩
    · exact (hfresh (mem_of_mem_removeItem ho)).elim

/-- 判据④（单步） 登记簿良态在单步合法修订下保持（再修订保持的归纳基） -/
theorem invariant_step (hinv : Invariant s) (r : Rev s s') : Invariant s' := by
  intro item hm d hs
  cases r with
  | addNeg e =>
    rw [List.mem_cons] at hm
    rcases hm with rfl | ho
    · cases hs
    · cases d with
      | scene => exact hinv item ho .scene hs
      | positive => exact hinv item ho .positive hs
  | toScene e _h _ap _hg _hp =>
    rw [List.mem_cons] at hm
    rcases hm with rfl | ho
    · cases hs
      exact List.mem_cons_self
    · have hdest := hinv item (mem_of_mem_removeItem ho) d hs
      cases d with
      | scene => exact List.mem_cons_of_mem _ hdest
      | positive => exact hdest
  | toPositive e _h _ap _hg _hp =>
    rw [List.mem_cons] at hm
    rcases hm with rfl | ho
    · cases hs
      exact List.mem_cons_self
    · have hdest := hinv item (mem_of_mem_removeItem ho) d hs
      cases d with
      | scene => exact hdest
      | positive => exact List.mem_cons_of_mem _ hdest

/-- 判据④ 不变量在再修订下保持：任意多步合法修订链保持登记簿良态 -/
theorem invariant_chain (hinv : Invariant s) (rs : Revs s s') : Invariant s' := by
  induction rs with
  | nil => exact hinv
  | cons r rs ih => exact ih (invariant_step hinv r)

end TDCA.NegativeSpace
