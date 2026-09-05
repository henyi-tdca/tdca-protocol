# TDCA 官方智能体矩阵（V2.2 · 全量）

> 文档标识: TDCA-AGENT-MATRIX-V2.2 | 编制: 2026-08-15 | 状态: ACTIVE
> 定位: TDCA 官方创设智能体集群能力底座（**26 个**）——含类型/职能/调用关系/备案
> 依据: 各 SKILL.md 注册 + 系统 Skills 索引 + 记忆 tdca-agent-matrix（V1：16 个）+ 新创设（archive/cls-officer/研究型 4/保险官/清算风控官/**scenario-architect 场景架构师**）
> 术语基线: 注册表 V2.1（T-001~T-109）

---

## 一、总览（26 个 = 18 服务 + 4 研究 + 4 运维金融）

| 类 | 数量 | 智能体 |
|----|------|--------|
| A 官方服务 | 18 | code-reviewer / compliance-auditor / contract-coder / economist / entropy-guard / examiner / glossarian / industry-advisor / kg-qa / mou-anchor / notary / ota-manager / pricer / scenario-designer / **scenario-architect** / ta / tax-officer / trainer |
| B 智库研究 | 4 | researcher / literature / critic / concept-proposer |
| C 运维金融 | 4 | archive / **cls-officer**（结算）/ **cls-risk-officer**（风控）/ **insurance-officer**（保险）|

## 二、全量明细表

| # | 智能体 | 类型 | runAs | 职能 | 输出仓/调用库 |
|---|--------|------|-------|------|--------------|
| 1 | tdca-code-reviewer | 执行型 | subagent | 代码审查（制度+技术 10 项清单）| tdca-code-reviewer-output/ |
| 2 | tdca-compliance-auditor | 执行型 | subagent | 制度合规审查（宪法/TERMS/NSFL 逐条）| tdca-compliance-output/ |
| 3 | tdca-contract-coder | 执行型 | subagent | 智能合约工程（宪法/经济模型→C01-C16）| tdca-contract-output/ |
| 4 | tdca-economist | 执行型 | subagent | 经济计算（MOU/Shapley/UPDA/五维，数据性质标注）| tdca-economist-output/ |
| 5 | tdca-entropy-guard | 执行型 | subagent | 接口熵检查（ID82）| tdca-entropy-guard-output/ |
| 6 | tdca-examiner | 执行型 | subagent | 考核测评（教材出题/评分/学习路径）| tdca-examiner-output/ |
| 7 | tdca-glossarian | 只读 | subagent | 术语检索（TERMS-001 精确查询）| 只读咨询 |
| 8 | tdca-industry-advisor | 执行型 | subagent | 行业落地（行业→方案匹配+缺口诊断）| — |
| 9 | tdca-kg-qa | 只读 | subagent | 知识图谱问答（KG 推理链，Mermaid）| 只读咨询 |
| 10 | tdca-mou-anchor | 执行型 | subagent | MOU 锚定（税收→MOU 全流程，模拟显式）| tdca-mou-anchor-output/ |
| 11 | tdca-notary | 执行型 | subagent | NCA 存证（生成/链式验证/追溯）| tdca-notary-output/ |
| 12 | tdca-ota-manager | 执行型 | subagent | OTA 版本管理（软宪法升级/回滚）| — |
| 13 | tdca-pricer | 执行型 | subagent | 配置权定价（P_C=ψ(ERI,MOU,Shapley,irrep)）| tdca-pricer-output/ |
| 14 | tdca-scenario-designer | 执行型 | subagent | 场景设计（画布/边界/负空间预检/S-Right）| tdca-scenario-designer-output/ |
| 15 | tdca-ta | 执行型 | subagent | 商学院助教（批改/答疑/进度，E-EDU 联动）| — |
| 16 | tdca-tax-officer | 执行型 | subagent | **税务官**（微交付税收全流程：计税/预缴/聚合/结算/争议/NCA）| 调用 tdca-microtax 库（183 绿）|
| 17 | tdca-trainer | 只读 | subagent | 官方培训导师（概念/术语/宪法/经济模型/场景）| 只读咨询 |
| 18 | tdca-researcher | 研究型 | subagent | 理论生成（NSFL/MEMO 预检→DRAFT 草案）| research/theories/ |
| 19 | tdca-literature | 研究型 | subagent | 文献综述（溯源链强制+SIMULATED 标注）| research/papers/ |
| 20 | tdca-critic | 研究型 | subagent | 批判审查（证伪≥1/红队≥2/最严厉反驳）| research/critique/ |
| 21 | tdca-concept-proposer | 研究型 | subagent | 概念提案（定义+冲突检测+登记模板）| research/concepts/ |
| 22 | tdca-archive | 运维型 | inline | 归档整理（会话步骤 0：扫描/去重/分类/索引）| 桌面归档文件夹 |
| 23 | tdca-cls-officer | 金融型 | inline | **金融闭环结算官**（TDCA 官方闭环结算服务，调度税运维）| 调用 tdca-cls（25 绿）+ tdca-microtax（183 绿）|

## 三、调用关系图

```
┌────────────── TDCA 官方服务层 ──────────────┐
│                                             │
│  审查链:                                    │
│  code-reviewer（代码）← compliance-auditor（制度）→ 输出整改清单        │
│                                             │
│  经济计算链:                                │
│  economist（MOU/Shapley/UPDA）              │
│    → pricer（配置权定价 P_C）               │
│    → mou-anchor（税收锚定）                 │
│    → tax-officer（微交付税收，tdca-microtax）│
│    → cls-officer（闭环结算，tdca-cls+microtax）  ← 🆕 金融链
│                                             │
│  知识服务链:                                │
│  glossarian（术语）→ kg-qa（图谱）          │
│  → trainer / ta / examiner（E-EDU 教学）    │
│                                             │
│  治理链:                                    │
│  ota-manager（软宪法）← entropy-guard（接口熵）│
│  scenario-designer（场景）→ industry-advisor（行业）│
│  notary（NCA 存证）← 全部智能体输出          │
└─────────────────────────────────────────────┘

┌────────────── 智库研究层 ───────────────────┐
│  researcher（理论 DRAFT）                   │
│    → literature（综述前置）                 │
│    → critic（红队证伪 ≥2 实例）             │
│    → glossarian（术语核对）                 │
│    → concept-proposer（NC 提案）            │
│    → 人类裁决（DCD）→ 入权威                │
└─────────────────────────────────────────────┘

┌────────────── 运维层 ───────────────────────┐
│  archive（步骤 0 归档）→ 每会话启动         │
│  cls-officer（金融闭环结算服务）→ TDCA 运维基础│
└─────────────────────────────────────────────┘
```

## 四、调用关系详情

| 调用方 | 被调用方 | 场景 |
|--------|---------|------|
| tax-officer | tdca-microtax 库 | 微交付税收（计税/预缴/结算/NCA）——A-1~A-6 全达标 |
| cls-officer | tdca-cls 引擎 | 闭环结算（GIM 环销/RTN 净额/DPI/DVP）——25 绿 |
| cls-officer | tdca-microtax（tax_calculator 等）| 同刻计税（只读复用，183 绿）|
| cls-officer | tax-officer 纪律 | 微交付域边界（∉CLS）衔接 |
| researcher | literature / critic / glossarian / concept-proposer | 研究流程六步（M0-M4 已实证：闭环结算专项）|
| 各项目 | code-reviewer / compliance-auditor | 交付前双层审查（代码+制度）|
| 各智能体 | notary | NCA 存证（生成/链式验证/追溯）|
| 各会话 | archive | 启动步骤 0（归档整理）|
| economist | pricer / mou-anchor | 配置权定价 ← MOU 锚定 ← 经济计算 |
| trainer/ta/examiner | E-EDU 教材/模拟器 | 教学/考核/学习路径 |

## 五、统一底线（全智能体强制）

1. **MOU 锚定**：不可降（ID79）；税收=进项+出项（T-039）
2. **负空间**：NSFL 边界（⊗ 禁止/⊘ 限制/⊙ 观察）；BV-3 只读心跳
3. **ID 纪律**：ID93 不引用/四符号体系（T-001）/注册表 V1.4 术语
4. **模拟态**：simulated=True 显式标注（D-011 参数）；真实锚定永不
5. **数据性质标注**：事实/推导/模拟强制区分（economist 纪律）
6. **审计**：NCA 存证链（notary 纪律）

## 六、备案与演进

- **备案**：tdca-official-kb/skills/skill-tdca-<name>.md（官方知识库，只读引用）
- **演进**：V1（16 个）→ V2.0（23 个）→ **V2.2（26 个）**——新增 archive（归档）/ 研究型 4（researcher/literature/critic/concept-proposer）/ **cls-officer（金融闭环结算官，2026-08-14 生效）** / **scenario-architect（场景架构师，2026-08-15）**——拥有场景构建全量理论知识（注册表 V2.1 T-040~T-109 + R-SCENE-1~6 + SCTPF/四机制/ECS）与场景画布设计能力（五步法/S-Right），面向场景体系架构规划；配套工具 **scenario-incubator（场景孵化器）**：场景创新并行试错（A8 第 22 条沙盒宽容，simulated=True）
- **待创设候选**：保险官（保险金兜底机制）/ 清算风控官（T-036/T-037 熔断治理）——按需 DCD 立项
