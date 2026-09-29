# government 行业场景负空间
# 版本: SCENE-NSFL-v1.0.0
# 关联 TDCA NSFL: TDCA-NSFL-v0.2
# ID92 模拟态标注: 本示例为示范产物

## 一、TDCA 公共负空间（必须完整包含）

引用 TDCA-NSFL-v0.2：三不可（AI-Blocked）/三可（Human-Only）/两层边界（ID85/86）/三档熔断。

## 二、government 特定负空间

### 2.1 法律禁止扩展（ID86 绝对负空间：无替代路径、无模糊计算、只识别并熔断）

| 规则 ID | 禁止事项 | 严重程度 | 触发动作 |
|---------|---------|---------|---------|
| SCENE-LEGAL-GOV-001 | 政务数据存储于境外服务器 | CRITICAL | BLOCK |
| SCENE-LEGAL-GOV-002 | 使用非国密算法加密敏感数据 | CRITICAL | BLOCK |
| SCENE-LEGAL-GOV-003 | 系统未通过等保测评即上线 | CRITICAL | BLOCK |
| SCENE-LEGAL-GOV-004 | 操作日志缺失或篡改 | CRITICAL | BLOCK |

### 2.2 伦理红线扩展（ID85 人类价值领地：不可算计，人类介入）

| 规则 ID | 禁止事项 | 严重程度 | 触发动作 | 人类介入 |
|---------|---------|---------|---------|---------|
| SCENE-ETHIC-GOV-001 | AI 自动决策涉及公民权利（无人类复核） | BLOCKING | HUMAN_OVERRIDE | 必须 |

## 三、场景负空间触发记录格式

```yaml
scene_nsfl_trigger:
  trigger_id: "SCENE-NSFL-{date}-{seq}"
  rule: "SCENE-LEGAL-GOV-001"
  action: "BLOCK"
  nca_ref: "TDCA-NCA-{date}-{seq}-SCENE-NSFL"
```
