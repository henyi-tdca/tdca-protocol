# EIOS 三层架构设计（M1）

> **文档编号：** EIOS-ARCH-001
> **Function-Call-ID：** TDCA-PHASE-E-INT-1（M1）
> **日期：** 2026-08-04
> **验收标准：** 基础层/认知层/应用层模块划分 + 接口契约 + 与 Phase A~D 的调用关系图
> **硬约束：** 复用 Phase A~D 已归档模块（破例识别），禁止重写

## 一、三层架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│ 应用层（Application Layer）—— 面向人类与智能体的统一入口          │
│  ├─ 全周期管理看板（复用 UI-001~007 组件组装）                    │
│  │    ├─ 智能体列表（UI-001 L5 扩展）                             │
│  │    ├─ 生命周期时间线（UI-007 拓扑穿越扩展）                    │
│  │    ├─ NCA 审计面板（UI-005 L1 实时监控扩展）                   │
│  │    └─ MOU 看板（UI-003 L3 控制台扩展）                        │
│  ├─ 商学院教学模拟器（E-EDU 联动，预留）                         │
│  └─ 效用精灵 API 网关（九大数学能力 REST 化）                    │
├─────────────────────────────────────────────────────────────────┤
│ 认知层（Cognition Layer）—— 编排与制度记忆                       │
│  ├─ FC-012 TDCA-FLOW 编排引擎（9 Phase 状态机，封装调用）         │
│  ├─ TIMA 制度记忆层（L0~L3 + 基变换 + CKS，封装调用）             │
│  └─ 效用精灵（优化/计量/贝叶斯/博弈/均衡/跨域 API 封装）           │
├─────────────────────────────────────────────────────────────────┤
│ 基础层（Foundation Layer）—— 原子能力与硬件抽象                   │
│  ├─ FC-001 NCA 生成器（封装）                                    │
│  ├─ FC-002 权限中枢（Token 验证，封装）                          │
│  ├─ FC-003A MOU/CLI 结算（封装）                                 │
│  ├─ FC-004 效用精灵计算引擎（封装）                              │
│  ├─ FC-005 知识图谱编译器（封装）                                │
│  └─ NMDeviceDriver（硬件抽象，mock 实现，E-HW-1 兼容）            │
└─────────────────────────────────────────────────────────────────┘
     协议层（贯穿三层）：ASP 调度协议 / CKS 知识同步 / e-CNY 结算
```

**分层原则（快慢系统）**：应用层=慢系统交互（人类介入 50-100%）；认知层=快慢切换中枢（9 Phase 中 P0~P3 慢、P4~P8 快）；基础层=快系统确定性执行（毫秒级）。

## 二、模块划分与职责

### 2.1 基础层（Foundation Layer）

| 模块 | 职责 | 封装的归档模块 | 接口风格 |
|------|------|---------------|---------|
| NCA Service | NCA 生成/存证 | FC-001 | REST `/api/v1/nca` |
| Auth Service | Token 验证/配置权门控 | FC-002 | REST `/api/v1/auth` |
| MOU Service | 税收锚定/结算 | FC-003A | REST `/api/v1/mou` |
| Utility Engine | 效用计算 | FC-004 | REST `/api/v1/utility` |
| KG Compiler | 知识图谱编译 | FC-005 | REST `/api/v1/kg` |
| Device Driver | 硬件抽象（PUF/TDID/熔断/OTA） | E-HW-1 规格书 | Python 类（本地调用） |

### 2.2 认知层（Cognition Layer）

| 模块 | 职责 | 封装的归档模块 | 接口风格 |
|------|------|---------------|---------|
| Flow Orchestrator | 9 Phase 编排 | FC-012 | REST `/api/v1/flow` + 状态回调 |
| Memory Layer | L0~L3 制度记忆 | TIMA | REST `/api/v1/memory` + CKS 同步 |
| Genie API | 九大数学能力 | 效用精灵（Phase A） | REST `/api/v1/genie` |

### 2.3 应用层（Application Layer）

| 模块 | 职责 | 复用的 UI | 新增点 |
|------|------|----------|--------|
| 全周期看板 | 生命周期总览 | UI-001/003/005/007 | 时间线组件（遵循视觉规范） |
| 教学模拟器 | E-EDU 联动 | UI-001~007 | 预留路由，E-EDU 阶段实现 |
| Genie Gateway | API 网关 | — | 认证+限流+审计转发 |

## 三、接口契约（REST API 草案，FastAPI）

### 3.1 基础层

```
POST /api/v1/nca/generate        {operation, path, pre_hash, post_hash} → {nca_id}
GET  /api/v1/nca/{nca_id}        → NCA 记录
POST /api/v1/auth/verify         {token, scene_id} → {permitted, config_boundary}
POST /api/v1/mou/record          {flow_id, tax_in, tax_out} → {mou_total}
GET  /api/v1/utility/{flow_id}   → {eri, cci, positive_sum}
POST /api/v1/kg/compile          {six_elements} → {prior_hash, nca_ref}
```

### 3.2 认知层

```
POST /api/v1/flow/start          {intent, six_elements} → {flow_id, phase: P0}
GET  /api/v1/flow/{flow_id}      → {phase, status, human_decision_points}
POST /api/v1/flow/{flow_id}/advance  {decision} → {next_phase}
POST /api/v1/memory/write        {layer, memory_type, content, version_vector} → {memory_id}
GET  /api/v1/memory/{layer}/{id} → InstitutionalMemory
POST /api/v1/genie/solve         {participants, objectives, constraints} → {solution, shapley}
```

### 3.3 应用层

```
GET  /api/v1/dashboard/agents    → 智能体列表（UI-001 数据源）
GET  /api/v1/dashboard/timeline  → 生命周期时间线（UI-007 数据源）
GET  /api/v1/dashboard/nca       → NCA 审计面板（UI-005 数据源）
GET  /api/v1/dashboard/mou       → MOU 看板（UI-003 数据源）
```

### 3.4 接口契约四要素明细（输入/输出/异常/制度锚定）

**代表端点 1：POST /api/v1/nca/generate（基础层 FC-001）**

| 要素 | 契约 |
|------|------|
| 输入 | `{operation: FileCreate\|FileEdit\|CodeGen\|Review\|Audit, path, pre_hash, post_hash}` |
| 输出 | `{nca_id, nca_path, sha256_full}`（201 Created） |
| 异常 | 400 非法 operation / 422 pre/post 哈希缺失 → `[NSFL-TRIGGER]` |
| 制度锚定 | FC-001 NCA 生成器（宪法第十六条可观测/自证 + Config-Right-Token 六字段） |

**代表端点 2：POST /api/v1/auth/verify（基础层 FC-002）**

| 要素 | 契约 |
|------|------|
| 输入 | `{token, scene_id}` |
| 输出 | `{permitted: bool, config_boundary: {scope, rollback, audit_trail}}` |
| 异常 | 401 token 无效 / 403 超出配置权边界 |
| 制度锚定 | FC-002 权限中枢（配置权边界六字段 + 人类签名权不可覆盖） |

**代表端点 3：POST /api/v1/flow/{flow_id}/advance（认知层 FC-012→ASP）**

| 要素 | 契约 |
|------|------|
| 输入 | `{decision, context: {六要素迁移条件}}` |
| 输出 | `{asp_state, fc_phase, human_intervention, nca_ref, fuse}` |
| 异常 | 422 迁移条件不满足 → FUSE（Level-1/2/3）/ 400 偏离 9 Phase → `ID38-EXCEPTION` |
| 制度锚定 | ASP 协议（与 FC-012 9 Phase 同构，HC-EINT-002） |

**代表端点 4：POST /api/v1/memory/write（认知层 TIMA）**

| 要素 | 契约 |
|------|------|
| 输入 | `{layer: L0..L3, memory_type, content, version_vector}` |
| 输出 | `{memory_id, updated_at}` |
| 异常 | 400 非法 layer/memory_type / 422 version_vector 为空 → `[NSFL-TRIGGER]` |
| 制度锚定 | TIMA InstitutionalMemory.validate()（CKS VersionVector 兼容，HC-EINT-003） |

## 四、与 Phase A~D 调用关系图

```
应用层（UI-001~007 复用 + 新增看板）
   │ REST
   ▼
认知层
  Flow Orchestrator ──调用──► FC-012（封装，9 Phase）
        │                        │
        │                        ├─ P2 → KG Compiler（FC-005 compile-prior）
        │                        ├─ P3 → Genie API（正和验证 + NSFL 检测）
        │                        ├─ P4 → NMDeviceDriver.register_to_l1()（mock）
        │                        ├─ P5 → NCA Service（FC-001 存证）
        │                        └─ P7 → Genie API（ERI>CCI 求解）
        │
  Memory Layer ──调用──► TIMA（封装：L0~L3 + VersionVector）
        │                        └─ CKS 同步（版本向量 merge/conflict 宪法收敛）
  基础层（FC-001~005 封装 + NMDeviceDriver mock）
```

**调用规则**：认知层是唯一允许调用基础层+FC-012/TIMA 的层；应用层只通过认知层 REST 接口访问，禁止直接调用基础层（层级隔离）。

### 4.1 跨层调用链（含 SQLite mock 存储）

```
应用层（React UI-001~007 + 看板）
  │ REST
  ▼
认知层（FastAPI）
  ├─ Flow Orchestrator（ASP→FC-012 委托）
  ├─ Memory Layer（TIMA 封装）
  └─ Genie API（效用精灵封装）
  │  import + wrapper（不修改源码）
  ▼
基础层（FastAPI）
  ├─ FC-001 NCA / FC-002 Auth / FC-003A MOU / FC-004 Utility / FC-005 KG
  └─ NMDeviceDriver（mock）
  │
  ▼
外部存储（SQLite mock，LIM-EINT-002）
  ├─ 表 nca_records        （mock TDCA 链存证）
  ├─ 表 config_memory      （mock Neo4j 配置权图）
  ├─ 表 utility_metrics    （mock TimescaleDB 时序）
  └─ 表 flow_states        （FC-012 状态持久化）
```

**SQLite mock 与生产存储映射**：SQLite 仅替换物理存储，制度逻辑（NCA 格式/9 Phase 状态机/NSFL 约束）与生产全同构——满足冒烟测试规格"仿真-生产制度同构"。

## 五、部署架构（软约束：模块化部署）

```
基础层集群（FastAPI，无状态，水平扩展）
  └─ 共享 Neo4j（L2 配置权）/ TimescaleDB（L3 效用）
认知层集群（FastAPI，有状态：flow_id 会话亲和）
  └─ 共享 TIMA 存储（L0/L1 强一致，Raft）
应用层 CDN（React 静态资源 + API 网关）
```

## 六、NSFL 合规自查（M1）

| 禁止操作 | 本设计状态 |
|---------|-----------|
| 修改已归档代码 | ✅ 全部封装调用，无源码修改 |
| 绕过 9 Phase | ✅ Flow Orchestrator 仅转发 FC-012 |
| 重实现 TIMA/FC-012 | ✅ 仅 API 封装层 |
| NMDeviceDriver 偏离 E-HW-1 | ✅ 接口与 E-HW-1 规格书逐项对应（见 M4 文档） |

## 六B、编码启动指令硬约束对照（HC-EINT）

| 硬约束 | 本设计状态 |
|--------|-----------|
| HC-EINT-001 禁止修改 Phase A~D 已归档代码 | ✅ import + wrapper，零源码修改 |
| HC-EINT-002 ASP 与 FC-012 9 Phase 同构 | ✅ M2 交付：12 态映射 + 集成验证 PASS |
| HC-EINT-003 CKS 与 TIMA VersionVector 兼容 | ✅ 委托 TIMA VersionVector（M3 细化） |
| HC-EINT-004 NMDeviceDriver 兼容 E-HW-1 | ✅ M4 交付：五接口逐项对应 |
| HC-EINT-005 看板复用 UI-001~007 | ✅ M5 看板组件映射（智能体列表→UI-001 等） |

## 七、审查与签批

- [ ] Kimi 制度一致性审查（M1）
- [ ] 人类签批（M1）
