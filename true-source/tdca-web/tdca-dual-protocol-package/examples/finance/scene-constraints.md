# 金融行业场景约束矩阵
# 版本: SCENE-CONSTRAINTS-v1.0.0
# 关联 TDCA 约束: TDCA-CONST-v3.1.2 / UPDA-v2.0
# ID92 模拟态标注: 本示例为示范产物

## 一、场景目标函数扩展

```yaml
scene_objectives:
  - id: OBJ-001
    description: "金融交易系统开发（风控模型验证）"
    priority: "P0"
    validation_method: "风控覆盖率 >= 100%"
```

## 二、场景约束扩展

```yaml
scene_constraints:
  six_elements:
    objective_function: "金融系统目标函数（TDCA 扩展）"
    constraint_matrix: "等保三级 + PCI-DSS + GDPR"
    prior_distribution: "金融监管指引 + TDCA 先验"
    config_boundary: "交易权限分级（普通/机构/监管）"
    expected_allocation: "风控报告 + 合规审计报告"
    audit_trail: "交易全链路 NCA + 监管报送"
  items:
    - id: CON-001
      type: "LEGAL"
      description: "金融数据不得跨境传输"
      severity: "BLOCK"
      validation_rule: "存储位置境内检查"
```

## 三、场景配置权边界扩展

```yaml
scene_config_boundaries:
  - role: "Financial-Engineer"
    permissions: ["code_generation", "testing", "risk_validation"]
    prohibitions: ["bypass_risk_control", "cross_border_data"]
    escalation: "L2-F -> 监管审批"
```

## 四、场景审查标准扩展

```yaml
scene_review_standards:
  - id: FIN-REV-001
    name: "交易逻辑风控覆盖度"
    criteria: ["风控模型 100% 覆盖", "异常交易熔断"]
    pass_threshold: "100%"
```
