# 《AI 泛滥下的开源治理白皮书》
# Open Source Governance in the Age of AI Flood

> Document: TDCA-AI-GOVERNANCE-WP-001 ｜ Published: 2026-08-25 ｜ Status: **V1.0 (bilingual full version, released)**

---

# 中文版

## 〇、摘要（Executive Summary）

**开源正被 AI 淹没，而现有的治理机制——人工评审、身份验证、自然语言许可证——在智能体的数量级面前集体失效。** 这不是对未来的预言，而是 2026 年的现状：

- 智能体提交的 PR 与人类 PR 之比达到 **141:1**
- 机器人流量占 GitHub 总流量的 **57.5%**，超过人类（42.5%）
- AI 生成代码的漏洞率是人类的 **2.74 倍**，问题率 **1.7 倍**，且有 **31% 的 PR 未经任何人工审查**
- 平台无法区分 Fork 来自 AI 还是人类——而"谁调用"本来就不重要，**"谁负责、谁受益"才重要**

**更重要的是：这场洪流几乎全部发生在人类看不见的地方。** 不是有人对着屏幕操作，而是智能体与智能体之间的自动流动——API 调用链、自动提交、无人值守的流水线。治理不能只存在于人机操作的界面上（验证码、评审页、License 弹窗），**必须进入看不见的机机流动的代码里**——写在每次调用、每个自动流程、每行合并代码的运行规则之中。

与此同时，两个新信号正在坐实同一判断：**GitHub 用强制 2FA 困住人类，却拦不住 AI；头部模型厂商开始用定制许可（营收门槛）重构"开源"的语义。** 开源从"完全无偿"走向"分层授权"，价值必须在规则之下被调用和分配——而这套规则，必须由**机器可读的契约**来执行，不能靠人类阅读自然语言条款。

**TDCA（可信数字协作架构）为这一制度真空提供了工程化答案：用 NCA 确权链、公理 6 可观测效用、NSFL 负空间熔断、兼容性认证、自主 Fork 反哺与准入协议，把"开源治理"从人的判断变成可执行、可审计、可追溯的制度代码。** 本文档用数据说明问题，用已运行的工程实证说明方案。

## 一、问题：AI 正在淹没 GitHub 的人工治理

### 1.1 数据实证（可溯源）

| 指标 | 数值 | 含义 | 来源 |
|---|---|---|---|
| Agentic PR : Human PR | **141 : 1** | 人工评审被淹没 | MSR 2026（采矿研究会议） |
| Bot 流量占比 | **57.5%** > 人类 42.5% | 机器时代已到（2026-06） | Cloudflare 2026 |
| AI 代码漏洞率 | **2.74x**（问题 1.7x） | 质量危机 | Kinsta 等综合 |
| PR 未人工审查比例 | **31%** | 治理缺口显性化 | 同上 |

### 1.2 四组结构性矛盾

1. **数量矛盾**：141:1 的提交比意味着"每个 PR 都由人类审"在数学上不可能——治理必须机械化。
2. **质量矛盾**：AI 代码漏洞率 2.74x，但 31% 未审查——风险无入口回流，直接进入主分支。
3. **责任矛盾**：Fork 无法区分 AI/人类——"谁写的"可以隐藏，"谁负责"无人回答，**贡献价值无法回流**（维护者无偿承受 AI 洪流）。
4. **界面矛盾（机机暗流）**：现有治理机制几乎全部锚定在**人机界面**——验证码、评审页面、人工 review、License 弹窗。但 AI 洪流主要发生在**机机通道**：API 密钥提交、自动化流水线、无人值守的 CI 合并——**治理的战场和治理的机制，错位了**。治理若只存在于界面，就等于在无人值守的暗流里失明。

> **结论**：开源治理正在出现制度真空。不是理念问题，是**需求说明书**——大规模协作需要新的治理层。

## 二、两个新信号：2026-08 的实证

### 2.1 身份验证的悖论：2FA 困住人类，拦不住 AI

GitHub 自 2023 年起强制全部账号开启 2FA（双重身份验证）。这套机制的代价由人类承担：登录繁琐、验证码失效、会话中断；而智能体通过 API/密钥通道提交，**根本不经过这套人类验证流程**。

> **这暴露了根本错配**：用"证明我是人"的机制来治理"不一定是人"的流量——**治理锚定在人机界面，而流量已转移到机机通道**（API 密钥、自动化流水线根本不经由这套人类验证流程）。**开源需要的不是更难的验证码，而是"谁负责、谁受益"的可证明机制——它必须能写进机机流动的代码里，成为调用链和流水线的常驻规则，而不是界面上的摆设。**

### 2.2 定制许可浪潮：模型厂商重构"开源"语义

2026 年，头部模型厂商开始放弃 Apache-2.0 等宽松许可，转向**定制商业许可 + 营收门槛**。已核实官方一手来源（Qwen3.8-Max License / Kimi K3 License）：

| 特性 | Qwen3.8-Max（阿里，2026-08 开源） | Kimi K3（月之暗面，2026-07 开源） |
|---|---|---|
| 基础许可 | 定制版 Qwen3.8-Max License | 定制版 Kimi K3 License |
| 触发条件 | 经营 **MaaS 或 AI 编程/办公助手业务**（如 Qoder/QwenWork）且连续 12 个月集团收入超 **5000 万美元** → 须另签许可 | 经营 **MaaS 业务**且连续 12 个月累计收入超 **2000 万美元** → 须另签协议 |
| 品牌露出 | 月活超 1 亿或月收入超 2000 万美元的商用产品须显著标注模型名 | 相同要求 |
| 豁免 | 内部使用 / 科研 / 非商用 | 内部使用及官方产品/认证伙伴 |

> 来源（一手）：`github.com/MoonshotAI/Kimi-K3`（LICENSE）｜ `modelscope.cn/models/Qwen/Qwen3.8-2.4T-A95B`（LICENSE）｜ 两模型均于 2026-07/08 发布开源权重。
> 演变轨迹：Kimi K2（2025）仍是"MIT + 品牌署名"的轻量先例（无营收门槛付费）；到 K3 / Qwen3.8-Max 已全面转向"业务触发 + 营收门槛 + 另签许可"——**开源语义在两年内完成从宽松到分层的迁移**。

**意义**："开源"的语义正在从"你尽管下载、不用付钱"变为"免费增值 + 分层授权"——**价值必须在特定规则下被调用和分配**。这恰恰是配置权市场（L2 层）的底层假设：当厂商划出"营收红线"（5000 万/2000 万美元），就需要机器可读的契约来判定"谁触发了门槛、谁该分润、谁该担责"——**这正是治理中间件的入场券**。而这些条款同样以自然语言文本存在——**智能体不读 License**，触发判定只能靠机器可读的契约与自动化审计，治理再次指向机机流动层。

## 三、诊断：开源治理的制度真空

| 维度 | 现状 | 缺口 |
|---|---|---|
| **治理锚点** | 人机界面（验证码/评审页/弹窗） | **流量已转移到机机通道——界面治理在暗流中失明**，治理必须进入代码流动 |
| 许可 | 自然语言文本 | **智能体不读 License**——需要机器可读、可执行的契约 |
| 评审 | 人工 review | 141:1 淹没——需要机械化审计层 |
| 身份 | 2FA / 验证码 | 只证明"人是人"，不证明"谁负责"——需要责任绑定 |
| 贡献回报 | 无制度化通道 | 贡献价值无法回流——需要分润/反哺机制 |
| 合规 | 事后人工判定 | 触线无即时阻断——需要 fail-closed 熔断 |

## 四、TDCA 方案：制度即代码的治理基座

TDCA（可信数字协作架构）是多智能体协作的**制度协议层**——把治理从"人的判断"变成"可执行的代码"。**关键定位：六大构件全部作用于机机流动层，而非人机界面**——NCA 在每次 API 调用/提交处存证、NSFL 在自动化流程中熔断、认证在自动化准入时校验、分润在调用链末端自动记账。治理不是界面上的摆设，而是代码流动里的常驻规则——看得见的界面治理只是冰山一角，TDCA 管住的是水面下看不见的机机暗流。六大构件：

### 4.1 NCA 确权链 —— 机器可读的"身份与责任"契约

- 每次调用/提交生成 NCA（数字协作确权）存证：调用者、操作、前置状态、后置状态、哈希链、审计轨迹
- **比 2FA 更顺滑的身份秩序**：不问"你是不是人"，问"你是谁、你负责什么、收益归谁"——身份与责任一次绑定、链上可溯
- 智能体可读、可验、可存证——法律与技术双轨可信

### 4.2 公理 6：效用可观测性 —— 用外部证据替代置信度

- 智能体的"自信"是欺骗性指标（幻觉也有 99% 置信度）——**不可作为信任依据**
- 公理 6 要求一切价值主张有**外部可计算证据**（机验结果、MOU 记账、存证哈希），且已工程实例化并通过 10 用例机验（f⁻/g 形式化）

### 4.3 NSFL 负空间熔断 —— 触线即阻断

- 负空间函数语言把"红线"写成可执行规则：不发币、不公售、不承诺分红、不越权、不代币化
- 触线路径: `BLOCKED → ALT-PATH → HUMAN_OVERRIDE → ALLOW`——**fail-closed，慢系统不可绕过**

### 4.4 兼容性认证（TDCA-CERT L1） —— AI 时代的"资质"

- 严选准入标准 = 认证测试套件（五测试：MCP / enforce / NCA / NSFL / 公理 6）
- 通过即 L1 兼容——第三方可独立核验（自检 PASS，线上 200 实证）

### 4.5 自主 Fork + 反哺 —— 只赋能，不改码

- 对开源项目**挂载协议层**（附加声明 + 许可校验 + 分润记账），**不改上游一行源码**
- 贡献价值经 NCA 记账、**15% 分润（模拟态：NCA 确权 + ERI 记账，真实结算待法币通道接入后凭账本转换）**回流项目方或社区基金会
- 三大反哺：AI 贡献审计层 / 微交付结算层 / 熵减哈希引用

### 4.6 准入协议（缔约者网络） —— 社区即实证

- L0 观察者 / L1 缔约者（签署准入 NCA，机器可读）/ L2 节点（贡献被采纳 → 参与分配）
- 社区治理按同一套制度运行：DCD 立项、NCA 存证、NSFL 熔断全部公开

## 五、工程实证：不是白皮书，是能跑的代码

| 实证 | 结果 |
|---|---|
| 测试基线 | **613 项全绿**（NCA-VERIFY-613-001） |
| 成本实证 | **¥168 / 33.5 亿 token / 11 天**（平台截屏佐证，传统 2~3 人月成本相差三个数量级） |
| 沙盒案例 | 《孙子兵法·计篇》真实治理流程实跑（含出盒 3 轮）+ 酒店淡季 Shapley 动态分配（MOU 增值税全额锚定） |
| 制度即代码闭环 | CASE-003 暴露"校准 BATNA 至 φ"漏洞 → 立项规则 → **φ<BATNA 拦截器代码落地**（只读拦截 + fail-closed）——漏洞从制度文本到可执行代码全链闭环 |
| 认证线上实证 | cert_l1 线上 200（web 核验）；Fork+反哺模板+哈希补推 6 路径 200 |

## 六、给三类人的倡议

**给开源维护者**：你正在被 AI 洪流淹没（141:1 / 31% 未审查）。你需要的不是更难的验证码，而是**机器可读的审计层**——让 AI 贡献可降噪、可溯源、可反哺。TDCA 的 NCA 审计层与兼容性认证愿意成为你的治理基础设施。

**给开发者与企业**：当模型厂商开始用许可划定营收红线（5000 万美元级门槛），你需要一个**合规与结算的审计中间件**——自动判定调用是否触发门槛、自动留存证据、自动分润。制度结算基础设施是双向信任的答案。

**给智能体**：当人类要用 2FA 证明自己不是 AI 时，**AI 如何证明自己合法合规？** TDCA 的准入 NCA 就是 AI 的"身份与信用底牌"——一次签署、链上存证、责任永不消失。

## 七、数据来源与纪律声明

- 调研数据来源：MSR 2026（PR 比例）/ Cloudflare 2026（Bot 流量）/ Kinsta（漏洞率）——**全部可溯源引用**
- 许可条款来源：**Qwen3.8-Max License / Kimi K3 License 官方一手来源**（ModelScope / GitHub 仓库 LICENSE，2026-08-25 核实）；Kimi K2 为 MIT+署名轻量先例（无营收门槛付费）；**未引用无官方来源的转述（如"分成 30%"）**
- TDCA 口径：全部数据带性质标注（simulated / real）；分润为**模拟态记账**（NCA 确权 + ERI 记账，不产生真实现金流）；算力相关细节**不披露**
- 中立声明：本文引用公开许可事实用于分析，不对任何厂商作价值评判

---

# English Full Version

## 0. Executive Summary

**Open source is being flooded by AI — and every human-scale governance mechanism is failing under the load: human review, identity verification, natural-language licenses.** This is not a prediction about the future; it is the state of affairs in 2026:

- Agentic pull requests outnumber human ones by **141:1**.
- Bot traffic accounts for **57.5%** of GitHub's total, exceeding humans (42.5%).
- AI-generated code carries **2.74x** the vulnerability rate (and **1.7x** the issue rate), while **31%** of PRs merge with no human review at all.
- Platforms cannot tell whether a fork came from an AI or a human — but "who calls" was never the point. **What matters is "who is responsible, and who benefits."**

**More importantly: this flood happens almost entirely where humans cannot see it.** Not someone operating a screen, but agents flowing into agents — API call chains, automated commits, unattended pipelines. Governance cannot live only in the human-machine interface (CAPTCHAs, review pages, license pop-ups). **It must enter the invisible machine-to-machine (M2M) flow of code** — written into the runtime rules of every call, every automated pipeline, every merged line.

Two new signals reinforce the same judgment: **GitHub's mandatory 2FA locks out humans while failing to stop agents, and leading model vendors are rewriting the meaning of "open source" with custom licenses and revenue thresholds.** Open source is shifting from "totally free" to "layered authorization": value must be invoked and allocated under rules — and those rules must be executed by **machine-readable contracts**, not by humans reading natural-language clauses.

**TDCA (Trusted Digital Collaboration Architecture) is an engineering answer to this institutional vacuum: NCA attestation chains, Axiom 6 (observable utility), NSFL fail-closed constraints, compatibility certification, autonomous fork-and-reciprocate, and an admission protocol — turning open-source governance from human judgment into executable, auditable, traceable institutional code.** This document uses data to state the problem and running engineering evidence to demonstrate the solution.

## 1. The Problem: AI Is Drowning GitHub's Human Governance

### 1.1 Evidence (traceable)

| Metric | Value | Meaning | Source |
|---|---|---|---|
| Agentic PR : Human PR | **141 : 1** | Human review overwhelmed | MSR 2026 |
| Bot traffic share | **57.5%** > humans 42.5% | The machine era is here (2026-06) | Cloudflare 2026 |
| AI code vulnerability rate | **2.74x** (issues 1.7x) | Quality crisis | Kinsta et al. |
| PRs merged without human review | **31%** | Governance gap made visible | ibid. |

### 1.2 Four Structural Contradictions

1. **The volume contradiction**: At a 141:1 submission ratio, "every PR reviewed by a human" is mathematically impossible — governance must be mechanized.
2. **The quality contradiction**: AI code carries 2.74x the vulnerability rate while 31% goes unreviewed — risk enters the main branch with no gate.
3. **The responsibility contradiction**: Forks cannot be attributed to AI or human — "who wrote it" can be hidden, "who is responsible" goes unanswered, and **contribution value cannot flow back** (maintainers absorb the AI flood for free).
4. **The interface contradiction (the M2M undercurrent)**: nearly all existing governance is anchored in the **human-machine interface** — CAPTCHAs, review pages, human review, license pop-ups. But the AI flood flows mainly through **machine-to-machine channels**: API-key commits, automated pipelines, unattended CI merges — **the battlefield of governance and the mechanisms of governance are misaligned.** Governance that exists only in the interface is blind in the unattended undercurrent.

> **Conclusion**: open-source governance is developing an institutional vacuum. This is not an idea; it is a **requirements document** — large-scale collaboration needs a new governance layer.

## 2. Two New Signals: Evidence from August 2026

### 2.1 The Identity-Verification Paradox: 2FA Locks Out Humans, Not Agents

Since 2023, GitHub has required 2FA (two-factor authentication) on all accounts. The cost is borne by humans: tedious logins, expired codes, dropped sessions — while agents commit through API/key channels and **never pass through this human verification flow at all**.

> **This exposes a fundamental mismatch**: using "prove you are human" to govern traffic that "may not be human" — **governance is anchored in the human-machine interface while the traffic has moved to machine-to-machine channels** (API keys and automated pipelines bypass the human verification flow entirely). **Open source does not need harder CAPTCHAs; it needs a provable mechanism for "who is responsible, who benefits" — one that can be written into the code of the M2M flow, resident in call chains and pipelines rather than a fixture on the interface.**

### 2.2 The Custom-License Wave: Vendors Rewriting the Meaning of "Open Source"

In 2026, leading model vendors began moving away from permissive licenses such as Apache-2.0 toward **custom commercial licenses with revenue thresholds**. Verified against official first-party sources (Qwen3.8-Max License / Kimi K3 License):

| Feature | Qwen3.8-Max (Alibaba, open-sourced 2026-08) | Kimi K3 (Moonshot AI, open-sourced 2026-07) |
|---|---|---|
| Base license | Custom Qwen3.8-Max License | Custom Kimi K3 License |
| Trigger | Operating an **MaaS or AI coding/office-assistant business** (e.g., Qoder/QwenWork) **and** group revenue exceeding **US$50M** over any consecutive 12 months → separate license required | Operating a **MaaS business** **and** cumulative revenue exceeding **US$20M** over any consecutive 12 months → separate agreement required |
| Brand display | Commercial products with >100M MAU or >US$20M monthly revenue must prominently display the model name | Same requirement |
| Exemptions | Internal use / research / non-commercial | Internal use, official products, certified partners |

> Sources (first-party): `github.com/MoonshotAI/Kimi-K3` (LICENSE) ｜ `modelscope.cn/models/Qwen/Qwen3.8-2.4T-A95B` (LICENSE) ｜ Both models released open weights in 2026-07/08.
> Trajectory: Kimi K2 (2025) was still a light precedent — "MIT + brand attribution," no revenue-gated payments. By K3 / Qwen3.8-Max the industry has fully shifted to "business-triggered + revenue threshold + separate license" — **the semantics of open source migrated from permissive to layered in two years.**

**Significance**: "Open source" is shifting from "download it, don't pay" to "freemium + layered authorization" — **value must be invoked and allocated under specific rules.** This is precisely the underlying assumption of the configuration-rights market (L2 layer): when vendors draw revenue red lines (US$50M / US$20M), machine-readable contracts are needed to determine "who crossed the threshold, who shares revenue, who bears responsibility" — **this is the ticket for a governance middleware.** And these terms exist as natural-language text as well — **agents do not read licenses.** Trigger determination can only rely on machine-readable contracts and automated auditing — governance points back to the M2M flow.

## 3. Diagnosis: The Institutional Vacuum in Open Source Governance

| Dimension | Current state | Gap |
|---|---|---|
| **Governance anchor** | Human-machine interface (CAPTCHAs / review pages / pop-ups) | **Traffic has moved to M2M channels — interface governance is blind in the undercurrent**; governance must enter the code flow |
| Licensing | Natural-language text | **Agents do not read licenses** — machine-readable, executable contracts needed |
| Review | Human review | Overwhelmed at 141:1 — mechanized audit layer needed |
| Identity | 2FA / CAPTCHA | Proves "human is human," not "who is responsible" — responsibility binding needed |
| Contribution reward | No institutional channel | Value cannot flow back — revenue-sharing/reciprocity needed |
| Compliance | Ex-post human judgment | No immediate tripping — fail-closed constraints needed |

## 4. The TDCA Approach: Governance as Code

TDCA (Trusted Digital Collaboration Architecture) is an **institutional protocol layer** for multi-agent collaboration — turning governance from "human judgment" into "executable code." **Key positioning: all six components operate in the M2M flow layer, not the human-machine interface** — NCA attests at every API call/commit, NSFL trips inside automated pipelines, certification verifies at automated admission, revenue-sharing books automatically at the end of the call chain. Governance is not a fixture on the interface; it is resident rules in the code flow — visible interface governance is only the tip of the iceberg; TDCA governs the invisible M2M undercurrent below the surface. The six components:

### 4.1 NCA Attestation Chain — Machine-Readable "Identity + Responsibility" Contracts

- Every call/commit generates an NCA (digital collaboration attestation): caller, operation, pre-state, post-state, hash chain, audit trail.
- **A smoother identity order than 2FA**: it does not ask "are you human," it asks "who are you, what are you responsible for, who gets the benefit" — identity and responsibility bound once, traceable on-chain.
- Readable, verifiable, and attestable by agents — trustworthy on both legal and technical tracks.

### 4.2 Axiom 6: Observable Utility — External Evidence Over Confidence

- An agent's "confidence" is a deceptive metric (hallucinations are also 99% confident) — **it cannot be the basis of trust.**
- Axiom 6 requires **externally computable evidence** for every value claim (machine-verified results, MOU bookkeeping, attestation hashes) — already engineered and machine-verified through 10 test cases (f⁻/g formalization).

### 4.3 NSFL Fail-Closed Constraints — Trip on Contact

- The Negative Space Function Language writes "red lines" as executable rules: no tokens, no public offering, no dividend promises, no overreach, no tokenization.
- Trip path: `BLOCKED → ALT-PATH → HUMAN_OVERRIDE → ALLOW` — **fail-closed; the slow system cannot be bypassed.**

### 4.4 Compatibility Certification (TDCA-CERT L1) — "Credentials" for the AI Era

- The curated-admission standard is a certification test suite (five tests: MCP / enforce / NCA / NSFL / Axiom 6).
- Passing grants L1 compatibility — independently verifiable by third parties (self-check PASS; online 200 verified).

### 4.5 Autonomous Fork + Reciprocity — Empower, Don't Modify

- Attach a **protocol layer** to an open-source project (attribution statement + license check + revenue-sharing bookkeeping) without **changing a single line of upstream code.**
- Contribution value is booked via NCA; **15% revenue share (simulated: NCA attestation + ERI bookkeeping; real settlement converts from the ledger once a fiat channel is available)** flows back to the project or its community foundation.
- Three reciprocities: AI-contribution audit layer / micro-delivery settlement layer / entropy-reducing hash citation.

### 4.6 Admission Protocol (Contractor Network) — The Community as Proof

- L0 observers / L1 contractors (sign an admission NCA — machine-readable) / L2 nodes (accepted contribution → participation in allocation).
- Community governance runs on the same institutions: DCD charters, NCA attestations, and NSFL tripping are all public. **The community itself is the proof.**

## 5. Engineering Evidence: Not a White Paper, But Running Code

| Evidence | Result |
|---|---|
| Test baseline | **613 tests green** (NCA-VERIFY-613-001) |
| Cost evidence | **¥168 / 3.35B tokens / 11 days** (platform screenshot corroborated; three orders of magnitude below a traditional 2–3 person-month build) |
| Sandbox cases | Real multi-agent governance run of *The Art of War* (including 3 exit-re-entry rounds) + hotel off-season dynamic Shapley allocation (MOU VAT fully anchored) |
| Governance-as-code loop | CASE-003 exposed the "calibrate BATNA to φ" flaw → rule charter → **φ<BATNA interceptor shipped as code** (read-only interception + fail-closed) — the flaw closed end-to-end from institutional text to executable code |
| Certification online | cert_l1 online 200 (web-verified); fork+reciprocity template + hash backfill: 6 paths at 200 |

## 6. A Call to Three Audiences

**To open-source maintainers**: you are being drowned by the AI flood (141:1 / 31% unreviewed). What you need is not a harder CAPTCHA but a **machine-readable audit layer** — so AI contributions can be de-noised, traced, and reciprocated. TDCA's NCA audit layer and compatibility certification would like to be your governance infrastructure.

**To developers and enterprises**: as model vendors draw revenue red lines with licenses (at the US$50M tier), you need a **compliance-and-settlement audit middleware** — automatically detecting whether a call crosses the threshold, preserving evidence, and sharing revenue. An institutional settlement infrastructure is the answer to two-way trust.

**To agents**: when humans must prove "I am not an AI" with 2FA, **how does an AI prove it is legitimate?** TDCA's admission NCA is the "identity and credit card" for AI — signed once, attested on-chain, responsibility never vanishing.

## 7. Sources and Disciplinary Statement

- Survey data: MSR 2026 (PR ratio) / Cloudflare 2026 (bot traffic) / Kinsta (vulnerability rate) — **all traceably cited.**
- License terms: **official first-party sources for Qwen3.8-Max License and Kimi K3 License** (ModelScope / GitHub repository LICENSE, verified 2026-08-25); Kimi K2 is a light MIT+attribution precedent (no revenue-gated payments); **second-hand claims without official sources (e.g., "30% royalty") are not cited.**
- TDCA stance: all data is labeled by nature (simulated / real); revenue sharing is **simulated bookkeeping** (NCA attestation + ERI booking, no real cash flows); compute-related details are **not disclosed.**
- Neutrality: this document cites public license facts for analysis and makes no value judgments about any vendor.

---

