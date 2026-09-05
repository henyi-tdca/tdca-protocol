# TDCA NS-OPS M1 原型 — API 文档

> FC: TDCA-FC-NS-OPS-001（M1 原型）| 版本: 0.1.0-M1 | 日期: 2026-08-09
> 制度锚定: BV-1~7（BV-3 人类写权 / BV-4 先沙盒 / BV-5 NCA 存证 / BV-6 快慢分离）
> 规范来源: NS-GOVERNANCE-SYSTEM-001（P0 返修版）+ 红队审查结论 + 负空间论丛 9 篇
> 交互式文档: 后端启动后访问 `http://127.0.0.1:8123/docs`（Swagger UI，OpenAPI 自动生成）

---

## 一、服务概览

| 项 | 值 |
|----|----|
| 服务名 | `tdca-ns-ops` |
| Base URL | `http://127.0.0.1:8123/api/v1` |
| 技术栈 | Python 3.12 + FastAPI 0.141 + pydantic 2.13 |
| 数据存储 | JSON 文件（`backend/data/*.json`，原子写入） |
| NCA 存证 | `.tdca-nca/NCA-TDCA-REASONIX-{date}-{seq}.yaml`（MEMO-006 附录 C 11 字段） |

## 二、人类签名注册表（BV-3 门）

所有写操作（约束 CRUD 写 / 调整发起与推进）必须携带 `human_signature`，签名须在册：

| 签名 | 角色 | 层级 |
|------|------|------|
| `HUMAN-FOUNDER-001` | TDCA 制度设计师（人类） | L0 |
| `HUMAN-ENGINEER-001` | 负空间工程师（人类） | L2 |
| `HUMAN-AUDITOR-001` | 审计师（人类） | L2 |

**硬隔离规则**：非在册签名（如 `AI-*`）一律 `403 [BV-3 BLOCKED]`；制度层约束禁止删除（走 OTA/宪法流程）。

## 三、约束管理（F1）

### 3.1 列出约束 `GET /constraints`

Query 参数（均可选）: `layer`（subject/scene/institutional）、`scope`、`status`。

```bash
curl "http://127.0.0.1:8123/api/v1/constraints?layer=subject"
```

### 3.2 创建约束 `POST /constraints`（BV-3）

请求体（关键字段）:

```json
{
  "layer": "subject",
  "scope": "personal",
  "action": "我不会向未授权方共享生物特征数据",
  "action_code": "NSFL: ⊗ bio.share(unauthorized)",
  "certainty": "high",
  "rationale": "隐私权是协作入场券",
  "consequence": "触碰=配置权调度税 5 倍 + NSCredit -5",
  "bottom_lines": ["合理", "合规"],
  "owner": "OPC-Developer-003",
  "human_signature": "HUMAN-FOUNDER-001"
}
```

响应: `201` + 约束对象（`status=draft`、`version=1`、`nca_refs` 含 NCA）。
`403` = BV-3 拒绝；`422` = 校验失败（制度层 certainty 必须 absolute 等）。

### 3.3 更新约束 `PUT /constraints/{id}`（BV-3）

请求体必须含 `human_signature`；每次更新 `version +1`。

### 3.4 删除约束 `DELETE /constraints/{id}?human_signature=...`（BV-3）

制度层（institutional）约束返回 `403`（L0 法律底线不可删除）。

## 四、三层负空间视图（F1）`GET /views/triple-layer`

响应结构:

```json
{
  "subject":  { "subject": "OPC-Developer-001", "entries": [...], "nsc_credit": 100 },
  "scene":    { "scene": "community", "six_elements": {...}, "theme": "...", "theme_health": 0.95, "entries": [...] },
  "institutional": { "layer_label": "L0-L1 全局只读（宪法/NSFL/L0 法律）", "entries": [...] },
  "bottom_lines": { "合法": true, "合规": true, "合理": true, "合情": true },
  "safe_domain": "四重底线透明重叠，协作安全域开放"
}
```

## 五、声明-行为校验（F3）`POST /judgments`

请求:

```json
{ "actor": "agent-x", "action": "实施违反法律底线的行为", "scene": "community" }
```

响应（判定枚举 NS-006）:

```json
{
  "decision": "block",
  "reason": "触碰制度负空间（L0 法律底线），绝对熔断（BV-1/NSFL ⊗）",
  "matched_constraints": ["NS-INST-001"],
  "fuse_triggered": true,
  "nca_ref": "TDCA-REASONIX-20260809-xxx"
}
```

`decision` ∈ `block | restrict | allow_with_conditions | allow`；
制度层 absolute 命中 → `block + fuse_triggered=true`（熔断）。

## 六、调整权操作（F2，NS-011 状态机）

### 6.1 发起调整 `POST /adjustments`（BV-3，人类专属）

```json
{
  "target_constraint_id": "NS-SUBJECT-001",
  "trigger": "社会变化：新隐私法规出台",
  "proposal": "将隐私约束从 high 升级为 absolute",
  "initiator": "HUMAN-FOUNDER-001",
  "human_signature": "HUMAN-FOUNDER-001"
}
```

→ `201`，`status=deliberation`（审议态）。

### 6.2 推进状态 `POST /adjustments/{id}/transition`

Query 参数: `to_status` + `human_signature`（每步必填，BV-3）；encoding 步附加 `final_version`、`effective_date`、`extra_signatures`（逗号分隔补充签名，确定态需 ≥3 异构三角）。

```bash
# 审议 → 沙盒（BV-4 自动执行三层沙盒，未过 422）
curl -X POST "http://127.0.0.1:8123/api/v1/adjustments/{id}/transition?to_status=sandbox&human_signature=HUMAN-FOUNDER-001"
# 沙盒 → 确定
curl -X POST ".../transition?to_status=determination&human_signature=HUMAN-FOUNDER-001"
# 确定 → 编码（3 签名）
curl -X POST ".../transition?to_status=encoding&human_signature=HUMAN-FOUNDER-001&final_version=2&effective_date=2026-09-01&extra_signatures=HUMAN-ENGINEER-001,HUMAN-AUDITOR-001"
# 编码 → 部署（约束置 rigid 刚性态）
curl -X POST ".../transition?to_status=deployment&human_signature=HUMAN-FOUNDER-001"
# 部署 → 反馈 → 闭合
curl -X POST ".../transition?to_status=feedback&human_signature=HUMAN-FOUNDER-001"
curl -X POST ".../transition?to_status=closed&human_signature=HUMAN-FOUNDER-001"
```

### 6.3 状态机

```
deliberation(①审议) → sandbox(②沙盒) → determination(③确定冻结)
→ encoding(④编码) → deployment(⑤部署) → feedback(⑥反馈) → closed(⑦闭合)
非法迁移 → 422；沙盒未过 → 422 [BV-4]；签名缺失/非在册 → 403 [BV-3]
```

### 6.4 台账 `GET /adjustments` / `GET /adjustments/{id}`

NSAR-Registry 格式（NS-011 §4.2）：审议记录、沙盒结果、确定记录（生效时间/回滚版本/签名）、部署记录、反馈列表、NCA 链。

## 七、错误码约定

| HTTP | 含义 | 触发 |
|------|------|------|
| 403 | BV-3 人类写权限门拒绝 / 制度层禁删 | 非在册签名、AI 代行 |
| 404 | 资源不存在 | 约束/调整 ID 错误 |
| 422 | 校验失败 / 非法状态迁移 / 沙盒未过 | 枚举非法、跳步、签名不足 |
| 201/200 | 成功 | — |

## 八、NCA 存证（F6）

每次写操作（约束创建/更新/删除、调整每步推进、沙盒模拟、判定）自动生成 NCA（11 字段：
NCA-ID/FC-ID/Operation/Operator/Timestamp/Pre-State/Post-State/Config-Right-Token/
Audit-Trail/Human-Signature/Negative-Space-Check），落盘 `.tdca-nca/`，响应中经 `nca_refs`/`nca_ref` 回引。
