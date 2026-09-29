# 医疗行业场景约束矩阵
# 版本: SCENE-CONSTRAINTS-v1.0.0
# 关联 TDCA 约束: TDCA-CONST-v3.1.2 / UPDA-v2.0
# ID92 模拟态标注: 本示例为示范产物

## 一、场景目标函数扩展

```yaml
scene_objectives:
  - id: OBJ-001
    description: "医疗业务系统开发（合规优先）"
    priority: "P0"
    validation_method: "行业合规审查通过"
```

## 二、场景约束扩展

```yaml
scene_constraints:
  six_elements:
    objective_function: "医疗系统目标函数（TDCA 扩展）"
    constraint_matrix: "医疗行业合规约束"
    prior_distribution: "行业监管指引 + TDCA 先验"
    config_boundary: "医疗权限分级"
    expected_allocation: "医疗合规报告"
    audit_trail: "医疗全链路 NCA"
  items:
    - id: CON-001
      type: "LEGAL"
      description: "医疗特定法律约束"
      severity: "BLOCK"
      validation_rule: "合规检查"
```

## 三、场景配置权边界扩展

```yaml
scene_config_boundaries:
  - role: "medical-Engineer"
    permissions: ["code_generation", "testing"]
    prohibitions: ["medical_prohibited_action"]
    escalation: "medical场景委员会"
```

## 四、场景审查标准扩展

```yaml
scene_review_standards:
  - id: medical-REV-001
    name: "医疗合规审查"
    criteria: ["合规项 100% 覆盖"]
    pass_threshold: "100%"
```
