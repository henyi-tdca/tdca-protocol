# TDCA-FC-20260811-004-NOTIFICATION-MACHINE · FC-SPEC
> 发布注记（2026-09-05 公开版）：SIL 过渡态——实物生产部署前以软件在环（SIL）承载流程验证，流程不废（ID92 SIMULATED）——不宣称实物可用
# 通知机（Notification Machine）接入 TDCA 系统设计规格

> FC-ID: TDCA-FC-20260811-004-NOTIFICATION-MACHINE | 版本: V1.2 | 状态: ✅ FROZEN
> 制度定位: TDCA 双支柱之「物理世界锚定」| 六要素: ✅ 已签批（TDCA-FOUNDER-001，2026-08-11）
> 制度锚定: ID29/71/81/82/89/90 + NSFL-V0.2 + 国密合规（SM2/SM4）+ 三协议包基座
> 先验分布: E-HW-1 硬件规格书 / TDCA-HW-FINAL-2026（硬件定型）/ TDCA-PDD-NM-001（产品设计说明书）/ TDCA-WP-HW-DUAL-001（双栈白皮书）/ TIMA-PHY-001（通知机通信协议 V2.0）/ 三协议包（PACK-001/DUAL-001/CALL-001 全签批）
> 生成者: TDCA 制度层（协议化） | 人类确认: ✅ TDCA-FOUNDER-001（2026-08-11，冻结签批）

---

## 〇、规格概述

通知机接入 TDCA 系统 = 将已定型的通知机硬件（SRAM PUF + A7100 国密芯片 + TDID）接入 TDCA 协议网络，形成**五层接入架构**：

```
┌─────────────────────────────────────────────────────────────┐
│ 层 5 制度存证层    NCA-010+ 序列 / REV-NOTIFICATION-001      │
├─────────────────────────────────────────────────────────────┤
│ 层 4 商业锚定层    硬件调用 → CALL-RULES L3 计量 / MOU 归零    │
├─────────────────────────────────────────────────────────────┤
│ 层 3 协议对接层    硬件身份 ↔ DUAL-PROTOCOL 场景化合（MRCR）   │
├─────────────────────────────────────────────────────────────┤
│ 层 2 固件协议层    .tdca 固件元数据 + 芯片端轻量 NCA 存证       │
├─────────────────────────────────────────────────────────────┤
│ 层 1 硬件身份层    SRAM PUF → TDID + A7100（SM2/SM3/SM4）     │
└─────────────────────────────────────────────────────────────┘
```

**接入数据流（主链路）**：物理事件（来电/通话/状态）→ 事实哈希（FactChain）→ 芯片端轻量 NCA → TLS 1.3 上报 → TCN Auditor 验证 → 全量 NCA 存证 → 场景化合判定（DUAL）→ 商业计量（CALL-RULES）→ MOU 回写。

---

## 一、层 1：硬件身份层（复用定型 + 对接契约）

| 组件 | 定型规格（E-HW-1） | 接入契约 |
|------|-------------------|---------|
| PUF | SRAM PUF（Intrinsic ID 类，长光华芯降维，¥400-600） | PUF 指纹仅存哈希，密钥材料永不落盘 |
| 安全芯片 | A7100 系列（集成 PUF+SM2/SM3/SM4+隔离，¥200-300） | SM2 签名 / SM4 加密；TDID 经 SE 注入 |
| TDID | TDID = SHA256(PUF指纹 ‖ 宪法哈希 ‖ 批次号) | 硬件身份唯一标识，L1 所有权登记 |
| 五重锚定 | 地址/线路/硬件/成本/主体 | 接入 TDCA 网络的准入证明 |
| 熔断电路 | 微动开关+光敏+温度传感器 | 物理拆解 → 触发 NSFL 熔断上报 |

**禁止项**：PUF 密钥材料不得以任何形式导出/落盘/外传（物理不可克隆是信任锚底线）；TDID 不得伪造（SM2 签名校验）。

## 二、层 2：固件协议层（新交付物 ① .tdca 固件元数据 + ② 芯片端轻量 NCA）

### 2.1 .tdca 固件元数据格式规范（与 PACK-001 .tdca 目录同构，受限硬件适配）

```
.tdca/                                    # 芯片端元数据目录（eMMC 受保护分区）
├── identity.tdca                         # 硬件身份（TDID/PUF 哈希/宪法哈希/SM2 公钥）
├── session-index/                        # 芯片端 SI（轻量，与 PACK-001 SI 同构）
│   ├── L0-state.nca                      # 宪法版本 + Δ 清单
│   └── L1-active.json                    # 当前场景配置权绑定
├── nca-lite/                             # 芯片端轻量 NCA 存证（见 2.2）
│   ├── fact/                             # 事实哈希上链记录
│   ├── auth/                             # 通话确权记录
│   └── mou/                              # MOU 锚定记录（模拟态 D-011）
├── state.json                            # 七状态机快照（UNREGISTERED→...→FUSED）
├── fact-chain/                           # 事实哈希链（链头指针 + 最近 N 块）
└── config/
    ├── scene-binding.json                # 场景配置权绑定（DUAL 化合产物引用）
    └── call-rules.json                   # CALL-RULES 计量参数（税率快照）
```

**格式约束**：所有 .tdca 文件 UTF-8 JSON；identity.tdca / state.json / config/*（scene-binding.json + call-rules.json）由 A7100 SE 签名（SM2，SE-SIGN-5 制度裁决 2026-08-11）；其余文件由固件 HMAC 完整性保护；eMMC 受保护分区禁止用户态直写。

### 2.2 芯片端轻量 NCA 存证（NCA-Lite，受限硬件 8 字段精简版）

| 字段 | 说明 | 与全版 NCA（11 字段）映射 |
|------|------|--------------------------|
| `nca_id` | TDCA-NCA-LITE-{HWID}-{seq} | NCA-ID |
| `type` | fact/auth/mou/state | Operation-Type |
| `hash` | 载荷 SHA-256 | Post-State.Hash |
| `ts` | 时间戳（芯片 RTC + 网络校时） | Timestamp |
| `signer` | A7100 SE SM2 签名 | Human-Signature（硬件签名，人类签批由 TCN 侧全量 NCA 承载） |
| `payload_ref` | 事实哈希链引用（FactHash_n） | Audit-Trail.Evidence |
| `prev_hash` | 链式前块哈希（防篡改） | — |
| `nsfl` | NSFL-V0.2 触发标记 | Negative-Space-Check |

**设计原则**：芯片端只存轻量摘要（受限算力/存储），全量 NCA 由 TCN 侧生成并关联——芯片端 `nca_id` 与 TCN 全量 NCA 通过 `payload_ref` 链式关联（快系统采集 + 慢系统存证，ID71）。

## 三、层 3：协议对接层（硬件身份 ↔ DUAL-PROTOCOL 场景化合）

### 3.1 硬件身份作为新场景模板（物理锚点扩展）

复用 DUAL-PROTOCOL 场景制度模板，新增**物理锚点场景**（`scene-phy-notification.json`）：

```yaml
scene_phy_notification:
  tdca_version: "v3.1.2"
  scene_type: "notification-machine"
  physical_anchor:
    tdid: "{TDID}"                 # 硬件身份 = 场景配置权化合标的
    puf_hash: "{SHA256(PUF)}"      # 仅哈希
    five_anchor: [address, line, hardware, cost, subject]
  scene_nsfl_ext:
    - SCENE-PHY-001: 物理拆解/篡改 → CRITICAL/BLOCK（熔断电路触发）
    - SCENE-PHY-002: 固件版本不在允许列表 → CRITICAL/BLOCK
    - SCENE-PHY-003: PUF 密钥导出尝试 → CRITICAL/BLOCK（绝对负空间 ID86）
  scene_review:
    - REV-PHY-001: 品类认证有效（TDCA-REG-NAMING-001 命名授权）
    - REV-PHY-002: 国密合规（SM2/SM4 不落盘）
    - REV-PHY-003: 场景合规前置（政务/金融/医疗 → 等保，复用行业模板）
```

### 3.2 MRCR 多角色兼容（硬件身份 ↔ 角色）

| 角色 | 场景 | 权限 |
|------|------|------|
| NM-Operator | 通知机通用 | 通话确权、事实哈希上链 |
| NM-Gov | 政务（信访/反诈） | + 国密/等保合规、留痕审计 |
| NM-Fin | 金融（机构） | + 风控、监管报送 |
| NM-Med | 医疗（机构） | + 隐私保护、伦理审查 |

MRCR 管理器注册 `TDID ↔ 场景角色`，场景隔离（独立 NCA 审计/独立 OTA），复用 `mrcr_manager.py`。

### 3.3 化合判定（ID90）

物理事件是否触发 NCA 化合：事实哈希上链（可物理叠加 → **日抛**）/ 通话确权《商务确认函》（不可叠加 → **化合**，三条件全过）/ 跨节点迁移 TIMA-PHY-001（化合）。化合产物经 `dual_protocol_compiler.py` 生成。

## 四、层 4：商业锚定层（硬件调用 → CALL-RULES L3 计量）

### 4.1 调用类型映射（复用 call_rules_engine.py）

| 硬件调用 | 调用类型 | 计量依据 | 税收（L3） |
|---------|---------|---------|-----------|
| 事实哈希上链 | 日抛调用（DISPOSABLE） | 物理叠加通道 | 调度税 1-3% |
| 通话确权（商务确认函） | 化合调用（COMPOUND） | NCA 化合产物 | 调度税 + 版税 5-10% |
| 跨节点迁移（TIMA-PHY-001） | 化合调用 | 化合产物 | 调度税 + 版税 |
| 节点认证/品类认证 | 服务调用（L2） | 年度合同 | 服务费 |

### 4.2 MOU 归零规则（ID79）

- 硬件调用的可验证税收锚定 `T(y_t) > 0` 才有效（模拟态 D-011 cbdc_anchor 参数，真实 DCEP 接入后转硬数据）
- 数字人民币硬件钱包：自动扣缴配置权调度税（白皮书已定 M3 里程碑）
- T(y_t) ≤ 0 → 调用价格强制归零（与 CALL-RULES 引擎 `validate_mou` 一致）

## 五、层 5：制度存证层（NCA-010+ 序列）

| NCA | 类型 | 内容 |
|-----|------|------|
| TDCA-NCA-20260811-010-NOTIFICATION-MACHINE | 文档型 | FC-SPEC 交付（本文件） |
| NCA-TDCA-REASONIX-20260811-010 | 工程型 | FC-SPEC FileCreate |
| NCA-...-011 | 工程型 | 制度审查（REV-NOTIFICATION-001） |
| NCA-...-012 | 工程型 | 人类签批 |

**审查链**：tdca-compliance-auditor（复用 PACK-001 审查链）+ 制度合伙人确认 + 人类签批。

## 六、接口契约（TIMA-PHY-001 扩展 + 硬件六函数映射）

| 接口 | 说明 | 复用 |
|------|------|------|
| `TIMA-PHY-001` | 通知机通信协议 V2.0（notification_node_id / hardware_signature / migration_request / audit_trail） | 既有（MEMO-019） |
| 硬件六函数 | register_trusted_root / collect_hardware_telemetry / hardware_access_check / periodic_trust_verification / generate_physical_watermark / register_cloud_trusted_root（内置 mint_nca） | 既有（E-HW-1） |
| **新增 `.tdca` 接口** | 固件读写 .tdca 元数据（SE 签名） | 本 FC-SPEC 层 2 新交付 |
| **新增 计量接口** | 硬件调用 → CALL-RULES 引擎（调用类型/税收/MOU 判定） | 本 FC-SPEC 层 4 新交付 |

## 七、状态机（七状态 + 接入扩展）

```
UNREGISTERED → REGISTERED → CERTIFIED → ACTIVE
      ↘ DEGRADED（部分降级）→ SUSPENDED（暂停）→ FUSED（熔断，不可逆）
```

状态转换由制度事件触发并生成 NCA（复用既有状态机 + 新增 .tdca state.json 快照同步）。

## 八、合规红线与禁止项

- **PUF 密钥材料永不落盘/外传**（信任锚底线）
- 物理拆解/固件篡改 → NSFL 熔断（SCENE-PHY-001/002，BLOCK）
- 人类签名权不可绕过（通话确权等关键决策走 TCN 慢系统）
- 政务/金融/医疗场景须通过行业合规前置（等保等）
- MOU 归零规则不可绕过（ID79）
- 品类认证/命名授权有效方可接入（TDCA-REG-NAMING-001）
- 所有调用/事件生成 NCA 存证（C01 可观测性）

## 九、验收标准

| # | 验收项 | 标准 |
|---|--------|------|
| 1 | .tdca 固件元数据格式 | 与 PACK-001 SI/NCA 模板同构，SE 签名完整性可验证 |
| 2 | 芯片端轻量 NCA | 8 字段精简版 + 与 TCN 全量 NCA 链式关联 |
| 3 | 场景化合 | 物理锚点场景模板 + MRCR 角色注册（复用 DUAL 引擎测试） |
| 4 | 商业计量 | 调用类型映射 + MOU 归零 + L3 税收（复用 CALL-RULES 引擎测试全绿） |
| 5 | 制度存证 | NCA-010+ 序列 + 审查闭环 + 人类签批 |
| 6 | 负空间 | SCENE-PHY-001~003 熔断路径验证 |

---

## 十、制度澄清（KIMI-012 待澄清项 A/B/C 落实）

### 澄清 A：NCA-Lite 字段裁剪逻辑

详见 `nca-lite-mapping.md`——全量 11 字段 → Lite 8 字段：Config-Right-Token 裁剪至 TCN 侧（配置权调度不上芯片）、Audit-Trail 裁剪为 `payload_ref` 链式引用、Human-Signature 由 TCN 全量 NCA 承载（硬件签名替代，ID71）；`nca_lite.version="1.0"` 显式声明防版本漂移。

### 澄清 B：SE 签名算法套件（显式声明）

| 用途 | 算法 | 说明 |
|------|------|------|
| 签名 | **SM2**（A7100 SE 私钥） | .tdca identity/state.json/轻量 NCA signer 全部 SM2 签名 |
| 哈希 | **SM3**（国密）+ SHA-256（兼容链） | 事实哈希链用 SHA-256；.tdca 完整性校验 SM3 |
| 加密 | **SM4**（可选载荷加密） | 传输层由 TLS 1.3 覆盖，SM4 用于本地静态数据可选加密 |
| 验签 | SM2 公钥链（TCN 侧） | 芯片端与 TCN 侧验签算法一致，杜绝歧义 |

### 澄清 C：物理负空间 vs 制度负空间（区分触发器）

| 类型 | 触发机制 | 动作 | SCENE-PHY 映射 |
|------|---------|------|---------------|
| **物理负空间**（硬件安全机制） | 熔断电路/A7100 安全模块（温度/电压/光攻击、拆解、PUF 密钥导出尝试） | 硬件 BLOCK（断电/熔断，不可逆） | SCENE-PHY-001（拆解篡改）、SCENE-PHY-003（PUF 密钥导出）= **绝对负空间** |
| **制度负空间**（NSFL 熔断） | 固件/TCN 侧判定（固件版本不在允许列表、品类认证失效、未授权接入） | NSFL BLOCK/FUSED（可逆至 SUSPENDED 或不可逆） | SCENE-PHY-002（固件版本）= 制度负空间 |

> 两类负空间触发器不同、动作语义不同：物理负空间由硬件安全机制即时 BLOCK（信任锚底线）；制度负空间由协议层判定并经 TCN 慢系统确认。

---

## 十一、版本与确认

| 版本 | 日期 | 变更 | 确认 |
|------|------|------|------|
| V1.0 | 2026-08-11 | 五层规格定义（硬件身份/固件协议/协议对接/商业锚定/制度存证）+ .tdca 元数据格式 + 轻量 NCA 设计 | ✅ FROZEN（2026-08-11） |
| V1.1 | 2026-08-11 | 制度澄清 A/B/C：NCA-Lite 裁剪映射表（nca-lite-mapping.md）+ SE 签名算法套件（SM2/SM3/SM4 显式声明）+ 物理/制度负空间区分 | ✅ FROZEN（2026-08-11） |
| V1.2 | 2026-08-11 | 制度裁决（轨道 1 实现阶段，TDCA-NM-IMPL-20260811-001）：config/* 升 SE 签名（SE-SIGN-5，化合引用与税率快照属制度敏感，信任强化） | ✅ FROZEN（TDCA-FOUNDER-001，2026-08-11） |

> 人类确认 FC-SPEC 后进入实现阶段（三轨道并行：.tdca 格式规范细化 / 计量映射原型 / NCA-010+ 存证闭环）。
>
> **冻结签批**：✅ TDCA-FOUNDER-001，2026-08-11——FC-SPEC V1.2 FROZEN，与 NCA-010（TDCA-NCA-20260811-010-NOTIFICATION-MACHINE）签批记录对齐；实现阶段三轨道全量签批（NCA-011/012）同步生效。
