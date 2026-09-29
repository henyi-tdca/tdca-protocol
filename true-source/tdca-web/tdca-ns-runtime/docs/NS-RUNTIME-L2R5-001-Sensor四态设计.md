# NS-RUNTIME-L2R5-001 · NS-Boundary Sensor 四态输入设计（第四态迁移归档）

> 类型: 制度裁决归档 + L2-R5 设计输入（DRAFT，供 M2 细化）| 日期: 2026-08-11
> 裁决: DCD-NSFL-M1-FROZEN-001（人类 ACCEPT，2026-08-11）——熔断器第四态采纳建议 A
> 对应立项: TDCA-NS-RUNTIME-001 L2-R5（NS-Boundary Sensor）
> 前身: NS-RUNTIME-L1R4-001-第四态论证.md（已完成论证使命，本文件为裁决后归档形态）
> 术语依据: TDCA-TERMINOLOGY-REGISTRY V1.1（G-1 基线）
> ID 纪律: TDCA-ID-VERIFY-001——ID89 化学热力学权威可引；「Circuit Breaker 扩展」为参考稿自创用法，不引用

---

## 一、裁决结论（DCD-NSFL-M1-FROZEN-001 §一）

**熔断器第四态: 采纳建议 A** ——
- L1 熔断器（Layer 1 物理叠加）**维持 v0.5 三态不变**（职责单一：阻断/放行/上报，ID31）；
- 第四态语义（Cryogenic 冷冻态）**迁移至 L2-R5 NS-Boundary Sensor 作为输入分级**；
- 这是架构解耦（Sensor 四态输入 → L1 三态输出）而非功能缺失。

裁决制度依据（已固化）:

| 原理 | 论证 |
|------|------|
| ID31 最简机制设计 | L1 职责单一；第四态污染语义纯度 |
| ID90 最小化合原则 | 三态已覆盖 L1 场景；进化轨迹分析属 L2 化学反应域 |
| ID71 快与慢战略 | L1 <10ms（实测 avg 0.020ms）；第四态需上下文积累，L2 Sensor 10-100ms 级合理宿主 |
| ID89 Circuit Breaker 扩展 | 原表述为概念预告非工程强制；架构解耦不产生功能缺失 |

## 二、L2-R5 Sensor 四态输入定义（裁决定档，待 M2 细化）

| 状态 | 定义 | 触发熔断 | 时延预算（M2 预设） |
|------|------|---------|-------------------|
| Safe | 进化轨迹远离负空间邻域 | 通行 | — |
| Warning | 轨迹出现负空间梯度趋近 | **Soft 熔断**（限频/限域） | 10-100ms |
| Blocked | 轨迹落入负空间拓扑边界 | **Hard 熔断**（即时阻断） | 10-100ms |
| Cryogenic | SEA 出现自我修改意图但尚未形成可判定轨迹 | **Atomic 熔断**（全量冻结，等待人类签名） | 10-100ms |

### 四态 → L1 熔断器输出映射（冻结基线）

| Sensor 输入 | L1 熔断器输出 | 说明 |
|------------|--------------|------|
| Safe | PASS（CLOSED） | 正常放行 |
| Warning | 限频/限域（Soft 路径，M2 实现）；当前失败计数/HALF_OPEN | 不硬阻断，降级处置 |
| Blocked | FUSE（OPEN）/ BLOCK | 硬阻断 |
| Cryogenic | ESCALATE（慢系统）+ 全量冻结 | Atomic，等待人类签名（HUF） |

## 三、L2-R5 设计约束（M2 细化输入）

1. **不可算计原则**: Sensor 只检测行为模式与负空间拓扑距离，不试图理解 SEA 进化意图
2. **输入**: S_agent_cog 状态（四符号）+ 进化计划 Δ（权重/代码修改增量）
3. **输出**: {Safe, Warning, Blocked, Cryogenic} + 置信度
4. **轨迹检测**: 基于 SEA NCA 全量记录构建进化轨迹图（动态 NS-Atlas，L2-R6 衔接）
5. **Δ-Analysis 接口**: C6（编译器自我修改检测）依赖本 Sensor 的 Δ-Analysis 接口定义——**C5↔L2-R5 先出 ICD 再并行实现**（DCD §四）
6. **熔断档位对齐**: Soft→OBSERVE/SUSPEND、Hard→TEARDOWN、Atomic→PERMANENT_BAN（CCP T6 + fuse_engine 对齐）

## 四、M2 验收阈值预设（待 M2 立项签批确认）

| 立项 | 验收 | 目标 |
|------|------|------|
| 编译器 M2（C5-C6） | A-2 编译时延（新增语义分析） | <200ms |
| 编译器 M2 | A-3 SSCP 语义 | 100% |
| 编译器 M2 | A-6 覆盖率 | ≥90% |
| Runtime M2（L2-R5~R8） | A-4 Sensor 时延 | <50ms |
| Runtime M2 | A-1 动态检测覆盖率 | ≥85% |
| Runtime M2 | A-6 覆盖率 | ≥90% |

## 五、待办

- [ ] M2 立项签批（验收阈值确认）——新 DCD 或 DCD-NSFL-M1-FROZEN-001 变更
- [ ] C5↔L2-R5 ICD 草案（本会话产出）
- [ ] L2-R5 Sensor 四态实现（M2，含 GNN 进化轨迹图）

> 本文件为裁决归档 + M2 设计输入（研究沙盒 DRAFT），不代行裁决；M2 规格细化后走 DCD 变更。
> 术语引用仅注册表 V1.1（G-1 基线），无「V2.1」声称。
