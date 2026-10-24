# TDCA-STD-SRIGHT-001 · 场景配置权调用接口规范（185.7 → S-Right）V1.2

> 文档编号: TDCA-STD-SRIGHT-001 ｜ 版本: **V1.2** ｜ 日期: 2026-09-11（+08）｜ 会话框: L1-SI-029 ｜ 编制: Reasonix ｜ 存证: GSEQ-1265（V1.1 = GSEQ-1193；V1.0 = GSEQ-1192）
> 依据: GB/Z 185.7 内化映射（内化白皮书 §2.2）+ 185.7 精读（8 步→14 步；CCV 五层）｜ TDCA-STD-LAYER-001 §四 ｜ M2 重排（GSEQ-1190）
> 实现: `tdca-adapters/tool_call_right/`（**42 用例全绿** = 10 基础回归 + 10 V1.1 高级 + **22 V1.2 深化**）｜ 性质: 制度规范（内部基线）
> **V1.1 变更**: M2 待细化 5 项首轮落地——①PCR-Token ②CCV 五层完整化 ③Shapley 分配接入 ④边界变更联动重评 ⑤MCP 工具面对接（dry-run 如实标注）
> **V1.2 变更（GSEQ-1265）**: M2 深化 5 项全部闭环——①**PCR-Token 交换载体**（进程内 / 文件跨进程替身 / **网络载体占位如实拒**）②**Shapley 分配落地结算**（→ CLS 闭环结算：计税 + 台账 + NCA；守恒三律 + CLS I-1~I-5）③**步 3/6 结构化**（`CommitmentDeclaration`：目标函数 + 约束矩阵摘要 + 转发上下文）④**MCP 真实执行**（`tdcad` CLI 四工具**实执** + 实执/dry-run 三分流）⑤**边界变更跨主体调用方通知**（送达/确认留痕，**不得代确认**）

---

## 一、三子流程映射（185.7 → S-Right）

| GB/Z 185.7 | 实现 | 语义升级 |
|---|---|---|
| ① 工具列表获取 | `list_tools` → CDP-Pre **经济索引** | 功能索引 → 按效用拟合度排序（含 MOU 锚定计数） |
| ② 工具列表更新 | `update_tools` → **边界变更事件** | 变更须重过正和评估；**在册授予自动标记复查** + **受影响调用方逐一通知**（见 §五） |
| ③ 工具调用 | `invoke` → **14 步精简** | 终止条件 = 完成 + 税收锚定确认 + NCA 归档 |

## 二、调用链（14 步，逐步可审计）

```
1  连接 + PCR-Token 交换（持有人/边界/有效期/预算校验；缺省降级并标注；载体见 §三）
2  工具解析 + CCV 五层验证（见 §四）
3  目标函数声明与约束矩阵摘要（**结构化**：CommitmentDeclaration.objective/constraints，见 §五）
4  配置权预算检查（PCR-Budget；超支拒绝不执行——拒绝路径亦留声明）
5  工具选择（效用最大化 + 边界合规）
6  请求转发（**结构化上下文**：token 模式 / OID / 负载键 / NCA 上下文）
7  正和性最终确认（执行前；不通过拒绝）
8  工具执行（实时生成 NCA 片段；真实通道见 §六）
9  负空间 Runtime 检查
10 结果回传（效用计量 / 税收锚定记录 / NCA 指纹）
11 效用计量与 Shapley 分配（见 §五）
12 纳税触发（进项/出项 + MOU 更新）
13 结果回传智能体（计量 / 分配比例 / 税收凭证）
14 完成判断（完成 + 税收锚定确认 + NCA 归档）→ 未完成循环 2~14
```

## 三、PCR-Token 规范与交换载体（V1.2 扩展）

| 字段 | 说明 |
|---|---|
| `token_id` | `PCR-` + 12 位（唯一） |
| `holder_tdid` | 持有人（须与调用方一致） |
| `scope` | 配置权边界（须覆盖工具边界；`*`/`all` 为全域） |
| `budget_total` | 承载预算（≥ 本次调用成本） |
| `issued_at` / `expires_at` | 有效期（默认 TTL 600s） |
| `oid` | 国标身份码（走出范围时随附） |
| `signature` | 签名（当前 = 本地签名式） |

**校验五项**：holder / scope_covers / not_expired / budget_ok / signed —— 任一不过即拒绝。

**交换载体（`pcr_carrier.py`，V1.2 新增）**：

| 载体 | 模式 | 语义 |
|---|---|---|
| `InProcessCarrier` | `in-process` | 同进程直传（等价 V1.1 现状；默认） |
| `FileExchangeCarrier` | `file-exchange` | 本地文件落盘交换——**跨进程语义的结构等价替身**（含 `carrier_schema=PCR-TOKEN-EXCHANGE-1` 校验） |
| `NetworkCarrierStub` | `network-pending` | **真实网络载体占位**：`ready()=False`，发布/取回**即拒**（`CarrierUnavailableError`） |

**如实边界**：真实网络交换仍**未实现**（待发布通道提供服务端点/凭据）；`exchange_roundtrip` 只走到可用载体，且**未就绪一律拒**（不虚报）；取回方须为令牌持有人；取回件一律复用 §三 五项校验（不自造口径）。

## 四、CCV 五层验证（V1.1 完整化，185.7 精读步骤 2）

| 层 | 判定 |
|---|---|
| ① 身份兼容 | TDID 格式有效；走出范围时 OID 与在册映射一致（复用身份桥接） |
| ② 效用兼容 | 工具-场景效用拟合度 ≥ 阈值（默认 0.5） |
| ③ 正和兼容 | 效用精灵正和评估（coalition > Σ独立） |
| ④ 负空间兼容 | 负空间声明检查（违规 → 熔断） |
| ⑤ **税收兼容** | 工具服务方具可验证 **MOU 锚定历史**（≥1 条；模拟态默认 1 条） |

## 五、声明结构化 / Shapley 落地结算 / 边界联动与通知（V1.2 扩展）

**① 承诺声明（步 3/6 结构化，#3）**：`CommitmentDeclaration`

| 段 | 内容 |
|---|---|
| `objective` | 目标陈述 / 场景 / 工具 / 效用目标 / 独立基线 / 正和目标 / 引擎 |
| `constraints` | 宪法条款（第十六条 / ID71 / ID92）/ 边界 / 拟合阈值（含实测值）/ 预算上限与本次成本 / 负空间声明 / 税率 / MOU 锚定数 |
| `forward_context` | PCR-Token 与模式（attached / absent 降级）/ OID / 负载键 / NCA 上下文 |

声明**不改变任何判定**，数值取自网关与工具在册状态（可复算），并随调用存证归档（`CallOutcome.commitment`）。

**② 分配（V1.1）**：授予后自动分账——`v(S) = Σ_{i∈S}u_i + delta×|S|/n`（效用精灵 `GameTheoryEngine.shapley_value`），分配表随授予存证；Σ分配 = 联盟总效用。

**③ 落地结算（V1.2 新增，#2）**：`settlement_bridge.settle_shares`

| 模式 | 语义 |
|---|---|
| `direct`（默认） | **逐方定向支付**（DPI 语义）：每方计税（`CLSTaxAdapter`）+ 记账（`CLSLedgerAdapter`）+ 存证（`CLSNCAAdapter`） |
| `netting` | 走 `CLSEngine`（GIM 环销 → RTN 净额 → DVP → 计税 → NCA），并回传 CLS **I-1~I-5** 不变量 |

**守恒三律**：Σ分配 = 联盟总效用（按分配表精度容差）｜ Σ税后净额 + Σ税 = Σ分配 ｜ 各参与方分配额 ≥ 0。
**正和前置**：未授予或 δ≤0 **不结算**（fail-closed）。CLS 侧**只读复用**（不改其实现）。

**④ 边界联动与跨主体通知（V1.2 扩展，#5）**：`update_tools` 边界变更 → 在册授予标记 `RECHECK_REQUIRED` + 事件载 `affected_grants` 与 `notifications` → `recheck_grant()` 复查（边界覆盖 → ACTIVE；否则 REVOKED）。

| 接口 | 语义 |
|---|---|
| `notifications(party_tdid=None, pending_only=False)` | 通知清单（只读；可按调用方过滤 / 只看未确认） |
| `deliver_notifications(party_tdid=None)` | 送达留痕（**不改变授予状态**） |
| `acknowledge_notification(notification_id, party_tdid)` | 调用方确认（**须本人**，代确认 `PermissionError`；幂等） |

## 六、MCP 工具面对接与真实执行（V1.2 扩展）

**语义映射**（S-Right → TDCA MCP server 四工具）：
`enforce_check`（准入）→ `nsfl_eval`（负空间）→ `nca_append`（存证）→ `nca_verify`（校验）

**三分流执行纪律（`execute_with_channel`）**：

| 条件 | 结果 |
|---|---|
| 注入 transport（如 `CliTransport`） | **实执**：`executed=true`，真实 `rc/stdout`，`simulated=false` |
| 未就绪 + 无 transport | **dry-run**：`executed=false` + 计划与原因（如实） |
| 就绪但未注入 transport | `ready-but-no-transport`：**仍 `executed=false`**（不得以探测就绪冒充已执行） |

**真实通道（V1.2 新增）**：`cli_transport.CliTransport` 把四工具映射为 `tdcad` CLI 子命令（接口熵=0，不新增协议）：

| 工具 | CLI | 负载 |
|---|---|---|
| `enforce_check` | `tdcad enforce check <card.json>` | AgentCard（`protocol_version=3.1.2` / `scene_id` / `role` / `nsfl_boundary` 非空） |
| `nsfl_eval` | `tdcad nsfl eval <trigger> <signal>` | signal 需命中 R1~R10（未知 fail-closed=BLOCK） |
| `nca_append` | `tdcad nca append <record.json>` | NcaRecord（`prev_hash=sha256:genesis` 单记录链） |
| `nca_verify` | `tdcad nca verify <records.json>` | 记录数组 → 链校验 |

**副作面纪律**：只执行**无持久副作用**子命令（core-go CLI 每次新建内存态链/引擎）；`tdcad mcp serve`（常驻 stdio 服务）**另议**（须先定会话生命周期规范）。未定位构建产物即拒（`CliTransportError`）。

## 七、接口（`sright.py` / `mcp_bridge_adapter.py` / `pcr_carrier.py` / `settlement_bridge.py` / `cli_transport.py`）

`register_tool` / `list_tools` / `update_tools` / `issue_token` / `verify_token` / `ccv_verify` / `invoke` / `recheck_grant` / `boundary_events` / `grants` ｜ **V1.2 新增**：`declare_commitment` / `notifications` / `deliver_notifications` / `acknowledge_notification` ｜ `McpToolFaceAdapter.plan/execute/**probe_channel**/**execute_with_channel**/**transport_cli**/consistency_report` ｜ **载体**：`TokenExchangeCarrier` / `InProcessCarrier` / `FileExchangeCarrier` / `NetworkCarrierStub` / `exchange_roundtrip` ｜ **结算**：`settle_shares` / `ShareSettlement` ｜ **通道**：`CliTransport`（`locate` / `version` / `__call__`）

## 八、验收（V1.2 实测）

- `test_sright.py`（10 基础回归）+ `test_sright_advanced.py`（10 V1.1 高级）+ **`test_m2_deepen.py`（22 V1.2 深化）** ——**42 用例全绿**（经 `_inherit_selfcheck.py --with-m2` 一次性执行，含继承线共 107 passed / 0 failed）
- V1.2 覆盖：载体三态（进程内/文件/网络未就绪拒）+ 持有人不一致 + 坏 schema｜direct/netting 双模式守恒与 I-1~I-5｜未授予/非正和/不守恒/负额拒｜步 3/6 结构化（含预算拒绝路径留声明）｜通知生成/送达/确认/代确认拒/幂等｜通道三分流 + 未定位产物拒
- **真实通道实测**：`tdcad version` → `tdcad 1.0.0`；四工具实执 → `enforce check`=PASS / `nsfl eval rate-limit`=WARN / `nca append`=appended / `nca verify`=true（`simulated=false`）
- 正和引擎实测 = `utility-genie/GameTheoryEngine`；结算引擎实测 = `tdca-cls`（守恒 + 五不变量）

## 九、剩余待细化（登记跟踪）

1. ~~PCR-Token 真实网络交换~~ → **载体已抽象**；**网络载体仍占位**（待发布通道提供服务端点/凭据，属外部依赖）
2. ~~Shapley 分配落地结算~~ → **已闭环**（CLS 计税/台账/NCA；守恒三律 + I-1~I-5）
3. ~~CCV 步 3/6 细化~~ → **已闭环**（`CommitmentDeclaration` 结构化）
4. ~~MCP 真实执行~~ → **CLI 通道已闭环且实测**；**`tdcad mcp serve` 常驻会话**（握手/心跳/断开纪律）另登记
5. ~~边界变更的调用方通知~~ → **已闭环**（逐调用方通知 + 送达/确认留痕；不得代确认）

---

*S-Right 接口规范 V1.2：M2 待细化 5 项全部闭环（载体抽象 / 落地结算 / 步 3·6 结构化 / MCP 真实执行 / 跨主体通知）——42 用例全绿，真实通道四工具实测通过 ｜ 存证: GSEQ-1265*
