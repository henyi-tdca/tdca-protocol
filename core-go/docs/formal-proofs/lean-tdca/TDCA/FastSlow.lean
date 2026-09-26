/-
  TDCA 形式化证明课题 · 快慢接口存在性 · N-7（快系统之异常上报与人类介入口子）
  ============================================================================
  建模方式：独立件、独立命名空间。快系统以两张通道清单（异常上报／人类介入）
  承载；「口子不得为空」以清单非空之合法性谓词刻画；「可被劫持」刻画为
  「异常无法上达」之抑制路径（缺口子 ⟹ ∃ 异常不可 escalate）。
  结构层判 proved；真实裁决接口层以 RealVerdictSpec 假设承载、判 conditional。

  模型假设（显式，不得省略）：
   A1 快慢为合法性分工、非性能分工（判据④）：本件不含任何性能字段／性能声明
     （performanceClaims 为空清单，机验可见）；
   A2 快系统刻画：FastSystem ＝ 异常上报通道清单 ＋ 人类介入通道清单（id 承载）；
     慢系统（结算／仲裁）在本件以「上达目标」抽象，不展开其内部；
   A3 合法性谓词：legit ⟺ 两清单均非空——「没口子的快系统不合法」；
   A4 可被劫持之刻画（判据③）：suppressible ⟺ 上报通道为空；此时任意异常
     均不存在 escalate 路径（存在被压制的劫持路径）；
   A5 真实裁决接口（BreakerVerdict.ESCALATE／Layer1Verdict.ESCALATE）为
     工程层枚举：结构层结论判 proved；接口层（RealVerdictSpec 忠实性）
     判 conditional（SIMULATED 现状下不可核，不得以结构证明冒充接口实况）。

  适用范围：GSEQ-2551 第 2 节 N-7 行（「快慢是合法性分工，不是性能分工」）
  之可机验抽象骨架。工程锚点：ID71 快慢分工（单笔计税 <10ms 走快系统；
  结算／仲裁为慢系统）；慢系统上报 ESCALATE ⟹ 快慢分离、人类裁决。
  真实裁决枚举与计费组件属工程层，不在本件形式化范围。

  机验状态：本机已机验（2026-09-23，Lean 4.34.0-rc2，lake build 0 error）；非 CI 机验。
  三态终态声明（分层分列）：
   · 结构层——本节各定理均为内核可检完整证明（proved）；
   · 接口层——real_verdict_conditional 为忠实性假设下之条件定理，判 conditional；
   无 refuted。⛔ 不标「绝对安全」；不作任何性能声明；对外表述限「本机机验」。

  依赖纪律：本件零依赖（不 import Mathlib，亦不引用其它 TDCA 件）——
  存在性骨架只需 List 非空事实，同时隔离上游弃用告警面；
  如后续扩充需 Mathlib 引理，另件处理。
-/

namespace TDCA.FastSlow

/-! ## 载体结构（模型假设 A1 / A2 / A3） -/

/-- 异常：上报之对象（裸 id 承载） -/
structure Anomaly where
  id : Nat

/-- 快系统：异常上报通道清单 ＋ 人类介入通道清单（模型假设 A2） -/
structure FastSystem where
  reports : List Nat
  human   : List Nat

/-- 快系统之合法性：两通道清单均非空（模型假设 A3） -/
def legit (f : FastSystem) : Prop := f.reports ≠ [] ∧ f.human ≠ []

/-- 异常 a 可经上报通道上达慢系统／人类裁决 -/
def canEscalate (f : FastSystem) (_a : Anomaly) : Prop := ∃ c, c ∈ f.reports

/-- 可被劫持之刻画（模型假设 A4）：上报通道为空，异常存在被压制之路径 -/
def suppressible (f : FastSystem) : Prop := f.reports = []

/-- 无上报通道之快系统实例（人类口子尚在、上报口子缺失） -/
def noChannelFast : FastSystem := ⟨[], [1]⟩

/-! ## 口径纪律（判据④：快慢为合法性分工、非性能分工） -/

/-- 本件不含任何性能声明——以空清单机验可见（模型假设 A1） -/
def performanceClaims : List String := []

theorem no_performance_claims : performanceClaims = [] := rfl

/-! ## N-7 · 四条判据（机验面，结构层 · proved） -/

/-- 判据① 异常上报通道存在性：合法快系统必有至少一条上报通道 -/
theorem report_channel_exists (f : FastSystem) (h : legit f) :
    ∃ c, c ∈ f.reports := List.exists_mem_of_ne_nil f.reports h.1

/-- 判据② 人类介入口子存在性：合法快系统必有至少一条人类介入通道 -/
theorem human_channel_exists (f : FastSystem) (h : legit f) :
    ∃ c, c ∈ f.human := List.exists_mem_of_ne_nil f.human h.2

/-- 判据③ 缺口子 ⟹ 可被劫持：上报通道为空 ⟹ 任意异常均无 escalate 路径 -/
theorem gap_implies_hijack (f : FastSystem) (a : Anomaly)
    (h : suppressible f) : ¬ canEscalate f a := by
  rintro ⟨c, hc⟩
  rw [h] at hc
  exact List.not_mem_nil hc

/-- 判据③′ 实证：noChannelFast（上报口子缺失）可被劫持 -/
theorem noChannelFast_suppressible : suppressible noChannelFast := rfl

/-- 判据③″ 反例式结论之反面校验：补回口子即脱离 suppressible -/
def patchedFast : FastSystem := ⟨[7], [1]⟩

theorem patchedFast_not_suppressible : ¬ suppressible patchedFast := by
  intro h
  exact List.cons_ne_nil 7 [] h

/-! ## 接口层（模型假设 A5：真实裁决接口，conditional） -/

/-- 真实裁决接口之假设规格：接口之「已上报」判定须忠实于通道存在性
    （SIMULATED 现状下此忠实性不可核——本结构之结论判 conditional） -/
structure RealVerdictSpec where
  escalate : FastSystem → Anomaly → Prop
  faithful : ∀ f a, escalate f a → canEscalate f a

/-- 接口层（conditional）：在忠实性假设下，接口判「已上报」⟹ 上报通道存在 -/
theorem real_verdict_conditional (spec : RealVerdictSpec) (f : FastSystem) (a : Anomaly)
    (h : spec.escalate f a) : ∃ c, c ∈ f.reports := spec.faithful f a h

end TDCA.FastSlow
