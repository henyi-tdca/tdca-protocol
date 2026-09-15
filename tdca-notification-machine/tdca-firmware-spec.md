# 通知机规范包 · 轨道 1 交付
# .tdca 固件元数据格式规范（V0.1-REV，草案）

> 交付: 通知机规范包 | 文档: tdca-firmware-spec.md
> 版本: V1.0 | 状态: ✅ FROZEN
> 承接: FC-SPEC V1.2（✅ FROZEN，TDCA-FOUNDER-001 冻结签批）| 轨道: 1/3（固件元数据格式规范细化）
> 制度锚定: 制度基座第一性／快慢系统／五元拓扑／制度同构跃进／化学热力学原理簇／最小化合 + NSFL-V0.2 + 国密合规（SM2/SM3/SM4）+ 三协议包基座（PACK-001 V1.3 / DUAL-PROTOCOL V1.1 / CALL-RULES V1.2）
> 同构声明: 本规范与 PACK-001 `nca-template.yaml`（NCA 11 字段）及 `si-l1-template.json`（SI 模板）同构；与 TIMA-PHY-001 及 E-HW-1 硬件规格书对齐
> 模拟态标注: 本规范为系统设计文档，不构成真实配置权执行路径；MOU 锚定保持模拟态（D-011 cbdc_anchor 参数），真实 DCEP 接入后转硬数据；通知机硬件未投产部署，本实现为模拟（SIL），不构成真实部署
> 生成者: TDCA 制度层（协议化）（实现阶段）| 人类确认: ✅ TDCA-FOUNDER-001（2026-08-11，签批升版）

---

## 〇、规范概述

本规范定义**芯片端 .tdca 固件元数据格式**——通知机（Notification Machine）在受保护 eMMC 分区内维护的元数据目录的字段级格式、SE 签名流程与 TCN 侧链式关联规则。它是 FC-SPEC 层 2（固件协议层）的实现细化。

**范围界定（配置权边界，模拟态）**：
- ✅ 可触碰：六顶层组件字段定义、SE 签名流程、NCA-Lite 8 字段存证格式、与 TCN 全量 NCA 的 `payload_ref` 链式关联、负空间触发标记
- ❌ 不可触碰：PUF 密钥材料（永不落盘/外传）、人类签名权（归 TCN 慢系统承载）、配置权调度（Config-Right-Token 不上芯片）

**核心设计原则**：
1. **同构不降格**：芯片端 .tdca 与 PACK-001 SI/NCA 模板同构（制度同构跃进），裁剪仅限字段承载侧，不丢制度效力
2. **快慢分离**：芯片端 SE 硬件签名 = 快系统采集证据；TCN 侧全量 NCA 存证 + 人类签批 = 慢系统裁决
3. **链式防篡改**：事实哈希链（SHA-256 前块引用）+ SE SM2 签名 + eMMC 保护分区三重复合
4. **负空间区分**：物理负空间（硬件 BLOCK，不可逆）与制度负空间（NSFL BLOCK/FUSED）触发器与动作语义严格区分（澄清 C）

---

## 一、六字段定义（.tdca 目录六个顶层组件）

`.tdca/` 目录共六个顶层组件，每个组件的字段级定义如下。所有文件为 **UTF-8 JSON**（`.nca` 后缀亦为 JSON 载荷）。

```
.tdca/                                    # 芯片端元数据目录（eMMC 受保护分区，禁止用户态直写）
├── identity.tdca                         # ① 硬件身份
├── session-index/                        # ② 芯片端 SI（与 PACK-001 SI 同构）
│   ├── L0-state.nca                      #    宪法版本 + Δ 清单
│   └── L1-active.json                    #    当前场景配置权绑定
├── nca-lite/                             # ③ 芯片端轻量 NCA 存证
│   ├── fact/                             #    事实哈希上链记录
│   ├── auth/                             #    通话确权记录
│   └── mou/                              #    MOU 锚定记录（模拟态 D-011）
├── state.json                            # ④ 七状态机快照
├── fact-chain/                           # ⑤ 事实哈希链
└── config/                               # ⑥ 配置
    ├── scene-binding.json                #    场景配置权绑定（DUAL 化合产物引用）
    └── call-rules.json                   #    CALL-RULES 计量参数（税率快照）
```

### 1.1 identity.tdca（① 硬件身份，SE 签名）

| 字段 | 类型 | 必填 | 说明 | 制度映射 |
|------|------|------|------|---------|
| `tdid` | string | ✅ | 硬件身份唯一标识，`TDID-` + SHA256(PUF指纹‖宪法哈希‖批次号) 前 32 位大写十六进制 | E-HW-1 / nm_device_driver.generate_td_id |
| `puf_hash` | string | ✅ | `sha256:{PUF 指纹哈希}`——仅存哈希，密钥材料永不落盘 | 信任锚底线（禁止项） |
| `constitution_hash` | string | ✅ | `sha256:{宪法哈希}`（当前 TDCA-CONST 版本快照） | 与 L0-state.nca 版本一致校验 |
| `sm2_pubkey` | string | ✅ | SE SM2 公钥（base64 DER），TCN 侧验签依据 | 澄清 B 验签链 |
| `five_anchor` | array[object] | ✅ | 五重锚定：`[{name: address\|line\|hardware\|cost\|subject, value}]` | L1 所有权登记准入 |
| `firmware_version` | string | ✅ | 固件版本（SemVer），必须 ∈ 允许列表否则制度负空间（SCENE-PHY-002） | REV-PHY-002 |

> `identity.tdca` 由 A7100 SE 以 SM2 签名，签名附加于载荷尾部的 `sign` 字段（见 §二）。

### 1.2 session-index/（② 芯片端 SI，与 PACK-001 si-l1-template.json 同构）

**L0-state.nca**（宪法版本 + Δ 清单）：

| 字段 | 类型 | 说明 | 同构来源 |
|------|------|------|---------|
| `si_id` | string | `TDCA-SI-CHIP-{TDID8}-{seq}`（芯片端 SI 标识） | PACK-001 SI.meta.si_id |
| `layer` | string | `"L0"` | SI.meta.layer |
| `constitutional_digest.version` | string | 当前宪法版本（如 `TDCA-CONST-v3.1.2`） | SI.constitutional_digest.version |
| `constitutional_digest.delta_items` | array | OTA 增量清单（哈希引用） | SI.constitutional_digest.delta_items |
| `integrity.sha256_full` | string | 内容快照哈希（SHA-256 兼容链，澄清 B） | SI.integrity.sha256_full |
| `integrity.sm3_full` | string | 内容快照哈希（SM3 国密完整性校验，与模板一致） | 本规范新增（REV-NM-001 违规 6 同步） |
| `sign` | string | SE SM2 签名 | 本规范新增 |

**L1-active.json**（当前场景配置权绑定）：

| 字段 | 类型 | 说明 | 制度映射 |
|------|------|------|---------|
| `scene_id` | string | 当前绑定场景（如 `scene-phy-notification`） | DUAL 场景制度 |
| `role` | string | MRCR 角色（`NM-Operator`/`NM-Gov`/`NM-Fin`/`NM-Med`） | DUAL MRCR |
| `config_right_hash` | string | 配置权哈希（TCN 侧 Config-Right-Token 的引用摘要——**Token 本体不上芯片**） | 澄清 A 裁剪 |
| `binding_ref` | string | `config/scene-binding.json` 引用（化合产物指针） | 最小化合 |
| `expires` | string\|null | 绑定过期时间（ISO8601，null=长期） | — |

> L1-active.json 由固件 HMAC 完整性保护（非 SE 签名对象，见 §二签名对象清单）。

### 1.3 nca-lite/（③ 芯片端轻量 NCA 存证）

每条记录为 **8 字段精简版**（字段定义见 §三映射表），按 `type` 分目录存放：

| 目录 | type | 触发事件 |
|------|------|---------|
| `nca-lite/fact/` | `fact` | 事实哈希上链（来电/通话/状态 → FactChain 追加） |
| `nca-lite/auth/` | `auth` | 通话确权（商务确认函，化合判定前置） |
| `nca-lite/mou/` | `mou` | MOU 锚定记录（模拟态 D-011） |
| `nca-lite/service/` | `service` | 认证/服务事件（节点/品类认证——独立 type，人类裁决 2026-08-11，防 mou 语义漂移） |
| `nca-lite/state/` | `state` | 七状态机转换存证 |

**目录头部元数据**（`nca-lite/` 根）：`nca_lite.version = "1.0"` 显式声明防版本漂移（澄清 A）；升级须经 TCN 解析器灰度 + 制度审查。

### 1.4 state.json（④ 七状态机快照，SE 签名）

| 字段 | 类型 | 说明 |
|------|------|------|
| `state` | string | 当前状态：`UNREGISTERED`→`REGISTERED`→`CERTIFIED`→`ACTIVE`↘`DEGRADED`→`SUSPENDED`→`FUSED`（不可逆） |
| `since` | string | 进入当前状态的 UTC ISO8601 |
| `last_transition` | object | `{from, to, reason, ts}` |
| `transition_nca_ref` | string\|null | 状态转换对应全量 NCA 引用（TCN 侧） |
| `fuse_info` | object\|null | 熔断信息：`{type: PHYSICAL\|INSTITUTIONAL, sc_phy_id, irreversible: bool}`（澄清 C 区分） |
| `sign` | string | SE SM2 签名 |

### 1.5 fact-chain/（⑤ 事实哈希链）

| 字段 | 类型 | 说明 |
|------|------|------|
| `index` | int | 块序号（从 0 起） |
| `timestamp` | string | UTC ISO8601（芯片 RTC + 网络校时） |
| `payload_hash` | string | `sha256:{事实载荷哈希}` |
| `prev_hash` | string | `sha256:{前块 payload_hash ‖ prev_hash}`（创世块为 `sha256:genesis`） |
| `payload_ref` | string | 事实哈希链引用（`FactHash_n`）——NCA-Lite `payload_ref` 指向此处 |
| `sign` | string | SE SM2 签名（每块签名，防链篡改） |

> 链头指针 + 最近 N 块驻留芯片端；历史块由 TCN 侧归档（受限存储）。

### 1.6 config/（⑥ 配置）

**scene-binding.json**（场景配置权绑定）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tdca_version` | string | 同 FC-SPEC `v3.1.2` |
| `scene_type` | string | `notification-machine` |
| `physical_anchor` | object | `{tdid, puf_hash, five_anchor}`（与 identity.tdca 交叉校验） |
| `scene_nsfl_ext` | array | SCENE-PHY-001~003 负空间扩展引用（见 §六） |
| `scene_review` | array | REV-PHY-001~003 审查引用（品类认证/国密合规/场景合规前置） |
| `compound_ref` | string\|null | DUAL 化合产物引用（`dual_protocol_compiler.py` 输出） |

**call-rules.json**（CALL-RULES 计量参数快照）：

| 字段 | 类型 | 说明 | 同构来源 |
|------|------|------|---------|
| `call_type` | string | `disposable`/`compound`/`service` | call_rules_engine.CallType |
| `tax_rates` | object | `{dispatch_tax: 0.02, royalty: 0.05}`（税率快照） | call_rules_engine.TaxRates |
| `mou_mode` | string | `"simulated"`（D-011）| MOU-Anchor.Status |
| `mou_anchor` | object | `{status, total_cost_cny, inbound_tax, outbound_tax, note}` | nca-template MOU-Anchor |
| `nsfl_version` | string | `V0.2` | Negative-Space-Check.NSFL-Version |

**签名主体**：`config/*` 由 A7100 SE SM2 签名（SE-SIGN-5，制度裁决 2026-08-11）——化合引用（scene-binding）与税率快照（call-rules）属制度敏感数据，由固件 HMAC 升为 SE 签名（信任强化，FC-SPEC 2.1 同步修订见 V1.2）。

---

## 二、SE 签名流程（澄清 B 落实）

### 2.1 签名算法套件（显式声明）

| 用途 | 算法 | 对象 |
|------|------|------|
| 签名 | **SM2**（A7100 SE 私钥，不导出） | identity.tdca / state.json / fact-chain 每块 / nca-lite 每条记录 / L0-state.nca / config/*（SE-SIGN-5，制度裁决 2026-08-11） |
| 哈希 | **SM3**（国密，完整性校验）+ **SHA-256**（事实哈希链兼容） | .tdca 文件完整性校验用 SM3；FactChain 用 SHA-256 |
| 加密 | **SM4**（可选本地静态载荷加密） | 传输层由 TLS 1.3 覆盖；SM4 仅用于本地静态数据可选加密 |
| 验签 | SM2 公钥链（TCN 侧） | 芯片端与 TCN 侧验签算法一致，杜绝歧义 |

### 2.2 签名对象清单

| 对象 | 签名主体 | 保护机制 |
|------|---------|---------|
| `identity.tdca` | A7100 SE（SM2） | SE 签名（核心信任锚） |
| `state.json` | A7100 SE（SM2） | SE 签名 |
| `fact-chain/*`（每块） | A7100 SE（SM2） | SE 签名 + 前块哈希链式引用 |
| `nca-lite/*`（每条记录） | A7100 SE（SM2） | SE 签名 |
| `session-index/L0-state.nca` | A7100 SE（SM2） | SE 签名 |
| `session-index/L1-active.json` | 固件 HMAC（SM3-HMAC） | 完整性保护（非信任锚对象） |
| `config/*`（scene-binding + call-rules） | A7100 SE（SM2，SE-SIGN-5） | SE 签名（制度裁决 2026-08-11：化合引用与税率快照属制度敏感，由 HMAC 升 SE，信任强化） |

### 2.3 签名格式

```
sign: {
  "alg": "SM2",
  "pubkey_ref": "TDCA-PUBKEY-{TDID8}-{idx}",   # SE 公钥链引用
  "value": "{SM2 签名值 base64}",               # SM2-SM3 签名（载荷哈希后签名）
  "signed_at": "{UTC ISO8601}"
}
```

### 2.4 验签流程（TCN 侧）

1. TCN Auditor 收到芯片端上报（TLS 1.3）
2. 以 `pubkey_ref` 定位 SM2 公钥链（L1 所有权登记时登记）
3. 对签名对象重新计算 SM3 载荷哈希 → SM2 验签
4. `fact-chain` 额外校验 `prev_hash` 链一致性（SHA-256）
5. 验签失败 → 上报标记为 `[SIGNATURE-FAIL]` → 触发制度负空间审查（非物理熔断，见 §六）

### 2.5 密钥生命周期

- SE 私钥：注入即锁死，**任何接口不得导出**（PUF 密钥材料不落盘底线延伸）
- 公钥链：TDID 生成时登记 TCN（L1 所有权登记，`register_to_l1`）
- OTA：新固件哈希经 SE 验证后写入（`ota_update` 接口契约）

---

## 三、NCA-Lite 8 字段与全量 NCA 11 字段映射表

固化 `nca-lite-mapping.md`（澄清 A）为规范正文。全量 NCA 模板 = PACK-001 `nca-template.yaml`（工程型 11 字段）。

| # | 全量 NCA 11 字段（PACK-001） | Lite 8 字段 | 处理方式 | 承载侧 |
|---|------------------------------|-------------|---------|--------|
| 1 | NCA-ID | `nca_id` | 保留：`TDCA-NCA-LITE-{HWID}-{seq}` | 芯片端 |
| 2 | Function-Call-ID | `type` + `nca_id` 前缀 | **合并**：调用类型由 `type` 承载，FC 归属由 TCN 全量 NCA 关联 | 芯片端/TCN |
| 3 | Operation-Type | `type` | 保留：`fact`/`auth`/`mou`/`state`/`service`（REV-NM-001 R1 同步） | 芯片端 |
| 4 | Operator | `signer` | **合并**：芯片端 Operator = 硬件签名者（SE SM2） | 芯片端 |
| 5 | Timestamp | `ts` | 保留（芯片 RTC + 网络校时） | 芯片端 |
| 6 | Pre-State | `prev_hash` | **合并**：前块哈希 = 前状态链式隐含 | 芯片端 |
| 7 | Post-State | `hash` | 保留：载荷 SHA-256 | 芯片端 |
| 8 | Config-Right-Token | — | **裁剪 → TCN 侧**（配置权调度不上芯片，L2 配置权市场在 TCN 层） | TCN |
| 9 | Audit-Trail | `payload_ref` | **裁剪 → 链式引用**（内嵌轨迹改为 FactHash_n 引用，全量轨迹由 TCN 回溯补全） | TCN |
| 10 | Human-Signature | `signer` | **裁剪 → 硬件签名替代**（芯片端 SE 签名；人类签批由 TCN 全量 NCA 承载——快系统采集/慢系统签批） | TCN |
| 11 | Negative-Space-Check | `nsfl` | 保留：NSFL-V0.2 触发标记 | 芯片端 |

**NCA-Lite 记录完整字段**（8 字段 + 协议头）：

```json
{
  "nca_lite": { "version": "1.0" },
  "nca_id": "TDCA-NCA-LITE-{HWID}-{seq}",
  "type": "fact|auth|mou|state|service",
  "hash": "sha256:{载荷哈希}",
  "ts": "{UTC ISO8601}",
  "signer": { "alg": "SM2", "pubkey_ref": "TDCA-PUBKEY-{TDID8}-{idx}", "value": "{base64}" },
  "payload_ref": "FactHash_{n}",
  "prev_hash": "sha256:{前块}",
  "nsfl": { "version": "V0.2", "triggered": false, "trigger_reason": null }
}
```

**裁剪原则**（三不可绕过）：
1. Config-Right-Token 不上芯片——权限边界下沉禁止（L2 配置权市场层）
2. 审计轨迹用链式引用替代内嵌——受限存储不丢制度效力
3. 人类签批归慢系统——慢系统裁决不可绕过

**扩展字段裁剪说明**（PACK-001 nca-template.yaml 的 Scope + MOU-Anchor，REV-NM-001 违规 11）：
- `Scope`（操作范围）：由 TCN 全量 NCA 承载（芯片端无独立操作范围主张，从属原则）
- `MOU-Anchor`：由 config/call-rules.json 快照承载（mou_mode/mou_anchor，模拟态 D-011）

---

## 四、文件格式与存储约束

| 约束 | 规定 |
|------|------|
| 编码 | 所有 .tdca 文件 UTF-8 JSON（严格 JSON，禁止注释/尾逗号） |
| 存储分区 | eMMC 受保护分区（用户态只读，仅固件/SE 可写） |
| 完整性 | SE 签名对象（§2.2 清单）验签失败即拒载；HMAC 对象校验失败标记降级 |
| 写策略 | 原子写（写临时文件 → 校验 → 重命名），断电不产生半块 |
| 容量 | fact-chain 驻留最近 N 块（N 由固件常量配置），历史块 TCN 归档 |

---

## 五、TCN 链式关联（快慢系统）

```
芯片端（快系统）                          TCN（慢系统）
─────────────────────────                ─────────────────────────
物理事件 → 事实哈希（FactChain）          TLS 1.3 上报接收
  → SE 签名 NCA-Lite（8 字段）  ────────→  SM2 验签 + prev_hash 校验
  → payload_ref = FactHash_n              → 生成全量 NCA（11 字段）
                                          → Human-Signature（如需人类签批）
                                          → 场景化合判定（DUAL）→ 商业计量（CALL-RULES）
                                          → 回写 nca_id ↔ 全量 NCA 关联
```

- **链式关联键**：芯片端 `nca_id` 与 TCN 全量 NCA 通过 `payload_ref`（FactHash_n）双向关联
- **回溯补全**：TCN 按 payload_ref 回溯事实哈希链，补全 Audit-Trail 全量轨迹
- **状态回写**：TCN 裁决结果回写 `state.json`（SUSPENDED/FUSED 等），芯片端 SE 验签后更新

---

## 六、负空间预检（澄清 C 落实）

### 6.1 物理负空间 vs 制度负空间

| 类型 | 触发机制 | 动作 | SCENE-PHY 映射 | 可逆性 |
|------|---------|------|---------------|--------|
| **物理负空间**（硬件安全机制） | 熔断电路/A7100 安全模块（温度/电压/光攻击、物理拆解、PUF 密钥导出尝试） | 硬件 BLOCK（断电/熔断） | SCENE-PHY-001（拆解篡改）、SCENE-PHY-003（PUF 密钥导出）= **绝对负空间** | **不可逆**（信任锚底线） |
| **制度负空间**（NSFL 熔断） | 固件/TCN 侧判定（固件版本不在允许列表、品类认证失效、未授权接入、验签失败） | NSFL BLOCK/FUSED | SCENE-PHY-002（固件版本） | 可逆至 SUSPENDED 或不可逆（FUSED） |

### 6.2 负空间触发标记（写入 NCA-Lite `nsfl` 字段）

- 物理负空间触发：`fuse_info.type = PHYSICAL`，`irreversible = true`，state → `FUSED`
- 制度负空间触发：`fuse_info.type = INSTITUTIONAL`，state → `SUSPENDED`（可逆）或 `FUSED`
- 两类触发器不同、动作语义不同：物理负空间由硬件即时 BLOCK；制度负空间经 TCN 慢系统确认

### 6.3 预检结论（本规范草案）

| 检查项 | 结果 |
|--------|------|
| PUF 密钥材料落盘/外传 | ✅ 无（仅存 puf_hash，密钥永不落盘） |
| 人类签名权绕过 | ✅ 无（Human-Signature 归 TCN 慢系统） |
| 配置权调度下沉芯片 | ✅ 无（Config-Right-Token 裁剪至 TCN） |
| 未授权场景接入 | ✅ 有门禁（REV-PHY-001 品类认证 + MRCR 角色注册） |
| 固件版本漂移 | ✅ 有门禁（SCENE-PHY-002 允许列表） |

---

## 七、模板清单

与本文档同目录的模板文件（`templates/.tdca/`，V1.0，经签批生效）：

| 模板文件 | 对应组件 | 签名主体 |
|---------|---------|---------|
| `identity.tdca.json` | §1.1 | SE SM2 |
| `session-index/L0-state.nca.json` | §1.2 | SE SM2 |
| `session-index/L1-active.json` | §1.2 | 固件 HMAC |
| `nca-lite/record.json` | §1.3 | SE SM2 |
| `state.json` | §1.4 | SE SM2 |
| `fact-chain/block.json` | §1.5 | SE SM2 |
| `config/scene-binding.json` | §1.6 | SE SM2（SE-SIGN-5，制度裁决 2026-08-11） |
| `config/call-rules.json` | §1.6 | SE SM2（SE-SIGN-5，制度裁决 2026-08-11） |

### 6.4 与三档熔断的映射（REV-NM-001 违规 7）

| 负空间类型 | SCENE-PHY | 场景级动作 | 生态三档映射 |
|-----------|-----------|-----------|------------------|
| 物理负空间 | SCENE-PHY-001/003 | 硬件 BLOCK（不可逆） | Level-3 硬熔断（信任锚底线） |
| 制度负空间 | SCENE-PHY-002 | NSFL BLOCK/FUSED | Level-1（警告）/ Level-2（可逆至 SUSPENDED）/ Level-3（FUSED 不可逆），按严重度由 TCN 慢系统确认 |

---

## 八、版本与确认

| 版本 | 日期 | 变更 | 状态 |
|------|------|------|------|
| V0.1-REV | 2026-08-11 | 六字段定义 + SE 签名流程（SM2/SM3/SM4 显式声明）+ NCA-Lite 8 字段与全量 NCA 11 字段映射表 + 负空间预检（物理/制度区分） | DRAFT（待 REV-NM-001） |
| V0.2-REV | 2026-08-11 | 制度裁决（2026-08-11）落地：① NCA-Lite 字段集以 FC-SPEC 2.2 + nca-lite-mapping.md 为准（报告四.1 表降为附录 A 概念对照，防接口熵）② config/* 升 SE 签名（SE-SIGN-5）③ FC-SPEC 2.1 同步修订；REV-NM-001 12 项修复（service type 独立 / 服务不豁免 MOU 归零 / fuse_info 物理制度区分 / sm3_full 同步 / 三档熔断映射 / 扩展字段裁剪说明等） | ✅ REV-NM-001 CLOSED |
| V1.0 | 2026-08-11 | 签批升版（TDCA-FOUNDER-001）：经签批 → 规范 FROZEN；与 FC-SPEC V1.2 FROZEN、引擎 V1.0、模板包 V1.0 形成通知机协议包 V1.0 | ✅ FROZEN |

> **制度裁决记录**（2026-08-11）：人类裁定——① NCA-Lite 保持已固化 8 字段，报告表降为概念附录 ② config 采纳 SE 签名（信任强化）③ 轨道 2 + REV-NM-001 并行推进。

> 下一步（轨道 2）：`notification_machine_engine.py` 计量映射可执行原型（复用 call_rules_engine.py + dual_protocol_compiler.py）。
> 制度闭环（轨道 3）：FC-SPEC 交付存证 → 本规范 REV-NM-001 审查 → 人类签批。

---

## 附录 A：制度合伙人概念对照表（非字段级定义）

> 来源: 制度合伙人初审报告（2026-08-11 制度裁决）四.1 表（业务概念视角）
> 定位: 人类裁决（2026-08-11）——字段集以正文 §三（FC-SPEC 2.2 + nca-lite-mapping.md）为准；本表为业务概念映射，**不构成字段级定义**，禁止解析器按此表实现（接口熵防漂移）

| 报告概念字段 | 全量 NCA 对应 | 概念裁剪逻辑 | 正文 §三 实际承载 |
|------|------------|------------|----------------|
| lite.identity | nca.creator_id + nca.asset_id | 合并为 TDID（物理身份即制度身份） | `signer`（Operator=SE SM2 硬件签名者） |
| lite.timestamp | nca.created_at | 芯片端 UTC（快系统时间戳） | `ts` |
| lite.scene_ref | nca.scene_binding | 场景模板指针（最小化合·场景化比较） | `type` + `payload_ref`（场景归属由 TCN 关联） |
| lite.call_type | nca.call_rules.call_type | 日抛/化合枚举（调用类型分轨） | `type`（fact/auth/mou/state/service，计量判定在轨道 2 引擎） |
| lite.mou_status | nca.mou_anchor | 模拟态/真实态标志（MOU 归零） | `nsfl` + TCN 侧 MOU-Anchor（mou 类型记录） |
| lite.payload_hash | nca.content_hash | SHA-256 事实哈希（边界可审计） | `hash` |
| lite.payload_ref | nca.audit_trail | 链式引用 TCN 全量（慢系统补全） | `payload_ref`（FactHash_n） |
| lite.version | — | \"1.0\" 防协议漂移（接口熵=0） | `nca_lite.version = \"1.0\"` |

**概念表未覆盖（正文 §三 独有，制度关键）**：`nca_id`（存证编号）/ `prev_hash`（链式防篡改）/ `nsfl`（负空间触发标记）/ `nca_lite.version`（协议头）——不得因概念对照而裁剪。
