/-
  TDCA 形式化证明课题 · 协调原理簇（COORD）· 第一批之一 · COORD-1（协商拓扑计数）
  ============================================================================
  建模方式：独立件、独立命名空间、零依赖（不 import Mathlib，亦不引用其它 TDCA 件）
  —— 计数骨架只需 Nat 事实；同时隔离上游弃用告警面（照本工程既有件纪律）。

  模型假设（显式，不得省略）：
   C1 对等商议拓扑 ＝ n 名对等商议者，两两一条对齐通道（无序对）；本件以递归计数
      `pairwiseChannels`（`C(0)=0`、`C(n+1)=C(n)+n`）承载，即 C(n)=0+1+…+(n−1)。
   C2 中枢-分发拓扑 ＝ 单一决策中枢 + n 个执行节点，对齐通道为树边：`starChannels n = n−1`。
   C3 本件只做计数：⛔ 不引入成本 c_d/c_i、编译成本 K 与复用次数 m —— 成本与最优性
      属第二批次（COORD-3/COORD-4，conditional），不在本件范围。

  适用范围：抽象计数骨架层。⛔ 不主张任何制度层结论；⛔ 不标「绝对安全」；
  对外表述限「本机机验」。

  机验状态：本机机验（Lean 4.34.0-rc2 · lake build）；非 CI 机验。
  三态终态声明：本件各定理均为内核可检完整证明（proved，以显式假设为前提）；
  无 refuted、无 conditional 残留项、无占位（sorry）。

  边界（如实）：本件给出三组结论 —— 基线实例、单调性、下界（不低于规模减一）；
  ⭐ 一般式「∀ n ≥ 3，`starChannels n < pairwiseChannels n`」需与计数闭式
  n(n−1)/2 桥接（除法定理），按「收窄不硬证」另列后续批次，⛔ 不以实例冒充一般式。
-/

namespace TDCA.Coord

/-! ## 载体：两种拓扑的计数（模型假设 C1 / C2） -/

/-- 对等商议拓扑的对齐通道数（无序对）：递归定义 `C(0)=0`、`C(n+1)=C(n)+n` -/
def pairwiseChannels : Nat → Nat
  | 0 => 0
  | n + 1 => pairwiseChannels n + n

/-- 中枢-分发拓扑的对齐通道数（树边）：`n − 1` -/
def starChannels (n : Nat) : Nat := n - 1

/-! ## COORD-1 · 基线实例（内核可检） -/

/-- 空系统：零通道 -/
theorem coord1_base_0 : pairwiseChannels 0 = 0 := rfl

/-- 单参与者：零通道 -/
theorem coord1_base_1 : pairwiseChannels 1 = 0 := rfl

/-- 三参与者：三条通道（0+1+2） -/
theorem coord1_base_3 : pairwiseChannels 3 = 3 := rfl

/-- 四参与者：六条通道（0+1+2+3） -/
theorem coord1_base_4 : pairwiseChannels 4 = 6 := rfl

/-! ## COORD-1 · 单调性（结构归纳） -/

/-- 通道数随规模不减：`C(n) ≤ C(n+1)` -/
theorem pairwiseChannels_mono (n : Nat) : pairwiseChannels n ≤ pairwiseChannels (n + 1) := by
  simp [pairwiseChannels]

/-! ## COORD-1 · 下界（结构归纳） -/

/-- 对等通道数不低于规模减一：`n − 1 ≤ C(n)` -/
theorem pairwiseChannels_ge_sub_one (n : Nat) : n - 1 ≤ pairwiseChannels n := by
  induction n with
  | zero => omega
  | succ m ih =>
      simp [pairwiseChannels]

/-! ## COORD-1 · 降维（星形 < 对等）· 基线实例 -/

/-- 实例 n = 3：星形 2 < 对等 3 -/
theorem coord1_reduction_3 : starChannels 3 < pairwiseChannels 3 := by decide

/-- 实例 n = 4：星形 3 < 对等 6 -/
theorem coord1_reduction_4 : starChannels 4 < pairwiseChannels 4 := by decide

/-- 实例 n = 5：星形 4 < 对等 10 -/
theorem coord1_reduction_5 : starChannels 5 < pairwiseChannels 5 := by decide

end TDCA.Coord
