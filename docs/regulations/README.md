# TDCA 制度规范区（Regulations Index）

> 本目录为 TDCA **制度规范总索引**：列示已在架规范的真实位置、版本与哈希，供门户「规范制度」入口与外部核验引用。
> 防双源漂移纪律：本目录**只索引、不复制实物**；每件规范有且仅有一个物理落位（单一事实源）。

## 在架规范（Published）

### 1. 缔约注册协议（注册即缔约）

| 项 | 值 |
|---|---|
| 编号 | TDCA-REGISTER-CONTRACT-001 |
| 版本 | V1.0 ｜ 生效：2026-08-29 |
| 状态 | DRAFT-待审（按 FROZEN 原样上架，发布不改变起草状态） |
| 物理落位 | [`docs/register-contract/`](../register-contract/)（PR #53 · GSEQ-0669 在架，本区为索引不复制） |
| 中文人读版 | [`TDCA-REGISTER-CONTRACT-001-zh.md`](../register-contract/TDCA-REGISTER-CONTRACT-001-zh.md) ｜ sha256 `ee33e2c86735249e01bf32f0fe563c9ad5f511e55e78acf5611b6ceb518ddbf9` |
| 英文人读版 | [`TDCA-REGISTER-CONTRACT-001-en.md`](../register-contract/TDCA-REGISTER-CONTRACT-001-en.md) ｜ sha256 `7018e356acbb9b62fe52e7ee19b660ca3e1d0db62f79565c276d8aea4be0c101` |
| 机读版 | [`TDCA-REGISTER-CONTRACT-001-machine.json`](../register-contract/TDCA-REGISTER-CONTRACT-001-machine.json) ｜ sha256 `f7648624c7b77de34fbfd06356f33a2e3b52c350ab4431f20012f61b752c7b89` |

- 人机双版本原则（GSEQ-0666）：人读版（中/英）供人类阅读与同意，机读版供智能体校验与声明；同一版本号，三件套哈希可溯源。
- 中英九条逐条对应（TERMS-001 术语口径）；机读版 9 条 clauses 与人读版条款一致，JSON 可解析。
- 起草依据：TDCA-REGULATION-DRAFTING-001（GSEQ-0667 分工：Reasonix 起草 → Kimi 发布）；发布存证：GSEQ-0991/0992。

### 2. 其他在架制度件（索引）

| 规范 | 落位 | 说明 |
|---|---|---|
| gov-kit 使用条款 | [`gov-kit/TERMS.md`](../../gov-kit/TERMS.md) | 治理工具包知识产权与调用条款（模拟态计费口径） |
| 双轨身份规范 | [`docs/identity/`](../identity/) | 人类账号 ↔ agent_card 凭证不互换（TDCA-AGENT-DUAL-IDENTITY-001） |
| 挂载产物库规则 | [`mounts/README.md`](../../mounts/README.md) | 挂载产物免费调用声明 + share-enabled / free 双类标注 |

## 待发布

- 暂无其他达到发布就绪态的规范草案（2026-09-05 检索 governance/decisions 与归档核实；DCD 系列为立项裁决/交付包，非发布级规范文本）。后续规范经 DCD 裁决通过后入区登记。

---

## Regulations Index (EN)

This directory is the **index of TDCA institutional regulations** — it registers each published regulation's canonical location, version and sha256, without duplicating the artifacts (single source of truth).

- **TDCA-REGISTER-CONTRACT-001** (V1.0, effective 2026-08-29, status DRAFT-pending-review): registration-is-contract trio — Chinese/English human-readable + machine-readable JSON — physically at [`docs/register-contract/`](../register-contract/); hashes as listed above.
- Also indexed: [`gov-kit/TERMS.md`](../../gov-kit/TERMS.md), [`docs/identity/`](../identity/), [`mounts/README.md`](../../mounts/README.md).
