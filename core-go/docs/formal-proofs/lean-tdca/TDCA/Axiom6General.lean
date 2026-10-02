/-
  TDCA 形式化证明课题 · 开放问题 P-3（公理 6 推广到 NCA 哈希链与 NSFL 熔断器）
  ============================================================================
  建模方式：独立件、独立命名空间、零依赖（不 import Mathlib）。
  ⭐ 做法＝**抽象层 ＋ 两实例**：先在抽象层给出「有裁剪域之可审计系统」
  （完备／可靠／右逆三约束作为**字段**即证明义务），再给出**两实例**：
   ① `NCA` 链（不可变历史；`dom` ＝ 全体）—— 含「只增不减」机验面；
   ② `NSFL` 熔断器（`dom` ＝ **非熔断态**）—— ⭐ 此即材料所述
      「`FUSED` 不可逆性与右逆存在性之张力」之解：**右逆定义域裁剪到 `Im(f)`**，
      熔断态**不在**完备性断言范围内。

  模型假设（显式，不得省略）：
   P3-1 状态与记录类型由各实例给出（本件均为零依赖之简单载体）；
   P3-2 「可审计系统」＝ `encode : S → R`（产出记录）＋ `audit : R → Bool`（审计）
        ＋ `restore : R → Option S`（还原）＋ `dom : S → Prop`（**断言域**）；
   P3-3 三约束：`complete`（域内 ⟹ 审计通过）／`sound`（审计通过 ⟹ 在像内且域内）／
        `rightInv`（域内 ⟹ 右逆还原）；
   P3-4 ⚠️ **复杂度约束（公理 6 之第 4 条）不在本件** —— 按 `CLAIMS-MATRIX` `C-12`
        既有口径，复杂度属**条件形态**（`conditional`），另列。

  适用范围：抽象骨架层（两实例皆为**零依赖简化载体**，⛔ 非真实 `NCA`／`NSFL` 实现；
  真实实现之链式哈希与分级熔断属工程层）。⛔ 不主张任何制度层结论；
  ⛔ 不标「绝对安全」；对外表述限「本机机验」。

  机验状态：本机机验（Lean 4.34.0-rc2 · lake build）；非 CI 机验。
  三态终态声明：本件各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项、无占位（sorry）。
-/

namespace TDCA.Axiom6General

/-! ## 一、抽象层：有裁剪域之可审计系统 -/

/-- 有裁剪域之可审计系统（三约束即字段，亦即**证明义务**） -/
structure AuditableDom (S R : Type) where
  /-- 产出记录 -/
  encode : S → R
  /-- 审计判定 -/
  audit : R → Bool
  /-- 还原（右逆候选） -/
  restore : R → Option S
  /-- **断言域**（完备性与右逆只在域上断言） -/
  dom : S → Prop
  /-- 约束 1 完备性：域内 ⟹ 审计通过 -/
  complete : ∀ s, dom s → audit (encode s) = true
  /-- 约束 2 可靠性：审计通过 ⟹ 记录在像内**且**域内 -/
  sound : ∀ r, audit r = true → ∃ s, dom s ∧ encode s = r
  /-- 约束 3 右逆：域内 ⟹ 可还原 -/
  rightInv : ∀ s, dom s → restore (encode s) = some s

/-- 公理 6 之抽象形态：三约束之合取 ⟹ **审计通过 ⟺ 记录在像内（且域内）** -/
theorem audit_iff_image_dom {S R : Type} (A : AuditableDom S R) (r : R) :
    A.audit r = true ↔ ∃ s, A.dom s ∧ A.encode s = r :=
  ⟨A.sound r, fun ⟨s, hd, he⟩ => he ▸ A.complete s hd⟩

/-- 公理 6 之抽象形态（右逆面）：域内状态可由其记录还原 -/
theorem restore_on_image {S R : Type} (A : AuditableDom S R) (s : S) (hd : A.dom s) :
    A.restore (A.encode s) = some s :=
  A.rightInv s hd

/-! ## 二、实例 ①：`NCA` 链（不可变历史） -/

/-- `NCA` 日志（不可变历史之简化载体）：已追加条数 ＋ 内容摘要 -/
structure NCALog where
  count : Nat
  digest : Nat

/-- 追加一条记录（链式推进） -/
def append (x : Nat) (l : NCALog) : NCALog :=
  ⟨l.count + 1, l.digest + x⟩

/-- ⭐ 不可变性（机验面）：追加**只增不减** -/
theorem nca_append_mono (x : Nat) (l : NCALog) : l.count ≤ (append x l).count := by
  show l.count ≤ l.count + 1
  omega

/-- `NCA` 实例：记录＝日志本身；审计恒真；还原恒等；**断言域＝全体** -/
def ncaAuditable : AuditableDom NCALog NCALog where
  encode := id
  audit := fun _ => true
  restore := some
  dom := fun _ => True
  complete := fun _ _ => rfl
  sound := fun r _ => ⟨r, trivial, rfl⟩
  rightInv := fun _ _ => rfl

/-- `NCA` 上之审计刻画（由抽象定理实例化） -/
theorem nca_audit_iff (r : NCALog) :
    ncaAuditable.audit r = true ↔ ∃ s, ncaAuditable.dom s ∧ ncaAuditable.encode s = r :=
  audit_iff_image_dom ncaAuditable r

/-! ## 三、实例 ②：`NSFL` 熔断器（**像集裁剪**） -/

/-- 熔断器状态：`none` ＝ **熔断态**（无产出）；`some v` ＝ 正常态 -/
abbrev FuseState := Option Nat

/-- `NSFL` 实例：⭐ **断言域＝非熔断态**（右逆定义域裁剪到 `Im(f)`） -/
def fuseAuditable : AuditableDom FuseState FuseState where
  encode := id
  audit := fun r => r.isSome
  restore := some
  dom := fun s => s.isSome = true
  complete := fun _ h => h
  sound := fun r h => ⟨r, h, rfl⟩
  rightInv := fun _ _ => rfl

/-- 熔断器之可审计域（＝非熔断态） -/
def FuseLive (s : FuseState) : Prop := fuseAuditable.dom s

/-- ⭐ 张力之解（机验面）：**熔断态不在完备性断言范围内** —— 断言域裁剪到像集 -/
theorem fuse_complete_only_on_live (s : FuseState) (h : FuseLive s) :
    fuseAuditable.audit (fuseAuditable.encode s) = true :=
  fuseAuditable.complete s h

/-- 熔断器上之审计刻画（由抽象定理实例化） -/
theorem fuse_audit_iff (r : FuseState) :
    fuseAuditable.audit r = true ↔ ∃ s, fuseAuditable.dom s ∧ fuseAuditable.encode s = r :=
  audit_iff_image_dom fuseAuditable r

/-- 熔断态确实**不**在域内（裁剪之必要性） -/
theorem fuse_none_not_live : ¬ FuseLive (none : FuseState) := by
  unfold FuseLive fuseAuditable
  simp

/-! ## 四、统一：两实例**同形**（同一抽象定理各自实例化） -/

/-- 公理 6 抽象形态在两实例上均成立（同一定理，各自实例化） -/
theorem axiom6_general_two_instances :
    (∀ r : NCALog, ncaAuditable.audit r = true ↔ ∃ s, ncaAuditable.dom s ∧ ncaAuditable.encode s = r)
    ∧ (∀ r : FuseState, fuseAuditable.audit r = true ↔ ∃ s, fuseAuditable.dom s ∧ fuseAuditable.encode s = r) :=
  ⟨nca_audit_iff, fuse_audit_iff⟩

end TDCA.Axiom6General
