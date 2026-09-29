# TDCA-TASK-ECOWEIGHT-001 · M1/M2 交付报告（主体配置权场景价值权重 + 零和负和熔断）

> 里程碑: M1（E-1 主体买卖总量 + E-2 生态权重）+ M2（E-3 零和负和熔断 + E-4 引擎集成）| 日期: 2026-08-12
> 任务书: TDCA-TASK-ECOWEIGHT-001（V1.0-FROZEN，DCD-ECOWEIGHT-001）| 状态: ✅ **M1+M2 完成，F-1~F-5 全达标，待人类整体签批冻结**
> 实现位置: `tdca-microtax/microtax/subject_eco_weight.py`（E-1/E-2/E-3）+ `economic_cognition.py`（E-4 集成）

---

## 一、交付物清单

| 功能 | 交付物 | 路径 | 说明 |
|------|--------|------|------|
| E-1 | 主体级买卖总量模型 | `subject_eco_weight.py` | MOU_i = buy_i + sell_i（进项+出项，非单边指标）|
| E-2 | 经济生态权重计算 | 同上 | w_i = MOU_i / ΣMOU_j（Σw=1；整体零和时均分）|
| E-3 | 零和/负和熔断 | 同上 | MOU_i ≤ 0 → 经济生态熔断 → 沙盒重塑/休眠（可恢复，区别于 SBX-BANNED 法律永久）→ 禁入该场景 → 配置价值低 |
| E-4 | 经济认知引擎集成 | `economic_cognition.py` | cognize 增加 subject_eco 参数 + 报告 subject_econ 块（assessments/weights/fused/blocked）|
| E-5 | 验收测试 | `tests/test_ecoweight.py`（12 用例）| F-1~F-5 |

## 二、验收证据（F-1~F-5）

| 编号 | 标准 | 阈值 | 实测 | 证据 |
|------|------|------|------|------|
| F-1 | 主体权重正确（买卖总量非单边）| Σw=1 | ✅ | 买卖总量 MOU_i=buy+sell 断言 + 单边≠总量 + Σw=1 |
| F-2 | 零和/负和熔断判定 | 熔断+处置+禁入 | ✅ | 零和/负和 → economic_fused + sandbox_reshape/dormant + scene_config_blocked + config_value=low |
| F-3 | 集成报告含主体级块 | subject_econ | ✅ | 报告 subject_econ（assessments/weights/fused_subjects/scene_config_blocked）|
| F-4 | 覆盖率 ≥90% | ✅ **98%** | microtax 全量 cov 98% |
| F-5 | 回归全绿 | ✅ | microtax 167 passed（+12）+ 四库回归保持 |

**测试结果**: microtax 167 passed（155 + 12 ecoweight）；COGNITION 旧测试适配 subject_econ 新字段（8 字段断言）。

## 三、端到端验证（主体生态权重 + 经济熔断）

```
1. 主体权重: {agent-a: 1.0（MOU 5000）, agent-b: 0.0（零和）} | Σ = 1.0
2. 经济熔断: fused=[agent-b] | 禁入该场景=[agent-b]
3. 处置:     agent-a disp=none value=high | agent-b disp=sandbox_reshape value=low
4. 场景级:   U_正和 1.0 | 完整经济认知 True
```

**闭环达成**: `主体买卖总量（MOU_i=buy+sell）→ 经济生态权重（w_i）→ 零和/负和→经济熔断（沙盒重塑/休眠 + 禁入该场景）→ 配置价值判定 → 完整经济认知报告`

## 四、纪律落实

- **语义确认（人类 2026-08-12）**: 主体价值=买卖总量→生态权重；零和/负和→经济熔断→沙盒重塑/休眠→禁入该场景→价值低——全部落实
- **经济熔断 vs 法律永久休眠区分**: 经济级处置可恢复（sandbox_reshape/dormant），区别于 SBX-BANNED（ID86 法律永久休眠不可逆）
- **COGNITION-001 不破坏**: 场景级 U_正和 三条件不变（θ/ϕ 不改）；仅新增主体级段
- **ID92**: simulated 标注（D-011）

## 五、里程碑状态

| 里程碑 | 内容 | 状态 |
|--------|------|------|
| M0 | 立项（DCD-ECOWEIGHT-001，语义确认）| ✅ 完成 |
| M1 | 主体模型 + 权重（E-1/E-2）| ✅ 完成 |
| M2 | 熔断处置 + 引擎集成（E-3/E-4）+ F-1~F-5 | ✅ 全达标（本报告）|

## 六、遗留核验项

- 主体级 buy_i/sell_i 真实采集（NIA-MACM PHASE-2；当前演示输入）
- 沙盒重塑路径与 SBX-OPS 生态实际衔接（经济级可恢复处置）
- 生态溢出 ϕ 真实标定

---

> 本报告为任务书整体交付证据（M1+M2）；验收通过后由人类签批（NCA 存证）冻结。
