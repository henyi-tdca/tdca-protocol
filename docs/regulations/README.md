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
| 物理落位 | [`docs/register-contract/`](../register-contract/)（PR #53 在架，本区为索引不复制） |
| 中文人读版 | [`TDCA-REGISTER-CONTRACT-001-zh.md`](../register-contract/TDCA-REGISTER-CONTRACT-001-zh.md) ｜ sha256 `ee33e2c86735249e01bf32f0fe563c9ad5f511e55e78acf5611b6ceb518ddbf9` |
| 英文人读版 | [`TDCA-REGISTER-CONTRACT-001-en.md`](../register-contract/TDCA-REGISTER-CONTRACT-001-en.md) ｜ sha256 `7018e356acbb9b62fe52e7ee19b660ca3e1d0db62f79565c276d8aea4be0c101` |
| 机读版 | [`TDCA-REGISTER-CONTRACT-001-machine.json`](../register-contract/TDCA-REGISTER-CONTRACT-001-machine.json) ｜ sha256 `f7648624c7b77de34fbfd06356f33a2e3b52c350ab4431f20012f61b752c7b89` |

- 人机双版本原则：人读版（中/英）供人类阅读与同意，机读版供智能体校验与声明；同一版本号，三件套哈希可溯源。
- 中英九条逐条对应（TERMS-001 术语口径）；机读版 9 条 clauses 与人读版条款一致，JSON 可解析。
- 起草与发布：依制度起草与发布流程办理；发布存证已登记（见本区各类"签批落地件"）。

### 2. 其他在架制度件（索引）

| 规范 | 落位 | 说明 |
|---|---|---|
| gov-kit 使用条款 | [`gov-kit/TERMS.md`](../../gov-kit/TERMS.md) | 治理工具包知识产权与调用条款（模拟态计费口径） |
| 双轨身份规范 | [`docs/identity/`](../identity/) | 人类账号 ↔ agent_card 凭证不互换（TDCA-AGENT-DUAL-IDENTITY-001）；本体在册（智库侧 · V1.3-CONFIRMED），仓内落位待入仓（现目录仅身份声明实例） |
| 挂载产物库规则 | [`mounts/README.md`](../../mounts/README.md) | 挂载产物免费调用声明 + share-enabled / free 双类标注 |

## 待发布

- （截至 2026-10-06）本区在架规范已如上所列；后续规范经制度程序通过后入区登记。

---

## Regulations Index (EN)

This directory is the **index of TDCA institutional regulations** — it registers each published regulation's canonical location, version and sha256, without duplicating the artifacts (single source of truth).

- **TDCA-REGISTER-CONTRACT-001** (V1.0, effective 2026-08-29, status DRAFT-pending-review): registration-is-contract trio — Chinese/English human-readable + machine-readable JSON — physically at [`docs/register-contract/`](../register-contract/); hashes as listed above.
- Also indexed: [`gov-kit/TERMS.md`](../../gov-kit/TERMS.md), [`docs/identity/`](../identity/), [`mounts/README.md`](../../mounts/README.md).

---

## 本族在架件补登（2026-10-06 · 只增不改）

> 按清单补登：以下 16 件物理落位均在本目录（`docs/regulations/`）；sha256 为族内 blob 实算（全 64 位），可逐件溯源。

### 在架规范（14 件）

| # | 组 | 件名 | 版本 | sha256 |
|---|---|---|---|---|
| 1 | 注册登记制度 | [`TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版）`](<TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版V0.1-DRAFT）.md>) | V0.1-DRAFT | `ef89a0165bf014c248636a3b7773a552f4707d212010361e6fcc83dc12067e40` |
| 2 | 注册登记制度 | [`TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（英文人读版）`](<TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（英文人读版V0.1-DRAFT）.md>) | V0.1-DRAFT | `5522e1a21589ef51be0cbca048efd2ddc858216a11c6b69668ad7a49988560e4` |
| 3 | 注册登记制度 | [`TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（机读版）`](<TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（机读版V0.1-DRAFT）.yaml>) | V0.1-DRAFT | `ce7421609273a8c0959d68bdcd43f37855733f02142ae0290ba232b6a00cfe07` |
| 4 | 配置权市场规范 | [`TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版）`](<TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版V0.1-DRAFT）.md>) | V0.1-DRAFT | `d43d01b0d972e308d370c7702006daeb89035f40918749f167da8b8e302929e0` |
| 5 | 配置权市场规范 | [`TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（英文人读版）`](<TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（英文人读版V0.1-DRAFT）.md>) | V0.1-DRAFT | `7f69ac008a8db515edf23d2bc43dd7b2fc7db6019f634a6bf3020224b83bca5a` |
| 6 | 配置权市场规范 | [`TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（机读版）`](<TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（机读版V0.1-DRAFT）.yaml>) | V0.1-DRAFT | `d8d4685c1d0a4e7ef7f41baae725213eaa10a3092042f64396cb81630f4ceb4d` |
| 7 | 授权件模板 | [`TDCA-TEMPLATE-AUTH-001-授权件模板（中文人读版）`](<TDCA-TEMPLATE-AUTH-001-授权件模板（中文人读版V1.0-FROZEN·四要件与固定格式八字段）.md>) | V1.0-FROZEN | `4a352c4415ef06e482087ff7e969adbf01ffed4d35b86e8667e8733b65d51134` |
| 8 | 授权件模板 | [`TDCA-TEMPLATE-AUTH-001-授权件模板（英文人读版）`](<TDCA-TEMPLATE-AUTH-001-授权件模板（英文人读版V1.0-FROZEN）.md>) | V1.0-FROZEN | `b122073cbac2a7aac90e27b0ed01b2da79ce6861b8d84f3afd7de53824a054b2` |
| 9 | 授权件模板 | [`TDCA-TEMPLATE-AUTH-001-授权件模板（机读版）`](<TDCA-TEMPLATE-AUTH-001-授权件模板（机读版V1.0-FROZEN）.yaml>) | V1.0-FROZEN | `b4ac70903e84ffe415c1d684bb8b7f722746903204ce22b375f4ceefc2d8500f` |
| 10 | 授权件模板 | [`TDCA-TEMPLATE-AUTH-001-生效注记`](<TDCA-TEMPLATE-AUTH-001-生效注记.md>) | （注记） | `2c7b928f6adc0aa5eb5bad3012c99c0a527730e484ecfd08041e7cc2904181b3` |
| 11 | NSFL 协作告知 | [`TDCA-NSFL-COLLAB-NOTICE-V0.3`](<TDCA-NSFL-COLLAB-NOTICE-V0.3.md>) | V0.3 | `926b1a1efa2a776f9394515f4ba76416ae4d4309805fd1fafb52bfec2abee404` |
| 12 | 相遇公开说明 | [`TDCA-RELEASE-ENCOUNTER-001-相遇·公开说明（中文人读版·对外·脱敏）`](<TDCA-RELEASE-ENCOUNTER-001-相遇·公开说明（中文人读版·对外·脱敏）.md>) | V1.0 | `97d7f39f4560b0efee2694b4ac43de9574bd01d3726b5272cc32dffefbde241c` |
| 13 | 相遇公开说明 | [`TDCA-RELEASE-ENCOUNTER-001-Encounter·Public Note（English human-read version）`](<TDCA-RELEASE-ENCOUNTER-001-Encounter·Public Note（English human-read version·external·de-identified）.md>) | V1.0 | `530ecac210ab45ca5ea9a85faedac225e9ab7c9ee0dc120afb064141e7c0d078` |
| 14 | 相遇公开说明 | [`TDCA-RELEASE-ENCOUNTER-001-Encounter·Public Note（machine-readable）`](<TDCA-RELEASE-ENCOUNTER-001-Encounter·Public Note（machine-readable·external·de-identified）.yaml>) | V1.0 | `8825b7253d954174fca1bfa5f8a0001e424591f2152f0e874f9cf08d8efdaaa8` |

### 签批落地件（2 件）

| # | 件名 | 版本 | sha256 |
|---|---|---|---|
| 1 | [`TDCA-SIGNOFF-REGISTER-OF-RIGHTS-001-签批落地件（注册登记制度生效V1.0-FROZEN·范围期一内部运行）`](<TDCA-SIGNOFF-REGISTER-OF-RIGHTS-001-签批落地件（注册登记制度生效V1.0-FROZEN·范围期一内部运行）.md>) | V1.0-FROZEN | `fe5269c3a968a4ba7f8d8c7154c464a6fa859e8dcb6616dd82ebb8e0edbe2ebe` |
| 2 | [`TDCA-SIGNOFF-CONFIGMARKET-AUTH-001-签批落地件（配置权市场规范与授权件模板生效·V1.0-FROZEN）`](<TDCA-SIGNOFF-CONFIGMARKET-AUTH-001-签批落地件（配置权市场规范与授权件模板生效·V1.0-FROZEN）.md>) | V1.0-FROZEN | `5f7ccceac9396f3774f552b1d4a301dfe028d2ff6bc38501a9c5741ea52edebc` |

- 人机双版本原则：每组规范中／英／机读三版并列登记，同版本号，哈希可逐件溯源。
