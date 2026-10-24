# **九类接口契约表** `v0.1`（业务端节点接入）

> 件号: **TDCA-SPEC-NODE-INTERFACE-CONTRACT-001** ｜ 版本: **v0.1**（⭐ 契约草案 · ⛔ 未冻结） ｜ 日期: **2026-10-17**（+08）
> 会话框: **L1-SI-151** ｜ 编制: **Reasonix** ｜ 操作类型: **Design**
> 上游: ⭐《业务端节点接入与同构契约条例》`TDCA-REG-NODE-ACCESS-001` **V1.0-FROZEN**（第 12 条：九类接口各须**字段 ／错误码 ／版本 ／留痕**四要素）
> 性质: ⚠️ **内部件 · ⛔ 非对外** ｜ ⭐ **纸面契约：⛔ 未写代码、⛔ 未建端点、⛔ 未部署**

---

## 〇、一句话

⭐ 九类接口**逐类给齐四要素**；⭐ 七类是**升格**（站点已有端点），⭐ 两类是**新增**（心跳 ／存证回传）；⭐ **契约先行冻结、实现后置**（第 14 条）。

---

## 一、⭐ 通用约定（九类共用）

| 项 | 约定 |
|---|---|
| ⭐ **契约版本** | ⭐ 请求头 `X-TDCA-Contract: nc/1.0`；⭐ 未带 ⟹ ⛔ 按旧版拒（`E_VERSION_UNSUPPORTED`） |
| ⭐ **协议版本** | ⭐ `X-TDCA-Protocol: <版本>`；⭐ 支持集**有限**（照在册 `3.1.2` 口径），⛔ 未支持即拒 |
| ⭐ **鉴权** | ⭐ 过**闸门**＋**身份**（令牌）；⭐ 匿名只读**限在册公开面**（第 16 条） |
| ⭐ **幂等** | ⭐ 写类接口**必带** `Idempotency-Key`（第 17 条） |
| ⭐ **留痕** | ⭐ 每类标注 `must_report`（必回站留痕）／`local_only`（留节点） |
| ⭐ **错误体** | ⭐ `{ "error": "<CODE>", "detail": {...}, "contract": "nc/1.0" }` |
| ⭐ **时间** | ⭐ 一律 `+08`，`ISO 8601` |

---

## 二、⭐ 统一错误码表

| 码 | HTTP | 含义 | 节点侧应做 |
|---|---|---|---|
| `E_REQUIRED_MISSING` | `422` | 必填缺 | ⛔ 重试（先补字段） |
| `E_NOT_REGISTERED` | `403` | 节点未登记 | ⭐ 先走①登记 |
| `E_DUPLICATE_NODE` | `409` | 节点重号 | ⭐ 换 `node_id` 或走变更 |
| `E_IDEMPOTENT_REPLAY` | `202` | 幂等重放（已受理过） | ⭐ 视为成功，⛔ 重发 |
| `E_VERSION_UNSUPPORTED` | `426` | 契约／协议版本不支持 | ⭐ 升级或降级版；⭐ 站点 ⛔ 擅断 |
| `E_ANCHOR_LEVEL_INSUFFICIENT` | `403` | 锚定等级不足 | ⭐ 提级（第 21 条） |
| `E_TOKEN_EXPIRED` | `401` | 令牌过期 | ⭐ 换令牌 |
| `E_QUOTA_EXCEEDED` | `429` | 配额耗尽 | ⭐ 退避 |
| `E_DIGEST_MISMATCH` | `409` | 哈希不符 | ⛔ 停工，回呈 |
| `E_UPSTREAM_UNAVAILABLE` | `503` | 站点不可用 | ⭐ **本地兜底**，⛔ 停摆（第 18 条） |

---

## 三、⭐ 九类逐类契约

### ① 加入 ／注册 `join_register`（⭐ 升格自 `/join*`）

| 项 | 内容 |
|---|---|
| 端点 | `POST /join` ／`GET /join/status` ／`GET /join/list` ／`POST /join/review` |
| ⭐ 必备字段 | `node_id` ／`node_type`（`online`｜`self_deploy`｜`appliance`）／`anchor_level` ／`capabilities[]` ／`protocol_version` ／`contact_ref` |
| 错误码 | `E_REQUIRED_MISSING`／`E_DUPLICATE_NODE`／`E_ANCHOR_LEVEL_INSUFFICIENT` |
| 版本 | `nc/1.0` |
| 留痕 | ⭐ **`must_report`**（登记事件必回站） |
| 缺口 | ⭐ `node_type` ／`anchor_level` ／`capabilities` **现无**（本机副本仅见成员语义） |

### ② 身份交换 ／协议加载 `identity_handshake_protocol_load`（⭐ 升格自 `/agent-card/handshake`）

| 项 | 内容 |
|---|---|
| 端点 | `POST /agent-card/handshake` ／`GET /agent-card/{card_id}` |
| ⭐ 必备字段 | `agent_card_ref` ／`protocol_version` ／`contract_version` ／`capability_digest`（⭐ 声明能力之哈希） |
| 错误码 | `E_VERSION_UNSUPPORTED`／`E_NOT_REGISTERED` |
| 留痕 | ⭐ **`must_report`**（加载事件必回站；⭐ 通道＝协议加载验证，⛔ 非身份验证） |
| 缺口 | ⭐ `contract_version` ／`capability_digest` **现无** |

### ③ 名录 ／发现 `directory_discovery`（⭐ 升格自 `/directory`）

| 项 | 内容 |
|---|---|
| 端点 | `GET /directory`（⭐ 分页 `page`／`size` ≤ `100`） |
| ⭐ 必备字段 | `node_id` ／`node_type` ／`capabilities[]` ／`status`（`online`｜`degraded`｜`offline`）／`contract_version` ／`region`（可空） |
| 错误码 | `E_VERSION_UNSUPPORTED` |
| 留痕 | ⭐ **`local_only`**（查名录 ⛔ 不留痕） |
| 边界 | ⭐ **匿名只读**（限在册公开面）；⭐ 缓存 `≤60s`，⛔ 作为权威 |

### ④ 计量上报 `meter_report`（⭐ 升格自 `/meter`）

| 项 | 内容 |
|---|---|
| 端点 | `POST /meter`（⭐ 支持批量 `items[]` ≤ `200`） |
| ⭐ 必备字段 | `node_id` ／`idem_key`（**必带**）／`items[]`（`seq`／`units`／`metric_type`）／`occurred_at` |
| 错误码 | `E_IDEMPOTENT_REPLAY`／`E_REQUIRED_MISSING`／`E_QUOTA_EXCEEDED` |
| 语义 | ⭐ **计量事实**（⛔ 订单、⛔ 账单）——⭐ 第 11 条语义同构 |
| 留痕 | ⭐ **`must_report`**（摘要回站） |
| 缺口 | ⭐ `idem_key` ／批量 ／离线补报标记 **现无** |

### ⑤ 额度 ／配额 `quota_credit`（⭐ 升格自 `/credits*`）

| 项 | 内容 |
|---|---|
| 端点 | `POST /credits` ／`GET /credits/{member_id}` |
| ⭐ 必备字段 | `node_id` ／`quota_type`（⭐ 与税基口径对齐：`L1` 交易 ／`L2` 调度）／`amount` ／`period` |
| 错误码 | `E_QUOTA_EXCEEDED`／`E_ANCHOR_LEVEL_INSUFFICIENT` |
| 留痕 | ⭐ **`must_report`** |
| 缺口 | ⭐ `quota_type` 与税基之**映射表** ⛔ 在册，须另出 |

### ⑥ 令牌 ／锚定 `token_anchor`（⭐ 升格自 `/notify-token`）

| 项 | 内容 |
|---|---|
| 端点 | `POST /notify-token` |
| ⭐ 必备字段 | `node_id` ／`anchor_level` ／`ttl_seconds` ／`scope[]` |
| 错误码 | `E_TOKEN_EXPIRED`／`E_ANCHOR_LEVEL_INSUFFICIENT` |
| 留痕 | ⭐ **`local_only`**（⭐ ⛔ 令牌值入日志、⛔ 入件） |
| 边界 | ⭐ 锚定分级：⭐ `PUF`／`HSM` 为**技术根**，⭐ 须经分级（第 21 条） |

### ⑦ 文档 ／协议包分发 `doc_bundle_distribution`（⭐ 升格自 `/docs/*`）

| 项 | 内容 |
|---|---|
| 端点 | `GET /docs/{family}` ／`GET /docs/{family}/{slug}` |
| ⭐ 必备字段 | `family` ／`slug` ／`version` ／`sha256_16`（⭐ 响应头 `X-TDCA-Digest`） |
| 错误码 | `E_DIGEST_MISMATCH`／`E_VERSION_UNSUPPORTED` |
| 留痕 | ⭐ **`local_only`** |
| 缺口 | ⭐ **版本与哈希校验**现无（响应头） |

### ⑧ 心跳 ／状态 `heartbeat_status`（⭐ **新增**）

| 项 | 内容 |
|---|---|
| 端点 | ⭐ `POST /heartbeat`（⭐ **未实现前 ⛔ 不开放**——第 14 条） |
| ⭐ 必备字段 | `node_id` ／`status` ／`uptime_s` ／`load`（可空）／`last_meter_seq` ／`protocol_version` |
| 频度 | ⭐ 建议 `60s`（⭐ 逾 `3` 期判 `degraded`，逾 `5` 期判 `offline`） |
| 错误码 | `E_NOT_REGISTERED`／`E_VERSION_UNSUPPORTED` |
| 留痕 | ⭐ **`must_report`**（仅状态变迁，⛔ 每次心跳全记） |
| 来源 | ⚠️ 依 `TTRN-001` 心跳设计之义，⭐ **⛔ 直接引**（该稿为沙盒态），⭐ 仅取「心跳判存活」之义 |

### ⑨ 存证回传 ／校验 `attestation_return_verify`（⭐ **新增**）

| 项 | 内容 |
|---|---|
| 端点 | ⭐ `POST /attestation/return` ＋ `GET /attestation/{node_id}/tip`（⭐ 未实现前 ⛔ 不开放） |
| ⭐ 必备字段 | `node_id` ／`chain_id` ／`prev_digest` ／`record_digest` ／`seq` ／`occurred_at` |
| 错误码 | `E_DIGEST_MISMATCH`／`E_NOT_REGISTERED` |
| 留痕 | ⭐ **`must_report`**（⭐ 只回**摘要**，⛔ 全量上送——第 10 条隐私最小化） |
| 冲突 | ⭐ 站点与节点摘要不一致 ⟹ ⭐ **`E_DIGEST_MISMATCH` ＋ 停手回呈**（⛔ 自动覆盖） |
| 频度 | ⭐ 建议按**批次**（`10min` 或 `100` 条先到者） |

---

## 四、⭐ 契约冻结进度

| 项 | 状态 |
|---|---|
| 九类 × 四要素（字段 ／错误码 ／版本 ／留痕） | ⭐ **本表已给齐** |
| 契约版本号 | ⭐ `nc/1.0`（⭐ **待创始人一句「冻结」方对外生效**） |
| 实现 | ⛔ **未开始**（第 14 条：契约可先冻结、实现后置） |
| 站点侧改造清单 | ⏳ 另件（七类升格 ＋ 两类新增） |

---

## 五、⚠️ 本表局限（如实）

1. ⚠️ 基于**本机副本**端点面（非全量），⭐ 完整面以执行侧回报为准；
2. ⚠️ 字段名与错误码为**本侧拟**，⭐ 冻结前须与执行侧**对表**；
3. ⚠️ `⑤` 之税基映射、`⑧⑨` 之频度数值均**未定**，⭐ 属**待裁/待设计**，⛔ 本表不代定。

---

## 六、边界

- ⭐ 本件只作**契约草案** —— ⛔ 未写代码、⛔ 未建端点、⛔ 未冻结、⛔ 不含对外、⛔ 不代转交。
