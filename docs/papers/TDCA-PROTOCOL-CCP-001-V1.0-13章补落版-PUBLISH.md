# TDCA-PROTOCOL-CCP-001 · 配置权调用协议规范 V1.0（13 章补落版）

> 文档编号: TDCA-PROTOCOL-CCP-001 | 版本: **V1.0-REV2（FROZEN，2026-08-10 人类签批）** | 状态: ✅ **FROZEN**——CCP 协议面审查（M-7）闭合；后续修改走 DCD-CCP-CHANGE-XXX
> 修订依据: 复审双红队（制度/安全均 PASS_WITH_MODERATE）+ 二次交叉验证（REV-2 补丁 R2-1~R2-13）+ 人类签批
> 补落依据: M-7 人类裁决（CCP 13 章不阻塞模板库 FROZEN，协议面单独立项审查）+ CCP 红队制度/安全约束 + TDCA-CCP-CONTRACTS-V0.1-REV2.1（FROZEN）+ CSCP 任务书 + R-1 理论（DEI/IIE）
> 适用范围: TDCA 协议网络（L2 配置权市场层）| 编制依据: 宪法十六条、UPDA、NIA-MACM 3.0、MCT、NSFL
> 术语基线: 术语注册表 V1.1+ 防火墙 V1.0（「V2.1」为无据声称，不采用，G-1）
> 层号体系: A（L0 所有权 / L1 用益权 / L2 配置权 / L3 效用）

---

## 第 1 章 协议概述

### 1.1 协议定位
TDCA-CCP（Configuration Call Protocol，配置权调用协议）是 TDCA 协议网络（L2 配置权市场层）的核心通信与执行协议。CCP 不是通用智能体通信协议，而是专门用于**配置权交易、履约调用、效用计量与税收锚定**的制度级协议（已登记）。

CCP 将 TDCA 制度框架核心概念——配置权、NCA 嵌套认知资产、MOU 最低可见效用、负空间熔断——编码为可执行协议规则，确保智能体协作在制度约束下完成正和交付。

### 1.2 协议目标（CC-001~CC-006）

| 目标 | 名称 | 描述 |
|------|------|------|
| CC-001 | 四元分离强制执行 | 「智能体不直接交易」编码为协议级强制——智能体仅执行载体，不持有/不流转资产所有权 |
| CC-002 | 六阶段不可篡改链 | 签署→编译→调用→交易触发→锚定→熔断完整执行链，每阶段输出为下阶段输入 |
| CC-003 | 快/慢系统边界硬化 | 快系统（<100ms）处理编译/触发/税收预计算/正和验证/熔断判定；慢系统处理配置决策/人类裁决/宪法 OTA |
| CC-004 | NCA 全链路生成 | 每次配置权调用自动生成 NCA，记录认知轨迹与审计轨迹（结构可信 + 认知可信） |
| CC-005 | MOU 实时锚定 | 数字人民币智能合约将进项/出项税收总和编码为不可伪造最低可见效用指标 |
| CC-006 | 负空间自动熔断 | 集成 NSFL，AI 可执行地识别负空间边界并自动触发熔断，保留人类最终介入权 |

### 1.3 适用范围
- **适用主体**: 持有配置权的人类主体、经授权智能体执行器、效用精灵、审计智能体
- **适用场景**: 配置权协议签署、跨域配置权调用（CSCP 扩展）、效用计量与分配、税收锚定、负空间检查
- **不适用**: L0 法律底层确权（法定交易中心）、**L0 所有权市场交易**（体系 A: 所有权=L0，非 L1）、纯 H-H 人际经验传播

### 1.4 术语规范（补全）

| 术语 | 定义 |
|------|------|
| 配置权（Configuration Right） | 场景内配置资源调用权，P-Right/S-Right/PUCR 三模式（法律定位） |
| CR-7Tuple | 配置权七元组: Who/What/When/How/Share/Cfg/Tax（§4.1，含 RightMode 扩展） |
| NCA | 嵌套认知资产（Nested Cognitive Asset）——配置权调用的结构/认知可信载体 |
| MOU | 最低可见效用（Minimum Observable Utility）——进项/出项税收锚定值 |
| NSFL | 负空间函数语言——⊗禁止/⊘限制/⊙观察 |
| DEI_{i,k} | 制度-技术同构度——声明-执行同构度量，L0 定标 1.0 |
| IIE | 制度排除事件——LEGAL 完整/场景降级/主体不构成 |

## 第 2 章 设计原则

1. **四元分离**: 智能体/资产所有权/配置权/效用计量四元分离——任何所有权流转操作 = 系统级违规（宪法第 8 条），离链至 L0 法定交易中心
2. **制度同构**: 协议每一步映射宪法十六条具体条款（CCP 模板库总表: T1→第 8 条/T2→C01-C16/T3→第 13 条/T4→第 10 条/T5→第 4/5 条/T6→第 9 条）——缺失映射即协议缺陷
3. **快/慢系统分离**: 快系统（<100ms）执行编译/调用/税收/熔断；慢系统（人类）执行配置决策/裁决/宪法 OTA——调整权人类专属（NS-011）
4. **人类签名权保留**（红队 B-1 落档）: 协议层强制人类签名插入点（onlyHuman + verifyHumanSignature + nonce 抗重放）——事前门禁非事后覆盖；OTA 四方联签（A-ECON:3008，4-of-4）；**硬宪法（十六条核心条款）不可 OTA 仅可解释，软宪法方支持 OTA**
5. **正和约束**: 所有 PCR 携带正和性声明（SWU 场景化）——全局正和可放行场景掠夺性配置，场景级 SWU 均正且趋势非负；**【可计算性前提】SC_s 度量协议与阈值待人类定标，定标前 SWU 正和仅作声明/设计约束，不设合约 require 前置**（对齐模板库 REV2.1 标注）

## 第 3 章 协议分层架构

### 3.1 CCP 协议栈（6 层）

> 【符号复用声明】协议栈 L1-L6 为协议分层编号，**与制度体系 A（L0 所有权/L1 用益权/L2 配置权/L3 效用）独立**——两者无映射关系，禁止混用（P-S4 修正）

| 层 | 名称 | 职责 |
|----|------|------|
| L6 应用层 | 场景应用（市场/沙盒/工作流） | 场景级业务编排（CSCP 握手入口） |
| L5 调度层 | 配置权调度（T3） | 调用调度/Shapley 分配/MRCR 隔离 |
| L4 履约层 | 智能合约执行（T4/T5） | 边界条件/资金结算/MOU 锚定 |
| L3 编译层 | NSFL 编译（T2/T6） | 宪法强制/负空间熔断 |
| L2 消息层 | JSON-LD 消息封装 | 协议消息结构化（§3.2） |
| L1 存证层 | NCA 存证（T1 辅助） | 全链路 NCA 上链 |

### 3.2 消息格式（JSON-LD 标准）

```json
{
  "@context": "https://tdca.org/ccp/v1/context.jsonld",
  "@type": "CrossSceneRequest",
  "requestId": "UUID",
  "callerScene": "scene-A", "calleeScene": "scene-B",
  "callerFunction": "f_A", "calleeFunction": "g_B",
  "callerDid": "did:tdca:...",
  "pcrBudget": 100.00,
  "requestedRight": "S-Right",
  "expectedMou": 12.5,
  "sceneContext": { },
  "crossSceneFlag": true,
  "ncaRef": "NCA-...",
  "nonce": "一次性令牌", "timestamp": "ISO8601"
}
```

## 第 4 章 核心数据结构

### 4.1 CR-7Tuple（含 RightMode 扩展）

```json
{
  "crId": "CR-...",
  "who": "caller_did", "what": "function_id", "when": "time_window",
  "how": "调用方式", "share": "Shapley 预分配", "cfg": "配置参数",
  "tax": { "deliveryTax": 0, "premiumTax": 0, "frictionTax": 0 },
  "rightMode": "P_RIGHT | S_RIGHT | PUCR",
  // 【偏序声明】P_RIGHT < S_RIGHT < PUCR（权限递增）——越级判定: requiredMode > 调用者层级 即拒绝（CCP-TIER-001）
  "terminationCompensation": { "preRegistered": 0, "transferable": false },
  "constraints": { "sceneBoundary": "scene-id", "nsflDeclaration": "..." }
}
```

### 4.2 NCA 结构（§7 详规）
```json
{ "ncaId": "...", "type": "FUNCTION_CALL|CONFIG_RIGHT|FUSE|MOU",
  "parentRef": null, "depth": 1, "content": { },
  "auditTrail": [ { "step": 1, "time": "...", "hash": "..." } ],
  "signatureChain": [ "did:..." ], "mouAnchor": 0 }
```

### 4.3 MOU 结构（§8 详规）
```json
{ "mouId": "...", "sceneId": "...", "components": { "deliveryTax": 0, "premiumTax": 0, "frictionTax": 0 },
  "timeWindow": { "signDate": "...", "settleDate": "..." }, "swuPositive": true }
```

## 第 5 章 六阶段执行流程（CC-002）

| Phase | 名称 | 输入→输出 | 快/慢 | 宪法映射 |
|-------|------|----------|-------|---------|
| P1 签署前置 | 四元分离检查（T1） | 协议草案→配置权协议（CR-7Tuple） | 快 | 第 8 条 |
| P2 编译 | 宪法强制检查（T2） | CR-7Tuple→编译通过/熔断 | 快 | C01-C16 |
| P3 调用 | 配置权调度（T3） | 调用请求→调度执行/Shapley | 快 | 第 13 条 |
| P3 边界 | 场景边界检查（**T4**）【表注: P3 边界为 P3 调用阶段内子步骤，非独立阶段（R2-12）】 | 场景边界条件检测→边界处置（独占/竞争/终止/增信） | 快（人类仲裁慢） | **第 10 条** |
| P4 交易触发 | L0 所有权交付出口（T1 routeToTradeGateway） | 所有权需求→离链 L0 交易中心 + 链上存证 | 慢（人类确认） | 第 8 条 |
| P5 锚定 | MOU 复合锚定（T5） | 调用完成→三组分 MOU 记录 | 快 | 第 4/5 条 |
| P6 熔断 | 负空间熔断（T6） | 越界行为→4 级熔断/NCA 析构 | 快（人类介入慢） | 第 9 条 |

**人类签名插入点（逐阶段标注，对齐模板库 P1 清单）**: P1 签署（人类签署协议）/ P2 编译（无签名，自动）/ P3 调用（**S-Right/PUCR 级调用须人类签名**；P-Right 经预设目标函数）/ P4 交易触发（**人类确认所有权交付**）/ P5 锚定（无签名，自动）/ P6 熔断（**人类介入覆盖须验签**）——跨场景另加 CSCP #1/#2。

- **跨系统回滚原子性（S-B10/R2-5）**: 三层超时分列——Step-4 锁定 1.5s / 调度确认失败 ≤30s 自动回滚（escrowRefund 触发）/ **人类裁决等待 72h 冻结上限（R-002 拒签路径，起算=锁定时刻）**；回滚顺序 = CBDC lock 释放 → NCA 标记 → P3 沙盒状态复位 → P5 工作流取消（Saga 补偿，幂等）；**refund 幂等载体 = refund request id + nonce（R2-5）**；dispatch 与 refund 竞态由幂等键排除

**跨场景扩展（CSCP）**: Phase 3 前置负空间预检（D-2 并集引擎）+ Phase 4 前置沙盒状态校验 + 人类签名插入点 #1（匹配后）/ #2（执行前）——详见 TDCA-TASK-CSCP-HANDSHAKE-001。

## 第 6 章 智能合约编译

- **编译输入**: CR-7Tuple + 场景 NSFL 声明 + MOU 预期
- **编译输出**: 模板库 T1~T6 合约实例（**基线: TDCA-CCP-CONTRACTS-V0.1-REV2.1 FROZEN**）
- **约束**:
  - 全部接口 `pragma solidity ^0.8.0`（内建溢出保护）
  - 全接口 `ncaRef` 字段（缺失即 revert）+ `event` 审计声明
  - 权限修饰: `onlyHuman`（人类签名门禁，验签 + nonce）/ `onlySystem`（系统白名单注册）
  - 宪法条款映射缺失 = 编译拒绝
- **模板引用**: T1 四元分离（CCP-ENFORCE-001）/ T2 宪法强制（CONST-ENFORCE-CCP）/ T3 UPDA 调度（UPDA-CCP-001）/ T4 边界条件（CONFIG-BOUNDARY-CCP）/ T5 MOU 锚定（MOU-ANCHOR-CCP）/ T6 负空间熔断（NSFL-FUSE-CCP）

## 第 7 章 NCA 生成与存证（CC-004）

### 7.1 5 阶段 NCA（阶段↔流程映射）

| NCA 阶段 | 对应流程 | type 枚举 |
|---------|---------|----------|
| 签署 NCA | P1 | CONFIG_RIGHT |
| 编译 NCA | P2 | CONFIG_RIGHT |
| 调用 NCA | P3 | FUNCTION_CALL |
| **交易 NCA** | **P4（交易触发——补 P-S3）** | **CONFIG_RIGHT** |
| 结算 NCA | P5 | MOU |
| 熔断 NCA | P6 | FUSE |

**粒度规则**: 协议阶段级 NCA（上表）+ CSCP Step 级 NCA（预检/锁定等）并存——Step 级 NCA 嵌套于阶段级（父链），深度限 max 5 层。
- **熔断 NCA**: 含熔断原因/档位/替代路径/人类介入记录（T6 postFuse）
- **完整性验证**: 分层哈希（Merkle 树）——嵌套深度限 **max 5 层**（R-CSCP-005）；单次存证 >2s 启用分层哈希优化
- **不可跳过**: 协议层强制——每个 Step 必须有 ncaRef 引用，缺失即协议异常（CCP 模板库 R2-5 落实）
- **存证层**: 联盟链（国创会/信通院标准）+ NCA 嵌套认知资产

## 第 8 章 MOU 锚定接口（CC-005）

- **3 核心方法**（对齐 T5 IMouAnchor）:
  - `recordDelivery(sceneId, amount, vatRate)` — 交付税硬化锚定（票款同步唯一可自动验证来源）
  - `recordPremium(sceneId, amount, evidenceRef)` — 溢价税预注册来源
  - `recordFriction(sceneId, amount, evidenceRef)` — 摩擦税预注册来源
- **自动锚定算法**: 票款同步 → 场景自动标注（sceneAutoTag，CBDC 侧签名 + 合约验签——MITM 防护）→ MOU_s = 三组分和 → 季度审计（注水即熔断）
- **正和验证**: 各场景 SWU 均正且趋势非负——全局正和不足，防场景掠夺性配置；**【前提标注】SC_s 度量协议与阈值待人类定标，定标前 SWU 正和仅声明不设 require；沙盒验证须先补 SC_s 度量与阈值定标，再以 SWU 为 require 前置（R2-13，完全对齐模板库 REV2.1）**
- **硬约束**: MOU=0 → 场景效用权重归零（否定性熔断）
- **时间窗口**: 签约日→清算完成日（verifyContinuity，时间源 = 链上时间戳 + 授权预言机校准）

## 第 9 章 负空间熔断（CC-006）

- **NSFL 集成**: ⊗禁止/⊘限制/⊙观察 + 4 级熔断档位（对齐 T6 INsflFuse）
  - 档位 1 观察 / 2 暂停 / 3 析构 / 4 永久撤销（升级须 onlyHuman，授权图随实现定稿）
- **LEGAL 绝对熔断**: LEGAL∧HARD → alt=∅——签名级强制（接口 require(isLegal==false)，对齐 fuse_engine.py:76）
- **人类介入**: humanOverride 验签（DID 白名单 + nonce 抗重放）——事后覆盖仅人类可发起
- **熔断后处理**: postFuse（幂等）——NCA 析构/保险/黑名单
- **跨节点同步（CCP-P3）**: ack 确认 + 风暴抑制 + 传播限速 + 多播树分片（防放大 DoS）；最大容忍延迟 <500ms（对齐 T-P2-002）
- **广播接口规格（S-B6/R2-7）**: 接口 `POST /trigger/sync`（P2 提供）——ack 超时 150ms / 重试上限 3 次（**并行 ack，总延迟 <500ms**）/ 限速 1000 事件/s/节点 / 多播树扇出 ≤8 / 分片粒度 = 场景域；**鉴权 + 频控（S-B7）**: 仅系统白名单节点可触发（onlySystem），触发事件含 nonce + 来源签名（防未鉴权广播放大器）
- **严重度分级**: 冲突严重度对齐 IIE——LEGAL=完整 IIE（绝对）/场景=降级 IIE（RESTRICT）/主体=不构成（信用降信）

## 第 10 章 安全与审计（红队安全约束落档）

### 10.1 6 维安全

| 维度 | 防护设计 | 落档来源 |
|------|---------|---------|
| 重放攻击 | 全消息 nonce + 时间戳（一次性消费） | 红队 #2 B-8 |
| 中间人 | 跨域 NCA/票款数据端到端加密 + 签名链 | 红队 #2 B-9 |
| 拒绝服务 | onlySystem 权限白名单（熔断触发）；广播 ack/抑制/限速 | 红队 #2 B-2/B-10 |
| 合约漏洞 | ^0.8 + CEI + 静态分析门槛（高危 0/中危 <3） | 红队 #2 B-13/B-5 |
| 权限绕过 | onlyHuman 验签 + nonce + 渗透测试 100% 阻断 | 红队 #2 B-1/B-3 |
| 时间戳操纵 | 授权预言机校准 + 时间窗口设计 | 红队 #2 T5-3 |

### 10.3 协议面安全规格（S-B1~S-B11 落档，2026-08-10）

| 项 | 规格 |
|----|------|
| S-B1 接口幂等 | CSCP 6 API 携带 `nonce` + `idempotency-key`（=handshake_id + endpoint）——**判定优先级（R2-1/R2-2）**: 先查幂等键（命中→返回原结果不重复执行）→ 未命中再查 nonce 消费（已消费→CCP-REPLAY-001） |
| S-B2 签名绑定 | `human_signature_1/2` 绑定 `handshake_id + nonce + 内容哈希`（**SM3 请求体规范字段: pcr_budget/mou_split_ratio/scene_ids/translator_id，R2-3**）——一次一用，跨握手重放拒绝 |
| S-B3 nonce 消费 | nonce 存储（mapping）+ 一次性消费 + 失效窗口 **72h**（对齐回滚上限，R2-4）；handshake_id 超时归档清理 |
| S-B4 消息认证 | CSCP 握手链路（6 API + 5 内部接口）消息级 HMAC（发送方 DID 密钥）——篡改检测 100% |
| S-B5 端到端加密 | 跨域数据 TLS 通道 + 应用层签名链；密钥 = DID 绑定密钥，生命周期对齐 TTRN 可信根 |
| S-B8 系统白名单 | onlySystem 节点注册/撤销接口 `POST /registry/system-node`（人类四方联签批准）——撤销即时生效 + 跨节点传播/缓存失效 ≤30s（R2-8）；**CBDC 票款来源地址入白名单（M-3 落档 R2-6）: 链上合约地址注册 + 回调签名验证** |
| S-B9 验签约束 | verifyHumanSignature/verifyQuadSignature: DID 白名单 + 密钥托管（HSM/TTRN）+ 验签预言机；**禁止 fuse_engine attempt_reset 式仅非空检查** |
| S-B11 预检认证 | D2 /nsfl/preflight/check 携带调用方签名 + nonce——响应可重放投喂拒绝 |

### 10.2 4 维审计

1. **NCA 完整性**: 每 Step ncaRef + 哈希链（§7）
2. **状态变更审计**: 状态转换 100% 上链（CSCP 状态机）
3. **人类签名审计**: human_gates 状态全程可查（签名人/时间/理由）
4. **术语合规审计**: 注册表 V1.1 + 防火墙 V1.0，冲突率 0%，差异报告归档

## 第 11 章 兼容性与映射

| 现有协议 | 映射方式 | 说明 |
|---------|---------|------|
| A2P2 | Bridge Layer → CCP 子集 | 智能体对智能体协议映射为配置权调用 |
| MCP | 工具调用 → 配置权调用封装 | 每 MCP 工具注册为函数接口 |
| SkillPay | 技能支付 → MOU 锚定 | 支付映射为税收锚定 |
| APOP | 权限协议 → CR-7Tuple | 权限映射为配置权七元组 |
| CSCP（新增） | CCP 跨场景扩展 | 握手与调度（CSCP 负责）；NCA 数据格式与存证（CCP-P2 负责）——接口边界冻结 |

## 第 12 章 错误码与异常

### 12.1 错误码体系（13 个）

| 码 | 含义 | 处理 |
|----|------|------|
| CCP-000 | 成功 | — |
| CCP-SEPARATION-001 | 所有权流转违规（四元分离） | 拒绝 + NCA + 转 L0 交易中心 |
| CCP-SEPARATION-002 | 非配置权模式调用 | 拒绝 |
| CCP-CONST-001 | 宪法检查失败 | 熔断（FUSE） |
| CCP-NSFL-001 | 负空间预检 FAIL | 拒绝 + Alt-Path |
| CCP-NSFL-002 | 负空间 TRIGGERED | 熔断 + BANNED |
| CCP-SANDBOX-001 | 沙盒状态非 ACTIVE | 拒绝 |
| CCP-TIER-001 | 配置权层级不足 | 拒绝（RightMode 越级） |
| CCP-TRANSLATOR-001 | 无可用翻译器 | 拒绝 + 建议 |
| CCP-LOCK-001 | 资金锁定失败/预算不足 | 拒绝 + escrowRefund |
| CCP-HUMAN-001 | 人类签名缺失/无效 | 拒绝（插入点强制） |
| CCP-NCA-001 | NCA 生成失败/引用缺失 | 协议异常回滚 |
| CCP-OTA-001 | OTA 签批不足（非四方联签） | 拒绝 |
| **CCP-REPLAY-001** | **重放检测命中（nonce 已消费/签名重复）** | **拒绝，不重复执行（R2-1 消矛盾）** |

### 12.2 异常决策树
- Step 级超时（预检 500ms/沙盒 1s/锁定 1.5s）→ 自动回滚至上一状态（Saga 补偿）
- 锁定后取消 → escrowRefund（T4 权限修复）
- 拒绝 → RejectionNCA（理由 + Step + 建议处置，human-readable）

## 第 13 章 附录

### 13.1 DID 规范
`did:tdca:<hex>`——人类 DID 绑定数字人民币钱包签名；L 级智能体 DID 绑定配置权授权链；TTRN 物理可信根（TDCA-TTRN-DEPLOY-001，独立立项）作为硬件签名锚点

### 13.2 场景 ID
`scene:<org>:<domain>:<seq>`——场景负空间声明与意义锚点关联

### 13.3 模板索引
见 TDCA-CCP-CONTRACTS-V0.1-REV2.1（FROZEN）——T1~T6 接口 + 宪法映射总表 + 实现期设计项（系统白名单/verifyHumanSignature/nonce 存储）

### 13.4 修订历史
- V0.1（2026-08-08）: 草案生成（会话记录，正文止于 1.4 首行）
- V1.0（2026-08-10）: 13 章补落——正文完整化 + 对齐模板库 REV2.1 FROZEN + 双红队约束 + CSCP 接口 + R-1 理论；术语基线注册表 V1.1
- **V1.0-REV1（2026-08-10）: 协议面修正 19 项**——制度（P-B1/P-B2/P-S1~S6）+ 安全（S-B1~B11 §10.3 规格表）
- **V1.0-REV2（2026-08-10）: 复审补丁 R2-1~R2-13**——幂等判定优先级/幂等键粒度/内容哈希 SM3/nonce 72h 窗口/M-3 CBDC 白名单落档/超时层次分列/refund 幂等/广播参数消冲突/P3 边界表注/SWU 沙盒前置复述
- 状态: DRAFT 待人类签批 → FROZEN

---

> 本文档为 CCP 13 章正文补落版（DRAFT）。补落目的: 闭合 CCP 红队 B-11 证据缺口 + 为协议面（P1 握手/P2 NCA/P3 熔断/CSCP）审查提供完整基线。待协议面红队审查（双红队）→ 修正 → 人类签批 → FROZEN。协议面审查范围: 重放/MITM/广播放大（安全主攻击面）+ 宪法映射完整性（制度面）。
