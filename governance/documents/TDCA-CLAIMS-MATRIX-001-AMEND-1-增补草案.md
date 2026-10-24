# CLAIMS-MATRIX 增补草案（2026-09-12）
> ⚠️ **自我更正（2026-09-12，GSEQ-1340）**：本件原表述「§五 后新增 §六」为**笔误**——依矩阵实际节序（§一 Tier A / §二 Tier B / §三 Tier C / **§四 规则**），正确表述应为「**§四 后新增 §五**」。主仓件已按创始人裁定顺次改号为 **§五**（指令件 GSEQ-1340）。
> ⏳ **已提请签批**：**DCD-004-TT-006**（GSEQ-1332，2026-09-12，创始人指示按 DCD 流程提请）；签批权不代行（ID71）。
> ✅ **已签批（ACCEPT）**：DCD-004-TT-006（GSEQ-1335，2026-09-12）。
> 状态：**✅ 已签批（DCD-004-TT-006，创始人 ACCEPT 2026-09-12 / GSEQ-1335）——待批次推送主仓**
> 用途：随 TDCA-PRINCIPLE-EVO-001 与 WP-MATERIALISM-001 §5.2.1 的
> Lean 候选证明一并提交 DCD。三处修改：规则增补 / 新条目 / 开放问题新条目。
>
> 性质: 内部草案（待 DCD 门禁评审后随批推主仓 `core-go/docs/formal-proofs/CLAIMS-MATRIX.md`）——非司法裁决、不得单独作为处分依据

---

## 一、规则增补（§四 后新增 §五）

### §五 三层归档原则（P3 × Tier 映射）

| 层 | 性质 | 归档去向 | "闭环"标准 |
| --- | --- | --- | --- |
| 事实层 | 存在性即正当性，不可辩驳 | 免判据，不入矩阵 Tier | 无需闭环 |
| 模型层 | 有损压缩，可竞争可证伪 | Tier A/B/C，走证明器 | proved / refuted / conditional 三态 |
| 制度层 | 建构物，活规则 | 不入 Tier，走 DCD 存证 | 修订程序闭环，永不走证明器 |

新增声称须先声明所属层，再按该层标准归档；跨层引用须注明层间映射。

## 二、新条目

### Tier B（新增）

| # | 声称 | 证明文件 | 状态 |
| --- | --- | --- | --- |
| B-3 | 命题 P4a：C < q(1−p)R ⟹ T_process 严格占优 | WP-MATERIALISM-001 §5.2.1 + `TDCA-P4a-Corollary2-Lean4-Candidate.lean` | 🔶 Lean 候选已证，待 CI 机验后升 A；模型假设：单次协作、C 由 A 承担 |
| B-4 | 推论 2：α ↑ ⟹ e_B* ↓（攫取问题的比较静态） | 同上 Lean 文件 | 🔶 含 1 处 sorry（初等单调性路径，★ 级）；清零路径已列，清零后升 A，证不出则降 conditional |

### Tier C（新增）

| # | 声称 | 状态 |
| --- | --- | --- |
| C-7 | 推论 2 的 α=0 社会最优校验 + FOC 由凹性证出（分析核心） | [proof: pending] —— 见 Lean 文件尾注 checklist [2][3] |

## 三、OPEN-PROBLEMS 新条目草案

### P-10 推论 2 初等证明路径机器化（★ 入门）

- **问题**：Lean 候选已给出初等单调性证明策略（WP-MATERIALISM-001 §5.2.1 尾注），
剩余第 2 步实数不等式链（by_contra + mul_lt_mul 系引理装配）未机器化。
- **目标**：sorry 清零 → corollary2_effort_comparative_statics 升 Tier A；
失败则输出精确反例或改述命题，二者皆为合法终态（EVO-001 三态原则）。
- **依赖**：仅 Mathlib.Data.Real.Basic，无分析库依赖。

---

*增补随 DCD 门禁评审；与 TDCA-PRINCIPLE-EVO-001 草案互引。*
