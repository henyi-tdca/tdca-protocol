# TDCA-TASK-MICROTAX-001 · M2 交付报告（正和税后集成 + 微交付实体，任务书整体收官）

> 里程碑: M2（M-3 正和满意解税后集成 + M-4 微交付域实体补全）| 日期: 2026-08-12
> 任务书: TDCA-TASK-MICROTAX-001（V1.0-FROZEN）| 立项: DCD-MICROTAX-001
> 会话框: TDCA-SI-20260812-004-L1-2c18fd | 状态: ✅ **M1+M2 全部完成，A-1~A-6 全达标，待人类整体签批**
> 实现位置: `tdca-microtax/`（microtax/ 包 + tests/）

---

## 一、交付物清单（M1+M2 全量）

| 任务 | 交付物 | 路径 | 说明 |
|------|--------|------|------|
| M-1 | 微交付计税器 | `microtax/tax_calculator.py` | 交付计量 → T(y_t) 分项金额（调度税/版税/交易费 + 合计）+ 税后净额 |
| M-2 | 税收预缴合约适配器 | `microtax/prepay_adapter.py` | 税款代扣托管（预缴语义，区别于预算 escrow）+ SM2 签名（模拟）+ 哈希审计 |
| M-3 | 正和满意解税后集成 | `microtax/positive_sum_integration.py` | 税后净额 → Shapley 分配（复用 MOUSplitContract）→ MOU 归零验证 |
| M-4 | 微交付域实体 | `microtax/models.py` | MicroDelivery（交付价值/税收/净额/预缴状态/participants 贡献）|
| 兜底 | Shapley 兜底 | `microtax/_fallback_split.py` | 无基座环境精确/近似 Shapley（100% 覆盖）|
| 测试 | 验收测试 | `tests/`（4 文件） | 54 用例，A-1~A-6 全覆盖 |

## 二、验收证据（A-1~A-6 全量）

| 编号 | 标准 | 阈值 | 实测 | 证据 |
|------|------|------|------|------|
| A-1 | 计税正确率（分项税率 × 价值） | 100% | ✅ | 5 组数值矩阵 + 化合/日抛/极小值断言（2%/7.5%/0.75% 逐项）|
| A-2 | 预缴托管完整性（预缴额 = 计税额） | 零漂移 | ✅ | 4 组零漂移矩阵 + verify_semantic 恒真 + 篡改拒绝 |
| A-3 | 正和税后一致性（Σ分配 = 税前 − 税款） | Shapley 效率性 | ✅ | 4 组一致矩阵 + 单/双/三参与方效率性 + 篡改拒绝 |
| A-4 | MOU 归零验证（T(y_t) > 0） | 恒成立 | ✅ | 归零拒绝（结算侧门）+ 恒真断言 |
| A-5 | 时延（实时计税快系统） | <10ms | ✅ | 单次 + 批量 1000 平均（ID71）|
| A-6 | 单元测试覆盖率 | ≥90% | ✅ **99%** | pytest --cov 实测（217 stmts / 3 miss）|

**测试结果**: `54 passed`（tdca-microtax）；基座回归: tdca-call-rules **11 passed** + tdca-translator-market **7 passed**（M-3 Shapley 复用方）。

## 三、全链路端到端演示（10000 元化合交付，三参与方）

```
1. 计税 T(y_t):  {dispatch_tax: 200.0, royalty: 750.0, trade_fee: 75.0, total: 1025.0}
   税后净额:     8975.0
2. 预缴:        TAXPRE-MD-E2E-001, 金额 1025.0, 零漂移 True, 完整性 True
3. 税后分配:    agent-a 4362.85 / agent-b 2717.43 / agent-c 1894.72
   Σ = 8975.0 = 净额（A-3 一致 True）
4. MOU 归零:    T(y_t)=1025.0 > 0（A-4 True）| 正和协同 synergy=1.2
```

**闭环达成**: `微交付完成 → 实时计税 → 税收预缴（合约托管）→ 正和满意解（税后）→ MOU 归零 → NCA 存证`

## 四、纪律红线核验（全量）

- **ID79 MOU 不可降**: 未计税/未预缴/计税额 ≤0 → 结算拒绝（NSFL-TRIGGER，前置门测试覆盖）✅
- **ID90 最小化合**: 复用 CALL-RULES `TaxRates` + translator-market `MOUSplitContract`，无新建平行体系 ✅
- **ID71 快慢分工**: 计税 <10ms（快系统）；预缴/结算为托管语义（慢系统）✅
- **F-4/BV-3 托管隔离**: 适配器无 withdraw/transfer/refund/release 提款接口（测试断言）✅
- **ID92 模拟态**: `simulated=True` 显式标注（D-011 cbdc_anchor 参数），全链路传递 ✅
- **ID91 审计**: 预缴 data_hash + signature + 规范化载荷（防注入）；结算结果含完整审计轨迹字段 ✅

## 五、缺口闭合状态（任务书 §六 6 项）

| 缺口 | 状态 | 闭合证据 |
|------|------|---------|
| 1. 无计税内核 | ✅ 闭合 | M-1 金额推导内核（分项+合计+净额）|
| 2. value 未参与计算 | ✅ 闭合 | value × 税率 = 分项金额 |
| 3. compute_taxes 未接入微交付/缺 trade_fee | ✅ 闭合 | trade_fee 分项补齐 + MicroDelivery 接入 |
| 4. mou_escrow 预算 escrow 非税收 | ✅ 闭合 | M-2 预缴语义独立（verify_semantic 强制）+ M-3 税后 Shapley 与预算分割语义区分 |
| 5. Solidity 空壳 | 🟡 模拟态落地 | 适配器已建（D-011）；真实合约待 DCEP 前置（遗留）|
| 6. 无 micro-delivery 实体 | ✅ 闭合 | MicroDelivery 域实体（M-4）|

## 六、遗留核验项（任务书 §八）

- D-010 法学家基准 → 税率档位校准（模拟态转真实）
- DCEP 真实接入 → 预缴转硬数据（ID33 OTA）
- 白皮书 Solidity `_withholdTax`/`_settle` 真实合约落地（待 DCEP 前置）

## 七、后续联动

- 本任务书整体交付 → 人类签批 → FROZEN（M1/M2 冻结确认）
- 与效用精灵正和结算/MOU 管线集成（既有 ns-ops/sbx-ops 生态衔接）
- 通知机接入（TDCA-FC-20260811-004）→ 暂缓解除后可恢复

---

> 本报告为任务书整体交付证据（M1+M2）；验收通过后由人类签批（NCA 存证）冻结。
