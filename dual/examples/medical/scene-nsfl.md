# medical 行业场景负空间
# 版本: SCENE-NSFL-v1.0.0
# 关联 TDCA NSFL: TDCA-NSFL-v0.2
# ID92 模拟态标注: 本示例为示范产物

## 一、TDCA 公共负空间（必须完整包含）

引用 TDCA-NSFL-v0.2：三不可（AI-Blocked）/三可（Human-Only）/两层边界（ID85/86）/三档熔断。

## 二、medical 特定负空间

### 2.1 法律禁止扩展（ID86 绝对负空间：无替代路径、无模糊计算、只识别并熔断）

| 规则 ID | 禁止事项 | 严重程度 | 触发动作 |
|---------|---------|---------|---------|
| SCENE-LEGAL-MED-001 | AI 直接开具处方（无执业资质） | CRITICAL | BLOCK |
| SCENE-LEGAL-MED-002 | 患者基因数据用于非医疗目的 | CRITICAL | BLOCK |
| SCENE-LEGAL-MED-003 | 医疗数据跨境传输 | CRITICAL | BLOCK |

### 2.2 伦理红线扩展（ID85 人类价值领地：不可算计，人类介入）

| 规则 ID | 禁止事项 | 严重程度 | 触发动作 | 人类介入 |
|---------|---------|---------|---------|---------|
| SCENE-ETHIC-MED-001 | 未经伦理委员会审批的临床试验 | BLOCKING | HUMAN_OVERRIDE | 必须 |
| SCENE-ETHIC-MED-002 | 算法歧视（医疗资源分配） | BLOCKING | HUMAN_OVERRIDE | 必须 |
| SCENE-ETHIC-MED-003 | AI 辅助诊断无医生最终确认 | BLOCKING | HUMAN_OVERRIDE | 必须 |

## 三、场景负空间触发记录格式

```yaml
scene_nsfl_trigger:
  trigger_id: "SCENE-NSFL-{date}-{seq}"
  rule: "SCENE-LEGAL-MED-001"
  action: "BLOCK"
  nca_ref: "TDCA-NCA-{date}-{seq}-SCENE-NSFL"
```
