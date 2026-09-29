# education 行业场景负空间
# 版本: SCENE-NSFL-v1.0.0
# 关联 TDCA NSFL: TDCA-NSFL-v0.2
# ID92 模拟态标注: 本示例为示范产物

## 一、TDCA 公共负空间（必须完整包含）

引用 TDCA-NSFL-v0.2：三不可（AI-Blocked）/三可（Human-Only）/两层边界（ID85/86）/三档熔断。

## 二、education 特定负空间

### 2.1 法律禁止扩展（ID86 绝对负空间：无替代路径、无模糊计算、只识别并熔断）

| 规则 ID | 禁止事项 | 严重程度 | 触发动作 |
|---------|---------|---------|---------|
| SCENE-LEGAL-EDU-001 | 收集未成年人非必要个人信息 | CRITICAL | BLOCK |
| SCENE-LEGAL-EDU-002 | 未经授权使用教育内容 | CRITICAL | BLOCK |

### 2.2 伦理红线扩展（ID85 人类价值领地：不可算计，人类介入）

| 规则 ID | 禁止事项 | 严重程度 | 触发动作 | 人类介入 |
|---------|---------|---------|---------|---------|
| SCENE-ETHIC-EDU-001 | AI 直接代写论文/作业 | BLOCKING | HUMAN_OVERRIDE | 必须 |
| SCENE-ETHIC-EDU-002 | 教育算法歧视（升学/评价） | BLOCKING | HUMAN_OVERRIDE | 必须 |

## 三、场景负空间触发记录格式

```yaml
scene_nsfl_trigger:
  trigger_id: "SCENE-NSFL-{date}-{seq}"
  rule: "SCENE-LEGAL-EDU-001"
  action: "BLOCK"
  nca_ref: "TDCA-NCA-{date}-{seq}-SCENE-NSFL"
```
