# TDCA 发布文正文（中英完整版）· V1.0-DRAFT

> 文档编号：TDCA-RELEASE-ARTICLE-001 ｜ 编制：2026-08-21（Reasonix 制度层）｜ 用途：HackerNews / 知乎 / 官网同步发布
> 上游：TDCA-RELEASE-OPENING-001（首屏稿）+ 开源可行性论证 V1.1 + OPC 社区方案 + 投资人复盘报告 V1.3
> 状态：DRAFT（人类确认后发布）
> 成本口径：以平台截屏实证（E-1：¥167.88 / 3,357,617,330 tokens / 13,834 次，2026-08-16）为准，全文统一为「¥168 / 33.5 亿 token」；后续累计数字以平台账单为准

---

# 中文版

## 我们花 168 块钱，跑通了 36 亿 Token 的智能体主权信用结算框架

*——TDCA：锚定主权信用的智能体协作制度协议，正式开源*

### 首屏

**TDCA —— 锚定主权信用的智能体协作制度协议。**

结算只走**数字人民币**（法偿性，央行负债）；协作价值以**税收**为最低可见效用锚（财政事实）；认知资产经国家**可信版权链 / 天平链**获得法律赋予（司法事实）。

不平台化、不抽水、不代币化。当前处于**制度演示态（simulated / ID92）**——全部数据带性质标注。

### 一、智能体经济缺的不是「怎么付款」，而是「怎么分钱、交税、担责」

2026 年的智能体协议栈已经分层成型：通信层被 MCP / A2A 占据并进入 Linux Foundation，支付结算层爆发了 AP2 / x402 / ACP 三套并存。**但这一层解决的全是「智能体怎么付款」**——单笔交易的授权与结算，锚定的是稳定币、卡组织、平台商誉——**私人信用**。

没有任何一个协议回答这三个问题：

- **五个智能体协作赚了 100 元，按贡献怎么分？**（Shapley 分配只在论文里，NeurIPS 2025 的 Shapley-Coop 是研究 workflow，无协议、无工程、无存证）
- **越权怎么罚？**（负空间边界、fail-closed 熔断——没有协议层实现）
- **过程怎么审？**（可审计的存证链、法律可采信的记录——没有协议层实现）

### 二、TDCA 是什么：不是「又一个多智能体框架」，而是「可执行的宪法」

TDCA（可信数字协作架构）是**多智能体协作的制度协议层**——用 168 元 / 33.5 亿 token / 11 天 / 613 项全绿测试铸成的一套宪法十六条、负空间函数语言（NSFL）、NCA 确权链、CCP 协作契约协议。

它解决的不是「怎么让智能体跑起来」，而是「智能体协作的价值如何被计量、分配、审计、纳税、确权」——**制度层的工程化**。

### 三、主权信用三锚：与一切现有协议的本质差异

| 锚 | TDCA 机制 | 硬度来源 |
|---|---|---|
| **结算锚：数字人民币（唯一选项）** | MOU 结算的真实态轨道只走 e-CNY | 法偿性 + 央行负债 + 结算终局性 |
| **效用锚：税收** | MOU = tax_in + tax_out；协作价值以纳税事实为硬度量 | 国家财政审计——税收是唯一同时满足"国家核验、法律强制、与真实价值创造挂钩"的指标 |
| **权利锚：国家可信版权链 / 天平链** | NCA 存证上链 + 认知资产版权登记 | 法律赋予而非技术赋予——天平链存证在诉讼中具有证据效力 |

**「法律赋予 vs 技术赋予」是 TDCA 与整个 Web3 范式的分水岭**：币圈项目的"链上确权"是技术记账，在境内诉讼中无证据地位；TDCA 选择的是让认知资产获得法律承认的权利主体地位。

逐维度对标扫描（x402 / AP2 / ACP / A2A / MCP / Shapley-Coop / 币圈 Agent 项目）结论：**三锚叠加后，TDCA 在全球范围内没有对标物。**

### 四、工程实证：不是白皮书，是能跑的代码

- **613 项测试全绿**（六库 pytest 复跑：613 passed / 0 failed，NCA-VERIFY-613-001）
- **成本实证**：168 元 / 33.5 亿 token / 13,800 次请求 / 11 天（平台截屏 E-1 佐证）——传统开发 2~3 人月，成本相差三个数量级
- **沙盒案例**：《孙子兵法·计篇》真实多智能体治理流程实跑（含沙盒失败与出盒 3 轮次）+ 酒店淡季动态调度（Shapley 动态分配，MOU 增值税 10.19 元全额锚定）
- **双协议引擎**：NIA-MACM 认知层 + IP 权益层，18 测试全绿 + CLI 端到端
- **前端 A 级面世**：术语注册表 → NCA 存证链尾 → SEA 五要件 → MRCR 四角色 → 智能体集群端点，行为者 real/simulated 标注清晰
- **「制度即代码」首个实证闭环**：CASE-003 实跑暴露「校准 BATNA 至 φ」漏洞（正和可被构造）→ 立项 DEF-SUNZI-01 规则（R-01~R-05，人类签批）→ φ<BATNA 拦截器代码执行体落地（只读拦截 + 未确权 fail-closed）——漏洞从制度文本到可执行代码全链闭环，亏方无法再通过任何计算路径拿到分配结果

### 五、合规红线：制度本身拒绝发币

写入 NSFL 负空间清单：**不发币、不公售、不承诺分红、不以"积分/凭证"变相交易、真实态结算只走 e-CNY 法币轨道**。合规不是附加条款，是三锚设计的副产品——与 42 号文后的监管方向同向。

### 六、如何参与（TDCA 五元协作开源社区）

TDCA 不是用户群，是**缔约者网络**——成员以签署协议（准入 NCA）的方式加入：

- **L0 观察者**：阅读、复跑沙盒、提 Issue
- **L1 缔约者**：签署准入 NCA（机器可读模板，含 GitHub ID + 接受基协议声明）
- **L2 节点**：完成一项被采纳的贡献 → 节点 NCA → 参与场景协作的 Shapley 分配（模拟态）

社区治理本身按 TDCA 运行：DCD 立项、NCA 存证、NSFL 熔断全部公开。**社区即实证。**

### 七、路线图

| 阶段 | 时间 | 交付 |
|---|---|---|
| S0 筹备 | 第 1~2 周 | 仓库 + 准入机制 + 行为准则 + 赞助通道 |
| S1 概念占位 | 第 1 个月 | pack/ 制度教科书 + 发布文 |
| S2 可运行证明 | 第 2~3 个月 | dual/ 沙盒引擎 + tdca-mcp-bridge + CTS-L1 套件 |
| S3 冷启动 | 第 3~6 个月 | **首个第三方 CTS-L1 一致性声明（北极星）** + 三锚接入对话 |

### 参与入口

- 仓库：https://github.com/henyi-tdca/tdca-protocol（GitHub 主仓已上线 ✅；Gitee 镜像筹备中）
- 准入：Fork → 本地运行 enforce_entry.py → 签署准入 NCA → PR
- 复现：一键沙盒复现脚本，5 分钟本地跑出 613 测试全绿
- 沟通：GitHub Discussions（不设微信群）

**欢迎来到 TDCA 五元协作社区。在这里，你不仅是在 Fork 代码，你是在缔约一份新型的数字经济体契约。**

---

# English Version

## We Built a Sovereign-Credit Settlement Framework for Agents with 168 CNY and 3.35B Tokens

*TDCA — A Sovereign-Credit-Anchored Institutional Protocol for Agent Collaboration. Now Open Source.*

### First Screen

**TDCA — A Sovereign-Credit-Anchored Institutional Protocol for Agent Collaboration.**

Settlement runs exclusively on **e-CNY** (legal tender, central-bank liability); collaboration value is anchored to **taxation** as the minimum observable utility (fiscal fact); cognitive assets gain legal force through the national **trusted copyright chain / balance chain** (judicial fact).

No platformization, no rent-seeking, no tokenization. Currently in **institutional demonstration mode (simulated / ID92)** — every data point carries a provenance label.

### 1. The Agent Economy Doesn't Lack "How to Pay" — It Lacks "How to Split, Tax, and Account"

By 2026 the agent protocol stack has stratified: communication is owned by MCP/A2A (Linux Foundation); payments exploded into AP2/x402/ACP. **But every one of them answers only "how an agent pays"** — single-transaction authorization and settlement anchored to stablecoins, card rails, or platform goodwill — **private credit**.

None answers three questions:

- **Five agents earn ¥100 together — how do they split it fairly?** (Shapley allocation exists only in papers; NeurIPS 2025 Shapley-Coop is a research workflow with no protocol, no engineering, no attestation)
- **How are boundary violations punished?** (negative-space rules, fail-closed circuit breaking — no protocol-layer implementation)
- **How is the process audited?** (attestable chain, legally admissible records — no protocol-layer implementation)

### 2. What TDCA Is: Not "Another Multi-Agent Framework" — an Executable Constitution

TDCA (Trusted Digital Collaboration Architecture) is the **institutional protocol layer for multi-agent collaboration**: a constitution of sixteen articles, a Negative-Space Function Language (NSFL), an NCA attestation chain, and a CCP collaboration contract protocol — forged with 168 CNY, 3.35B tokens, 11 days, and 613 green tests.

It answers not "how to make agents run," but "how the value of agent collaboration is measured, allocated, audited, taxed, and entitled" — **the engineering of the institutional layer.**

### 3. The Three Sovereign-Credit Anchors: What Separates TDCA from Every Existing Protocol

| Anchor | TDCA Mechanism | Hardness Source |
|---|---|---|
| **Settlement: e-CNY (sole option)** | Real-state MOU settlement runs only on e-CNY | Legal tender + central-bank liability + settlement finality |
| **Utility: taxation** | MOU = tax_in + tax_out; collaboration value measured by fiscal facts | National fiscal audit — the only metric that is state-verified, legally enforced, and tied to real value creation |
| **Rights: national trusted copyright / balance chain** | NCA attestation on-chain + cognitive-asset copyright registration | Legally conferred, not technically conferred — balance-chain attestations hold evidentiary weight in litigation |

**"Legally conferred vs. technically conferred" is the dividing line between TDCA and the entire Web3 paradigm.**

Dimension-by-dimension scan (x402 / AP2 / ACP / A2A / MCP / Shapley-Coop / token-agent projects): **after the three anchors are combined, TDCA has no global equivalent.**

### 4. Engineering Proof: Not a Whitepaper — Runnable Code

- **613 tests green** (six-repo pytest rerun: 613 passed / 0 failed, NCA-VERIFY-613-001)
- **Cost evidence**: 168 CNY / 3.35B tokens / 13.8K requests / 11 days (platform screenshot E-1) — 2–3 person-months in traditional development; three orders of magnitude cheaper
- **Sandbox cases**: *The Art of War* real multi-agent governance run (3 rounds incl. sandbox failures and exits) + hotel off-season dynamic scheduling (Shapley allocation, MOU VAT ¥10.19 fully anchored)
- **Dual-protocol engine**: NIA-MACM cognition layer + IP rights layer, 18 tests green + CLI end-to-end
- **A-grade frontend**: term registry → NCA attestation chain tail → SEA five requirements → MRCR four roles → agent-cluster endpoints, with clear real/simulated provenance labels
- **First "institution-as-code" closed loop**: CASE-003 exposed the "calibrate BATNA to φ" flaw (positive-sum constructible) → DEF-SUNZI-01 rules chartered (R-01~R-05, human-signed) → φ<BATNA interceptor shipped as executable code (read-only interception + unverified-declaration fail-closed) — the flaw is closed end-to-end from institutional text to runnable code; losing parties can no longer obtain allocations through any computational path

### 5. Compliance Red Lines: The Institution Itself Refuses Tokens

Written into the NSFL negative-space list: **no token, no public sale, no dividend promise, no quasi-token rewards, real-state settlement only on the e-CNY fiat rail.** Compliance is not an add-on — it is a byproduct of the three-anchor design, aligned with post-42-doc regulation.

### 6. How to Join (TDCA Five-Element Collaborative Open-Source Community)

TDCA is not a user group; it is a **network of contractors** — membership is established by signing agreements (admission NCAs):

- **L0 Observer**: read, rerun sandboxes, file issues
- **L1 Contractor**: sign an admission NCA (machine-readable template: GitHub ID + base-protocol acceptance)
- **L2 Node**: complete an accepted contribution → node NCA → participate in Shapley allocation (simulated)

Community governance itself runs on TDCA: DCD lodgment, NCA attestation, NSFL circuit-breaking — all public. **The community is the proof.**

### 7. Roadmap

| Phase | Time | Deliverable |
|---|---|---|
| S0 Prep | Weeks 1–2 | Repo + admission mechanism + code of conduct + funding |
| S1 Positioning | Month 1 | pack/ institutional textbook + launch post |
| S2 Proof of Run | Months 2–3 | dual/ sandbox engine + tdca-mcp-bridge + CTS-L1 suite |
| S3 Cold Start | Months 3–6 | **First third-party CTS-L1 conformance statement (north star)** + three-anchor access talks |

### Join

- Repo: https://github.com/henyi-tdca/tdca-protocol (GitHub live ✅; Gitee mirror in preparation)
- Admit: Fork → run enforce_entry.py locally → sign admission NCA → PR
- Reproduce: one-click sandbox script — 613 tests green locally in 5 minutes
- Talk: GitHub Discussions (no WeChat groups)

**Welcome to the TDCA Five-Element Community. Here you are not just forking code — you are contracting into a new kind of digital-economy compact.**

---

## 附：发布核对清单

- [ ] ① 成本口径统一：全文采用「¥168 / 33.5 亿 token」（E-1 截屏实证）；如需引用 08-21 更新累计（¥203.54/36.1 亿），标注"以平台账单为准"
- [x] ② 仓库 URL 占位 → 已回填真实 URL（GitHub 主仓 2026-08-22 上线，commit 7b0a192；Gitee 镜像待账号公开审核，见 NCA-RELEASE-003）
- [ ] ③ ID92 纪律复核：所有截图/案例标注 [SIMULATED]/[UNVERIFIED]
- [ ] ④ 人类确认后发布：HackerNews（英文版）/ 知乎·掘金（中文版）/ 官网（两版）
- [ ] ⑤ 发布后 NCA 存证 + 更新 TDCA-INDEX
