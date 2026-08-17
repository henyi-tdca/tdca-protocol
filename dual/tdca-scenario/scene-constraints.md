# {场景名称} 场景约束矩阵
# 版本: SCENE-CONSTRAINTS-v1.0.0
# 关联 TDCA 约束: TDCA-CONST-v3.1.2 / UPDA-v2.0
# ID92 模拟态标注: 本模板为可复制产物，不构成真实配置权执行路径

## 一、场景目标函数扩展

在 TDCA 通用目标函数基础上，增加以下场景特定目标：

```yaml
scene_objectives:
  - id: OBJ-001
    description: "{场景特定目标描述}"
    priority: "P0/P1/P2"
    validation_method: "{验证方法}"
  - id: OBJ-002
    description: "{场景特定目标描述}"
    priority: "P0/P1/P2"
    validation_method: "{验证方法}"
```

## 二、场景约束扩展

在 TDCA 通用约束矩阵基础上，增加以下场景特定约束：

```yaml
scene_constraints:
  six_elements:
    objective_function: "{目标函数（TDCA 六要素）}"
    constraint_matrix: "{约束矩阵（TDCA 六要素）}"
    prior_distribution: "{先验分布（TDCA 六要素）}"
    config_boundary: "{配置权边界（TDCA 六要素）}"
    expected_allocation: "{预期分配（TDCA 六要素）}"
    audit_trail: "{审计轨迹（TDCA 六要素）}"
  items:
    - id: CON-001
      type: "LEGAL/TECHNICAL/ETHICAL/BUSINESS"
      description: "{约束描述}"
      severity: "BLOCKING/WARNING/INFO"
      validation_rule: "{验证规则}"
    - id: CON-002
      type: "LEGAL/TECHNICAL/ETHICAL/BUSINESS"
      description: "{约束描述}"
      severity: "BLOCKING/WARNING/INFO"
      validation_rule: "{验证规则}"
```

## 三、场景配置权边界扩展

```yaml
scene_config_boundaries:
  - role: "{场景角色}"
    permissions:
      - "{权限 1}"
      - "{权限 2}"
    prohibitions:
      - "{禁止 1}"
      - "{禁止 2}"
    escalation: "{升级路径}"
```

## 四、场景审查标准扩展

```yaml
scene_review_standards:
  - id: REV-001
    name: "{审查项名称}"
    criteria:
      - "{审查标准 1}"
      - "{审查标准 2}"
    pass_threshold: "{通过阈值}"
  - id: REV-002
    name: "{审查项名称}"
    criteria:
      - "{审查标准 1}"
      - "{审查标准 2}"
    pass_threshold: "{通过阈值}"
```
