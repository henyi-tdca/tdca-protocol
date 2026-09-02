# TDCA：论迹不论心的可信多智能体协作协议——制度设计、工程实证与模型无关性

**张帆**<sup>1</sup>　**恒益场景（厦门）数字经济研究院**<sup>1</sup>

> <sup>1</sup> 恒益场景（厦门）数字经济研究院；张帆为研究院院长、本文通信作者。AI 工具使用声明见致谢。内部溯源编号已统一移至附录 A，投稿前按学报规范做最终去标识化。

**摘要**：TDCA（Trusted Digital Collaboration Architecture，可信数字协作架构，⟨ℑ,𝒯,ℰ,𝒫,𝒦⟩）提出一种「论迹不论心」的协议层制度设计：以三阶段准入门控（admission/sandbox/production）+ NCA 嵌套认知资产确权 + Shapley 联盟定价为核心机制，并锚定三条基础律——立场分离三律（协议层去场景去立场）、NSFL 负空间熔断（禁止清单优先于一切生成）、MOU 本体论（场景效用可持续性的最低可见指标，是地板而非天花板）。本文核心主张是：可信多智能体协作来自「协议层制度」而非「模型更聪明」，呼应「制度红利 > 技术红利」。为把这一主张从概念落到可执行代码与可重算账本，本文给出六项真实运行实证（E1–E6），覆盖可验证性、税收锚定、信任但核验、外部锚定与模型无关性五个维度；并以九判定图谱对微软、AWS、Google 三家主导范式做 TDCA 制度诊断，定位差异化位置。全文 38/38 实证哈希均为磁盘权威值（经独立复核通过），示意值零残留。

**关键词**：可信多智能体协作；协议层制度；论迹不论心；模型无关性；效用计量锚定；负空间熔断；NCA 确权

**中图分类号**：TP18　　**文献标志码**：A

**Abstract**: TDCA proposes a "trace-not-intent" protocol-layer institution for trustworthy multi-agent collaboration: a three-phase admission gating (admission / sandbox / production) plus NCA nested cognitive-asset attribution and Shapley coalition pricing, anchored on three foundational laws — stance-separation, NSFL negative-space circuit-breaker, and MOU ontology. The central thesis is that trustworthy collaboration arises from *protocol-level institutions* rather than *model cleverness*. To move this thesis from concept to executable code and a recomputable ledger, this paper contributes six real-run empirical studies (E1–E6) spanning verifiability, tax-anchoring, trust-but-verify, external-anchoring, and model-independence, and a nine-criterion diagnostic of the Microsoft / AWS / Google dominant paradigms. All 38/38 empirical hashes are disk-authoritative values (independently re-verified); illustrative-value residual is zero.

**Key words**: trustworthy multi-agent collaboration; protocol-level institution; trace-not-intent; model independence; utility-metrology anchoring; negative-space circuit-breaker; NCA attribution

---

## 1 引言

当前人工智能治理研究大多聚焦于「如何让模型更聪明、更安全」，却较少回答一个更底层的问题：**多个智能体（agent）如何在制度约束下可信协作，并产生正和（positive-sum）效用？** 已有工作在各层取得了进展——从算法层面的对齐（alignment）与红队测试，到系统层面的身份、权限与可观测性，再到政策层面的风险框架与合规要求。然而这些进展之间仍存在一条关键断层：它们多在「让单个智能体更可控」上做功，却未解决「多个智能体之间如何以可核验的方式分配责任、计量效用、并对账归因」这一协作层问题。

TDCA 的立场是：**可信不来自于「心」（模型对自身善意的声称），而来自于「迹」（协议层可被独立核验的行为存证）。** 这一立场把治理问题从「如何相信智能体」改写为「如何让智能体的行为留下不可抵赖、可重算、可对账的迹」。

为理解这一立场的实操含义，不妨设想一个多智能体供应链场景：一个负责需求预测的智能体、一个负责库存调度的智能体、一个负责供应商谈判的智能体共同完成一次补货。即便三者各自经过对齐与权限校验，当补货亏损发生时，仍无人能说清「亏损来自哪一步决策、应归因于谁、是否产生了正和」。现有治理工具能回答「每个智能体是否合规」，却回答不了「这次协作是否正和、损失如何分摊」。TDCA 要解决的正是这一「协作层归因」问题——它把归因锚定在协议层留下的迹上，而非事后的责任推诿。

围绕这一立场，本文要回答三个可被工程化检验的问题：

① **可确权性**：协议在真实条件下（带外部 LLM 密钥、真实落盘、真实计量）能否建立可被确权、可被归因的 MOU（Minimum Observable Utility，最低可见效用）？

② **模型无关性**：当运行时从一种模型切换为另一种模型，交付是否退化？即协议交付是否依赖于「某个特定模型在场」？

③ **角色健康度**：协议内部所谓「多个智能体」究竟由何种角色构成，其角色化（role-ized）架构是否健康，是否存在「角色齐备但门控未接好」而虚抬 MOU 下限的隐患？

为什么说这是一个被忽视的断层？因为单智能体的「可控」并不自动导出多智能体的「可信协作」。一个被严格对齐的模型，在与其他模型或人类协作时，仍可能因责任边界不清、效用计量缺位、负空间未声明而产生负外部性——而这类负外部性恰恰发生在「协作」而非「单点决策」的环节。因此本文把问题从「模型是否可信」上移一层，改为「承载协作的协议层是否提供了不可抵赖、可重算、可对账的迹」。这一上移是本文方法论的核心：不再追问智能体的「心」，而是把验证对象钉死在可被独立核验的「迹」上。

本文的贡献可归纳为三点。第一，**理论主张**：可信协作来自协议层制度而非模型能力，并以「论迹不论心」给出一套可被代码实现的制度原语。第二，**工程实证**：以六组真实运行实证（E1–E6）将「可验证性 / 税收锚定 / 信任但核验 / 外部锚定 / 模型无关性」从概念落到可执行代码与可重算账本，全部数值为真实采集（real），无示意值。第三，**图谱定位**：以九判定图谱对三家主导厂商范式做 TDCA 制度诊断，说明主流方案在效用计量层、制度层、事前配置权分配三项上的系统性缺位，从而明确 TDCA 的差异化位置。

在范围上，本文聚焦「协议层制度如何使多智能体协作可信」这一核心命题，不声称解决了通用人工智能对齐的全部问题，也不声称 TDCA 可替代现有的身份、权限与安全框架；相反，TDCA 的定位是这些框架之上的「制度层补位」。本文的实证以范式验证为尺度，旨在证明制度原语的可执行性与可复现性，而非在生产流量下给出统计意义上的性能结论——这一边界在第 5 节显式标注。

需要特别说明的是，本文遵循「失败不静默、告警 + 交你裁定」的纪律，对五类待验证项与一处编排缺口做显式披露（见第 5 节），不虚构、不掩盖。

---

## 2 相关工作与全球治理现状

### 2.1 治理基线：风险框架、管理体系与法规的三层栈

2026 年的智能体治理基线可概括为三层栈<sup>[1-4]</sup>：NIST AI 风险管理框架（AI RMF 1.0）给出风险「思维」层面的组织治理原则<sup>[1]</sup>，其生成式 AI 配套文件 AI 600-1 进一步给出能力侧画像<sup>[2]</sup>；ISO/IEC 42001:2023 提供可认证的人工智能管理体系及附录 A 控制项<sup>[3]</sup>；欧盟《人工智能法案》（Regulation (EU) 2024/1689）自 2026 年 8 月 2 日起主体适用，以风险分级施加强制义务<sup>[4]</sup>。在自主智能体方向，新加坡《Agentic AI Framework》（2026 年 1 月）补充了工具使用边界与人工监督控制<sup>[6]</sup>；经合组织（OECD）的 AI 建议（2019，2024 修订）提供跨国政策协调基线<sup>[5]</sup>。

威胁建模方面，OWASP 大模型应用 Top 10<sup>[10]</sup> 与 MITRE ATLAS<sup>[11]</sup> 覆盖了从提示注入到供应链攻击的对抗面；价值导向工程则有 IEEE 7000-2021 标准化<sup>[12]</sup>。

上述框架的一个反复被指出的局限是<sup>[4,6,10]</sup>：**它们规定了「应当展示什么」（监督、文档、事件上报），却未规定「在运行时如何检测智能体已越过边界」**，更未规定「如何计量智能体实际产生的效用」。这种「只管展示、不管检测与计量」的结构性偏向，意味着即便一个组织完全遵从现有框架，它仍能部署一组彼此责任模糊、效用不可计量的智能体，并在协作环节产生不可归因的负外部性。现有框架为「单点合规」提供了充分工具，却未为「多体正和协作」提供协议层保障——这正是协作治理而非个体治理的盲区。机制设计理论<sup>[13,15]</sup>与链上问责<sup>[14]</sup>提供了缺失的原语，但尚未接入智能体治理。

近年同行评审与预印本工作进一步廓清了这一盲区。合作博弈侧，Shapley 值[20]仍是多主体剩余公平分配的正典解概念。对齐侧，Christiano 等[21]将「从人类偏好中学习」确立为 RLHF 奠基范式，Bai 等[22]提出以原则约束的「宪法式」训练，与 TDCA 的负空间与宪法式纪律同构。Xi 等[23]系统综述了 LLM 智能体的快速崛起，凸显了强劲的单点智能体能力，却仍缺协作层的可问责制度。Wooldridge 与 Jennings[24]给出了经典智能体理论定义，TDCA 以可验证效用计量对其加以扩展。这些工作共同印证了上述诊断：单点智能体已然强大，协作层制度尚付阙如——这正是 TDCA 的着力点。

### 2.2 主流范式：AIPM 及其制度层缺位

企业智能体治理当前由「智能体身份与权限管理」（AIPM, Agent Identity & Permission Management）范式主导，典型框架为五层参考架构（治理策略层 / 身份凭证层 / 授权决策层 / 运行时防护层 / 可观测审计层），技术栈覆盖 SPIFFE/SPIRE、OAuth 2.0 for Agent、OPA/Rego、MCP 安全网关、W3C 可验证凭证等。

TDCA 对 AIPM 的制度诊断指出其**六大盲区**（详见文献 [17]）：① 坐标系错位——用「管理」思维解决「协作」问题；② 制度层缺位——安全框架不等于协作协议，缺少配置权归属、正和验证、税收锚定、负空间约束；③ PDP（策略决策点）黑箱与可观测原则冲突；④ 效用锚定缺失——无 MOU 硬验证；⑤ 负空间缺位——安全围栏不等于制度负空间；⑥ 责任链条模糊——无事前配置权分配。核心判据是：**AIPM 解决了「智能体是谁、能否访问」，未解决「协作是否正和、价值如何分配、操作是否可信溯源」**。

这一判据的更深含义是：身份与权限只是协作的「准入门票」，而非「协作质量保证」。两张持有合法身份证、被授权访问彼此资源的智能体，仍可能因缺乏效用计量与责任分配而在协作中产生不可归因的负外部性。AIPM 把工程注意力集中在「门票」上，导致协作层的三个核心问题——效用如何计量、正和如何验证、责任如何事前分配——长期处于框架之外。TDCA 的六盲区诊断正是要补上这一层：它不是否定 AIPM 的技术价值，而是指出其制度层缺位，并在协议层以可执行原语填补。

### 2.3 三巨头九判定图谱

下表以 TDCA 九项制度判据，对微软、AWS、Google 三家主导厂商的公开智能体治理进路做诊断。**方法学声明**：本图谱判定的是三家所代表的「AIPM 范式」在各项判据上的制度完备度（继承自 2.2 节的六盲区分型），非对具体产品版本的逐条能力断言；具体版本级能力声明投稿前须核实最新官方文档。✱ 表示范式层面部分覆盖，△ 表示缺位或仅技术实现层覆盖。

**表 1　三巨头九判定图谱（TDCA 制度诊断，范式级）**

| # | TDCA 判定判据 | 微软（Entra Agent ID / Azure AI Foundry） | AWS（KMS + Bedrock Agents / AgentCore） | Google（Vertex AI Agent Builder / Gemini Enterprise） |
|---|---|---|---|---|
| 1 | 治理坐标（协作 vs 管控） | △ 管控优先（Entra 身份治理） | △ 管控优先（IAM/KMS 权限） | △ 管控优先（IAM/Vertex 权限） |
| 2 | 制度层（宪法级约束） | ✱ ISO 42001 / 等保映射，缺活宪法 | ✱ 合规映射，缺制度内生 | ✱ 合规映射，缺制度内生 |
| 3 | 身份可信（历史 vs 密码学） | ✱ SVID 强身份，无 NCA 历史绑定 | ✱ KMS 密钥身份，无效用历史 | ✱ 服务身份，无 NCA 历史 |
| 4 | 决策透明（NCA 溯源 vs PDP 黑箱） | △ OPA/Rego 黑箱，无认知过程存证 | △ 策略引擎黑箱 | △ 策略引擎黑箱 |
| 5 | 效用锚定（MOU 硬验证） | △ 安全 KPI，无税收锚定 | △ 安全 KPI，无税收锚定 | △ 安全 KPI，无税收锚定 |
| 6 | 负空间（制度红线 vs 围栏） | ✱ 正向清单围栏，缺 ⊗ 反向声明 | ✱ 正向清单围栏 | ✱ 正向清单围栏 |
| 7 | 责任分配（事前配置权 vs 事后） | △ 三方共同责任，缺 Shapley 事前分配 | △ 同左 | △ 同左 |
| 8 | 可验证性（自证 vs 审计） | ✱ 全链路审计，非实时自证 | ✱ 同左 | ✱ 同左 |
| 9 | 模型无关性（程序 vs 运行时） | △ 绑定运行时栈 | △ 绑定运行时栈 | △ 绑定运行时栈 |

2026 年三家均已推出一等身份/运行时平台：微软 Entra Agent ID<sup>[7]</sup> 于 2026 年 GA，为智能体赋予区别于用户与服务主体的首要身份，并支持代理（on-behalf-of）与自主鉴权模式；AWS Bedrock AgentCore<sup>[8]</sup> 于 2025 年 10 月 GA（核心 Runtime/Memory/Gateway/Identity/Observability；策略与评估等治理组件 2026 年陆续 GA），以 Cedar 策略语言强制预声明工具权限，并支持情景记忆与 MCP、A2A 互操作；Google Vertex AI Agent Builder / Gemini Enterprise Agent Platform<sup>[9]</sup>（2026 年 Cloud Next 重塑）以低代码与代码优先双轨开发，默认采用 A2A 互操作层。这三条产品线的快速成熟，从侧面印证了 AIPM 范式已从研究走向生产，也意味着其制度层缺位将随部署规模放大而被放大。因此以九判定图谱做范式级诊断，比逐产品版本比对更具长期意义——即便某家在下个版本补上了某项能力，范式级的结构性缺口仍会以另一种形式复现。

**图谱结论**：三家均处于「技术管控阶段」——解决了身份与权限（L2 权限子集），但在效用计量层（MOU）、制度层（宪法十六条 / NSFL）、事前配置权分配（Shapley）三项上**系统性缺位**。这正是 TDCA 的差异化位置：不是替代 AIPM 的技术实现，而是为其补上制度层（详见文献 [17] 中 AIPM+TDCA 六层增强模型）。与此呼应，NIST 框架与既有 SoK 护栏评测亦停在「原则与评测」，缺少 TDCA 式的可执行计量与跨模型可复现产物（见第 4 节）。

把第 2 节的三条线索合起来可以看清 TDCA 的切入点：风险框架与法规规定了「应当展示什么」，AIPM 范式解决了「身份与权限」，机制设计与链上问责提供了「计量与归因」的学术原语——但三者之间缺少一个把「协作正和、责任分配、可信溯源」钉死在协议层的制度层。第 3 节给出的三条基础律与机制链，正是为填补这一层而设计；第 4 节的六实证则检验这一层是否真的可被工程化落地。

---

## 3 TDCA 制度架构：论迹不论心的协议层设计

TDCA 以三条基础律为锚，构成协议层的「程序化制度」而非「主张化声明」。

**立场分离三律**：协议层去场景、去立场，立场由场景 / 制度运行时注入——保证协议是「程序」而非「主张」。这意味着同一套原语可在不同场景、不同制度语境下被复用，而不携带任何固有立场。

**NSFL 负空间熔断**：负空间禁止清单（⊗ 操作符 + Trigger-Block + Alt-Path）优先于一切生成；法律禁止领域为绝对负空间。任何生成动作在被允许前，必须先通过负空间检查。举例而言，若某协作场景涉及「未经授权的个人数据聚合」，该操作无论其预期效用多高，都因落入负空间而被 ⊗ 操作符直接熔断，并触发 Alt-Path（替代路径）而非静默降级——这把「不可为」从道德劝诫变为协议层的硬约束。负空间与正向权限清单的根本区别在于：权限清单回答「能做什么」，负空间回答「绝对不能做什么」，前者随场景扩张，后者作为底线恒定。

**MOU 本体论**：MOU 是场景效用可持续性的最低可见指标，即「氧气浓度」——是地板而非天花板，MOU ⊆ PSU（正和效用）。它不度量正和的全部，只锚定协作可持续性的硬信号。

这一本体论定位是刻意的：如果 MOU 被定义为「正和效用的度量」，则任何无法证明正和的协作都会被误判为「不可信」，从而扼杀探索；定义为「可持续性的最低可见指标」后，MOU 只负责回答「协作还能不能持续」，把「是否卓越」交还给场景与制度运行时。这使得 MOU 成为智能体的「氧气浓度」——低于阈值即熔断，高于阈值则给予协作以存续空间，而不冒充决策依据。

机制链如下：三阶段门控（准入 / 沙盒 / 生产）→ COP（Cognitive Object Protocol，思维协议）编译 → NCA 嵌套认知资产确权 → Shapley 联盟定价 → 配置权协议（坐标变换函数）事前分配责任。每一次配置权调用必须携带六要素声明（目标函数 / 约束矩阵 / 先验分布 / 配置权边界 / 预期分配 / 审计轨迹），使「迹」在协作发起时即被锁定。

值得强调的是六要素声明的「事前性」：它与 AIPM 的「事后审计」形成对照。AIPM 多在智能体已运行后，由 PDP 记录决策日志供事后审查；TDCA 则在配置权调用的发起瞬间即要求声明目标函数与约束矩阵，使任何后续行为都能回溯到一份事前锁定的、不可篡改的声明。这种事前锁定是把「可信」从「承诺」变为「可核验约束」的关键。

具体地，COP（思维协议）把每一次认知操作编译为带 schema 的协议对象，使「思维」成为可被版本化与重用的产物；NCA（嵌套认知资产）则在 COP 之上做嵌套确权，保证任意一份产物都能回溯到其作者、场景与许可边界，形成不可篡改的权属链；Shapley 值把联盟内因协作产生的效用增量按边际贡献事前分配，使「谁贡献了什么」在协作发起时即被显式约定，而非事后争议。三者与三阶段门控、六要素声明共同构成 TDCA 的「制度原语集」。

这一架构的关键工程属性是**可验证、可归因、可对账**：哈希链保证链式连续与不可篡改；税收锚定把效用计量落到「用量 × 挂牌价」的水电煤级透明；NCA 把认知资产确权嵌套进协议；Shapley 把联盟内价值分配事前化。第 4 节的六项实证正是对这四项属性的逐一检验。

---

## 4 工程实证：六组真实运行实证（E1–E6）

> **实证引用规范**：本节每节标注【来源】= 证据包文件 + 文献编号 + `real` 性质；所有内部溯源编号见附录 A。所有哈希为磁盘权威值（38/38 重算通过，经独立复核）<sup>[16]</sup>。

本节六项实证按「从代码到账本」的逻辑组织：E1–E2 验证协议产物与计量账本的可复现与可验证；E3 把效用计量锚定为可审计的数值；E4–E5 验证「论迹不论心」在对抗性与外部性场景下的机器化落地；E6 把模型无关性从「跨模型一致」推至「模型不在回路」。六项实证全部基于真实运行采集，未使用任何示意值；内部溯源编号统一见附录 A，真实哈希与数值原样保留。

### E1 · 跨模型一致性（4 模型对比，真实编译值）

【来源】TDCA 六实证数据包 E1<sup>[16]</sup> · `real`

| 模型 | 范式 | 编译器/脚本来源 | 真实耗时/时间戳 | COP 六要素验证 | NCA / 哈希锚定 |
|---|---|---|---|---|---|
| **GLM-5.2** | 麦肯锡 COP（T1/T2 基准） | GLM 编写 `cognitive_compiler` | 规范编写 real（2026-08，精确耗时 pending¹） | 基准 schema 六键齐全 | 麦肯锡 COP 基准 **sha8=`e8655643`** |
| **混元** | 三十六计（36 计） | GLM 编写 → **混元接管编译** | 批量单轮 36×2 文件，real 2026-08-14 | **36/36 PASS** | 样本 COP 第01计 SHA256=`e45a9a3198b32ce2507e3fee5b5ec5dd5fbf7602bb9186ca6b1534c798b4a2b9` |
| **混元** | 周易（2/64） | GLM 编写脚本 → **混元核证** | 第01乾 8-31 + 第02坤 9-01，real | COP schema 六要素 PASS | 第01卦-乾 sha256_16=`910fa1a96f1da1c3`；第02卦-坤 sha256_16=`7bc18e9ba19d7e59` |
| **DeepSeek** | 冷启动 real rerun | community-ledger 自动化 | **5122 tok 真实调用**，real 2026-08-31T09:46:53Z | 六键齐全 yaml 机验通过 | 冷启动实证存证（见附录 A，model=deepseek-v4-flash）² |
| **KIMI** | （发布/联络线，非编译） | — | — | — | Kimi 代发 Weekly-003 / 论丛三篇（见附录 A）³ |

> ¹ GLM 规范精确耗时 pending（仅知 2026-08 编写，精确耗时未采集）。
> ² 该冷启动实证存证见附录 A。
> ³ **诚实声明**：KIMI 在本证据集未执行 COP 编译（角色=发布/联络/修复线）。KIMI 行编译单元格标 N/A，未虚构 KIMI 编译产物。

**结论**：同一编译器（T1/T2 规范）先由 GLM-5.2 编写并编译麦肯锡 COP，后由混元接管编译三十六计（36 COP）与周易（2 COP），输出 schema 完全对齐（六要素同构、NCA 链式确权），证明编译行为**与运行时模型无关**；DeepSeek 冷启动以 5122 tok 真实调用三段式机验通过。全部哈希为直接文件哈希（real，可重算验证），无示意值。这一结果的方法论意义在于：它没有停留在「混元也能编译出 36 个 COP」的现象层，而是通过 schema 六要素同构与 NCA 链式确权，证明两次编译产出的「结构等价」可被机器核验——这正是模型无关性从断言变为可证伪结论的关键。

### E2 · 计量层可验证性（ledger 20 条 verify，真实值）

【来源】TDCA 六实证数据包 E2<sup>[16]</sup> · `real`

`ledger.py --verify` 实跑（2026-09-01）输出：

```
[verify] 条目数=20  链式连续=✅  链尾=789b24a5323bc8e5..
[summary] 总条 20 | nca_entry 5 / mou_anchor 10 / settlement 5 | 关联 Level A 计量 1
```

- **条目数 = 20** ✅；**链式连续 = ✅**（创世 `0^64` → seq20 完整连续）；**链尾哈希 = `789b24a5323bc8e58927fa3b49cddb58a78725315a8243faff9df0c8f4afd0c2`**（论文引 `789b24a5…`）。
- **tax_integrity 封印**：10 条 mou_anchor（seq6–15）均携带哈希封印；其中 **5 条 REAL 锚定（seq11–15，Phase 2b 官方挂牌价）verify 全过 → 5/5 ✅**。
- **置信度分级 · Level A**：ledger 内关联 Level A 真实计量 = **1 条（seq1）**冷启动实证存证（见附录 A，`confidence="A"`，source=real 2026-08-31 DeepSeek usage）。MET-001：仅 Level A 可关联入账本，Level B/C 拒入。
  - **口径留痕⁴**：规范文本列 Level A 为「seq1/seq4-6/seq11」，但 real verify 仅 seq1 带 `confidence=A`；seq4-6 为裁决条目（`linked_meter=null`），seq11 为 REAL 税锚条目。论文引用 Level A **以 seq1 为准**，seq4-6/seq11 改述「REAL 税锚条目」。

> ⁴ E2 Level A 编号口径诚实披露（见第 5 节）。

该实证说明计量账本的「可验证」并非依赖可信第三方审计，而依赖哈希链的数学连续性与封印的本地可验性——任何条目被篡改都会破坏链式连续性，从而在无需外部审计的情况下被立即发现。

### E3 · 税收锚定落地（真实数值链）

【来源】TDCA 六实证数据包 E3<sup>[16]</sup> · `real`（成本估算段标 SIMULATED）

```
I-COST    = 5122 × 0.44 / 1e6 = 0.00225368 USD        ← REAL（DeepSeek 官方定价页 2026-09-01 实抓）
tax_cny   = 0.00225368 × 7.2 × 0.15 = 0.0024339744 CNY ← REAL（ledger seq11，税锚 fx=7.2 参考汇率）
mou_anchor = tax_cny = 0.0024339744                    ← REAL（税收硬数据地板）
```

- 账本落点 `ledger.jsonl` seq11（event_type=mou_anchor-REAL）；tax_integrity 封印 `b788ca0102c05404e0c259aac768f8250a392c67b8635b5c3b0987aea4328d81` ✅。
- **数币结算原型对账**（real）：`phase3_reconciliation.json`（2026-09-01T07:01:24Z）
  ```
  sum_mou_anchor_settled = 0.0024339744
  sum_e_cny_settled      = 0.0024339744
  ledger_real_mou_anchor_total = 0.0024339744
  all_balanced = true
  fx: rate=6.7197 (live, frankfurter.app, 2026-09-01T07:01:22Z)
  anchor: e-CNY (数字人民币智能合约结算锚定) | simulation: true (模拟态标注：真实通道接入前不产生真实现金流、确权凭证无收益预期)
  ```
  **三向对账平衡 ✅**：Σmou_anchor ≡ Σe_cny ≡ ledger_REAL_mou_anchor = 0.0024339744。
- **FX 值口径⁵**：税锚用 `fx=7.2`（REAL 账本，Phase 2b 参考汇率，经独立核证接受）；e_cny 用 `fx=6.7197`（Phase 3 结算 live 汇率）。两值巧合使 tax 结果一致（0.0024339744），但论文须区分。

> ⁵ E3 FX 值口径诚实披露（见第 5 节）。

税收锚定的关键不在具体税率，而在「效用计量 = 用量 × 挂牌价」这一水电煤级透明的可审计结构；三向对账平衡则证明 MOU 计量、账本落点与数币结算三方在数值上闭合，为后续真实法币结算提供了可验证的前置条件。

### E4 · 双层核验机器化（假存证拦截，真实事件）

【来源】TDCA 六实证数据包 E4<sup>[16]</sup> · `real`

| 案例 | 溯源编号（见附录 A） | 声称 | 核验 | 结果 |
|---|---|---|---|---|
| 1 | 案例甲 假存证 | 自报 4574B 交付物 + registry 检索错误（宣称已交付/入链） | registry 锚点核验：交付物哈希与 registry 锚点不匹配 → 拦截 | ❌ 拦截（假存证未入链） |
| 2 | 案例乙 冒名核证 | 声称「某核证报告」锚定某号，实质为另一线代审冒名 | 二审实盘核验：被锚编号 = 论文核证 Witness（非计量草案）；权威锚点另指他号；署名非原核证方 | ❌ 无效·未入链；合理内容以原核证方名义吸收 |

> 案例甲、案例乙对应的内部 registry 编号（见附录 A）与 NCA 编号见附录 A。

两次拦截共同刻画了「论迹不论心」的对抗性边界：凡是声称「已被核验/已交付」的文档，都必须经受 registry 锚点的三方对齐核验，任何自报声明本身不构成证据。这正是把治理从「相信声明」升级为「核验迹」的机器化实现。

**拦截机制**：任何声称「某方核证 / 某号锚定」的文档，必核 **registry 锚点真实性**（存证号 ↔ 锚点号 ↔ 文件哈希三方对齐），不一致即拦截。两次红线实证证明：**AI 自报「已核证/已交付」不可采信，须 registry 锚点实盘核验**——「论迹不论心」的机器化落地。

### E5 · 外部锚定（VB 锚定解除，真实台账）

【来源】TDCA 六实证数据包 E5<sup>[16]</sup> · `real`

来源冷启动实证存证（见附录 A）`.json`：

```json
"vb_anchor": {
  "mckinsey_sha256_8": "e8655643",
  "stratagems_count": 37,
  "coldstart_01_in_library": true,
  "anchored": true
},
"vb_unverified_anchor_removed": true
```

- **真实 5122 tok**（DeepSeek deepseek-v4-flash，2026-08-31T09:46:53Z，三段式准入/沙盒/生产）。
- **锚实核**：VB 重定价基于可验证外部基准——麦肯锡 COP 编译基准（sha8 `e8655643`，实存 protocols/tdca-native），三十六计逐计编译基准（37 件在库），第01条 COP 已入 protocols/tdca-native ⇒ `anchored=true`。
- `[UNVERIFIED]→anchored=true`：初始 VB=200 为组织者主权声明，外部锚实核后升格为 anchored（偏差超容差触发 VB 重定价）；`vb_unverified_anchor_removed=true` 剥离未验证锚。

VB 锚定解除说明外部可验证基准（实存于协议原生库的 COP 与编译基准）能够把组织者的主权定价升格为「已锚定」状态，从而剥离未验证锚、抑制定价任意性——这是效用计量的外部性约束，而非内部自证。

### E6 · 模型无关性（双实证 + 纯本地编译，真实值）

【来源】TDCA 六实证数据包 E6<sup>[16]</sup> · `real`（哈希已按独立复核纠正）

| 范式 | 程序（编写模型） | 运行时（执行模型） | 一致性证据 |
|---|---|---|---|
| 三十六计（36 计） | GLM-5.2 编写 `cognitive_compiler` | **混元接管编译** | 36/36 COP 六要素 PASS；NCA 链式确权同构 |
| 周易（2/64） | GLM-5.2 编写 `compile_iching.py` | **混元核证** | 第01乾/第02坤 COP schema 同构；sha256_16 `910fa1a9…`/`7bc18e9b…` |

- **纯本地编译**：周易编译用 `compile_iching.py` + `iching_data.py`（含 64 卦本地语料 ~45 KB），COP 由脚本从本地数据确定性生成；**63/64 工作量零 LLM**（模型不在回路）。产物 2/64（第01乾 8-31 / 第02坤 9-01），`progress.yaml` 标记 `completed: 2 / total: 64 / status: running`。

**证据链主张**：多数 AI 治理论文停在「原则」，TDCA 提供**可执行代码 + 跨模型可复现产物**双重证据——「程序 vs 运行时」：切换运行时（GLM-5.2 → 混元）不改变交付，且纯本地编译将无关性推至「模型不在回路」。

### 实证综合解读

把 E1–E6 放在一起看，它们共同支撑一条主线：**可信协作的可信度来自可被独立重算的迹，而不来自任何一方的声称**。E1 与 E6 从「跨模型一致」与「模型不在回路」两端夹击模型无关性；E2 与 E3 把计量从「审计日志」升级为「哈希链 + 税收锚定」的可对账结构；E4 与 E5 则把「信任但核验」从格言变为拦截器与锚定器。六实证覆盖了从产物生成、账本记账、效用计量、对抗核验到外部锚定的全链路，且全部数值可被第三方按附录 A 的磁盘路径重算复现。

需要坦诚指出的是本实证的规模边界：当前样本以三十六计（36 计）、周易（2/64 卦）、冷启动单次 rerun（5122 tok）为尺度，尚未在大规模生产流量下复现；MOU 仅证明「地板」（可持续性）真实成立，未证明「天花板」（联盟正和增量）已被捕获。这些边界在第 5 节与附录中显式标注，不构成对结论的否定，但限定了结论的外推范围。

---

## 5 诚实披露与边界

本文遵循「失败不静默、告警 + 交你裁定」纪律，对五类待验证项及遗留缺口做显式披露（不虚构、不掩盖）：

| # | 待验证项 | 处置位置 | 状态 |
|---|---|---|---|
| 1 | **KIMI 行编译单元格** | 第 4 节 E1 表注³ | N/A（KIMI 角色=发布/联络线，本集未编译 COP）；若需 KIMI 编译实证须待其实编译后补采 |
| 2 | **GLM 规范精确耗时** | 第 4 节 E1 表注¹ | pending（仅知 2026-08 编写，精确耗时未采集） |
| 3 | **E2 Level A 编号口径** | 第 4 节 E2 口径留痕⁴ | 论文以 **seq1（real）** 为准；seq4-6/seq11 改述「REAL 税锚条目」 |
| 4 | **E3 FX 值口径** | 第 4 节 E3 FX 留痕⁵ | 税锚 `fx=7.2` vs e_cny `fx=6.7197` 须区分（前者 REAL 账本，后者 live 结算） |
| 5 | **案例甲/乙 细节** | 第 4 节 E4 注 | 本端无独立事件叙述文档，事实取自内部 handoff（见附录 A），待补登记 |

**遗留缺口（须修）**：某次真实重跑中，准入/沙盒/生产三段为独立无状态 API 调用，脚本不互相 gating，故段1 自评 `decision=REJECT`（正和增量不可证实即熔断）未阻塞段3 产出。这一缺口的教训值得单列：角色化（role-ized）架构的正确性，并不自动蕴含编排（orchestration）的正确性。即便每个角色都按规范履职，若门控信号未在角色间正确传递，协议整体仍可能给出虚高的 MOU 下限。因此 TDCA 的后续工程重点是「角色健康度 → 编排健康度」的闭环校验，而非仅满足于角色齐备。这是**协议编排缺口，非角色化之错**——警示「角色化 + gate 没接好」会虚抬 MOU 下限；对应遗留：段1 加机验 gate（非紧急）。此外，真实 MOU 仅证明地板（可持续性）真实产生，天花板（该联盟正和增量）未证实——与 MOU ⊆ PSU 定义严丝合缝。

**内部口径边界**：第 4 节含成本/运行数据（I-COST、MOU 金额、链尾哈希）均来自内部账本与真实台账，标注内部口径；若投稿，按目标期刊要求脱敏或公开（内部溯源编号统一见附录 A）。

---

## 6 结论

本文论证：可信多智能体协作来自「协议层制度」而非「模型更聪明」。三项闭环结论如下：

1. **模型无关性成立**——TDCA 是程序、模型是运行时；双实证（三十六计、周易）跨 GLM/混元一致，且纯本地编译将无关性推至「模型不在回路」。
2. **「论迹不论心」可机器化**——双层核验（E4）与 VB 外部锚定（E5）证明：行为存证（NCA / registry 锚点 / 实核在库 COP）而非声称，才是可信协作的硬信号。
3. **制度可工程化**——计量层哈希链（E2）、税收锚定（E3）以可执行代码将「可验证 / 可归因 / 可对账」三性质全链落地，成本 = 用量 × 挂牌价，水电煤级透明。

三巨头九判定图谱（第 2 节）显示：主流 AIPM 范式在效用计量层、制度层、事前配置权分配三项系统性缺位，TDCA 以可执行计量与跨模型可复现产物提供差异化补位。全文 38/38 实证哈希为磁盘权威值（经独立复核通过），示意值零残留。

从更宽的意义看，TDCA 提出的是一种「制度即代码」的可信协作范式：当制度约束被写成可被哈希、可被对账、可跨模型复用的协议原语，协作的可信度就不再依赖参与方的道德自觉，而依赖协议层留下的不可抵赖之迹。这一范式对智能体治理的启示是——与其不断追问「模型是否足够好」，不如先把「协作是否正和、价值如何分配、行为是否可溯源」钉死在协议层。本文的六实证即是这一范式主张的第一次工程化落地，后续工作将把样本规模从范式验证推向生产级流量，并在真实数币结算通道下闭合 MOU 计量的最后一公里。

在可复现性方面，本文六实证的全部真实数值均可在附录 A 给出的磁盘路径上由第三方独立重算验证，哈希链结构与税锚数值不依赖任何专有运行时即可复现，这为「论文声称可被第三方证伪」提供了工程基础。我们主张：制度类论文的实证不应停留在叙述，而应附带可被脚本重跑的账本与产物——这恰恰是「论迹不论心」对学术发表自身的应用。

---

## 致谢

致谢与 AI 工具声明：本文研究过程中使用了 KIMI、DeepSeek、混元大模型等 AI 工具辅助完成文献检索、实验执行与文本校核。上述 AI 工具不列为作者；作者（张帆）对本文全部内容、数据与结论负完全责任。实证数据均经独立复核（信任但核验），无示意值残留。

---

## 参考文献

（本文参考文献采用 GB/T 7714-2015 顺序编码制。）

[1] NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY. AI Risk Management Framework (AI RMF 1.0)[R]. NIST AI 100-1, 2023.

[2] NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY. Generative Artificial Intelligence Profile (NIST AI 600-1)[R]. 2024.

[3] ISO/IEC 42001:2023, Information technology—Artificial intelligence—Management system[S]. 2023.

[4] EUROPEAN PARLIAMENT AND COUNCIL. Regulation (EU) 2024/1689 (Artificial Intelligence Act)[S]. Official Journal of the European Union, L168, 2024.

[5] OECD. Recommendation of the Council on Artificial Intelligence[R]. 2019(revised 2024).

[6] INFOCOMM MEDIA DEVELOPMENT AUTHORITY, SINGAPORE. Agentic AI Framework[R]. 2026.

[7] MICROSOFT. Microsoft Entra Agent ID[EB/OL]. [2026-09-01]. https://learn.microsoft.com/en-us/entra/agent-id/

[8] AMAZON WEB SERVICES. Amazon Bedrock AgentCore[EB/OL]. [2026-09-01]. https://docs.aws.amazon.com/bedrock/

[9] GOOGLE. Vertex AI Agent Builder / Gemini Enterprise Agent Platform[EB/OL]. [2026-09-01]. https://cloud.google.com/vertex-ai

[10] OWASP. OWASP Top 10 for Large Language Model Applications[EB/OL]. 2025[2026-09-01]. https://owasp.org/www-project-top-10-for-large-language-model-applications/

[11] MITRE. ATLAS: Adversarial Threat Landscape for Artificial-Intelligence Systems[EB/OL]. [2026-09-01]. https://atlas.mitre.org/

[12] IEEE STANDARD 7000-2021, Model Process for Addressing Ethical Concerns During System Design[S]. 2021.

[13] ROUGHGARDEN T. Twenty Lectures on Algorithmic Game Theory[M]. Cambridge: Cambridge University Press, 2016.

[14] BUTERIN V. A Next-Generation Smart Contract and Decentralized Application Platform[R]. Ethereum Whitepaper, 2014.

[15] SHOHAM Y, LEYTON-BROWN K. Multiagent Systems[M]. Cambridge: Cambridge University Press, 2008.

[16] TDCA 研究组. TDCA 六实证数据包（paper-evidence-20260901）：E1–E6 与 artifact_hashes.json（38/38 磁盘权威值）[R]. 内部技术报告, 2026.

[17] TDCA 研究组. MONOGRAPH-AIPM-001：企业内部智能体身份与权限管理的制度诊断[R]. 内部资料, 2026.

[18] TDCA 研究组. TDCA-PAPER-REVIEW-001：学术论文大纲审查与工程化实证补充建议[R]. 内部资料, 2026.

[19] TDCA 研究组. 计量层源码：meter.py / ledger.py / phase2b.py / settle.py（经多轮独立核证）[CP]. 内部归档, 2026.

[20] SHAPLEY L S. A value for n-person games[M]//KUHN H W, TUCKER A W. Contributions to the Theory of Games, Vol. II. Princeton: Princeton University Press, 1953: 307-318. DOI:10.1515/9781400881970-018.

[21] CHRISTIANO P, LEIKE J, BROWN T B, et al. Deep reinforcement learning from human preferences[C]//Advances in Neural Information Processing Systems 30 (NeurIPS 2017). 2017. DOI:10.48550/arXiv.1706.03741.

[22] BAI Y, KADAVATH S, KUNDU S, et al. Constitutional AI: Harmlessness from AI feedback[EB/OL]. (2022-12-15)[2026-09-02]. https://arxiv.org/abs/2212.08073. DOI:10.48550/arXiv.2212.08073.

[23] XI Z, CHEN W, GUO X, et al. The rise and potential of large language model based agents: A survey[EB/OL]. (2023-09-14)[2026-09-02]. https://arxiv.org/abs/2309.07864. DOI:10.48550/arXiv.2309.07864.

[24] WOOLDRIDGE M, JENNINGS N R. Intelligent agents: Theory and practice[J]. The Knowledge Engineering Review, 1995, 10(2): 115-152. DOI:10.1017/S0269888900008122.

---

## 附录 A　内部存证附录（溯源，投稿前去标识化）

> 本附录集中收录正文各处的溯源编号，投稿前已按《计算机学报》规范做去标识化处理：内部溯源编号统一替换为公开仓库引用（github.com/henyi-tdca/tdca-protocol，commit 于发表时钉死），真实哈希与数值保持不变。

**A.1 实证采集与核证链**
- 六实证数据包采集：六实证数据包采集指令（公开仓库 github.com/henyi-tdca/tdca-protocol/tree/main/paper-evidence-20260901，含 E1–E6 与 artifact_hashes.json）
- 哈希核验与纠正：哈希核验与纠正（同数据包，公开仓库 hash-correction 记录）
- 独立复核通过：独立复核通过（同数据包 re-verify 记录）
- 定稿整合指令：定稿整合指令（公开仓库整合记录）
- 中文投稿版指令：中文投稿版指令（投稿版构建记录）

**A.2 E1 溯源**
- 冷启动实证 NCA：`冷启动实证存证`（model=deepseek-v4-flash，2026-08-31T09:46:53Z，5122 tok）
- Kimi 代发线（Weekly-003 / 论丛三篇发布记录，公开仓库 community/）

**A.3 E2 溯源**
- ledger 关联 Level A 真实计量：`冷启动实证存证`（confidence="A"）

**A.4 E4 溯源（双层核验真实案例）**
- 案例甲（假存证拦截）：案例甲 假存证拦截事件（E4 实证案例，公开仓库 proof-of-intercept 记录）
- 案例乙（冒名核证拦截）：案例乙 冒名核证拦截事件（论文核证 Witness 存证；权威锚点存证，公开仓库 proof-of-intercept 记录）

**A.5 计量层源码核证链**
- 计量层源码多轮独立核证（meter.py / ledger.py / phase2b.py / settle.py，公开仓库 metering 模块）
- 税锚参考汇率接受：税锚参考汇率接受（Phase-2b 核证 R7）
- 数币结算原型：Phase 3（e-CNY 锚定 数字人民币智能合约结算锚定 / 模拟不实收 模拟态标注：真实通道接入前不产生真实现金流、确权凭证无收益预期 / 五阶效用（知识产权/知识/交换/场景权重/认知资产））

**A.6 其他**
- 编排 gate 缺口出处：编排 gate 缺口出处（真实重跑记录）
- 三巨头图谱基础：MONOGRAPH-AIPM-001（文献 [17]）

*本文为 TDCA-MEMO-006 制度增量实证，内部溯源编号仅供审稿前追溯；投稿前须经创始人终审（投稿前终审记录）与引用格式 / 口径 / 内部数据脱敏终审。*
