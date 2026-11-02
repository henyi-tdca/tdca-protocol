# TDCA-HANDOFF-KIMI-DATAFLOW-M1-001 · Kimi 施工指令：COP 动态数据流 M1

> 文档编号: TDCA-HANDOFF-KIMI-DATAFLOW-M1-001 ｜ 编制: 2026-08-28（Reasonix 制度层）｜ 状态: ✅ **已下令**（创始人批准 DCD-COP-DATAFLOW-001）
> 依据: DCD-COP-DATAFLOW-001（已批准，附约束：API 接口=外部依赖，**优先免费开放 API**）
> 存证: GSEQ-0604

---

## M1 施工（数据流抽象层）

对 `tdca-protocol`（tools/thingsboard_pool + COP 运行时）新增：

| 项 | 内容 |
|---|---|
| ① context provider 接口 | 实时状态数据 → `context: Situation` 实际值（抽象接口 + 注册机制） |
| ② thingsboard 适配 | tdca-thingsboard-pool → context provider 适配层（设备状态流 → COP 动态上下文） |
| ③ **API 外部依赖** | **优先免费开放 API**：ThingsBoard 社区版 / 公共 MQTT/HTTP 数据源 / 免费 IoT 演示流；收费 API 一律不用（预算纪律） |
| ④ 数据性质 | real 设备流标 real；模拟流标 simulated/ID92；无数据流 fail-closed（拒动态决策） |
| ⑤ 熔断联动 | NSFL 熔断接动态数据（实时状态触发负空间熔断） |
| ⑥ 测试 | ≥10 用例（provider 注入/无数据 fail-closed/流式更新/熔断联动/数据性质标注） |

## M2 试点（待触发）

- 1 个场景动态决策用例（设备流 → COP decision）——M1 验收后另行指令

## 纪律（红线不变）

- 免费开放 API 优先 ｜ 收费 API 禁用（¥111 预算纪律）｜ 无敏感词 ｜ 算力零提及 ｜ 分润模拟态 ｜ 凭证零落盘
- 不改原语（立场分离整改另行并行）——本 M1 只加运行层

## 回报

M1 完成后回报：① context provider 实现说明 ② thingsboard 适配说明 + 所用免费 API 清单 ③ 测试结果（≥10 绿）④ NCA 存证号。

---

> 本指令为 COP 动态数据流 M1 施工唯一执行依据；M2 试点另发指令。
> 关联: [[tdca-session-20260828]] ｜ DCD-COP-DATAFLOW-001 ｜ TDCA-STANCE-SEPARATION-001 律三补充
