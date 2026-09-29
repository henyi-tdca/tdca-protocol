# TDCA-TASK-COGNITION-001 · M1/M2 交付报告（多主体认知 × 效用精灵 × 税收计算 = 完整经济认知）

> 里程碑: M1（C-1 认知接入 + C-2 效用精灵扩展）+ M2（C-3 经济认知引擎 + C-4 融合验证）| 日期: 2026-08-12
> 任务书: TDCA-TASK-COGNITION-001（V1.0-FROZEN，DCD-COGNITION-001）| 状态: ✅ **M1+M2 完成，D-1~D-5 全达标，待人类整体签批冻结**
> 实现位置: `tdca-utility-genie/solvers/positive_sum_solver.py`（C-2）+ `tdca-microtax/microtax/economic_cognition.py`（C-3/C-1/C-4）
> **本体论修正（2026-08-12，用户纠偏后）**: 正和效用 = MOU（进项+出项税收总额）= 场景总效用正和，**非税后净额**（税后净额仅分配语义）——实现已按此修正

---

## 一、交付物清单

| 功能 | 交付物 | 路径 | 说明 |
|------|--------|------|------|
| C-1 | 多主体认知接入 | `tdca-microtax/microtax/economic_cognition.py` | CognitiveDistanceCalculator 集成（距离矩阵 + 不对称 + 协商触发 0.35）|
| C-2 | 效用精灵正和扩展 | `tdca-utility-genie/solvers/positive_sum_solver.py` | solve 增加 `resource_pool` 可选参数（税后净额注入；缺省硬编码——向后兼容 78 测试绿）|
| C-3 | 完整经济认知引擎 | `tdca-microtax/microtax/economic_cognition.py` | EconomicCognitionEngine：认知 → 计税 → 正和 → 报告四段闭环；participants 传递链补全 |
| C-4 | 融合验证 | 同上（verdict 块）| U_正和 三条件（TREATISE-026：ΔMOU>0 ∧ min(S_协作)≥θ=0.70 ∧ 生态溢出/核心MOU>ϕ=0.30）|
| C-5 | 验收测试 | `tdca-microtax/tests/test_cognition.py`（13 用例）| D-1~D-5 |

## 二、验收证据（D-1~D-5）

| 编号 | 标准 | 阈值 | 实测 | 证据 |
|------|------|------|------|------|
| D-1 | 认知距离矩阵正确 | 100% | ✅ | 不对称距离矩阵（0.0456/0.0479）+ 低认知组协商触发测试 |
| D-2 | 正和效用 = MOU（场景总效用） | Σ分配 = MOU = 进项+出项 | ✅ | resource_pool=5000（MOU）→ Σ分配 5000.00（pool_semantics="mou"）|
| D-2' | 本体论纠偏落实 | 净额不作正和度量 | ✅ | taxation 块区分 mou_value（正和依据）/net_value（分配语义）；ΔMOU 判定基于 MOU |
| D-3 | 完整经济认知报告全字段 | 认知+税收+正和+判定 | ✅ | to_dict 7 字段断言（cognition/taxation/positive_sum/verdict/full_cognition/simulated）|
| D-4 | 覆盖率 ≥90% | ✅ **98%** | microtax 全量 cov 98% |
| D-5 | 回归全绿 | ✅ | microtax 155 + utility-genie 78 + toolchain 109 + nsfl-compiler 121 + ns-runtime 111 |

**测试结果**: microtax 155 passed（+13 cognition）；utility-genie 78（C-2 向后兼容确认）；toolchain 109（认知基座）。

## 三、端到端验证（完整经济认知闭环，本体论修正版）

```
1. 多主体认知: 距离矩阵 {a-a:0.0, a-b:0.0456, b-a:0.0479, b-b:0.0} | min 认知 0.8365
2. 税收:       计税 200.0 | MOU（进项+出项）5000.0 | 净额（分配语义）9800.0
3. 正和(场景总效用): 资源池语义 mou = MOU 5000.0 | Σ分配 5000.0
4. 融合判定:    U_正和 1.0 | ΔMOU>0 True | 溢出比例 0.4 > 0.30 True
5. 完整经济认知: full_cognition True
```

**闭环达成**: `多主体认知（距离/对齐/协商）→ 税收计算（计税/预缴/MOU/法规）→ 效用精灵正和（MOU 场景总效用资源池）
→ 融合验证（U_正和 TREATISE-026）→ 完整经济认知报告`

## 三·A 本体论修正记录（用户纠偏 2026-08-12）

- **纠偏**: 「在 TDCA 中正和效用不是算税收净额，是算税收进项与出项的总额；效用正和不是买卖的正和剩余，是场景总效用正和」
- **修正**: ① 效用精灵资源池 net_value → **MOU（tax_in+tax_out）**；② ΔMOU 判定 tax_total → **MOU>0**；③ 生态溢出比例分母 tax_total → **MOU**；④ 报告标注 pool_semantics="mou" + taxation 块区分 mou_value（正和依据）/net_value（分配语义）
- **对齐权威**: MOU = 进项+出项（TERMS-001:147）+ TREATISE-026（U_正和 基于 ΔMOU）
- **M-3 关系**: TaxAfterPositiveSumSettlement（V1 冻结）的 net_value Shapley 分配为**分配语义**（已冻结不重启）；本引擎的正和**判定语义**用 MOU——两者职责区分，若后续需统一走 DCD 变更

## 四、纪律落实

- **T-007**: θ=0.70 恒为登记值（测试断言，不得改值）
- **TREATISE-026**: U_正和 三条件合取（R5=B 人类裁决）落地为 verdict 块
- **裁决①**: EconomicCognitionEngine 在 tdca-microtax 扩展（ID90——复用税务官 on_delivery 税后净额）
- **裁决②**: resource_pool 参数注入（缺省行为不变，向后兼容 78 测试绿）
- **fail-closed**: 认知/效用精灵基座缺失 → 拒绝完整认知（运行时自举，禁止静默降级）
- **法规约束**: 违规交付 → 完整认知 fail-closed（L-CN-TX-001 测试）
- **ID92**: 报告 simulated=True 标注（D-011）

## 五、里程碑状态

| 里程碑 | 内容 | 状态 |
|--------|------|------|
| M0 | 立项（DCD-COGNITION-001，两项裁决）| ✅ 完成 |
| M1 | 认知接入 + 效用精灵扩展（C-1/C-2）| ✅ 完成 |
| M2 | 经济认知引擎 + 融合验证（C-3/C-4）+ D-1~D-5 | ✅ 全达标（本报告）|

## 六、遗留核验项

- D-010 法学家基准（税率档位校准，ID33 OTA）
- 认知状态 S_协作 真实采集（当前演示输入；对接 NIA-MACM PHASE-2 交换协议）
- 生态溢出指标真实标定（ϕ 参数）

---

> 本报告为任务书整体交付证据（M1+M2）；验收通过后由人类签批（NCA 存证）冻结。
