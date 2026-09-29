# 效用精灵 × 模糊数学层化合交付报告

> 交付编号: TDCA-FUZZY-INTEGRATION-001 | 日期: 2026-08-11
> 授权: TDCA-PRINCIPLE-FUZZY-DISTANCE-001（§五 化合授权，人类确认）
> 实现: `tdca-utility-genie/fuzzy_integration.py`（FuzzyUtilityGenieIntegration）
> 验收: 69 测试全绿（化合 18 + 既有 51），化合层覆盖率 96%
> 术语依据: TDCA-TERMINOLOGY-REGISTRY V1.1（G-1 基线）

---

## 一、交付物

| # | 交付物 | 说明 |
|---|--------|------|
| 1 | fuzzy_input 接口 | utility_genie 接收模糊层输出（置信度/包含度/聚类）→ fuzzy_context |
| 2 | ID90 三条件检查 | 不可拆分性/涌现价值/非线性（化合必要性，最小化合） |
| 3 | 模糊度水印 | λ 阈值/算子选择/fail-closed 触发记录 → NCA 审计 |
| 4 | 三化合场景 | 配置权定价/负空间预警/NCA 质量评估 |
| 5 | 测试 | test_fuzzy_integration.py（18 用例） |

## 二、接口契约（TDCA-PRINCIPLE §五 对齐）

```
utility_genie.fuzzy_input(confidence_matrix, subsethood_matrix, lambda_clusters)
    → fuzzy_context {confidence_matrix, subsethood_matrix, lambda_clusters,
                     lambda_threshold, operator_selection}
    → utility_genie.compute(config_vector, fuzzy_context)
```

## 三、三化合场景实现

### 1. 配置权定价（compound_pricing）——Shapley 认知权重修正
- 认知权重: 主体被 others 包含度均值（subsethood(s→o)）**相对群体均值修正**
  （绝对值受认知重叠干扰——高认知主体互含度高拉高 contained）
- 低认知主体（contained > 均值）→ 权重上浮（哑元风险补偿，UPDA 倾斜）
- 效率性保持: 加权后归一化回原 Shapley 总额

### 2. 负空间预警（compound_early_warning）——群体理性约束
- 分裂度 = (簇数−1)/(主体−1)（0=凝聚，1=完全分裂）
- HIGH（>0.5）/ MEDIUM（>0.25）/ LOW——预判协作破裂，正和满意解可靠性
- 空输入 → fail-closed（UNKNOWN + 水印标记）

### 3. NCA 质量评估（compound_nca_quality）——认知资产折旧率
- 平均包含度（高=低原创性）→ 折旧率 → MOU 锚定降权
- 低包含度（高原创性）→ 折旧率低 → MOU 保持

## 四、制度合规

- ✅ ID90: 化合前三条件检查（未知场景拒绝——不盲目化合）
- ✅ ID71: 低置信/无显著差异 → 经典结果标记「需人工复核」（慢系统接口预留）
- ✅ ID86: 模糊层不替代经典精确阈值判定（负空间熔断仍精确）
- ✅ 审计: 模糊度水印恒入 NCA（λ/算子/fail-closed 记录）
- ✅ 术语 G-1: 仅注册表 V1.1

## 五、遗留

- 化合场景扩展（ID90 三条件逐场景实判——当前三场景常量通过，扩展需动态验证）
- 与 ECE 引擎化合（TDCA-PRINCIPLE 授权范围含 ECE ENGINE——下一步）
- fuzzy_input 与 utility_genie.compute 全流程串联（当前化合层独立工具集）

## 六、签批

| 角色 | 签署 | 状态 |
|------|------|------|
| 化合工程师 | Reasonix（代行落档） | ✅ |
| 制度设计师（H） | HUMAN-FOUNDER-001（人类裁决 2026-08-11） | ✅ **APPROVED → FROZEN**（DCD-FUZZY-INTEGRATION-001） |

> **冻结备注（人类裁决）**: 效用精灵×模糊层化合层基线锁定（fuzzy_input/ID90/水印/三场景）；遗留推进：化合与 ECE 引擎（TDCA-PRINCIPLE 授权范围）、ID90 动态实判、fuzzy_input→compute 全流程串联。
