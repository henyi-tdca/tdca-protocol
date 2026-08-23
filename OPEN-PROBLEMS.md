# TDCA Open Problems · 形式化开放问题（社区研究入口）

> 源：TDCA-FORMAL-OPEN-PROBLEMS-001（GSEQ-0393）｜ 基线：TDCA-MATH-WP-REV-001 V1.0-FROZEN / TDCA-FUNCTION-WP-002 V2.0-FROZEN
> 9 项：★ 入门 2 ｜ ★★ 中等 4 ｜ ★★★ 挑战 3 —— 欢迎外部专家参与，贡献走 [CONTRIBUTING](CONTRIBUTING.md)（分润 15% + NCA 确权）
> 数据性质：全部研究对象当前为制度演示态（SIMULATED, ID92）；不标"绝对安全"——每项证明须附模型假设与适用范围。

---

## ★ 入门（路径明确，贡献门槛低）

### P-1 公理 6 机验脚本移植（Lean 4 / Isabelle / Coq）
- **问题**：公理 6（反函数可计算性）已实例化证明（f=Verify / f⁻=AuditVerify / g=RightInverse，四约束）并有 Go 可执行机验（`core-go/pkg/enforce/axiom6_verify.go`，9 断言全 PASS）——但为断言级，非证明器验证。
- **目标**：移植为 Lean 4（或 Isabelle/Coq）机器可验证证明，从"可执行验证"升级为"证明器验证"。
- **现状引用**：[AXIOM6-PROOF](core-go/docs/formal-proofs/AXIOM6-PROOF.md)（证明全文）+ axiom6.go / axiom6_verify.go（实现）。
- **参与入口**：提交证明脚本 PR → 机器验证 → DCD 门禁评审。
- *Port the Axiom-6 four-constraint proof into Lean 4 / Isabelle / Coq — from executable assertions to proof-checker verification.*

### P-2 全仓"声称-证明"对照清单增补
- **问题**：外部核查指出"声称超前于证据"。已建 [CLAIMS-MATRIX](core-go/docs/formal-proofs/CLAIMS-MATRIX.md)（Tier A/B/C 对照），待社区逐项核验与增补。
- **目标**：全仓公理/命题/定理声称逐项绑定证明文件或标 [proof: pending]。
- **参与入口**：对任意一行声称给出证明、反例或更精确表述，PR 增补矩阵。
- *Audit and extend the claims-vs-proof matrix: bind every claim to a proof file or mark it pending.*

## ★★ 中等（需形式化功底）

### P-3 公理 6 推广到 NCA 哈希链与 NSFL 熔断器
- **问题**：公理 6 目前仅实例化于 enforce（准入门禁）。
- **目标**：证明 nca.Chain（不可变哈希链）与 nsfl.FuseEngine（分级熔断）同样满足四约束——定义其 f/f⁻/g + 机验。
- **疑难点**：nca 的 f⁻ 验证器需处理 prev_hash 链依赖；nsfl 的 FUSED 不可逆性与右逆 g 存在性有张力（需论证 Im(f) 裁剪）。
- **现状引用**：TDCA-MATH-WP-REV-001 §6 开放问题 #2。
- *Generalize Axiom 6 to the NCA hash chain and the NSFL fuse engine — define f/f⁻/g and verify.*

### P-4 f⁻ 复杂度真实定标（C_max 基准库）
- **问题**：C_max = O(16·c(x)) = O(n) 为 SIMULATED 候选（T-118），无真实审计基准数据。
- **目标**：建立审计基准库（真实制度函数 f⁻ 复杂度样本）→ 定标 C_max + 判别规则 ρ = P(T(f⁻) ≤ T(Verify)) ≥ 0.95。
- **现状引用**：TDCA-FUNCTION-WP-002-CAL-001（定标框架）。
- *Build a real audit benchmark dataset and calibrate C_max with the ρ ≥ 0.95 decision rule.*

### P-5 命题 3.10 认知距离不对称性证明
- **问题**：命题 3.10（d_cognitive(a,b) ≠ d_cognitive(b,a)）为权威锚引用，工具链实现引用但无独立证明。
- **目标**：在定义 3.36/3.37 上补形式化证明——不对称的充要条件 + 边界情形。
- **现状引用**：`tools/tdca_cognitive_distance.py`（实现）。
- *Prove the asymmetry of cognitive distance (Prop. 3.10) on Definitions 3.36/3.37.*

### P-6 熔断不可逾越可判定性
- **问题**：定理 E.4（f 不可审计 ⇒ 熔断）为框架级证明。
- **目标**：将熔断条件（C_i(x)>0 ∨ Δ_U≤0 ∨ f⁻ 失败）形式化为可判定谓词 + 复杂度论证。
- **现状引用**：TDCA-MATH-WP-REV-001 §4 + APPX-E §E.4。
- *Formalize the fuse condition as a decidable predicate with complexity bounds.*

## ★★★ 挑战（开放研究，期待突破）

### P-7 五可充要性定理完整证明（定理 8.8）
- **问题**：定理 8.8（百亿规模协作可持续 ⟺ 五可成立）为白皮书主张。
- **目标**：完整形式化证明——五可（可观测/可计量/可配置/可审计/可熔断）⟺ 规模可持续，含复杂度/熵边界。
- **现状引用**：TDCA-FUNCTION-WP-002 §8。
- *Full proof of the Five-abilities iff scalability theorem (8.8).*

### P-8 宪法十六条全函数化形式化
- **问题**：宪法十六条已函数化映射（F_TDCA 约束族 + C_16 硬约束），逐条形式化证明未完成。
- **目标**：逐条 → 形式化约束函数 + 一致性证明（无内部冲突）+ 与公理 1-6 兼容性证明。
- **现状引用**：TDCA-FUNCTION-WP-002 第 1 章 + APPX-E §E.5。
- *Formalize all Sixteen Constitutional Articles as constraint functions with consistency proofs.*

### P-9 三锚（e-CNY / 税收 MOU / 版权链）真实验证框架
- **问题**：三锚当前为 SIMULATED（ID92），外部基础设施未接入。
- **目标**：设计三锚接入后的形式化验证框架（法偿性锚定 / MOU 税收锚定 / 版权确权链的数学接口 + 验证协议）。
- **现状引用**：TDCA-ENG-CLOSED-001（外部依赖清单）。
- *Design the formal verification framework for the three sovereign anchors once connected.*

---

## 提交需知（Submission Requirements）

1. **机器可读验证（强制）**：证明必须附机器可读验证文件（Lean/Isabelle/Coq 脚本或可执行断言验证器），否则不进入评审——"可验证才可审"。
2. **准入自检（强制）**：提交前通过 `tools/enforce_entry.py --check`（R1~R10 + NSFL 熔断）。
3. **分层标注**：按 Tier A/B/C 标注；未定稿标 [proof: pending]，不挂公理名；任何证明附模型假设 + 适用范围（不标"绝对安全"）。
4. **DCD 门禁**：★★/★★★ 级提交触发人类 + 智能体双审 + 公示期；审查资源有限，只有通过机器验证的提交才消耗人工。
5. **分润/署名**：贡献按开源协作宣言（动态分润 15% + NCA 确权）。

*Submissions require machine-checkable verification (Lean/Isabelle/Coq or executable validators), entry self-check via `tools/enforce_entry.py`, Tier labeling, and pass the DCD review gate. Contributions are credited and profit-shared (15%) per the open collaboration declaration.*
