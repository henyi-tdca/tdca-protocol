# 通知机物理锚点场景负空间（scene-phy-notification）
# 版本: SCENE-NSFL-v1.0.0
# 关联 TDCA NSFL: TDCA-NSFL-v0.2
# 交付: 通知机规范包（层 3 场景化合，FC-SPEC §3.1/澄清 C）
# 模拟态标注: 本场景为模拟态示范（MOU 锚定 D-011）；通知机硬件未投产部署，本场景为 SIL 模拟

## 一、TDCA 公共负空间（必须完整包含）

引用 TDCA-NSFL-v0.2：三不可（AI-Blocked）/三可（Human-Only）/两层边界/三档熔断。

## 二、通知机特定负空间（SCENE-PHY-001~003）

### 2.1 物理负空间（绝对负空间：硬件安全机制即时 BLOCK，不可逆——信任锚底线）

| 规则 ID | 禁止事项 | 类型 | 严重程度 | 触发动作 |
|---------|---------|------|---------|---------|
| SCENE-PHY-001 | 物理拆解/篡改（熔断电路：微动开关+光敏+温度触发） | 物理负空间 | CRITICAL | BLOCK（不可逆） |
| SCENE-PHY-003 | PUF 密钥导出尝试（A7100 安全模块检测） | 物理负空间 | CRITICAL | BLOCK（绝对负空间，不可逆） |

### 2.2 制度负空间（NSFL 熔断：协议层判定，TCN 慢系统确认，可逆至 SUSPENDED）

| 规则 ID | 禁止事项 | 类型 | 严重程度 | 触发动作 |
|---------|---------|------|---------|---------|
| SCENE-PHY-002 | 固件版本不在允许列表 | 制度负空间 | CRITICAL | BLOCK（可逆至 SUSPENDED） |

## 三、场景负空间触发记录格式

```yaml
scene_nsfl_trigger:
  trigger_id: "SCENE-NSFL-{date}-{seq}"
  rule: "SCENE-PHY-001"
  type: "PHYSICAL"        # PHYSICAL（不可逆）/ INSTITUTIONAL（可逆）
  irreversible: true
  action: "BLOCK"
  nca_ref: "TDCA-NCA-{date}-{seq}-SCENE-NSFL"
```
