# {场景名称} 场景负空间函数语言
# 版本: SCENE-NSFL-v1.0.0
# 关联 TDCA NSFL: TDCA-NSFL-v0.2
# ID92 模拟态标注: 本模板为可复制产物，不构成真实配置权执行路径

## 一、TDCA 公共负空间（必须完整包含）

{自动引用 TDCA-NSFL-v0.2 全部条款——见 tdca-public/constitution/NSFL-v0.2.md：
三不可原则（AI-Blocked）/ 三可原则（Human-Only）/ 两层边界（ID85/86）/ 三档熔断}

## 二、场景特定负空间（扩展）

### 2.1 法律禁止扩展

| 规则 ID | 禁止事项 | 严重程度 | 触发动作 | 替代路径 |
|---------|---------|---------|---------|---------|
| SCENE-LEGAL-001 | {场景法律禁止} | CRITICAL | BLOCK | {无（绝对负空间）} |
| SCENE-LEGAL-002 | {场景法律禁止} | CRITICAL | BLOCK | {无（绝对负空间）} |

### 2.2 伦理红线扩展

| 规则 ID | 禁止事项 | 严重程度 | 触发动作 | 人类介入 |
|---------|---------|---------|---------|---------|
| SCENE-ETHIC-001 | {场景伦理禁止} | BLOCKING | HUMAN_OVERRIDE | 必须 |
| SCENE-ETHIC-002 | {场景伦理禁止} | BLOCKING | HUMAN_OVERRIDE | 必须 |

### 2.3 业务规则扩展

| 规则 ID | 禁止事项 | 严重程度 | 触发动作 | 自动修复 |
|---------|---------|---------|---------|---------|
| SCENE-BIZ-001 | {场景业务禁止} | WARNING | ALT_PATH | {自动修复方案} |
| SCENE-BIZ-002 | {场景业务禁止} | WARNING | ALT_PATH | {自动修复方案} |

## 三、场景负空间触发记录格式

```yaml
scene_nsfl_trigger:
  trigger_id: "SCENE-NSFL-{date}-{seq}"
  rule: "{触发的规则 ID}"
  operation: "{触发操作}"
  context: "{触发上下文}"
  timestamp: "{timestamp}"
  action: "BLOCK/ALT_PATH/HUMAN_OVERRIDE"
  resolution: "{处理方式}"
  nca_ref: "TDCA-NCA-{date}-{seq}-SCENE-NSFL"
```
