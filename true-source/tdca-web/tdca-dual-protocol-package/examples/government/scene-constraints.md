# 政务行业场景约束矩阵
# 版本: SCENE-CONSTRAINTS-v1.0.0
# 关联 TDCA 约束: TDCA-CONST-v3.1.2 / UPDA-v2.0
# ID92 模拟态标注: 本示例为示范产物

## 一、场景目标函数扩展

```yaml
scene_objectives:
  - id: OBJ-001
    description: "政务业务系统开发（合规优先）"
    priority: "P0"
    validation_method: "行业合规审查通过"
```

## 二、场景约束扩展

```yaml
scene_constraints:
  six_elements:
    objective_function: "政务系统目标函数（TDCA 扩展）"
    constraint_matrix: "政务行业合规约束"
    prior_distribution: "行业监管指引 + TDCA 先验"
    config_boundary: "政务权限分级"
    expected_allocation: "政务合规报告"
    audit_trail: "政务全链路 NCA"
  items:
    - id: CON-001
      type: "LEGAL"
      description: "政务特定法律约束"
      severity: "BLOCK"
      validation_rule: "合规检查"
```

## 三、场景配置权边界扩展

```yaml
scene_config_boundaries:
  - role: "government-Engineer"
    permissions: ["code_generation", "testing"]
    prohibitions: ["government_prohibited_action"]
    escalation: "government场景委员会"
```

## 四、场景审查标准扩展

```yaml
scene_review_standards:
  - id: government-REV-001
    name: "政务合规审查"
    criteria: ["合规项 100% 覆盖"]
    pass_threshold: "100%"
```
