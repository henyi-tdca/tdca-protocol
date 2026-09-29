# TDCA-TASK-TAXLAW-001 · M1/M2 交付报告（财税法规纳入负空间编译器 + 税务官决策依据）

> 里程碑: M1（L-1 法规清单 + L-2 素材导入）+ M2（L-3 编译验证 + L-4 税务官接入）| 日期: 2026-08-12
> 任务书: TDCA-TASK-TAXLAW-001（V1.0-FROZEN，DCD-TAXLAW-001）| 状态: ✅ **M1+M2 完成，B-1~B-5 全达标，待人类整体签批冻结**
> 实现位置: `tdca-ns-runtime/ns_runtime/static_list.py`（L-1）+ `tdca-nsfl-compiler/nsfl_compiler/`（L-2/L-3）+ `tdca-microtax/microtax/tax_officer.py`（L-4）

---

## 一、交付物清单

| 功能 | 交付物 | 路径 | 说明 |
|------|--------|------|------|
| L-1 | 财税法规清单扩展 | `tdca-ns-runtime/ns_runtime/static_list.py` | L1-R1 静态清单新增 NSL-LEGAL-013~016（偷税/骗税/规避锚定/申报失实，domain=tax，LEGAL/HIGH）|
| L-2 | 法规素材导入内容化 | `tdca-nsfl-compiler/nsfl_compiler/tax_regulations.py` | 5 条法规素材（税收征管法 63/66 条种子 + 宪法第12/18条 + 定义5.19）+ 违规模式→法规映射 |
| L-3 | TAX 域编译验证 | `tdca-nsfl-compiler/nsfl_compiler/compiler.py` | compile_for_scene 的 legal_refs 支持法规内容 dict（要点注入审计，str 向后兼容）|
| L-4 | 税务官法规决策接入 | `tdca-microtax/microtax/tax_officer.py` | check_regulatory_compliance（显式违规 + 自动检测 bypass_mou）+ fail-closed 前置熔断 + 轨迹 law_id；法规基座缺失拒绝决策（防静默降级）|
| L-5 | 验收测试 | `tdca-microtax/tests/test_taxlaw.py`（14 用例）| B-1~B-5 |

## 二、验收证据（B-1~B-5）

| 编号 | 标准 | 阈值 | 实测 | 证据 |
|------|------|------|------|------|
| B-1 | 财税法规编译正确率（偷税/骗税/规避锚定/申报失实 → ⊗ LEGAL 熔断）| 100% | ✅ | 静态清单 4 条断言 + 4 违规模式熔断测试 + 合规不熔断 |
| B-2 | 税务官法规决策（违规交付 fail-closed 拒绝）| fail-closed | ✅ | 显式偷税（L-CN-TX-001）/自动检测规避锚定（TDCA-ART-12）/申报失实（TDCA-ART-18）→ NSFL-TRIGGER |
| B-3 | 决策轨迹含法条引用 | 100% | ✅ | regulatory 字段 + 异常含 law_id（B-2 证据）|
| B-4 | 覆盖率 ≥90% | ✅ **98%** | microtax 全量 cov 98%（tax_officer.py 100%）|
| B-5 | 回归全绿 | ✅ | microtax 142 + nsfl-compiler 121 + ns-runtime 111 全 passed |

**测试结果**: microtax 142 passed（+14 taxlaw）；编译器 121 passed（+L-3 兼容回归）；ns-runtime 111 passed（+L-1 扩展未破坏）。

## 三、端到端验证（法规决策链路）

```
1. 合规交付: tax 20.0 | regulatory [] | prepay PREPAID
2. 偷税:      BLOCKED（L-CN-TX-001 fail-closed——禁止偷税）
3. 规避锚定:  BLOCKED（TDCA-ART-12 自动检测——MOU=0 大额）
4. 静态清单:  偷税 True | 骗税 True | 合规 False
```

**闭环达成**: `财税法规（制度条款+种子）→ 负空间编译器（静态清单 + 法规素材 + 场景编译）
→ 税务官决策（计税/预缴/结算前法规检查，fail-closed）→ 决策轨迹（law_id 入审计）`

## 四、纪律落实

- **fail-closed（ID85）**: 法规基座缺失 → 拒绝税务决策（运行时自举，禁止静默降级为空——修复了初版降级缺陷）
- **ID86**: 全部法规条目 fuse_type=LEGAL + severity=HIGH（法律负空间绝对边界，无替代路径）
- **BV-3**: 静态清单构建后不可变（新增条目为源级扩展，运行期冻结不变）
- **裁决①**: 法规源=制度条款+KG-LEGAL 种子（模拟态 SEED）；真实法规全文留待 D-010
- **税率纪律**: 未引入外部增值税档（6%/9%/13%，DCD-MICROTAX-003 裁决①）；CALL-001 三档不变
- **ID90**: 复用既有通道（静态清单/legal_refs/沙盒映射/KG-LEGAL），无平行体系

## 五、里程碑状态

| 里程碑 | 内容 | 状态 |
|--------|------|------|
| M0 | 立项（DCD-TAXLAW-001，两项裁决）| ✅ 完成 |
| M1 | 法规清单 + 素材导入（L-1/L-2）| ✅ 完成 |
| M2 | 编译验证 + 税务官接入（L-3/L-4）+ B-1~B-5 | ✅ 全达标（本报告）|

## 六、遗留核验项

- D-010 法学家基准 → 真实法规全文导入（税率档位 + 法条全文，ID33 OTA）——本任务裁决①明确排除
- DCEP 硬数据接入 → 税务官真实申报能力
- 税务官 skill 已同步更新（§六 法规决策依据）

---

> 本报告为任务书整体交付证据（M1+M2）；验收通过后由人类签批（NCA 存证）冻结。
