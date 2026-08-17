# 六要素标准模板（TDCA 公共部分）

> 层级: L1 模板 | 用途: 通用开发六要素声明（场景制度在此模板上扩展 Scene-Six-Elements）

```markdown
# FC 六要素声明模板
# FC-ID: TDCA-FC-{YYYYMMDD}-{SEQ}
# 生成时间: {timestamp}
# 生成者: {human_signatory}

## 1. 目标函数
[本次开发要解决什么问题？预期产出是什么？]

## 2. 约束矩阵
[宪法十六条相关条款 + UPDA 定价约束 + NSFL 负空间边界 + 配置权层级限制]

## 3. 先验分布
[上游 FC 依赖（bond_type=strong）+ 历史审查记录 + 制度基线版本]

## 4. 配置权边界
[可触碰的制度层级 + 不可触碰的负空间 + 跨主体协作权限]

## 5. 预期分配
[代码交付物 + NCA 审计轨迹 + 审查通过标准 + MOU 税收锚定]

## 6. 审计轨迹
[主 NCA: TDCA-NCA-{date}-{seq}-{FC-ID} + 审查 REV + NSFL 触发]

---
人类签批: ____________
签批时间: ____________
```

> 场景制度扩展：在 2/4/5 追加场景特定约束、权限、审查项（见 tdca-scenario/scene-constraints.md）。
