/-
  TDCA 形式化证明课题 · 协调原理簇（COORD）· 第一批之二 · COORD-2（硬阈值二分类必存误分带）
  ============================================================================
  建模方式：独立件、独立命名空间、零依赖（不 import Mathlib）。
  ⭐ 本件为「离散收窄版」——「风险连续 ⇒ 误分带测度为正」之**连续版**需测度论
  （`MeasureTheory`），按「收窄不硬证」另列后续批次，⛔ 不以本件冒充连续版。

  模型假设（显式，不得省略）：
   D1 能力坐标取离散档位（本件以 Nat 承载，档位间为全序）；
   D2 风险 r : Nat → Nat 为档位到风险的赋值（本件不假设单调性——结论只用到
      「最低档低于阈值」与「存在不低于阈值之档」两条）；
   D3 判决为硬阈值二分类：`verdict r τ x := decide (τ ≤ r x)`。

  陈述：若最低档低于阈值（`r 0 < τ`）且存在不低于阈值之档，则**存在相邻两档
  判决相异**（`k` 判负、`k+1` 判正）—— 即**阈值处必有类型翻转**，硬阈值二分类
  在结构上无法避免「带内误分」。细分档数只压缩该带，不能消除。

  适用范围：抽象离散骨架层。⛔ 不主张任何制度层结论；⛔ 不标「绝对安全」；
  对外表述限「本机机验」。

  机验状态：本机机验（Lean 4.34.0-rc2 · lake build）；非 CI 机验。
  三态终态声明：本件各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项、无占位（sorry）。
-/

namespace TDCA.CoordThreshold

/-- 判决函数（模型假设 D3）：硬阈值二分类 `x ↦ (τ ≤ r x)` -/
def verdict (r : Nat → Nat) (τ : Nat) (x : Nat) : Bool :=
  decide (τ ≤ r x)

/-- 辅助（结构归纳）：存在不低于阈值之档 ⟹ 存在相邻跨阈值之对 -/
theorem coord2_threshold_band_aux (r : Nat → Nat) (τ : Nat) (h0 : r 0 < τ) :
    ∀ n, τ ≤ r n → ∃ k, r k < τ ∧ τ ≤ r (k + 1) := by
  intro n
  induction n with
  | zero =>
      intro h
      exact absurd h (Nat.not_le_of_gt h0)
  | succ m ih =>
      intro h
      rcases Nat.lt_or_ge (r m) τ with hlt | hge
      · exact ⟨m, hlt, h⟩
      · exact ih hge

/-- COORD-2 · 阈值带（离散版）：
    若最低档低于阈值且存在不低于阈值之档，则存在相邻两档 `k`、`k+1` 跨阈值
    —— 即 `r k < τ ≤ r (k+1)`（阈值必落在相邻两档之间） -/
theorem coord2_threshold_band (r : Nat → Nat) (τ : Nat)
    (h0 : r 0 < τ) (hhi : ∃ n, τ ≤ r n) :
    ∃ k, r k < τ ∧ τ ≤ r (k + 1) := by
  obtain ⟨n, hn⟩ := hhi
  exact coord2_threshold_band_aux r τ h0 n hn

/-- COORD-2 · 类型翻转：存在相邻两档判决相异（`k` 判负、`k+1` 判正）
    —— 硬阈值二分类必有「误分带」之机验面 -/
theorem coord2_flip (r : Nat → Nat) (τ : Nat)
    (h0 : r 0 < τ) (hhi : ∃ n, τ ≤ r n) :
    ∃ k, verdict r τ k = false ∧ verdict r τ (k + 1) = true := by
  obtain ⟨k, hk1, hk2⟩ := coord2_threshold_band r τ h0 hhi
  refine ⟨k, ?_, ?_⟩
  · unfold verdict
    exact decide_eq_false_iff_not.mpr (Nat.not_le_of_gt hk1)
  · unfold verdict
    exact decide_eq_true_iff.mpr hk2

/-- 机验基线实例：恒等风险（`r n = n`）、阈值 `3` ⟹ 存在翻转 -/
theorem coord2_example :
    ∃ k, verdict (fun n => n) 3 k = false ∧ verdict (fun n => n) 3 (k + 1) = true := by
  apply coord2_flip
  · decide
  · exact ⟨3, by decide⟩

end TDCA.CoordThreshold
