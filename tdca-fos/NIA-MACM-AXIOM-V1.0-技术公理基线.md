# NIA-MACM 3.0 技术公理体系 · v1.0 基线

> 基线编号: NIA-MACM-AXIOM-V1.0 | 日期: 2026-08-11
> 授权: TDCA-PRINCIPLE-FUZZY-DISTANCE-001（人类确认，APPROVED FOR INTEGRATION）
> 定位: TDCA 数学能力验证双轨的技术公理基线——结构可信 + 认知可信
> 术语依据: TDCA-TERMINOLOGY-REGISTRY V1.1（G-1 基线）

---

## 一、基线组成（双协议技术公理对）

| 公理 | 验证对象 | 验证内容 | 状态 |
|------|---------|---------|------|
| **AXIOM-STRUCTURAL**（结构可信） | 效用精灵数学能力 | EXP-UTILITY-GENIE-MATH-001——Shapley/正和/反函数/优化/贝叶斯/MOU 锚定 51 测试绿 | ✅ v1.0 |
| **AXIOM-COGNITIVE**（认知可信） | 模糊数学运算层 | EXP-FUZZY-DISTANCE-001——贴近度/包含度不对称/置信度/三角模糊数/聚类 19 测试绿 | ✅ v1.0 |

## 二、公理内容摘要

### AXIOM-STRUCTURAL（源自 EXP-UTILITY-GENIE-MATH-001）
- 精确计算能力: Shapley 值（效率性/对称性/哑元公理）/ 正和满意解（ID84）/ 反函数（ID21）/
  优化（模拟退火/NSGA）/ 贝叶斯共轭后验 / MOU 税收锚定（ID79+ID43）
- 制度嵌入: 负空间熔断（NSFL-TRIGGER）/ 满意解非最优 / 人类决策权

### AXIOM-COGNITIVE（源自 EXP-FUZZY-DISTANCE-001）
- 不确定性表达: 模糊贴近度 4 算子 / 模糊包含度（命题 3.10 不对称）/ FUZZY_CONFIDENCE
  （方向+区间，ID85 可模糊计算）/ 三角模糊数 fail-closed / 模糊聚类
- 双保险: 模糊层 fail-closed 软拒绝 + 经典层 NSFL-TRIGGER 硬熔断

## 三、关联文档（存库位置）

| 文档 | 位置 |
|------|------|
| EXP-UTILITY-GENIE-MATH-001（效用精灵数学能力验证） | `tdca-utility-genie/EXP-UTILITY-GENIE-MATH-001-数学能力验证报告.md` |
| EXP-FUZZY-DISTANCE-001（模糊数学运算层验证） | `tdca-toolchain/EXP-FUZZY-DISTANCE-001-模糊数学运算层验证报告.md` |
| EXP-COGNITIVE-DISTANCE-001（多主体认知距离验证） | `tdca-toolchain/EXP-COGNITIVE-DISTANCE-001-多主体认知距离验证报告.md` |
| TDCA-PRINCIPLE-FUZZY-DISTANCE-001（制度确认） | `tdca-thinktank/governance/decisions/` |
| 本索引（NIA-MACM 技术公理基线） | `tdca-fos/NIA-MACM-AXIOM-V1.0-技术公理基线.md` |

## 四、适用域

- L2 配置权市场层认知辅助
- L3 效用计量层不确定性表达
- 限制: 不得替代经典层精确阈值判定（ID86 负空间熔断仍精确）

## 五、后续

- 模糊层 × 效用精灵化合（配置权定价/负空间预警/NCA 质量评估）→ DCD 立项或维护流程
- 公理版本演进: v1.0 基线冻结，扩展走 OTA（ID33）

> 本基线为技术公理存档（人类确认授权）；化合实现另行立项。
