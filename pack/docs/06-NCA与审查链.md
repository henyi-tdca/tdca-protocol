# 06 · NCA 与审查链

> TDCA-PACK-001-DOC-06 | 依据 TDCA-WORKING-SPEC-001 §五/§六 + 方法论 V1.1 第十二章
> 定义：NCA 命名/生成、审查闭环（REV）、跨模型验证。

---

## 1. NCA 是什么

NCA（Nested Cognitive Asset，嵌套认知资产）= TDCA 的可信存证单元。每个决策、每段代码、每次交互都必须有 NCA 记录——**过程黑箱化违反宪法第 4 条（C01 可观测性原则）**（参见 KB-INST-020 转译编码；本协议包对宪法条文仅作引用性声明，不内嵌全文——L0 法律底层不可由 L2 协议层承载）。

## 2. NCA 命名规范

### 文档型命名（方法论 V1.1）
```
TDCA-NCA-{YYYYMMDD}-{SEQ}-{TYPE}-{FC-ID}.md
```
TYPE ∈ {CODE, REV, AUDIT, MOU, NSFL}

### 工程型命名（MEMO-006 附录 C，YAML 11 字段）
```
TDCA-NCA-{OPERATOR}-{YYYYMMDD}-{SEQ:03d}.yaml
```
11 字段（MEMO-006 附录 C：NCA-ID / FC-ID / Operation / Operator / Timestamp / Pre-State / Post-State / Config-Right-Token / Audit-Trail / Human-Signature / Negative-Space-Check）+ Scope 扩展字段（生成器附加）；另含 MOU-Anchor（税收锚定硬下限，模拟态标注）

## 3. NCA 内容必含（文档型）

- 元信息：FC-ID / 类型 / 时间 / 生成者 / 前置 NCA
- 六要素快照
- 执行记录
- 决策点（人类签批）
- 性能指纹：Token / 费用 / 时长 / 缓存率
- 完整性校验：SHA-256 / 签名

## 4. 审查闭环（REV，MEMO-008）

### 触发条件

| 触发 | 审查类型 | 审查人 |
|------|----------|--------|
| 六要素声明完成 | 六要素审查 | Auditor + 人类签批 |
| 代码开发完成 | 代码审查（REV） | Auditor + 人类签批 |
| 负空间规则触发 | 熔断审查 | 人类强制介入 |
| 上下文 > 60% | 会话健康审查 | 系统 + 人类确认 |

### 五步审查流程

1. 自审查（六要素对照）
2. 提交 REV 请求（附代码 + NCA）
3. Auditor 审查（六要素 / NSFL / 正和 / 代码质量）
4. 人类签批（PASSED / PASSED_WITH_MODERATE / BLOCKING）
5. 归档（生成 NCA + REV 记录）

### REV 记录必含字段

```
rev_id / status / issues（类型 + 严重度 + 位置 + 描述）/ resolution / nca_ref / human_signatory
```

> 修正后必须重新通过六要素审查并生成新 NCA，原 REV 保留关联。

## 5. 跨模型验证协议（K3 Auditor + Trea Validator）

| 模型 | TDCA 角色 | 验证职责 | 速度 |
|------|----------|---------|------|
| DeepSeek V4-Flash | Protocolizer（协议编译器） | 制度意图编译、六要素生成 | 毫秒级 |
| Kimi K3 | Auditor（制度审查员） | 制度逻辑一致性、正和博弈验证 | 秒级 |
| Kimi K2.7 Code（Trea） | Validator（工程验证器） | 代码工程严格性、边界条件覆盖 | 分钟级（异步） |

### 验证流程

```
[代码开发完成] ← Protocolizer
    ↓ Step 1: 制度审查 ← K3 Auditor（六要素完整性/制度逻辑一致性/正和验证）→ REV-K3-001
    ↓ Step 2: 工程验证 ← Trea（异步，边界条件/异常处理/类型安全/并发/资源泄漏）→ REV-TREA-001
    ↓ Step 3: 差异分析 ← 人类 + Auditor Genie
         Type A: K3 通过但 Trea 发现 → 制度表述模糊，需显式化
         Type B: 双方都发现 → 代码缺陷，需修正
         Type C: K3 发现但 Trea 通过 → 制度意图理解偏差，需校准
    ↓ Step 4: 修正与再验证 ← Protocolizer（重新 Step 1 + Step 2）
```

### Trea 异步审查要点

- 不阻塞编译流程：接收代码草案（异步推送）→ 后台深度审查 → 推送 REV-TREA 报告
- 不审查制度逻辑（那是 K3 的职责），只审查工程严格性
- 发现的问题进入 OTA 队列，下一版本处理

## 6. NCA 生成流程（工程落地）

1. 开发完成 → 生成 CODE-NCA
2. 审查完成 → 生成 REV-NCA
3. 人类签批 → git 提交归档
4. 会话分裂时 → 生成 L1-SI

> 模板：`templates/nca-template.yaml`（工程型 11 字段）、`templates/rev-template.yaml`（REV 记录）。
