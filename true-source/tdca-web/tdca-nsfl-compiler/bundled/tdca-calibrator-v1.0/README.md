# TDCA 通用校准器（tdca-calibrator）v1.0

> 许可：Apache-2.0（LICENSE 全文在包内）｜ 本包为 TDCA 自研件，许可由 TDCA 自选
> 性质：按使用者声明之参数集做经验校准；参数名／值域／单位皆由使用者给，本器不硬编码任何特定参数。

## 一、这是什么

通用经验校准工具：给定参数声明（名／值域／单位／初值）、判据声明（收敛或误差带＋迭代或耗时上限）、样本（含来源标注与缺失值口径），在参数值域内搜索使模型残差最小之校准值，并给出误差带与拟合质量读数。纯 Python 标准库，零第三方依赖。

## 二、三件输入（缺一拒跑，⛔ 取默认值）

| 件 | 格式 | 要件 |
|---|---|---|
| 参数声明 `params.json` | `{"parameters":[{"name","min","max","unit","initial"}, …]}` | 名／值域／单位／初值四要素齐；初值须落于值域内 |
| 判据声明 `criteria.json` | `{"max_rmse":…, 和/或 "max_error_band":…, "max_iterations":…, 和/或 "max_seconds":…}` | 收敛判据与上限各至少其一 |
| 样本 `samples.json` | `{"source":"real"│"synthetic"│"simulated", "missing_policy":…, "observations":[{"x":…, "y":…}, …]}` | 来源标注三选一必写；缺失值口径必写；每观测须有目标 `y`，协变量为观测自身字段 |

另有第四件 **`model.txt`**（模型表达式，以参数名与观测字段为变元，如 `a + b*x`）：未给时无法建立参数→目标映射，按输入自相矛盾如实报（⛔ 空跑）。

**缺任一件 ⟹ 拒跑**，明示缺哪件，退出码 2。

## 三、四件输出（齐）

```json
{
  "calibrated_values":  {"a": …, "b": …},
  "error_band_95":      0.0109,
  "fit_quality":        {"rmse","residual_std","mean_abs_residual","sample_coverage","outlier_count","outlier_indices","dof"},
  "unmet_criteria":     [],
  "criteria_met":       true,
  "run_meta":           {"tool","version","input_summary_sha256_16","sample_source","missing_policy","n_samples","n_parameters","seed","iterations","seconds"}
}
```

质量不足（样本量仅勉强过线）时误差带标 `null` 并说明——**⛔ 只给数不给限**。

## 四、失败面四类（如实报，⛔ 择一执行）

| 面 | 触发 | 出口 |
|---|---|---|
| 不收敛 `not_converged` | 迭代/耗时上限用尽仍不达声明判据 | 报判据声明值与实测值，退出码 1 |
| 样本不足 `insufficient_samples` | n < k+1 等自由度不足 | 给最小所需量估计，退出码 2 |
| 参数不可识别 `unidentifiable` | 某参数对目标敏感度近零 | 列可疑参数组，退出码 1 |
| 输入自相矛盾 `contradiction` | 值域/初值/判据/模型彼此冲突 | 报冲突点，退出码 2 |

## 五、⛔ 不该用

- ⛔ 替代理论推导或形式化证明（本器为经验拟合）；
- ⛔ 用于安全关键阈值的最终裁定；
- ⛔ 以合成样本声称真实精度（source 标注须如实，合成即合成）；
- ⛔ 跨域外推而不标风险。

## 六、边界与已知事项

- 搜索策略：值域均匀随机采样（固定种子）＋坐标轮询局部细化；同输入同版本输出可复现（`run_meta.seconds` 为环境读数除外）。
- 误差带为残差标准误×1.96 的大样本近正态近似；小样本（n  barely > k）时读数偏乐观，请结合 sample_coverage 与 outlier_count 判断。
- 模型表达式经受限命名空间求值（无内建，仅 math 常用函数），⛔ 任意代码执行面。
- 观测协变量缺字段时模型求值按输入矛盾如实报，不静默补默认。

## 七、用法与自测

```
python calibrator.py params.json criteria.json samples.json model.txt
python selftest.py     # 7 项：正常校准/拒跑/四类失败面各一/可复现；退出码 0 全过
```

## 八、编号说明

出包前经脱敏八模式复扫（六模式＋会话框号族＋编制者名）：**0 命中**（样例数据为合成演示数据，件内已标注，不冒充真实运行协议）。

---

*出包：TDCA 执行侧 · v1.0 · 合成样例数据；本器输出不构成任何合规、认证或审计效力。*
