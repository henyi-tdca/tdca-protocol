# TDCA 论文与实证证据包 / TDCA Paper & Empirical Evidence Package

## 理论白皮书 / Theoretical White Papers

- **函数白皮书 V2.1**（制度效用配置的形式化理论）= 主文档 V2.0-FROZEN（[TDCA-FUNCTION-WP-002-函数白皮书.md](TDCA-FUNCTION-WP-002-函数白皮书.md)，人类签批 2026-08-21）+ 附录 G（[TDCA-FUNCTION-WP-002-APPX-G-附录G-制度大模型与制度孪生函数化登记.md](TDCA-FUNCTION-WP-002-APPX-G-附录G-制度大模型与制度孪生函数化登记.md)，人类签批 2026-08-26 并入构成 V2.1）
- **数学基础白皮书（修订本）**：[TDCA-MATH-WP-REV-001-数学基础白皮书修订本.md](TDCA-MATH-WP-REV-001-数学基础白皮书修订本.md)（V1.0-FROZEN，人类签批 2026-08-23）——公理化体系与可执行证明，含公理 6 实例化闭环（机验见 [core-go/docs/formal-proofs/](../../core-go/docs/formal-proofs/)）

## 论文 / Papers

**中文定稿**：TDCA：论迹不论心的可信多智能体协作协议——制度设计、工程实证与模型无关性
→ [TDCA-paper-CN.md](TDCA-paper-CN.md)（FROZEN 定稿，SHA256 `12cbc770d7ef220a2a4e0d23d38b68c3114d94afea5ab8bf5939eb09eaf5dab2`）

**English version**：TDCA: Governing Multi-Agent Collaboration by Protocol-Level Institutions Rather Than Model Capability — Engineering Empirics and Cross-Model Reproducibility
→ [TDCA-paper-EN.md](TDCA-paper-EN.md)（FROZEN final, SHA256 `4323f5c492c36070b83d8b646269f461ffa731e283c43d5fa7b59e1e9ebb591d`）

**作者**：张帆（Zhang Fan）——恒益场景（厦门）数字经济研究院（Hengyi Scene (Xiamen) Digital Economy Research Institute），通信作者。

## 摘要 / Abstracts

**中文摘要**：TDCA（Trusted Digital Collaboration Architecture，可信数字协作架构，⟨ℑ,𝒯,ℰ,𝒫,𝒦⟩）提出一种「论迹不论心」的协议层制度设计：以三阶段准入门控（admission/sandbox/production）+ NCA 嵌套认知资产确权 + Shapley 联盟定价为核心机制，并锚定三条基础律——立场分离三律（协议层去场景去立场）、NSFL 负空间熔断（禁止清单优先于一切生成）、MOU 本体论（场景效用可持续性的最低可见指标，是地板而非天花板）。本文核心主张是：可信多智能体协作来自「协议层制度」而非「模型更聪明」，呼应「制度红利 > 技术红利」。为把这一主张从概念落到可执行代码与可重算账本，本文给出六项真实运行实证（E1–E6），覆盖可验证性、税收锚定、信任但核验、外部锚定与模型无关性五个维度；并以九判定图谱对微软、AWS、Google 三家主导范式做 TDCA 制度诊断，定位差异化位置。全文 38/38 实证哈希均为磁盘权威值（经独立复核通过），示意值零残留。

**English Abstract**: TDCA (Trusted Digital Collaboration Architecture, ⟨ℑ,𝒯,ℰ,𝒫,𝒦⟩) proposes a "trace-not-intent" protocol-layer institution: three-phase admission gating (admission / sandbox / production) + NCA nested cognitive-asset attribution + Shapley coalition pricing, anchored on three foundational laws — stance-separation, NSFL negative-space circuit-breaker, and MOU ontology. We make three contributions: (1) a theoretical claim that trustworthy collaboration arises from *protocol-layer institutions* rather than *model cleverness* (echoing the principle that institutional dividend exceeds technical dividend); (2) an **engineering-empirical section** of six real-run studies (E1–E6) that take verifiability / tax-anchoring / trust-but-verify / external-anchoring / model-independence from concept to executable code and recomputable ledger; (3) a related-work map — a nine-criterion diagnostic of the Microsoft / AWS / Google dominant paradigms — locating TDCA's differentiation. All 38/38 empirical hashes are disk-authoritative values (re-verified); illustrative-value residual is zero.

## 实证证据包 / Empirical Evidence（E1–E6，与论文同库、开源可重验）

| 编号 | 文件 | 主题 |
|---|---|---|
| E1 | [evidence/E1_cross_model_consistency.md](evidence/E1_cross_model_consistency.md) | 跨模型一致性 |
| E2 | [evidence/E2_meter_verifiability.md](evidence/E2_meter_verifiability.md) | 计量可验证性 |
| E3 | [evidence/E3_tax_anchor.md](evidence/E3_tax_anchor.md) | 税收锚定 |
| E4 | [evidence/E4_dual_layer_interception.md](evidence/E4_dual_layer_interception.md) | 双层拦截（信任但核验） |
| E5 | [evidence/E5_external_anchor_vb.md](evidence/E5_external_anchor_vb.md) | VB 外部锚定 |
| E6 | [evidence/E6_model_independence.md](evidence/E6_model_independence.md) | 模型无关性 |

- [evidence/artifact_hashes.json](evidence/artifact_hashes.json) —— 38/38 实证工件哈希（磁盘权威值，重跑 `sha256sum` 可复验）
- [evidence/EVIDENCE-INDEX.md](evidence/EVIDENCE-INDEX.md) —— 证据索引

## 38/38 哈希声明

论文实证部分全部数值为真实运行捕获（工程实跑 / 账本 / 台账直接捕获），38/38 工件哈希为磁盘权威值并经独立复核（信任但核验）；示意值零残留。验证方式：对本目录 evidence/ 文件重跑 SHA256，与 artifact_hashes.json 对照即得。

## AI 工具声明

研究过程中使用了 AI 工具辅助文献检索、实验执行与文字校对；AI 工具不列为作者，作者对全文内容、数据与结论负全部责任。
