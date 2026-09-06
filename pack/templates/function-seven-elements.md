# function-seven-elements · 函数七要素 docstring 模板

> SPDX-License-Identifier: Apache-2.0
> 落位候选: pack/templates/（门户「函数七要素模板」解锁件）｜ 许可: Apache-2.0（仓库根 LICENSE 覆盖）
> 规范: TDCA-FUNCTION-7ELEM-001（V1.0-FROZEN，ID68 修订裁决 ACCEPT GSEQ-1067）
> 基座: working-spec §4.2 六要素（语义零改动）+ 第七要素拆分新增

## 一、七要素速览

| # | 要素 | 回答的问题 |
|---|---|---|
| 1 | 目标函数 | 解决什么问题？预期产出（可验收）？ |
| 2 | 约束矩阵 | 技术约束（输入校验/输出格式/禁止越权）？ |
| 3 | 先验分布 | 基于哪些已有 NCA/验证报告/制度文件？ |
| 4 | 配置权边界 | 可触碰/不可触碰范围？ |
| 5 | 预期分配 | 返回/副作用/失败如何分配？ |
| 6 | 审计轨迹 | 输入输出哈希/时间戳/NCA 关联？ |
| **7** | **负空间约束声明** | **「我不会」什么？触碰即熔断？（i_will_not，新增）** |

## 二、Python docstring 模板

```python
def publish_function(...) -> Result:
    """函数七要素 docstring（working-spec §4.2 + 第七要素）

    [1] 目标函数: 动词 + 对象 + 产出（可验收）。
    [2] 约束矩阵（技术约束）: 输入校验 / 输出格式 / 禁止越权。
    [3] 先验分布: 上游依赖 / 制度基线 / 历史 REV。
    [4] 配置权边界: 可触碰 / 不可触碰（负空间约束调整 = 人类专属）。
    [5] 预期分配: 返回 / 副作用 / 失败原因分类。
    [6] 审计轨迹: 输入哈希 / 输出哈希 / 时间戳 / NCA。
    [7] 负空间约束声明（i_will_not）:
        - 机器可读块见 __ns_boundary__ 属性（JSON）
        - 声明缺失 → 发布拦截（NS-009 入场券）
        - BV-1 机械绑定: 函数入口断言禁止行为
        - 触碰即熔断: subject→信用降信 / scene→RESTRICT / institutional→alt=∅
    """
```

## 三、机器可读块（__ns_boundary__）

```json
{
  "element": 7,
  "type": "i_will_not",
  "version": "0.1",
  "declarations": [
    {
      "constraint_id": "NS-SUBJECT-001",
      "scope": "subject",
      "action_code": "NSFL: ⊗ data.leak(third_party)",
      "certainty": "high",
      "consequence": "触碰=配置权调度税 5 倍 + NSCredit -5",
      "verification": "Runtime_Audit",
      "binding": true
    }
  ],
  "institutional_floor": false
}
```

- 公开函数 docstring 后附 `__ns_boundary__`（JSON 字符串）
- 发布期 L8 校验 / 运行期 NSFL 熔断读同源（φ 直映）
- scope: subject（信用降信）/ scene（RESTRICT）/ institutional（alt=∅ 绝对熔断）

## 四、质量检查

- [ ] 六要素保持 working-spec §4.2（零改动）
- [ ] 约束矩阵仅含技术约束（负空间已拆至第七要素）
- [ ] 第七要素存在（非空 __ns_boundary__）
- [ ] institutional_floor=true 时含 LEGAL 型约束

规范全文: TDCA-FUNCTION-7ELEM-001（V1.0-FROZEN）。
