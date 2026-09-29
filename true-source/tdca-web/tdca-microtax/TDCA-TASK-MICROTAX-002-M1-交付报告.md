# TDCA-TASK-MICROTAX-002 · M1 交付报告（基座修订 V2）

> 里程碑: M1（M-1 计税器 V2 + M-2 预缴适配器 V2 + M-3 扩展 + M-4 实体 V2）| 日期: 2026-08-12
> 任务书: TDCA-TASK-MICROTAX-002（V1.0-FROZEN，DCD-MICROTAX-003）| 状态: ✅ M1 完成，待人类签批（M2 启动）
> 实现位置: `tdca-microtax/`（V1 基座不动，V2 扩展层新增）

---

## 一、交付物清单（M1）

| 任务 | 交付物 | 路径 | 说明 |
|------|--------|------|------|
| M-1 | 微交付计税器 V2 | `microtax/event_tax_calculator.py` | TaxEventType 事件分档（6 类映射 CALL-001 三档）+ 双向进项/出项贡献事实（MOU=和）+ Decimal 精度 + 纳税事实记录 |
| M-2 | 税收预缴适配器 V2 | `microtax/v2_prepay_adapter.py` | fail-closed 预冻结（数据不足→不上链）+ 纳税事实记录（不随归零丢失）+ 零漂移 + 托管隔离 |
| M-3 | 正和税后集成扩展 | `event_tax_calculator.py::to_v1_taxes()` | V2 计税结果 → V1 兼容结构（positive_sum_integration 无改动复用，双轨输入兼容）|
| M-4 | 微交付实体 V2 | `microtax/models.py` | TaxEventType/DeliveryForm/DisputeStatus 枚举 + tax_in/tax_out/event_type/delivery_form/dispute_status/tax_fact_recorded 字段（默认值向后兼容 V1）|

## 二、验收证据（M1 范围）

| 编号 | 标准 | 实测 | 证据 |
|------|------|------|------|
| A-1 | 计税 100%（事件分项 × 双向贡献） | ✅ | 6 类事件分档矩阵（配置权调用/NCA 化合/Skill 调用/跨域/托管释放/负空间）+ 数值一律映射 CALL-001 三档 |
| A-2 | 预缴零漂移 + fail-closed | ✅ | 正常零漂移 + MOU 溢出/归零 → FAIL_CLOSED 预冻结（amount=0）|
| A-3 | 正和税后一致性 | ✅ | V1 A-3 测试保留（V2 经 to_v1_taxes 兼容层接入）|
| A-4 | MOU 归零 + 纳税事实记录 | ✅ | T(y_t)>0 恒成立；负空间归零时 tax_fact_recorded=True（语义修正核心）|
| A-5 | 时延 <10ms | ✅ | V2 单次 + 批量 1000 平均 |
| A-6 | 覆盖率 ≥90% | ✅ **98%** | pytest --cov 实测（365 stmts / 6 miss）|

**测试结果**: `82 passed`（V1 54 + V2 28）；基座回归 tdca-call-rules **11 passed**（未受影响）。

## 三、裁决/纪律落实（DCD-MICROTAX-003）

| 项 | 落实 |
|----|------|
| 裁决① 税率口径 | TaxEventType 分档结构采纳；数值一律 `CALL-001` 三档（2%/7.5%/0.75%，模拟态 D-011）；6%/9%/3% 未引入 |
| 裁决② 三池分流 | 未实现（DRAFT 不入代码）；税收去向=预缴托管归集 |
| 裁决③ 报告税 | 未引入（M-9 阶段默认 0）|
| ID 纪律 | 代码注释一律 ID79/ID80/ID43/ID71/ID85/ID91/ID92；ID69/ID70 未引用 |
| 第四态 | 未实现 BLOCKED（fail-closed 仅为预缴状态语义，遵循 DCD-NSFL-M1-FROZEN-001）|
| mou_contribution | 未用 10% 估算（双向 tax_in/tax_out 显式输入，链上申报语义）|

## 四、本体论基线落实（TDCA-TAX-SEMANTIC-REVISION-001）

- 「调用即产生纳税事实」: `tax_fact_recorded=True` 在**一切路径**置位（正常/冻结/归零）——纳税事实成立不随税额归零丢失（测试断言）
- 双向贡献: `MOU = tax_in + tax_out`（买方进项事实 + 卖方出项事实，ID79）
- 负空间熔断: 税额归零但事实记录（`NEGATIVE_SPACE_FUSE` 路径）

## 五、M2 计划（待人类签批 M1 后启动）

| 任务 | 内容 | 验收 |
|------|------|------|
| M-5 领域一聚合缴纳器 | 小散高频批量计税 + 聚合申报（Σ聚合 = Σ单笔）| A-7 聚合零漂移 / A-5 批量 <10ms/千笔 |
| M-8 实时税收账本 | 事件溯源不可变追加（ID80 O(n) 审计）+ NCA 索引 | A-6 保持 ≥90% |

## 六、遗留核验项

- D-010 税率档位校准（模拟态转真实，ID33 OTA）
- DCEP 真实接入 → 预缴转硬数据（ID33 OTA）
- M-6/M-7/M-9（领域二交付结算 + 争议增信保险 + 税收 NCA）→ M3 里程碑

---

> 本报告为 M1 交付证据；验收通过后由人类签批（NCA 存证）进入 M2。
