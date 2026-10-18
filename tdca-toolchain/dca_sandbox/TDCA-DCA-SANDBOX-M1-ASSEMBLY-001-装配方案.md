# DCA-重塑版沙盒 M1 装配方案 · 沙盒模型装配（merchant_loop M1 + 模拟参数）

> 文档标识: TDCA-DCA-SANDBOX-M1-ASSEMBLY-001 ｜ 日期: 2026-09-08（+08）｜ 会话框: L1-SI-023-FE6B63
> 上游: DCD-DCA-SANDBOX-001（✅ ACCEPT：M1 沙盒模型装配）｜ DCD-MERCHANT-LOOP-001（✅ M1 FROZEN）｜ TDCA-DCA-RESHAPE-001 §二
> 状态: ✅ 方案定稿（施工执行中）

---

## 一、装配目标（DCD-DCA-SANDBOX-001 §四 M1）

「M1 沙盒模型装配（merchant_loop M1 + 模拟参数）」——把已 FROZEN 的 merchant_loop M1 工具包接入 DCA-重塑版模拟运营模型，形成可运行 26 周模拟的装配件（M2 执行 26 周模拟运行；M3 出盒报告）。本 M1 只做**装配 + 短程验证**，不做 26 周完整运行（M2）。

## 二、装配形态（复用 SBX-OPS 三空间 + 新增 merchant_loop 模拟模块）

| 层 | 内容 | 依据 |
|---|---|---|
| **模拟引擎**（新建） | `tdca-toolchain/dca_sandbox/` 包——日清结算模拟引擎（零穿池检测）+ 周推进 + 核销率聚合 + 0 金融化违例审计 + CCA 信号预留 | SBX-OPS 状态机语义（Phase0 准入→P0 实验→P1 评估→Exit/Closed，对齐 sandbox_core 转换） |
| **装配模块**（复用 FROZEN） | `merchant_loop` engine/roi/notary——权益发布模板校验、核销闭环、ROI 测算、NCA 落证 | DCD-MERCHANT-LOOP-001 M1 FROZEN |
| **入盒纪律** | 纯模拟参数（ID92 SIMULATED）；Δ 实时备案；BLOCKED/CRYOGENIC 自动回滚；观察期 ≥30 天语义 | DCD-DCA-SANDBOX-001 §三 |
| **出盒门槛预埋** | 核销率 ≥60% 连续 8 周 / 26 周零穿池 / 0 金融化违例 / CCA 响应率 ≥ 阈值——M1 只实现检测器，M3 出盒评估用 | DCD §二 指标表 |

## 三、模拟器参数模型（SIMULATED 候选——M2 校准，不冒充定标）

| 参数 | 候选 | 说明 |
|---|---|---|
| 周数 | 26 周（M2 完整）；M1 验证跑 8~13 周 | DCD §二 |
| 商户数 | 3~5（含示例咖啡） | SIMULATED |
| 客单价 | ¥50~150（正态分布，均值 100） | SIMULATED |
| 核销率驱动 | 消费事件到达率 λ（周）——M1 固定参数，M2 校准 | SIMULATED |
| 让利结构 | discount 10% + rebate 3%（示例权益） | 复用示例 |
| 日清 | 每核销逐笔即时（无池）——现金流日结零滞留 | merchant_loop no_cls |
| 激活系数 | 预埋计算位（>1.2 出盒——M3 用） | ID27 |

## 四、交付物（落位 tdca-toolchain/dca_sandbox/）

1. `__init__.py` — 导出 + 包说明
2. `engine.py` — SandboxSimulation（周推进/日清/核销聚合/指标检测：零穿池、核销率≥60% 连续 8 周、0 金融化违例、CCA 响应率）
3. `metrics.py`（并入 engine 或独立）— 周指标聚合 + 连续达标检测
4. `notary.py` — DCA-沙盒运行 NCA 落证（NCA-DCASANDBOX-*）
5. `cli.py` — `dca_sandbox run --weeks <n> --seed <n>`（M1 短程验证运行）
6. `tests/test_dca_sandbox.py` — 装配测试（merchant_loop 接入冒烟/日清/指标检测）
7. 本方案 + M1 装配交付报告（TDCA-DCA-SANDBOX-M1-ASSEMBLY-001 转交付报告）

## 五、装配纪律

- merchant_loop 模块**只装配不改写**（FROZEN 不动）；模拟器在 dca_sandbox 内 import merchant_loop
- 全部 SIMULATED（ID92）；0 真实资金流；0 配置权真实调用
- 红线：无资产/无保本/无资金池/无庞氏——模拟器内嵌违例审计（检出即 BLOCKED 回滚语义）
- NCA 存证链：装配交付 → GSEQ 登记（Reasonix 线）

---
*DCA-重塑版沙盒 M1 装配方案定稿——merchant_loop M1 FROZEN 装配件 + 模拟引擎 ｜ 施工中*
