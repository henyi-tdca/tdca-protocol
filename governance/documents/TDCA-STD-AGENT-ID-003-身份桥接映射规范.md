# TDCA-STD-AGENT-ID-003 · 身份桥接映射规范（TDID ↔ 国标身份码）V1.0

> 文档编号: TDCA-STD-AGENT-ID-003 ｜ 版本: V1.0 ｜ 日期: 2026-09-10（+08）｜ 会话框: L1-SI-024 ｜ 编制: Reasonix ｜ 存证: GSEQ-1191
> 依据: TDCA-STD-AGENT-ID-001 V1.1 §二/§四（作用域界分与外部链接层，GSEQ-1185）｜ 落实: 对齐审计 G1 并入 M1（GSEQ-1190 重排）
> 性质: 制度规范（内部基线）｜ 实现: `tdca-adapters/identity_bridge/`（10 用例全绿）

---

## 一、目的与范围

规范 **TDID（TDCA 内身份）↔ 国标身份码（OID）** 的链接映射：字段、纪律、接口与失效同步。适用于智能体**走出 TDCA 范围**时的身份链接（对内不改基线，对外可识别）。

## 二、映射模型

| 身份 | 作用域 | 角色 |
|---|---|---|
| **TDID**（`TDID-` + 32 位大写十六进制，源自通知机 PUF‖宪法哈希‖批次号） | TDCA 范围内 | **唯一主键**（primary key） |
| **国标身份码 OID**（GB/T 26231 分层，`1.2.156.…`） | TDCA 范围外 | **链接字段**（national_agent_id），不改变内部身份基线 |

**原则**：范围内一律以 TDID 为主键；OID 仅在链接建立后作为外部可识别字段随事件附出（`identity.primary_key=TDID` / `identity.national_agent_id=OID`）。

## 三、链接记录结构（字段级）

| 字段 | 类型 | 说明 |
|---|---|---|
| `tdid` | str | 内部主键（格式强校验） |
| `oid` | str | 国标身份码（GB/T 26231 分层格式强校验；模拟态不作真实注册） |
| `created_at` | str | 链接建立时间（+08 ISO8601） |
| `status` | `ACTIVE` / `REVOKED` | 链接状态（解析仅命中 ACTIVE） |
| `nca_ref` | str | **映射存证引用**（建立与撤销的 NCA id，`;` 连接） |
| `revoked_at` / `revoke_reason` | str | 失效同步信息（可审计） |

## 四、纪律（强制）

1. **映射必存证（fail-closed）**：无 NCA 生成器不建立映射；建立/撤销各生成一条存证（`identity-link` / `identity-unlink`）
2. **一码一链接**：一个 OID 同一时刻仅可链接一个 TDID（对齐国标"一码一智能体"语义）
3. **变更须先失效**：同 TDID 更换 OID 须先 `revoke`（失效同步），不得直接覆盖
4. **失效同步**：撤销即终止双向解析（`resolve_*` 返回空），**历史记录保留可溯**（状态置 REVOKED）
5. **不回写内部基线**：映射仅增加外部链接字段，内部主键始终 TDID
6. **数据性质（ID92）**：OID 校验与链接为模拟态（不构成真实国标注册）；对外使用时遵披露纪律

## 五、接口（实现 `identity_bridge.py`）

| 接口 | 语义 |
|---|---|
| `link(tdid, oid)` | 建立链接（幂等：同对返回既有；冲突报错；生成 `identity-link` 存证） |
| `resolve_by_tdid(tdid)` / `resolve_by_oid(oid)` / `resolve(...)` | 双向解析（仅 ACTIVE；参数须且仅须其一） |
| `revoke(tdid, reason)` | 失效同步（终止链接 + 生成 `identity-unlink` 存证 + 历史保留） |
| `stamp_event(event, tdid, oid=None)` | **主键嵌入**：事件加 `identity{primary_key, national_agent_id}`；OID 须与在册映射一致 |
| `export()` / `stats()` | 映射表导出 / 统计（total/active/revoked） |

## 六、接入点

- **事件侧**：`stamp_event`（本次实现）——后续 ECE 引擎 / 网关 / 适配器在生成事件时调用，即完成"身份码主键字段嵌入"（原 30 日冲刺 D+7 项，并入本 M1）
- **令牌侧**：通知机 `identity.tdca` 的 TDID 为链接源；自动化桥接（令牌签发→链接注册）列为待细化
- **失效联动**：通知机令牌失效（日抛终态 / 普通注销）应触发 `revoke`（联动列为待细化）

## 七、验收（本版实测）

- `tdca-adapters/identity_bridge/tests/test_identity_bridge.py` —— **10 用例全绿**（0.13s）：双向解析 / 幂等 / 双冲突 / 格式校验 / 映射存证（封印可校验）/ 失效同步 / 撤销异常 / 主键嵌入 / 导出与参数纪律

## 八、待细化（登记跟踪）

1. 通知机令牌签发 → 链接自动注册（桥接自动化）
2. 令牌失效 → `revoke` 自动联动
3. 批量映射与导出格式（供对外互操作报送）
4. OID 真实注册对接（若将来进入国标体系；涉对外动作须先裁定）

---
*身份桥接映射规范 V1.0：TDID 主键 / OID 链接字段 / 映射必存证 / 一码一链接 / 失效同步 / 主键嵌入接口——实现 10 用例全绿（M1 落地）｜ 存证: GSEQ-1191*
