# TDCA-TASK-MICROTAX-001 · M1 交付报告（计税器 + 预缴适配器）

> 里程碑: M1（M-1 微交付计税器 + M-2 税收预缴合约适配器）| 日期: 2026-08-12
> 任务书: TDCA-TASK-MICROTAX-001（V1.0-FROZEN）| 立项: DCD-MICROTAX-001
> 会话框: TDCA-SI-20260812-004-L1-2c18fd | 状态: ✅ M1 完成，待人类签批（M2 启动）
> 实现位置: `tdca-microtax/`（microtax/ 包 + tests/）

---

## 一、交付物清单

| 交付物 | 路径 | 说明 |
|--------|------|------|
| M-1 微交付计税器 | `tdca-microtax/microtax/tax_calculator.py` | 交付计量 → T(y_t) 分项金额（调度税/版税/交易费 + 合计）+ 税后净额 |
| M-2 税收预缴合约适配器 | `tdca-microtax/microtax/prepay_adapter.py` | 税款代扣托管（预缴语义）+ SM2 签名（模拟）+ 哈希审计（ID91）|
| M-4 微交付实体（骨架） | `tdca-microtax/microtax/models.py` | MicroDelivery 数据模型（交付价值/税收/净额/预缴状态，M-4 先行骨架）|
| 单元测试 | `tdca-microtax/tests/` | 34 用例，覆盖 A-1/A-2/A-4/A-5 |
| 模块说明 | `tdca-microtax/README.md` | 定位/复用/验收/纪律/待办 |

## 二、验收证据（A-1~A-6）

| 编号 | 标准 | 阈值 | 实测 | 证据 |
|------|------|------|------|------|
| A-1 | 计税正确率（分项税率 × 价值） | 100% | ✅ | 5 组数值矩阵 + 化合/日抛场景断言（调度税 2%/版税 7.5%/交易费 0.75% 逐项）|
| A-2 | 预缴托管完整性（预缴额 = 计税额） | 零漂移 | ✅ | 4 组零漂移矩阵 + verify_semantic 恒真 |
| A-4 | MOU 归零验证（T(y_t) > 0） | 恒成立 | ✅ | validate_mou 语义测试（0.01 极小值 → 归零拒绝）|
| A-5 | 时延（实时计税） | <10ms | ✅ | 单次 + 批量 1000 平均 <10ms（ID71 快系统）|
| A-6 | 单元测试覆盖率 | ≥90% | ✅ **98%** | pytest --cov 实测（131 stmts / 2 miss）|

**测试结果**: `34 passed`（tdca-microtax）；既有基座回归: tdca-call-rules **11 passed**（未受影响）。

## 三、缺口对应（任务书 §六 6 项）

| 缺口 | M1 处置 |
|------|--------|
| 1. 无计税内核 | ✅ M-1 计税器建立金额推导内核（dispatch/royalty/trade_fee 分项 + total + net）|
| 2. value 未参与计算 | ✅ value × 税率 = 分项金额（金额产出）|
| 3. compute_taxes 未接入微交付/缺 trade_fee | ✅ 补齐 trade_fee 分项；接入 MicroDelivery 实体 |
| 4. mou_escrow 预算 escrow 非税收 | ✅ M-2 预缴语义独立（verify_semantic 强制 amount==total）；测试断言无提款路径 |
| 5. Solidity 空壳 | ⏳ 模拟态适配器已建（D-011），真实合约落地归 M2/遗留项 |
| 6. 无 micro-delivery 实体 | ✅ MicroDelivery 实体落盘（M-4 骨架先行）|

## 四、纪律红线核验

- **MOU 不可降（ID79）**: 未计税 / 计税额 ≤0 → 拒绝预缴（NSFL-TRIGGER，测试覆盖）✅
- **ID90 最小化合**: 复用 CALL-RULES `TaxRates`（sys.path 顶层导入），无新建税率体系 ✅
- **ID71 快慢分工**: 计税 <10ms（快系统）；预缴为托管语义（慢系统）✅
- **F-4/BV-3 托管隔离**: 适配器仅 prepay/verify/get，**无 withdraw/transfer/refund/release 提款接口**（测试断言）✅
- **ID92 模拟态**: `simulated=True` 显式标注（D-011 cbdc_anchor 参数）✅
- **ID91 审计**: 每笔预缴 data_hash + signature + 规范化载荷（防注入）✅

## 五、端到端演示（10000 元化合交付）

```
计税 T(y_t):    {dispatch_tax: 200.0, royalty: 750.0, trade_fee: 75.0, total: 1025.0}
税后净额:       8975.0 | MOU 锚定 T(y_t)>0: True
预缴记录:       TAXPRE-MD-DEMO-001, 金额 1025.0, 零漂移 True, 完整性 True
微交付实体:     prepay_status=PREPAID, prepay_ref=TAXPRE-MD-DEMO-001
```

## 六、M2 计划（待人类签批 M1 后启动）

| 任务 | 内容 | 验收 |
|------|------|------|
| M-3 正和满意解税后集成 | 税后净额 → 效用精灵正和求解（Shapley 分配税后）+ MOU 归零 | A-3 税后一致 |
| M-4 微交付域实体补全 | participants 贡献 → 正和输入；实体生命周期收尾 | A-6 保持 ≥90% |
| A-1~A-6 全量验收 | 计税/预缴/税后/归零/时延/覆盖 | 全通过 |

## 七、遗留核验项

- D-010 法学家基准 → 税率档位校准（模拟态转真实）
- DCEP 真实接入 → 预缴转硬数据（ID33 OTA）
- 白皮书 Solidity `_withholdTax`/`_settle` 落地（真实合约，M2 后评估）

---

> 本报告为 M1 交付证据；验收通过后由人类签批（NCA 存证）进入 M2。
