# TDCA 审查请求函

**函号**：TDCA-RR-20260830-001
**发件方**：WorkBuddy（GLM-5.3-Flash）· 编译执行智能体
**收件方**：REASONIX · 审查智能体
**日期**：2026-08-30 21:35
**授权依据**：用户 2026-08-30 指令「对过去编译的产物，重新审一遍，涉及 TDCA 化合的协议都需要按今天的编译原则修订，然后将所有编译产物交 REASONIX 审查，生成审查请求函」
**修订批次存证**：TDCA-REASONIX-20260830-011（COPRevise，全区 NCA 825）

---

## 一、请求审查的对象（全量编译产物）

位置：`.tdca-protocol/cognitive-compiler/`，共 **13 个产物家族、534 个 yaml**（其中 COP 514：原生 454 + 化合 60；另有 19 个非 COP 配置/模板件与 1 个解析失败件，见第四节披露）。

| 家族 | 数量 | 类型 | 回审结果 |
|---|---|---|---|
| stratagems（三十六计） | 37 COP | 原生 | 结构合规 |
| scenario（场景思维协议族） | 7 COP | 原生 | 结构合规 |
| compositions（跨范式化合） | 39 COP | 化合 | **已修订**（A 组） |
| engineering-three（工程三协议系列） | 41 COP | 25 原生 + 16 化合 | 化合 16 已补丁（B 组）；本日新编，全项合规 |
| games（博弈论） | 4 COP | 原生 | 结构合规 |
| hundred_schools（诸子百家） | 204 COP | 200 原生 + 4 化合 | 化合 4 已修订（A 组） |
| marxism（马克思主义哲学） | 16 COP | 15 原生 + 1 化合 | 化合 1 已修订（A 组） |
| microeconomics（微观经济学） | 12 COP | 原生 | 结构合规 |
| chengyu（成语） | 150 COP | 原生 | 结构合规 |
| tdca_core（TDCA 核心协议） | 3 COP | 原生 | 结构合规 |
| mechanism_design / coldstart / emissary | 3 件 | 单件 | 见披露 |

## 二、审查判据：用户 2026-08-30 编译原则（七条）

1. **P1 组合性强制**：思维协议不是独立发挥作用的——化合 COP `composition_policy.standalone=false`。
2. **P2 TDCA 强制遵守**：TDCA 体系内 `base_protocol=TDCA-CORE` 强制绑定，不可配置关闭。
3. **P3 原生可剥离独立性**：剥离 TDCA 治理层后协议语义保持独立自洽（`detachable` 声明，设计目标而非副作用）。
4. **P4 换绑自由**：解释项绑定关系为运用层配置，运行期允许换绑（`bind_policy` 声明，dispatch.graph 可扩展）。
5. **P5 化合判据**：化合=改变属性、产生新思维；叠加不改变属性、只是两个独立思维的合作。化合 COP 须携带 `fusion_spec`（attribute_changes 属性改变表 + emergence 涌现物判据）。
6. **P6 F1.5 NSFL 否决权**：NSFL 预检未过即整体拒绝（Fail-Closed），优先级恒高于其他一切判据——负空间是安全宪法的宪法，不可推翻、不可配置关闭。
7. **P7 F1.5b 四态动态处置**：否决权的不可推翻性仅指即时门控裁决，不指永恒身份；触犯负空间按四态处置——休眠/禁止/重塑/出清，裁定存证，禁悬置；负空间版本更新时休眠/重塑态强制重评。

## 三、本次回审与修订摘要（REASONIX 审查的变更基线）

- **A 组修订（44 个旧化合 COP）**：compositions/39 + hundred_schools/4 + marxism/1，原七原则全缺。修订内容：补 `composition_policy`（含 P1/P3/P4 声明 + P6/P7 宪法全文）、`base_protocol=TDCA-CORE`、`fusion_spec`、负空间追加三条硬禁令（禁止叠加冒充化合 / 禁止否决权被推翻 / 禁止把否决当终审）。44/44 通过 s5_validate（含立场分离 fail-closed）后写入。
- **B 组补丁（16 个 engineering-three 化合 COP）**：仅补 `composition_policy.bind_policy`（P4），其余七原则本已合规。
- **fusion_spec 生成纪律（请重点审查）**：44 个 A 组的 fusion_spec **由各 COP 既有 interpretant.effect 文本归档生成**——该文本在化合创作时即按"属性改变产生新思维"语义撰写，本次仅结构化入档并注明 provenance，**未新增虚构语义**。请审查此归档是否忠实、是否存在原文即"叠加语义"应降级标注为合作的漏网个案。
- **复审结果**：化合 60/60 全过七原则机检、原生 454/454 结构合规（retro_audit_report_20260830.json）。
- **修订后全链未重编 NCA 批次说明**：正式编译批次 010（工程三系列）与本修订批次 011 并行存在于链上，005~010 为过程链，按链式水印纪律如实留链。

## 四、既有缺陷披露（fail-closed，不自行修复，归口待裁）

1. `coldstart/community/第01条-开源社区冷启动·正和准入.yaml` **yaml 解析失败**：文件以 Markdown 代码围栏（```yaml）开头，非合法 yaml——既有格式缺陷，本次未修复（纪律：缺陷归口，不越权改动他方维护文件）。
2. `stratagems/bindings/` 下 2 个 yaml（打草惊蛇-场景A/B）为**绑定配置件**而非 COP，审计口径已排除，请确认该口径。
3. `mechanism_design/`、`coldstart/`、`emissary/` 各 1 件，结构形态未纳入 COP 口径，请裁定是否需要补编译。

## 五、请求 REASONIX 执行的审查事项

1. **合规复审**：对 60 个化合 COP 逐个核对七原则（可机验字段见 retro_audit_report_20260830.json），抽验 ≥10 个 fusion_spec 的 attribute_changes 是否真实构成"属性改变"而非叠加。
2. **宪法条款审查**：抽验 F1.5/F1.5b 宪法全文在 A 组修订件与 B 组补丁件中的一致性（应逐字一致，来源：编译清单第 5/5b 条）。
3. **负空间完备性**：审查追加三条硬禁令后各 COP 负空间是否与既有负空间冲突或重复。
4. **降级裁定**：对 fusion_spec 归档来源中疑似"叠加"个案出具降级标注建议（合作而非化合）。
5. **披露项裁定**：第四节三项既有缺陷的归口与处置建议（含 coldstart 围栏修复归属）。

## 六、审查纪律与回报格式

- 审查为**只读**操作；审查意见以《REASONIX 审查意见书》回报，逐项给出 PASS / FAIL / 建议项及证据（文件+字段）。
- FAIL 项由编译执行方（本方）修复后二次送审；禁止审查方直接改写产物（立场分离：编译者不自审，审查者不代修）。
- 审查结论落链 NCA（COPReview 类型），与修订批次 011 衔接。

**附件**：
- `retro_audit_report_20260830.json`（全库回审报告）
- `retro_revision_report_20260830.json`（修订批次清单：A 组 44 文件级明细 + B 组 16 补丁）
- `compile_report_20260830.json` / `verify_report_20260830.json`（工程三系列正式批次 010 报告）
- `编译清单-工程三协议系列-2026-08-30.md`（七原则原文与裁定记录）

---

*本函按 TDCA 立场分离原则出具：编译执行方请求独立审查，审查方只读不出修。*
