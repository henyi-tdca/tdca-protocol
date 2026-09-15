# 通知机物理锚点场景约束矩阵（scene-phy-notification）
# 版本: SCENE-CONSTRAINTS-v1.0.0
# 关联 TDCA 约束: TDCA-CONST-v3.1.2 / UPDA-v2.0 / CALL-RULES V1.2
# 交付: 通知机规范包（层 3 场景化合，FC-SPEC §3.1）
# 模拟态标注: 本场景为模拟态示范（MOU 锚定 D-011）；通知机硬件未投产部署，本场景为 SIL 模拟

## 一、场景目标函数扩展

```yaml
scene_objectives:
  - id: OBJ-001
    description: "通知机硬件调用商业计量（物理世界锚定 → 配置权市场）"
    priority: "P0"
    validation_method: "CALL-RULES 计量 + MOU 归零验证"
```

## 二、场景约束扩展

```yaml
scene_constraints:
  six_elements:
    objective_function: "硬件调用 → 类型映射（日抛/化合/服务）→ 税收 → MOU 归零"
    constraint_matrix: "物理/制度负空间区分 + 国密合规（SM2/SM3/SM4）"
    prior_distribution: "E-HW-1 定型规格 + TIMA-PHY-001 + CALL-RULES V1.2"
    config_boundary: "L2 配置权市场层；Config-Right-Token 不上芯片（澄清 A）"
    expected_allocation: ".tdca 固件元数据 + NCA-Lite 8 字段 + 全量 NCA 存证"
    audit_trail: "fact-chain 事实哈希链 + NCA-Lite 链式关联（自反化合）"
  items:
    - id: CON-001
      type: "PHY"
      description: "PUF 密钥材料永不落盘/外传（信任锚底线）"
      severity: "CRITICAL"
      validation_rule: "SE 私钥不导出"
    - id: CON-002
      type: "PHY"
      description: "TDID 不得伪造（SM2 签名校验）"
      severity: "CRITICAL"
      validation_rule: "SM2 验签"
    - id: CON-003
      type: "BIZ"
      description: "MOU 归零规则不可绕过（T(y_t)>0 才有效）"
      severity: "CRITICAL"
      validation_rule: "CALL-RULES validate_mou"
    - id: CON-004
      type: "BIZ"
      description: "人类签名权不可绕过（通话确权等关键决策走 TCN 慢系统）"
      severity: "BLOCKING"
      validation_rule: "TCN 慢系统确认"
```

## 三、场景配置权边界扩展

```yaml
scene_config_boundaries:
  - role: "NM-Operator"
    scene: "scene-phy-notification"
    permissions: ["fact_hash_upload", "call_authorization", "telemetry_collect"]
    prohibitions: ["puf_key_export", "tdid_forge", "config_right_mutation"]
    escalation: "TCN Auditor"
  - role: "NM-Gov"
    scene: "scene-phy-notification"
    permissions: ["fact_hash_upload", "call_authorization", "compliance_review"]
    prohibitions: ["puf_key_export", "tdid_forge", "config_right_mutation", "compliance_bypass"]
    escalation: "政务合规审查"
  - role: "NM-Fin"
    scene: "scene-phy-notification"
    permissions: ["fact_hash_upload", "call_authorization", "risk_validation"]
    prohibitions: ["puf_key_export", "tdid_forge", "config_right_mutation", "risk_bypass"]
    escalation: "金融机构风控"
  - role: "NM-Med"
    scene: "scene-phy-notification"
    permissions: ["fact_hash_upload", "call_authorization", "privacy_review"]
    prohibitions: ["puf_key_export", "tdid_forge", "config_right_mutation", "privacy_violation"]
    escalation: "医疗伦理审查"
```

## 四、场景审查标准扩展

```yaml
scene_review_standards:
  - id: REV-PHY-001
    name: "品类认证有效"
    criteria: ["TDCA-REG-NAMING-001 命名授权"]
    pass_threshold: "100%"
  - id: REV-PHY-002
    name: "国密合规"
    criteria: ["SM2 签名 / SM4 加密不落盘"]
    pass_threshold: "100%"
  - id: REV-PHY-003
    name: "场景合规前置"
    criteria: ["政务/金融/医疗 → 等保（复用行业模板）"]
    pass_threshold: "100%"
```

## 五、MRCR 多角色兼容（FC-SPEC §3.2）

| 角色 | 场景 | 权限 |
|------|------|------|
| NM-Operator | 通知机通用 | 通话确权、事实哈希上链 |
| NM-Gov | 政务（信访/反诈） | + 国密/等保合规、留痕审计 |
| NM-Fin | 金融（机构） | + 风控、监管报送 |
| NM-Med | 医疗（机构） | + 隐私保护、伦理审查 |
