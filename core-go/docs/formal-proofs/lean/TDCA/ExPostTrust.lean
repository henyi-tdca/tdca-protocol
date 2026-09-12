/-
  TDCA-WP-MATERIALISM-001 V1.1 · §5.2.1 博弈模型 · Lean 4 候选
  ============================================================================
  内容：命题 P4a（替代条件）证明 + 推论 2（攫取问题比较静态）形式化
  状态：CANDIDATE——未经 Lean 工具链机器验证，须 CI（lake env lean）零错误。
        P4a 已完整证明；推论 2 含 1 处显式 sorry，sorry 清零前不得标 Tier A
        （TDCA 分层标注纪律 + 闭环时机内生原理：不强行闭环）。
  模型假设（按 V1.2 修订建议取定：存证成本 C 由委托方 A 承担——
    委托方为过程可信付费，与 L1 增值服务结构自契）：
    · 单次协作；V 关于 e_B 严格凹、递增、连续可微（分析假设）
    · 内点解条件：(1-α)·∂V/∂e_B (e_A, 0) > 1
  不标"绝对安全"：本模型刻画单次协作的期望成本比较，
  重复博弈、参与约束与 C 的内生分摊为模型外因素。
-/

import Mathlib.Data.Real.Basic

namespace TDCA.ExPostTrust

/-! ## 模型参数（§5.2.1） -/

/- 争议概率 q ∈ (0,1) -/
variable (q : ℝ)
/- 过程可观测性 p ∈ [0,1]：过程记录事后可被独立查证的概率 -/
variable (p : ℝ)
/- 篡夺收益 R > 0（声誉与资产再分配收益） -/
variable (R : ℝ)
/- 存证固定成本 C > 0（由委托方 A 承担） -/
variable (C : ℝ)

/-! ## 命题 P4a：T_process 替代条件（已证） -/

/-- T_ex-post 预期争议成本：q·(1−p)·R -/
def costExPost (q p R : ℝ) : ℝ := q * (1 - p) * R

/-- T_process 预期存证成本：C（A 承担） -/
def costProcess (C : ℝ) : ℝ := C

/-- P4a：C < q(1−p)R ⟹ T_process 严格占优，占优间隙为正。
    证明：纯不等式差，sub_pos 逆向引用，核心一行。 -/
theorem P4a_substitution_condition
    (h : C < q * (1 - p) * R) :
    0 < costExPost q p R - costProcess C := by
  unfold costExPost costProcess
  exact sub_pos.mpr h

/-! ## 推论 2：攫取问题的比较静态（1 处 sorry，义务见尾注） -/

/- 边际产出 D = ∂V/∂e_B（e_A 固定截面；严格递减 ⟸ V 对 e_B 严格凹） -/
variable (D : ℝ → ℝ)

/-- 推论 2：被篡夺比例 α 越大，执行方最优努力 e_B* 越低；
    α = 0（T_process，篡夺风险归零）时 e_B* 收敛于社会最优。
    · hD        ：D 严格递减（严格凹性的微分形态）
    · e / hFOC  ：e_B*(α) 处处满足内点一阶条件 (1−α)·D(e_B*) = 1
    · hinterior ：内点条件 D(e_B*) > 0
    · hα / hβ   ：参数域 α, β < 1（保证 1−α > 0，倒数运算合法） -/
theorem corollary2_effort_comparative_statics
    (hD : ∀ a b : ℝ, a < b → D b < D a)
    (e : ℝ → ℝ)
    (hFOC : ∀ α : ℝ, (1 - α) * D (e α) = 1)
    (hinterior : ∀ α : ℝ, 0 < D (e α))
    (α β : ℝ) (hα : α < 1) (hβ : β < 1) (hab : α < β) :
    e β < e α := by
  have h1 : (0:ℝ) < 1 - β := sub_pos.mpr hβ
  have h3 : (1:ℝ) - β < 1 - α := sub_lt_sub_left hab 1
  have hDe : D (e α) < D (e β) := by
    by_contra hle
    push_neg at hle
    have h4 : (1 - β) * D (e β) ≤ (1 - β) * D (e α) :=
      mul_le_mul_of_nonneg_left hle (le_of_lt h1)
    have h5 : (1 - β) * D (e α) < (1 - α) * D (e α) :=
      mul_lt_mul_of_pos_right h3 (hinterior α)
    have h6 : (1 - β) * D (e β) < (1 - α) * D (e α) := lt_of_le_of_lt h4 h5
    rw [hFOC β, hFOC α] at h6
    exact (lt_irrefl _) h6
  by_contra hge
  push_neg at hge
  rcases eq_or_lt_of_le hge with heq | hlt
  · rw [heq] at hDe
    exact (lt_irrefl _) hDe
  · exact absurd hDe (not_lt_of_gt (hD _ _ hlt))
  /- 证明策略（初等单调性路径，无需分析库——★ 级而非 ★★ 级）：
     1. 由 hFOC 得 (1−α)·D(e α) = (1−β)·D(e β)
     2. 反设 D(e β) ≤ D(e α)：由 0 < 1−β < 1−α 及 hinterior，
        (1−β)·D(e β) ≤ (1−β)·D(e α) < (1−α)·D(e α)，与 1 矛盾
        （by_contra + mul_lt_mul 系列引理，全部在 Mathlib 实数序公理内）
     3. 故 D(e β) > D(e α)；由 hD 反单调性得 e β < e α
     ────────────────────────────────────────────────────────────
     剩余义务（sorry 清零 checklist）：
     [1] 第 2 步实数不等式链的机器形式化（mul_lt_mul_of_pos 系引理装配）
     [2] α = 0 即社会最优的单独陈述与 FOC 退化校验
     [3] 由"假设 FOC 处处成立"升级为"从 V 的凹性证出 FOC 刻画"
         （唯一性由严格凹保证）——此项为分析核心，失败则降级为
         conditional 命题并更新适用范围，亦为合法终态。 -/

end TDCA.ExPostTrust
