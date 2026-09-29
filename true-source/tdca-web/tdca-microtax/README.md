# TDCA 微交付税收模块（tdca-microtax）

> 任务编号: TDCA-TASK-MICROTAX-001（V1.0-FROZEN，人类签批 2026-08-12）
> 立项: DCD-MICROTAX-001 | 存证: NCA-TDCA-REASONIX-20260812-001（Signed）
> 会话框: TDCA-SI-20260812-004-L1-2c18fd | **M1+M2 已完成（待整体签批）**

## 定位

智能体微交付（micro-delivery）的**实时税收计算 + 智能合约税收预缴**——
协作收益分配先扣除税款（调度税/版税/交易费）并**预缴**至税收智能合约托管，
方可进入正和满意解结算与 MOU 归零闭环（正和效用满意解硬指标）。

```
微交付完成 → 实时计税（T(y_t) 金额推导）→ 税收预缴（智能合约托管/代扣）
→ 正和满意解（税后净额参与分配）→ MOU 归零验证 → NCA 存证
```

## 模块

| 模块 | 任务 | 说明 |
|------|------|------|
| `microtax/models.py` | M-4 | micro-delivery 域实体（交付价值/税收/净额/预缴状态） |
| `microtax/tax_calculator.py` | **M-1** | 微交付计税器：交付计量 → T(y_t) 分项金额（调度税/版税/交易费 + 合计）|
| `microtax/prepay_adapter.py` | **M-2** | 税收预缴合约适配器：税款代扣托管（预缴语义，区别于预算 escrow）|
| `microtax/positive_sum_integration.py` | **M-3** | 正和满意解税后集成：税后净额 → Shapley 分配 → MOU 归零验证 |
| `tests/` | 验收 | 54 测试，覆盖率 99% |

## 复用基座（ID90 最小化合，不新建平行体系）

- `tdca-call-rules/engine/call_rules_engine.py` — `TaxRates`（2% / 7.5% / 0.75%，模拟态 D-011）
- `tdca-fos/tdca_adapters/mou_pipeline.py` — `MOUPipeline` / `SimulatedTaxAuthority`（M-3 集成目标）
- `tdca-cscp/cscp_gateway/mou_escrow.py` — 预算 escrow（**非税收**，语义区分参照）

## 验收状态（M1+M2 全量）

| 编号 | 标准 | 阈值 | 状态 |
|------|------|------|------|
| A-1 | 计税正确率（分项税率 × 价值） | 100% | ✅ 分项矩阵测试 |
| A-2 | 预缴托管完整性（预缴额 = 计税额） | 零漂移 | ✅ 零漂移矩阵测试 |
| A-3 | 正和满意解税后一致性（Σ分配 = 税前 − 税款） | Shapley 效率性 | ✅ 一致矩阵测试 |
| A-4 | MOU 归零验证（T(y_t) > 0） | 恒成立 | ✅ |
| A-5 | 时延（实时计税快系统） | <10ms | ✅ 单次 + 批量 1000 平均 |
| A-6 | 单元测试覆盖率 | ≥90% | ✅ 99%（54/54 绿） |

## 运行

```bash
cd tdca-microtax
python -m pytest tests -q --cov=microtax --cov-report=term
```

## 纪律红线

- **MOU 不可降（ID79）**: 未计税/计税额 ≤0 拒绝预缴（NSFL-TRIGGER）
- **托管隔离（F-4/BV-3）**: 适配器无 withdraw/transfer/refund/release 提款路径
- **模拟态（ID92）**: `simulated=True` 显式标注（D-011 cbdc_anchor 参数）
- **快慢分工（ID71）**: 计税 <10ms 快系统；预缴为智能合约托管慢系统语义

## 待办（M2 后遗留）

- D-010 法学家基准 → 税率档位校准（模拟态转真实）
- DCEP 接入 → 预缴转硬数据（ID33 OTA）
- 白皮书 Solidity `_withholdTax`/`_settle` 真实合约落地（模拟适配器已建，真实合约待 DCEP 前置）
