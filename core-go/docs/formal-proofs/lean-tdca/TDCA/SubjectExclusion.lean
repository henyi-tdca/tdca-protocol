/-
  TDCA 形式化证明课题 · 智能体定义骨架 P1 · 主体排他（SubjectExclusion）
  ============================================================================
  施工：四条形式化陈述骨架 · P1（交办令 TDCA-HANDOFF-FORMAL-AGENT-DEFINITION-001）
  状态：本机机验（2026-10-16，Lean 4.34.0-rc2）——exit 0、零 sorry；**非 CI 机验**，
        对外不得称「已证明」（表述与机验纪律，与在册各件同）。

  陈述：调用之主体限于智能体；⛔ 离散资产不可调用（类型层封闭）。
  范式（照设计件 · 与在册准入模块同范式）：**封闭归纳式**——只列主体构造子，
  未列出者即不可调用；⛔ **弃用外部之类型类（class）写法**（实例可后加、不可证）。

  模型假设（显式，不得省略）：
   A1 AgentKind ≠ DiscreteAssetKind（两类型显式不等前提，定理之显式参数）；
   A2 Callable 之封闭列举（归纳定义本身即「未列出者不可调用」之刻画）。
  适用范围：类型层排他之抽象骨架（与准入七态机之封闭迁移同一范式）；
  不主张任何制度层结论；不标「绝对安全」；对外表述限「本机机验」。

  三态终态声明：本件定理为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项。
-/

namespace TDCA.SubjectExclusion

/-- 可调用关系（**封闭归纳** —— 只列主体构造子；未列出者即不可调用）。
    参数 AgentKind 为唯一可调用主体类型（模型假设 A2 之载体）。 -/
inductive Callable {AgentKind : Type} : Type → Prop
  | agent : Callable AgentKind

/-- 主体排他定理：离散资产不可调用。
    前提（⛔ 显式，不得省略）：AgentKind ≠ DiscreteAssetKind（模型假设 A1）。 -/
theorem discrete_asset_not_callable {AgentKind DiscreteAssetKind : Type}
    (hneq : AgentKind ≠ DiscreteAssetKind) :
    ¬ Callable (AgentKind := AgentKind) DiscreteAssetKind := by
  intro h
  cases h
  exact hneq rfl

end TDCA.SubjectExclusion
