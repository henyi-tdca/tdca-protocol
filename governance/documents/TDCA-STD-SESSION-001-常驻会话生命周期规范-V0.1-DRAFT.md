# TDCA-STD-SESSION-001 · 常驻会话生命周期规范（MCP 常驻会话）V1.0-FROZEN

> 文档编号: **TDCA-STD-SESSION-001** ｜ 版本: **V1.0-FROZEN（M2 ② 收官冻结版：裁定落地 + 整改 + 合入 main + 一次性收口）** ｜ 日期: 2026-09-11T23:21:11+08:00（+08）｜ 会话框: **L1-SI-030-EB4E10** ｜ 编制: Reasonix
> 存证: **GSEQ-1276**（首版）/ **GSEQ-1277**（V0.1-DRAFT-REV1）/ **GSEQ-1279**（裁定 Ruling）/ **GSEQ-1280**（V0.2 定版）/ **GSEQ-1281**（V0.2-DRAFT-REV1 补正）/ **GSEQ-1284**（REV2：D-1/D-2 整改同步）/ **GSEQ-1289**（REV3：§一 现状回填）/ **GSEQ-1293**（Ruling：D-3 `scope` 最小集）/ **GSEQ-1294**（REV4：§四 条款落地）/ **GSEQ-1297**（Ruling：D-6 版本协商 + D-7 匿名只读）/ **GSEQ-1298**（REV5）/ **GSEQ-1304**（合并核证）/ **GSEQ-1305**（**V1.0-FROZEN 冻结**）（双库）｜ 性质: **制度规范（**V1.0-FROZEN 已冻结**）**——本件为规范起草件，**非司法裁决、不得单独作为处分依据**
> 依据: TDCA-STD-SRIGHT-001 **V1.2** §六（副作面纪律：「`tdcad mcp serve` 常驻 stdio 服务**另议**，须先定会话生命周期规范」）｜ SRIGHT-001 §九-4（登记余项）｜ TDCA-STD-LAYER-001 §四 ｜ DCD-CORE-GO-001 §三（MCP 桥接）｜ NCA 统一编码与归档纪律（TDCA-NCA-CODING-STANDARD-001）
> 触发: **M2 ②（G 块余项）**——`tdcad mcp serve` 常驻会话（触发条件 = 先定本规范）
> 实现状态: **已实现且已合入 main**——PR **#121**（squash `7fc548d9e6250e19c53df85cfb492620aa80b347`）；CI **四路全绿**（run #16 push / #17 pull_request / #18 main），含 `go test -race -count=1 ./...`（原文：五包全 ok、无 `FAIL` / 无 `DATA RACE`）。见 §一 现状与 §十三 验收。

---

## 零、本件定位与范围

| 项 | 内容 |
|---|---|
| 目的 | 为 `tdcad mcp serve` **常驻工具会话**确立握手 / 心跳 / 断开三段纪律，使常驻用法与一次性 CLI 通道**口径一致、可审计、可拒绝** |
| 适用 | core-go `pkg/mcp` stdio 常驻服务（`tdcad mcp serve`）与任何 TDCA 侧发起的常驻工具会话连接 |
| 不适用 | ① 一次性 CLI 通道（`CliTransport`，SRIGHT-001 §六，**已有独立纪律，不受本件约束**）② 跨主体协作编排（Paperclip 化合线）③ 人类签批流程（ID71，**永不入会话**） |
| 交付物 | 本规范（**V1.0-FROZEN**）+ 会话层接口契约（§十）+ 参数默认表（§七）+ 验收用例计划（§十三） |
| 不交付 | **不施工代码**；不接通 Python 侧；不改动已发布公开副本与 FROZEN 件 |

## 一、现状（**实现后实测**，2026-09-11 回填）

> 依据来源：**本侧实跑**（Go 1.23.12，`%LOCALAPPDATA%\Programs\go\bin\go.exe`）＋ 源码核对——`go build ./...` **exit=0**；`go test ./pkg/mcp/... -v` **44 PASS / 0 FAIL**；`go test ./...` **五包全绿**；V4 同构复核三工具两路**逐字段一致**。**早前「本环境无 go 工具链」系 PATH 误判，已更正。**

**已实现（可复用，接口熵=0）**

| 能力 | 现状 |
|---|---|
| 传输 | MCP **JSON-RPC 2.0 over stdio**，逐行 JSON，零第三方依赖 |
| 协议版本 | `ProtocolVersion = "2025-06-18"`（MCP tools 子集） |
| 方法集 | `initialize` / `notifications/initialized` / `tools/list` / `tools/call` / **`ping`（request→response）** / **`close`（通知）** |
| 工具四件 | `enforce_check` / `nsfl_eval` / `nca_append` / `nca_verify`（与 CLI、Python 桥接 JSON **同构**） |
| fail-closed | 工具参数 JSON Schema 校验（缺必填 / 未知字段 / 类型不符 → 拒）；`initialize` **三层未知字段**（顶层 / `_meta` 命名空间 / `_meta.tdca`）拒绝 |
| CLI 入口 | `tdcad mcp serve`（九个 flag：`--allow-anonymous --t-handshake --t-ping --t-pong --n-stale --n-abort --t-drain --t-gc --max-inflight`，默认值 = §七） |
| **会话层（新）** | `pkg/mcp/session.go`（528 行）：**八态状态机**（含 `SUSPENDED`）、`SessionPolicy`（§七 默认表逐值一致）、**四类事件**（`type=service`，**内存累积不落盘**）、**握手三要素校验**（fail-closed）、**心跳**（服务端定时 `ping`，miss ≥2→`STALE`、≥3→`ABORTED`）、**断开四步**（`DRAINING`→`CLOSED` / `ABORTED`）、**会话小结**（`_meta.tdca.session_summary`）、**半开检测**（`OnTransportBroken()` → 立即 `ABORTED(transport-broken)`） |
| 服务端接线 | `pkg/mcp/server.go`（847 行）：`initialize` 解析 `_meta.tdca` 并回 `session_id`(=`PCS-{token_id}`) / `session_policy`；`initialized` 推进 H3；`tools/call` 前置**会话态闸门**；`ping`/`close`；错误统一 `-32000` + 前缀 `tdca/session:` |
| 既有会话对象（相邻层，本件复用） | `layer_interop/ath_token.py`：ATH 握手 → **配置权会话** `PCS-{token_id}`（`state=INITIALIZED`）+ 边界切片 `BS-{token_id}` |
| 用例 | `pkg/mcp/session_test.go`（943 行）：**44 用例**，A1~A17 按 §十三 编号对齐（含 A9 半开、A12a/A12b GC 拆分、A13 session_id 复用拒绝、A17 会话期到期） |

**未实现 / 明确边界（如实登记）**

| 项 | 说明 |
|---|---|
| **D-15 通道字段差** | MCP `nca_append` schema（`additionalProperties=false`）**不含 `payload`**：CLI 通道接受、MCP 通道 fail-closed 拒 → **两通道表达力不等价**（既有防注入设计，非缺陷）；口径须**明示**（经 MCP 通道走 `payload_ref`） |
| Python 侧未接通 | `CliTransport` 明确**不执行** `mcp serve`（SRIGHT-001 §六 副作面纪律，保持） |
| 多连接 / 多主体 | **未实现**（裁定 D-4A 后续扩展点）；匿名态 `session_id="PCS-anon"` 不可区分——**已登记为本扩展点的前置条件（P-6，已关闭）**：启用多连接前须先改 ID 生成 |
| **接口熵=0 的强度限定（P-1 + D-15）** | 同构性（V4 复核）**仅在 schema 已声明字段子集内**成立；MCP 通道表达力**窄于** CLI（`payload` 不在 MCP `nca_append` schema，`additionalProperties=false`）→ **经 MCP 通道提交 NcaRecord 须走 `payload_ref` 引用**；**不得据此宣称两通道完全等价** |
| 竞态证伪 | **已证伪 ✅**：CI `go test -race -count=1 ./...`（run #16/#17/#18）全 `ok`（`cmd/tdcad` 1.019s ｜ `pkg/enforce` 1.018s ｜ **`pkg/mcp` 2.029s** ｜ `pkg/nca` 16.102s ｜ `pkg/nsfl` 1.487s），**无 `FAIL` / 无 `DATA RACE`**（原文在档） |
| scope 语义 | **已裁定 ✅**（D-3①，GSEQ-1293）：本通道最小集 = `pcr_token.scope` **须含字面量 `"mcp"`**；通用口径仍依 SRIGHT-001 §三 `scope_covers`；扩展工具面须先裁定（见 §四） |
| **已整改并合入 main（R-11/R-12，GSEQ-1304）** | 实现已按 D-6 **支持集协商**（`SupportedProtocolVersions` 含 `2025-11-25`）与 D-7 **默认匿名只读**（`AllowAnon=true`、`writeTools={nca_append}`）落地；PR #121 squash 合入，CI 四路全绿 |

**结论**：会话层**已实现并经本地实跑通过**（44 用例）；余 = **CI `-race`（R-6）** 与**签批转 FROZEN**；边界项（D-15 / scope / 多连接）见《《TDCA-M2-SESSION-MCP-001-ISSUE-REGISTER-遗留问题清单》》。


## 二、会话模型

| 概念 | 定义 |
|---|---|
| **会话（session）** | 一次 stdio 连接从握手完成到断开的完整区间；**stdio 下与会话一一对应**（连接即会话） |
| `session_id` | **复用既有配置权会话口径**：`PCS-{token_id}`（来源 TDCA-STD-LAYER-001 V1.1 §四 + `layer_interop/ath_token.py`，GSEQ-1198）；同一配置权存在多连接时追加连接序号 `#{n}`（如 `PCS-…-#2`）。**不进入对外协议字段**，仅置于 MCP 允许的 `_meta.tdca.session_id`（见 §十四 D-5） |
| 会话主体 | **单会话单主体**（`agent_id` / TDID）：一个会话只服务一个挂载主体，**禁止跨主体复用** |
| 三要素绑定 | 会话 = ① 主体身份（AgentCard）② 配置权（**PCR-Token**）③ 协议版本（MCP + TDCA 兼容矩阵）；**三者齐备方可进入 ESTABLISHED** |
| 持权复用 | PCR-Token 校验**逐项复用 SRIGHT-001 §三「校验五项」**（holder / scope_covers / not_expired / budget_ok / signed）——**不自造口径、不新增校验维度**；**本通道 `scope` 最小集见 §四**（裁定 D-3①） |
| 判定语义 | 会话层**只负责「连得上、看得住、断得干净」**；`enforce/nsfl/nca` 的判定语义**不因常驻而改变** |
| **会话 ≠ 调用权** | 沿用既有口径（`ath_token.handshake_to_session`：`call_right_granted=false`）——会话建立只代表**「连得上」**；调用权仍由 **CCV 五层 + 正和评估**授予（SRIGHT-001 §四/§五）；本件**不新增前缀、不重定义会话对象** |

**生命周期总览**

```
IDLE ──initialize──▶ HANDSHAKING ──notifications/initialized──▶ ESTABLISHED
                          │(超时/版本不相容/持权不足)                │
                          ▼                                          ├─ ping/pong 正常 ─┐
                       REJECTED(不建立)                                │                  │
                                                                       │◀─────────────────┘(心跳 miss ≥2 → STALE；≥3 → ABORTED)
                                                                       │
                                                    （client close / EOF / 服务端主动）
                                                                       ▼
                                                                   DRAINING ──(排空或超时)──▶ CLOSED
```

## 三、状态机与迁移

> **与既有配置权会话的衔接**：既有 `PCS-{token_id}` 配置权会话（`ath_token.handshake_to_session`，state=`INITIALIZED`）管**持权边界**；本节状态机管**连接可用性**——两者并存、互不替代。进入 `ESTABLISHED` 的前置 = 已有 `PCS-*`（或本会话握手时经 ATH 握手派生）；**会话建立不等于授予调用权**。

| 状态 | 语义 | 允许的入向操作 |
|---|---|---|
| `IDLE` | 进程已起，未握手 | 仅 `initialize` |
| `HANDSHAKING` | 已收 `initialize`，待 `notifications/initialized` | 仅 `notifications/initialized`；其余一律 `session-not-established` |
| `ESTABLISHED` | 会话可用 | `tools/list` / `tools/call` / `ping` / 通知类 |
| `STALE` | 心跳 miss ≥2（连接疑似半开） | 仅 `ping` 应答与主动 `close`；**新 `tools/call` 拒绝**（`session-stale`） |
| `SUSPENDED` | **PCR-Token 到期**（裁定 **D-2A**）：持权失效、连接仍可用 | 仅 `ping` / `tools/list`（只读）/ 主动 `close`；**新 `tools/call` 拒绝**（`token-expired`） |
| `DRAINING` | 已收到关闭意图，在途请求排空中 | 不接受新请求；仅回填在途响应 |
| `CLOSED` | 正常结束 | 无（连接应已关闭） |
| `ABORTED` | 异常结束（心跳超时 / 管道破裂 / 进程退出） | 无 |

| 迁移 | 触发条件 | 处置 |
|---|---|---|
| IDLE → HANDSHAKING | 收到合法 `initialize` | 记 `session_open_pending`（内存） |
| HANDSHAKING → ESTABLISHED | 收到 `notifications/initialized` 且三要素齐备 | 记 `session_open` 事件（§八） |
| HANDSHAKING → REJECTED | `T_handshake` 超时 / 版本不相容 / 持权不足 / 主体缺声明 | 返回错误 + **不建立会话**；连接可关闭；**不得降级静默继续** |
| ESTABLISHED → STALE | 连续心跳 miss ≥ `N_stale`(2) | 停止受理新请求（fail-closed），保留在途 |
| STALE → ESTABLISHED | 收到有效 `pong` 或新 `ping` | 计数清零，恢复受理 |
| ESTABLISHED → SUSPENDED | PCR-Token 到期（SRIGHT-001 §三 `not_expired` 不过；裁定 **D-2A**） | 停收 `tools/call`（`token-expired`）；**保留连接与心跳**（不断开） |
| SUSPENDED → ESTABLISHED | 续期到位：按 D-2bA **断开重连重新握手**（或原 token 复检于有效期内通过） | 恢复受理；不接受会话内 in-band 换 token |
| STALE/ESTABLISHED → DRAINING | 收到 client 关闭意图（`close` / stdin 关闭 / 服务端主动关停） | 停止受理新请求，等待在途 ≤ `T_drain` |
| DRAINING → CLOSED | 在途清空，或 `T_drain` 超时 | 记 `session_close`（含超时标记） |
| 任意 → ABORTED | 心跳 miss ≥ `N_abort`(3) / stdout 写失败 / 进程终止 | 记 `session_abort`（含原因） |

**不变量**

1. `session_id` **不跨会话复用**；重连须重新握手。
2. `DRAINING/CLOSED/ABORTED` 状态下**一律不再执行工具**；`SUSPENDED` 状态下**不执行 `tools/call`**（仅 `tools/list` 只读可用）。
3. 状态迁移**单向可审计**：每次迁移生成一条会话事件（§八）。
4. 任何异常路径**默认拒绝**（fail-closed），不得为「保持会话」而放宽门禁。
5. **匿名会话 = 未认证主体**：仅授**只读工具面**（`enforce_check` / `nca_verify` / `nsfl_eval` 可用；**`nca_append` 等写类工具一律拒** `token-missing`）——**不得因匿名而放宽任何写路径门禁**（裁定 D-7）。

## 四、握手（HANDSHAKE）

**四步（严格顺序）**

| 步 | 方向 | 内容 | 失败处置 |
|---|---|---|---|
| H1 | client → server | `initialize`：`protocolVersion` + `clientInfo{name,version}` + `_meta.tdca`（`agent_card` / `pcr_token` / `scene`） | 缺 `_meta.tdca` → 建立**匿名只读会话**（`session_id=PCS-anon`；服务端**默认** `allow_anonymous=true`，裁定 **D-7**）；**仅当显式配置 `allow_anonymous=false` 时**拒（`token-missing`） |
| H2 | server → client | `initialize` 结果：`protocolVersion`（协商后） + `capabilities` + `serverInfo` + `_meta.tdca.session_id` + `_meta.tdca.session_policy`（超时/心跳参数，供客户端对齐） | 客户端版本**不在支持集**（或低于最低基线）→ 返回自身版本并以 `-32000 tdca/session:version-incompatible` 终止（**不静默降级**）；**在支持集内 → 接受**（协商版本记入 `session_open` 事件），结果回**服务端自身版本** |
| H3 | client → server | `notifications/initialized` | 超 `T_handshake` 未收到 → `REJECTED`（`handshake-timeout`） |
| H4 | server | 三要素校验：`agent_card`（复用 `enforce` 准入门）+ PCR-Token（**SRIGHT-001 §三 五项**）+ 版本兼容 | 任一项不过 → `REJECTED`（`token-missing` / `token-scope-insufficient` / `entry-rejected`），并**携带具体失败项**（不虚报）；涉及 ATH 侧时，令牌 → 边界切片 → CCV **复用** `layer_interop/ath_token.py` 口径（不新增前缀、不自造） |

**握手纪律**

- 握手阶段**不得执行任何工具**（`tools/call` → `session-not-established`）。
- 握手**不产生持久副作用**：不新建持久账本、不写盘（与 `CliTransport` 副作面纪律同源）。
- `agent_card` 校验**复用** `enforce` 准入门（`protocol_version/scene_id/role/allowed_calls/nsfl_boundary`），**不新增字段**——接口熵=0。
- 握手结果（成功/拒绝）**一律记会话事件**；拒绝原因须可复算（原始入参摘要入事件）。
- **版本协商纪律（裁定 D-6，GSEQ-1297）**：本服务端版本 = `2025-06-18`（tools 子集）；**支持集** = `{2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25, …}`（MCP 官方 SDK 现行值，随生态基线更新）。
  - 客户端版本 ∈ 支持集 → **接受**，结果回服务端自身版本（`2025-06-18`），客户端自行判定是否继续；
  - 客户端版本 **∉ 支持集** 或低于最低基线 → 拒 `version-incompatible`（**不静默降级**）；
  - **协商 ≠ 降级**：版本协商**不得**导致回落更弱校验（schema / 门禁 / 超时阈值一律不因版本而放宽）；
  - TDCA 侧 `protocol_version` = `3.1.2`（core-go `SupportedProtocol`）**不变**；**不新增版本宣告字段**（接口熵 = 0）。
- **持权 `scope` 最小集（裁定 D-3① = 规范承认 `"mcp"` 为最小集，GSEQ-1293）**：TDCA MCP 通道的 `pcr_token.scope` **必须含字面量 `"mcp"`**——此为**本通道最小集**；`scope_covers` 的**通用口径**仍依 SRIGHT-001 §三（覆盖工具边界），本通道**以 `"mcp"` 为覆盖判据**（实现已如此，本节即**承认并固化**）；**扩展工具面**（新增工具族/子通道）时**另定义更细 scope 记号**，**须先裁定**（不得自行新增记号）。

## 五、心跳（HEARTBEAT）

| 项 | 纪律 |
|---|---|
| 机制 | 复用 MCP `ping`（request）→ `pong`（response）；**双向可发**（服务端为主动方做保活） |
| 频率 | 服务端每 `T_ping`(30s) 发一次 `ping`；空闲期亦发（保活），**不因无业务而停发** |
| 应答时限 | 客户端须在 `T_pong`(15s) 内应答；超时计 1 次 miss |
| 失联判定 | 连续 miss ≥ `N_stale`(2) → `STALE`（停收新请求）；≥ `N_abort`(3) → `ABORTED` |
| 时钟 | **以单调时钟计数**（不接受 wall-clock 依赖；跨机时钟偏斜不得影响判定） |
| 半开检测 | stdout 写失败 / 管道破裂 / 进程退出 → **立即** `ABORTED`（不等心跳阈值） |
| 空载性 | 心跳**不改变任何判定**、不消耗配置权预算、**不写 NCA**（见 §八） |
| 恢复 | 收到有效 `pong` 即清零 miss 计数；回 `ESTABLISHED`（若持权已失效则回 `SUSPENDED`） |
| **token 到期（裁定 D-2A）** | **不停止心跳**：会话转 `SUSPENDED` 但保活继续（避免误判半开）；仅 `tools/call` 被拒 |
| 模拟态 | 若心跳由替身实现（无真实连接）**必须**标 `simulated=true` 并注明替身类型（ID92） |

## 六、断开（DISCONNECT）

**正常断开（四步）**

| 步 | 动作 | 时限 |
|---|---|---|
| D1 | 关闭意图：client 发 `close`（TDCA 扩展通知）或直接关闭 stdin | — |
| D2 | 服务端转 `DRAINING`：停收新请求，回填在途响应 | ≤ `T_drain`(5s) |
| D3 | 服务端回 **会话小结**（`_meta.tdca.session_summary`：`session_id` / 时长 / 请求数 / 工具计数 / 拒绝数 / 结束原因） | 一次性 |
| D4 | 关闭连接，转 `CLOSED`，记 `session_close` 事件 | — |

**异常断开**

| 场景 | 判定 | 结果 |
|---|---|---|
| 心跳超时 | miss ≥ `N_abort` | `ABORTED`（`heartbeat-timeout`） |
| 管道破裂 / 写失败 | 立即 | `ABORTED`（`transport-broken`） |
| 进程被终止 | 无事件（不可捕获） | 由对端按 `ABORTED` 记录，**原因标 `unknown`**（不推测） |
| 排空超时 | 在途未清空 | `CLOSED`（`drain-timeout`，标记在途残余数） |

**断开纪律**

- 断开**不失效** PCR-Token（凭证生命周期独立于会话）；但**同一 token 的新会话须重新握手**（不复用会话态）。
- 资源回收：内存态链/引擎随会话终结即弃（沿用「无持久副作用」）；**不引入跨会话缓存**（裁定 **D-1A**：保持无状态）。
- **会话 GC（裁定 D-2 处置）**：`DRAINING` 超 `T_gc`(60s) 未收尾 → 强制回收并记 `session_abort(gc-timeout)`；**`STALE`/`SUSPENDED` 连续超 `T_gc` 同适用同一回收**（实现已覆盖，本版补记）。
- 断开事件**必须可复算**（时长、计数、结束原因三项为最小集）。

## 七、参数与超时默认表（可配置，配置须存证）

| 参数 | 默认 | 说明 |
|---|---|---|
| `T_handshake` | 10s | 握手总时限（H1→H3） |
| `T_ping` | 30s | 服务端保活间隔 |
| `T_pong` | 15s | 应答时限 |
| `N_stale` / `N_abort` | 2 / 3 | 连续 miss 阈值 |
| `T_drain` | 5s | 在途排空上限 |
| `T_gc` | 60s | 残留会话回收 |
| `allow_anonymous` | **true** | 是否允许无主体匿名会话；**匿名 = 只读面**（写类工具仍须 PCR-Token；裁定 **D-7**，GSEQ-1297） |
| `max_inflight` | 1 | 在途请求上限（stdio 逐行语义；≥2 即须显式声明） |

**配置纪律**：任何偏离默认值的配置**必须随会话事件存证**（否则视为口径漂移，审计不可复算）。

| ⚠️ **凭证族默认时长**（名称待件主定） | ⛔ **待定** | ⭐ 取值归**件主／创始人**（一处定值）；⭐ 偏离默认值须**随会话事件存证**（照 §七 既有配置纪律） |

## 八、会话事件与 NCA 存证挂点

| 事件 | 触发 | 最小集字段 | 是否入 NCA |
|---|---|---|---|
| `session_open` | HANDSHAKE 成功 | `session_id` / 主体 `agent_id` / 场景 / PCR-Token `token_id`（**不含 token 值**）/ 协商版本 | **由调用侧决定**（裁定 **D-3A**） |
| `session_close` | 正常断开 | 上述 + 时长 / 请求数 / 工具计数 / 拒绝数 / `close` | 同上 |
| `session_abort` | 异常断开 | 上述 + `abort_reason`（枚举）/ 在途残余 | 同上 |
| `session_rejected` | 握手被拒 | 失败项（枚举）/ 原始入参摘要 | 同上 |
| 心跳 / pong | 每次 | — | **禁止入 NCA**（噪声，无独立证据价值） |

- 事件类型统一为 **`service`**（NCA type 枚举既有值，不新增类型）。
- **默认不落盘**：core-go 侧无持久账本（既有纪律），事件仅在会话内内存累积并由小结回传；**是否写入统一索引由调用侧（S-Right / 网关）决定**。
- 凭据纪律：`pcr_token` **只记 `token_id`，永不记 token 值**；token 不落文件 / 日志 / NCA / git。

## 九、错误码与 fail-closed

会话层错误**不新增协议字段**：统一复用 JSON-RPC `-32000`，`message` 前缀 `tdca/session:`。

| 子码 | 触发 | 语义 |
|---|---|---|
| `handshake-timeout` | H3 超时 | 不建立会话 |
| `version-incompatible` | 版本**不在支持集**（或低于最低基线） | 拒绝，不降级（**支持集内接受**，见 §四 D-6） |
| `entry-rejected` | `agent_card` 不过 | 复用 `enforce` 结论 |
| `token-missing` / `token-scope-insufficient` | PCR-Token 缺 / 越界 | 复用 SRIGHT-001 §三 五项（握手期）；**匿名默认仅只读**（D-7）——`token-missing` 此时**仅**在匿名会话调**写类工具**或显式禁用匿名时触发。**补注（P-7，已关闭）**：握手期「**过期**」与「**越界**」同归本子码（区分依赖 `session_rejected` 事件详项）；**会话期**过期另用 `token-expired`（D-2A），审计时须按**阶段**区分 |
| `token-expired` | PCR-Token 到期（裁定 **D-2A**） | 停 `tools/call`，会话转 `SUSPENDED`（**不断开**） |
> **加注（2026-09-29 · GSEQ-2345 · 追加式）**：`token-expired` 之适用范围 ⭐ **由「PCR-Token」扩至「凭证族」**（含**委托令牌**）；⚠️ **阶段区分口径不变**（握手期归 `token-scope-insufficient`，会话期归 `token-expired`）；⛔ **不新增子码**（接口熵维持既有口径）。
| `session-not-established` | 握手期调用工具 | 拒绝 |
| `session-stale` | `STALE` 期新请求 | 拒绝 |
| `heartbeat-timeout` | 心跳超阈值 | `ABORTED` |
| `transport-broken` | 写失败/管道破裂 | `ABORTED` |
| `drain-timeout` | 排空超时 | `CLOSED` + 残余标记 |
| `max-inflight-exceeded` | 在途超限 | 拒绝 |

**fail-closed 总则**：**未知状态、未知方法、未知字段、未知子码一律拒绝**；不得以「宽容继续」换取会话存活。

## 十、接口熵与协议基线（不新增协议）

| 层 | 基线 | 本件增量 |
|---|---|---|
| 传输 | MCP stdio（逐行 JSON-RPC 2.0） | **无** |
| 协议版本 | MCP `2025-06-18`（**本服务端版本**；支持集见 §四 D-6） | **无**（仅规定协商与拒绝纪律；**不新增版本宣告字段**） |
| 方法 | `initialize` / `notifications/initialized` / `tools/list` / `tools/call` / `ping` | 复用；新增仅 **`close` 通知** 与 **`_meta.tdca.*` 载域**（MCP 规范的扩展位，**不占用工具 schema**） |
| 工具四件 | `enforce_check` / `nsfl_eval` / `nca_append` / `nca_verify` | **无改动**（输出与 CLI/Python 桥接继续同构） |
| TDCA 扩展字段 | — | `_meta.tdca`：`session_id` / `session_policy` / `session_summary` / `agent_card` / `pcr_token` |

> **扩展位纪律**：因工具 schema 为 `additionalProperties=false`（注入拦截），TDCA 会话字段**只允许**出现在 `_meta` 命名空间内，**永不混入工具参数**——否则将被既有 fail-closed 校验拒绝。

## 十一、安全与红线（强制随行）

1. **模拟态与真实执行严格区分（ID92）**：`simulated` 三态（模拟态 / 计划态未执行 / **真实执行**）——会话未真实建立即**如实拒或如实标注**，绝不虚报「已连上 / 已执行」。
2. **人类签批权不代行（ID71）**：会话**不得承载人类签批 / 授权动作**；会话内的任何「同意」均为机器语义，须另行登记。
3. **判定语义不动**：会话层不参与 `enforce/nsfl/nca` 判定；判定仍以 core-go 三包与 S-Right / CLS 侧为准。
4. **凭据纪律**：token / 口令不落文件、日志、NCA、git；生成即提醒记事本。
5. **单会话单主体**：禁止跨主体共享会话；跨主体协作须走既有编排线（Paperclip 化合）。
6. **门禁不可放宽**：不得为使会话通过而放宽 schema 校验、门槛或超时阈值（宁缺毋假）。
7. **平台中立**：本件不改变已发布链接与 FROZEN 件；公开副本随**正常发布批次**版本化重推。
8. **披露口径铁律（GSEQ-1089）**：本件为内部规范，若对外披露须零内部编号 / 零角色名 / 算力零提及。

## 十二、与既有规范的关系

| 规范 | 关系 |
|---|---|
| SRIGHT-001 **V1.2** §六 | 本件即其「`mcp serve` 另议」的**落地前置件**；PCR-Token 校验逐项复用其 §三；常驻通道**不替代** CLI 通道，二者并存 |
| TDCA-STD-LAYER-001 **V1.1** §四 | 层间定位沿用；**配置权会话口径（`PCS-{token_id}` / 边界切片 `BS-{token_id}`）逐项复用**——本件**不重复定义**会话对象，只补**传输会话**的握手 / 心跳 / 断开纪律 |
| TDCA-STD-AGENT-ID-001/002/003 | 主体身份与桥接映射沿用（`agent_card.agent_id` / TDID / OID） |
| TDCA-NCA-CODING-STANDARD-001 | 会话事件若入 NCA，编码与归档纪律沿用（追加制 / 链尾 +1 / 双库 MD5） |
| DCD-CORE-GO-001 §三 | MCP 桥接的立项依据（本件不改其范围，仅补会话层纪律） |

## 十三、验收与用例计划（**实现施工时执行，本件不含实跑**）

| # | 用例 | 期望 |
|---|---|---|
| A1 | 握手四步正常流 | `ESTABLISHED` + `session_id` 回传 + `session_open` 事件 |
| A2 | `protocolVersion` **不在支持集** | `REJECTED` + `version-incompatible`（**无静默降级**）；**支持集内**（如 `2025-11-25`）→ `ESTABLISHED`，结果回服务端版本 |
| A3 | 缺 PCR-Token | **默认**（`allow_anonymous=true`）→ **匿名只读会话**（`PCS-anon`），`session_open` 记 `anonymous=true`；**显式** `allow_anonymous=false` → `REJECTED` + `token-missing` |
| A4 | PCR-Token 越界 / **握手期**过期 | `REJECTED` + `token-scope-insufficient`（复用 §三 五项；**仅握手期**——会话期见 A17） |
| A5 | 握手期调用 `tools/call` | `session-not-established` |
| A6 | 心跳 2 次 miss | 转 `STALE`，新请求 `session-stale` |
| A7 | 心跳 3 次 miss | `ABORTED` + `heartbeat-timeout` |
| A8 | `pong` 恢复 | `STALE → ESTABLISHED`，计数清零 |
| A9 | 半开（写失败） | 立即 `ABORTED` + `transport-broken`（不等阈值） |
| A10 | 正常断开 + 在途排空 | `DRAINING → CLOSED` + 小结四项一致 |
| A11 | 排空超时 | **终态 = `CLOSED`**（**非** `ABORTED`）+ `drain-timeout` + **在途残余数标记** |
| A12 | 残留会话 GC | `T_gc` 后回收 + `gc-timeout` |
| A13 | `session_id` 跨会话复用尝试 | 拒绝（不变量 1） |
| A14 | 未知方法 / 未知字段 | `-32601` / `-32602`（既有 fail-closed 保持） |
| A15 | 心跳不入 NCA | 事件计数中**无**心跳记录 |
| A16 | 凭据纪律 | 事件与日志中**无** token 值（仅 `token_id`） |
| A17 | **会话期** token 到期（裁定 D-2A） | 会话转 `SUSPENDED`：`tools/call` 拒 `token-expired`；**心跳继续**；服务端**不断开**；重连续期后回 `ESTABLISHED` |
| A18 | **匿名会话**调写类工具（`nca_append`） | 拒 `token-missing`（**只读面边界**，D-7） |
| A19 | 客户端版本 = `2025-11-25`（官方 SDK 实际值）+ 无 `_meta.tdca` | `ESTABLISHED`（匿名只读）——**互操作冒烟恢复**（`handshake`/`tools/list`/`enforce_check` 全通） |
| A20 | **凭证族周期性到期处置**（承 `A4`／`A17`；裁定 **D-2A** 之通用化） | **凭证族**（含会话 `PCR-Token` 与**委托令牌**，依 §九「凭证生命周期独立于会话」）至**默认时长**（见 §七）：① **握手期**过期 ⟹ `REJECTED` + `token-scope-insufficient`（同 `A4`）；② **会话期**到期 ⟹ 会话转 `SUSPENDED`；`tools/call` 拒 `token-expired`；**心跳继续**；⛔ **不断开**（同 `A17`）；③ **断开不失效** —— 凭证生命周期**独立于会话**，⛔ 不因断开提前作废 |

**验收门槛**：全用例绿 + 与 CLI 通道**同构性复核**（同一工具经 CLI / 常驻会话两通道输出一致，接口熵=0——**强度限定见 §一 P-1/D-15**）。

> **补注（P-8，已关闭）**：本节列 **A1~A19**；实现**允许按状态拆分用例**（如 A12a/A12b），**用例编号与口径一律以本节为准**，实现侧拆分不改变验收语义。
> **实测（GSEQ-1304）**：`pkg/mcp` 合计 **46** 用例（`session_test.go` 29 + `server_test.go` 17），覆盖 A1~A19 及拆分项，全绿。

## 十四、裁定结果（**已裁定：创始人全采纳推荐项**）

> 裁定日期 **2026-09-11（+08）** ｜ 裁定入口 = `TDCA-STD-SESSION-001-DECISION-001`（GSEQ-1278）§三 勾选表 ｜ 裁定内容 = **D-1A / D-2A / D-2bA / D-3A / D-4A / D-5A（全采纳推荐项）**
> 裁定登记 = **GSEQ-1279（Ruling）**；本件定版 = **GSEQ-1280（Delivery）**。**本件为制度登记，非司法裁决、不得单独作为处分依据。**

| # | 事项 | 裁定 | 生效口径 |
|---|---|---|---|
| **D-1** | 会话态 NCA 链 | **(a) 保持无状态** | `nca_append` 每次新建内存链；多记录链的**校验**由既有 `nca_verify(records[])` 承担；**不引入会话态链**（会话中断即丢 = 不可复算证据，故不取） |
| **D-2** | PCR-Token 到期策略 | **(a) `SUSPENDED`** | 到期 → 拒新 `tools/call`（`token-expired`），**保留连接与心跳**；续期到位后回 `ESTABLISHED`（见 §三 / §五 / §九） |
| **D-2b** | 会话内续期方式 | **(i) 断开重连** | **不新增** in-band 续期语义（`_meta.tdca.pcr_token` 更新法**不采纳**）；接口熵维持 **0** |
| **D-3** | 会话事件入统一索引 | **(a) 由调用侧决定** | core-go 侧**不落盘**；是否写入统一索引由 S-Right / 网关决定（§八 口径不变） |
| **D-4** | 并发与多主体 | **(a) 单会话单主体 + `max_inflight=1`** | 同主体多连接登记为**后续扩展点**；跨主体多路复用**不予采纳** |
| **D-5** | 会话标识形态 | **(a) 复用 `PCS-{token_id}`，仅 `_meta.tdca.*`** | 不新增前缀；**不进入对外协议字段**（标准面变更流程另议） |
| **D-6** | 协议版本协商（**新增，GSEQ-1297**） | **(丙′) 按 MCP 标准协商** | 客户端版本 ∈ 支持集 → **接受**并回服务端版本；∉ → 拒 `version-incompatible`。**替代**原「任一不相容即拒」；依据 = 官方 SDK 支持集含 `2025-06-18` 且固定发 `2025-11-25`；**门禁不动** |
| **D-7** | 匿名会话（**新增，GSEQ-1297**） | **(丁-2) 默认匿名只读** | 默认 `allow_anonymous=true`，匿名会话**仅只读面**（写类工具拒 `token-missing`）；**替代**原默认禁匿名；**冒烟门禁零改动**（保持「默认配置即互通」语义） |

- **后续扩展点登记**：D-4(b) 同主体多连接（`PCS-…-#n`）——须先定**并发预算计量口径**方可启动。
- **实现施工**：本裁定即解锁（见 `TDCA-STD-SESSION-001-DECISION-001` §四 动作链）；施工落点 `tdca-core-go/pkg/mcp` + `cmd/tdcad`，验收 = §十三 16 用例 + 与 CLI 通道同构复核。


## 十五、版本与变更记录

| 版本 | 日期 | 变更 | 存证 |
|---|---|---|---|
| **V0.1-DRAFT** | 2026-09-11 | 首版起草（M2 ② 前置）：现状判读 + 会话模型 + 三态纪律（握手/心跳/断开）+ 参数表 + 事件挂点 + 错误码 + 接口熵纪律 + 红线 + 验收计划 + 待裁定 5 项 | **GSEQ-1276** |
| **V0.1-DRAFT-REV1** | 2026-09-11 | **衔接既有会话口径修订**（§一/§二/§三/§四/§十二/§十四）：传输会话标识**复用 `PCS-{token_id}`**（多连接 `#{n}`）；新增「会话 ≠ 调用权」（`call_right_granted=false`）与状态机衔接说明；ATH 侧令牌 → 切片 → CCV 复用 `ath_token.py`；**不新增前缀、不重复定义会话对象** | **GSEQ-1277** |
| **V0.2-DRAFT** | 2026-09-11 | **依创始人裁定定版（全采纳推荐项：D-1A / D-2A / D-2bA / D-3A / D-4A / D-5A）**：§三 新增 `SUSPENDED` 态（+2 条迁移、不变量 2 调整）、§五 心跳补 token 到期纪律、§九 新增 `token-expired`、§六/§八 去掉「待裁定」标注、§十四 由「待裁定项」改为「裁定结果（DECIDED）」 | **GSEQ-1279**（Ruling）+ **GSEQ-1280**（Delivery） |
| **V0.2-DRAFT-REV1** | 2026-09-11 | **一致性补正（Amendment）**：§十三 A4 限定为「握手期」过期；**新增 A17**（会话期 token 到期 → `SUSPENDED` / `tools/call` 拒 `token-expired` / 心跳继续 / 不断开），与 §三 / §五 / §九（D-2A）对齐 | **GSEQ-1281** |
| **V0.2-DRAFT-REV2** | 2026-09-11 | **D-1 / D-2 整改同步（创始人同意处置方向）**：§六 GC 纪律补记「`DRAINING` 与 `STALE`/`SUSPENDED` **同适用**同一回收」；§十三 **A11** 期望补注「终态 = `CLOSED`（非 `ABORTED`）+ 在途残余数标记」 | **GSEQ-1284** |
| **V0.2-DRAFT-REV3** | 2026-09-11 | **§一 现状按实跑回填**（Go 1.23.12：build exit=0 / 44 用例 PASS / 五包全绿 / V4 同构一致）：会话层由「未实现」转为「已实现」；新增 D-15 通道字段差、多连接/匿名态、竞态证伪、scope 待裁定等**边界项**如实登记 | **GSEQ-1289** |
| **V0.2-DRAFT-REV4** | 2026-09-11 | **D-3 裁定落地（①规范承认 `"mcp"` 为最小集）**：§四 握手纪律新增「持权 `scope` 最小集」条款（本通道最小集 = 含字面量 `"mcp"`；通用口径仍依 SRIGHT-001 §三 `scope_covers`；扩展工具面须先裁定）；§二 持权复用行加指向 | **GSEQ-1293**（Ruling）+ **GSEQ-1294**（Delivery） |
| **V0.2-DRAFT-REV5** | 2026-09-11 | **开源互操作冲突裁定落地（D-6 / D-7）**：§四 版本条款由「任一不相容即拒」改为**支持集协商**（D-6，丙′）；§四 H1 / §七 默认表 / §三 不变量 5 确立**匿名只读**（D-7，丁-2）；§九 / §十 / §十三（A2/A3 重写，新增 A18/A19）/ §十四 同步；§一 登记「待整改」行。**依据**：官方 Python MCP SDK 支持集含 `2025-06-18` 但固定发 `2025-11-25`、且 `initialize()` 无 `_meta` 注入 → 原口径下**任何标准客户端均不可用**（= 互操作倒退）。**门禁与 workflow 一律不动**（禁 `--allow-anonymous` 短路 / 禁 pin 旧 SDK） | **GSEQ-1297**（Ruling）+ **GSEQ-1298**（Delivery） |
| **V0.2-DRAFT-REV6** | 2026-09-29 | **凭证族到期处置并入（`GSEQ-2345`）**：§十三 **新增 `A20`**；§九 **加注**（适用范围扩至凭证族）；§七 **增参数行**（⚠️ 取值待定）—— ⭐ **追加式 · ⛔ 原行未改** |
| **V1.0-FROZEN** | 2026-09-11 | **冻结版（M2 ② 收官）**：D-6 支持集协商 + D-7 默认匿名只读**已落地并合入 main**（PR #121 / squash `7fc548d`）；**一次性收口**：§一 回填（已整改 / `-race` 已证伪 / `scope` 已裁定）+ **P-1/D-15 接口熵强度限定** + **P-6/P-7/P-8 补注**；遗留清单 P-1~P-8 **全数关闭**；**其余边界项随批登记**。本件转 **FROZEN**（文件名不改，沿用 LAYER-001 先例） | **GSEQ-1304**（合并核证）+ **GSEQ-1305**（收口） |

---

*TDCA-STD-SESSION-001 **V1.0-FROZEN**：`tdcad mcp serve` 常驻会话的握手 / 心跳 / 断开纪律**冻结版**——**实现已落地并合入 `main`**（PR **#121** / squash `7fc548d`；CI **四路全绿**含 `-race` 原文）；**接口熵=0**（不新增协议，仅 `_meta.tdca` 扩展位 + `close` 通知，**强度限定见 §一 P-1/D-15**）；§一 已按**实跑与合并结果**回填，遗留项 **8/8 CLOSED**；**后续 = 随正常批次重推公开副本（口径 A）** ｜ 编制: Reasonix（L1-SI-030-EB4E10）｜ 存证: GSEQ-1276（V0.1-DRAFT）/ GSEQ-1277（DRAFT-REV1）/ GSEQ-1279（裁定）/ GSEQ-1280（V0.2-DRAFT）/ GSEQ-1281（REV1）/ GSEQ-1284（REV2）/ GSEQ-1289（REV3）/ **GSEQ-1294（V0.2-DRAFT-REV4）** / **GSEQ-1297（裁定 D-6/D-7）** / **GSEQ-1298（V0.2-DRAFT-REV5）** / **GSEQ-1304（合并核证）** / **GSEQ-1305（V1.0-FROZEN）** / **GSEQ-1307（叙述更正）***
