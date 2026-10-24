# TDCA-STD-INTEROP-001 · 合约 × 国标交互对接规范（185.6 → 合约 → 计税触发）V1.1

> 文档编号: TDCA-STD-INTEROP-001 ｜ 版本: **V1.1** ｜ 日期: 2026-09-11（+08）｜ 会话框: L1-SI-029 ｜ 编制: Reasonix ｜ 存证: GSEQ-1266（V1.0 = GSEQ-1195）
> 依据: 内化白皮书 §2.2（185.6 交互 → NCA 生成协议通信层）+ §4.1（**国标交互日志 = 税收事件触发器**）｜ GB/Z 185.6-2026（原文：§6.2~§6.4 / §7.1~§7.6 / §8.2~§8.3）｜ M4 重排（GSEQ-1190）
> 实现: `tdca-adapters/contract_interop/`（**34 用例全绿** = 10 基础 + **24 M4 深化**）｜ 性质: 制度规范（内部基线）
> **V1.1 变更（GSEQ-1266）**: M4 待细化 4 项全部闭环——①**C01-C16 合约族真实对接**（`contract_family.py`）②**185.6 内容元素完整映射**（`g185_6.py`：Data/Message/Task/Session）③**群组/混合参与方权限 + MRCR 联动**（`g185_6.py`）④**结算接 CLS 管线**（`interop_cls.py`）

---

## 一、三模式映射（185.6 §6.2~§6.4 → 交互事件）

| 国标模式 | 条文 | 交互事件 | 嵌套形态（内化白皮书 §2.2） |
|---|---|---|---|
| p2p 点对点 | §6.2 | `from_agent → to_agents[1]` | 单嵌套 NCA |
| group 群组 | §6.3 | `from_agent → to_agents[n]`（经消息分发功能模块） | 多嵌套 NCA |
| hybrid 混合 | §6.4 | 群组内子点对点（**由请求智能体决定**各服务方参与模式） | 网络嵌套 NCA |

交互事件字段：`event_id / mode / from_agent(TDID) / to_agents[TDID] / action / value / oid(可选) / payload`。

## 二、处理链（交互 → 合约 → 计税 → 结算）

```
交互事件 → ① 交互日志（= 税收事件触发器）
        → ② 计税（tax = value × 税率；**value=0 亦记录纳税事实**）
        → ③ 合约调用意图（**经合约族装配**：模板选择 + C01~C16 条款核验，见 §五）
        → ④ 存证（NCA）
结算：settle() → tax-settle 合约调用 + MOU 模拟态更新 + 存证
      **CLS 管线**：settle_interactions() → 环销/净额 → 定向支付 → 同刻计税 → 台账 → NCA（见 §七）
```

## 三、纪律（强制）

1. **交互日志即税收事件触发器**——每次受理的交互必产生一条税收事件（逐条对应，验收口径）
2. **幂等**：同 `event_id` 不重复计税、不重复生成合约意图（返回既有结果）
3. **身份前置**：from/to 的 TDID 须格式合法（复用身份桥接校验）
4. **负空间熔断**：声明违规 → 拒绝，**不计纳税事实**（日志记拒绝态）；亦**不入结算**
5. **存证必在**：合约意图与结算各生成 NCA（fail-closed）
6. **MOU 模拟态**（ID92）：结算更新 MOU 标注 Simulated
7. **字段名权威 = 国标原文**（V1.1）：交互内容元素不得自造字段名，缺失**如实标注不推测填补**

## 四、185.6 交互内容元素（V1.1 新增，#11）

字段名**逐字采 GB/Z 185.6-2026 原文**：

| 元素 | 条文 | 字段 |
|---|---|---|
| 数据 `data` | §7.3 | `type` / `metadata` / `payload` |
| 消息 `message` | §7.4 | `senderRole` / `senderId` / `sessionId` / `taskId` / `id` / `artifact` / `final` / `chunkIndex` / `lastChunk` / `dataItems` |
| 任务 `task` | §7.5 | 任务标识符 `taskId` / 会话标识符 `sessionId` / `state` / `stateChangedAt` / `messages` / `artifacts` |
| 会话 `session` | §7.6 | 会话标识符 `sessionId` / `sender` / `receivers` / `context` |

**关系（§7.2 六条）**：① 会话由请求智能体管理（创建/维护/注销，创建时决定参与方与模式）② 任务存在于会话中，会话内可有多个任务 ③ 消息可包含 `taskId`；任务可包含 `messages` ④ 消息内容封装在 `dataItems` 中（消息与数据为必要元素）⑤ 特定场景经**任务**交互（应含 `taskId`/`sessionId`/`state`）⑥ 特定场景经**消息**交互。

**实现**：`Data` / `Message` / `Task` / `Session` + `project_interaction()`（交互 → 四元素投影）+ `field_coverage()`（对账表）+ `validate_element()`（必填缺失 / 未知键 → `missing` / `unknown_key` warnings，**不推测填补**）。

## 五、参与方权限与 MRCR（V1.1 新增，#12）

**群组（§6.3）**：创建/配置/管理由**请求智能体**发起并维护，或由**第三方机构**预先配置；请求方可**直接邀请**服务智能体，也可**审核加入申请**；第三方机构可**代为发起邀请或审核**。

`GroupRegistry`：`create_group(creator_kind=requestor|third-party)` / `invite` / `request_join` / `approve` / `remove`，**写操作须经授权主体**（创建者或被授权第三方），越权即 `GroupPermissionError`；逐写操作生成存证（`interop-1856-group-*`）。

**混合模式（§6.4）**：`plan_hybrid(requestor, {tdid: p2p|group})` —— 参与模式**由请求智能体决定**；同一服务方可同时参与点对点与群组交互。

**MRCR（ID54「多角色兼容性」）**：同一主体**不可同时持有冲突的协议层角色**。
触发口径（tp-rules-v1.0 规则 3）：`|Scenes(agent)| > 1 ∧ ¬Isolated(agent, scenes)` → 动作 **`WARN_AND_AUDIT`**（不阻断但须审计留痕）；`mrcr_check()` 另检出**同场景内请求/服务角色冲突**。

## 六、合约族对接（V1.1 新增，#10）

**权威源（只读）**：`tdca-official-kb/contracts/contract-templates-v1.0.yaml`（`TDCA-CONTRACTS-v1.0`）

| 模板 | 类型 | 制度锚 |
|---|---|---|
| `CONST-ENFORCE-001` | 宪法十六条强制执行 | TERMS-001 §2.1 / ID29（含 **C01~C16 条款编码**） |
| `NSFL-FUSE-001` | 负空间熔断执行 | NSFL / ID85/ID86 |
| `MOU-ANCHOR-001` | MOU 税收锚定 | TERMS-001 §2.4 / ID79/ID92 |
| `CONFIG-RIGHT-SCHEDULE-001` | 配置权调度（七元组 + Shapley + **MRCR**） | TERMS-001 §2.2 / ID76 / ID54 |
| `DCEP-MOU-001` | 数字人民币智能合约对接 | ID43/ID70/ID80 |

**对接语义**：交互事件 → **模板选择**（负空间声明优先 → NSFL 模板；否则按动作映射）→ **调用装配**（`template_id` + 模板 `functions` 参数面）→ **条款核验** → 存证。

**条款核验三态**：`pass` / `fail` / **`not_evaluated`**——C01 可观测（须有 NCA 引用）、C02 正和（须 δ>0）、C03 自证（须证据哈希）、C04 配置权第三极（须七元组/调度声明）、C05 刚需线保护；**C06~C16 无逐条判定依据 → 一律 `not_evaluated`**（不默认为通过）。

**纪律**：`official-kb` **只读**（本层不写权威源）；未在权威源中定义的合约号一律拒（**不自造合约号**）。

## 七、结算与 CLS 管线对接（V1.1 新增，#13）

`settle_interactions(gateway, mode=netting|direct)`：

| 模式 | 链路 |
|---|---|
| `netting` | 交互价值 → 债务边 → CLS **GIM 环销** → **RTN 净额（T_net）** → DVP 定向支付 → 同刻计税 → NCA（回传 I-1~I-5） |
| `direct` | 逐笔**定向支付**（DPI 语义）→ 计税 → 台账 → NCA |

**口径分层（不混）**：

| 层 | 名称 | 来源 |
|---|---|---|
| interop 层 | **交易税**（`value × tax_rate`） | `tax_events()`（本层**只记账不重算**） |
| CLS 层 | **配置权调度税**（T-031，默认 2%） | `CLSTaxAdapter.compute_for_settlement`（按净额支付金额） |

**守恒/纪律**：定向性（`payer≠payee` 且金额>0，I-1）｜ 净额守恒（Σ定向支付 = T_net，I-2）｜ 异常不中断（I-5）｜ 拒绝态与熔断事件**不入结算**｜ CLS 侧**只读复用**（零改动）。

## 八、集成装配口径（M5 核验发现 — 重要）

**跨模块集成须共享存证层**：各网关应注入**同一 NCA 生成器实例**，否则各模块各自实例化会导致跨模块存证彼此不可见（M5 全链路核验首次暴露）。

```python
gen = NCAGenerator()                     # 单一存证层实例
bridge  = IdentityBridge(nca_generator=gen)
sright  = SRightGateway(..., nca_generator=gen)
interop = ContractInteropGateway(..., nca_generator=gen)
family  = ContractFamily(nca_generator=gen)          # V1.1
```

## 九、接口

`interop.py`：`on_interaction` / `settle` / `interaction_log` / `tax_events` / `contract_calls`
**V1.1 新增**：`contract_family.ContractFamily`（`load` / `select` / `bind` / `check_clauses` / `call_for_interaction`）｜ `g185_6`（`Data`/`Message`/`Task`/`Session` / `project_interaction` / `field_coverage` / `validate_element` / `GroupRegistry` / `plan_hybrid` / `mrcr_check`）｜ `interop_cls.settle_interactions`

## 十、验收（V1.1 实测）

- `tests/test_interop.py`（10）+ **`tests/test_m4_deepen.py`（24）** ——**34 用例全绿**（经 `_inherit_selfcheck.py --with-m4` 执行；全量五线共 **163 passed / 0 failed**）
- V1.1 覆盖：四元素字段名与国标逐字一致 / 关系六条 / 缺失与未知键如实标注 / 投影四元素齐备 / 群组双权威创建 + 越权拒 + 邀请-申请-审核-移除 + 第三方代管 / 混合模式请求方决定 / MRCR 多场景未隔离与同场景角色冲突（`WARN_AND_AUDIT`）、隔离放行 / 合约族权威源装载 + 模板选择 + 未定义合约号与函数拒 + 条款三态 + **权威源只读哈希核验** / netting 守恒与 I-1~I-5 + direct 与两税分层 + `value=0` 仍记税事实 + 熔断不入结算

## 十一、待细化（登记跟踪）

1. ~~与 C01-C16 合约族真实对接~~ → **已闭环**（V1.1 §六；C06~C16 逐条判定依据待权威源补充）
2. ~~185.6 交互内容元素完整映射~~ → **已闭环**（V1.1 §四）
3. ~~群组/混合参与方权限（MRCR）联动~~ → **已闭环**（V1.1 §五）
4. ~~结算与 CLS 管线对接~~ → **已闭环**（V1.1 §七）

**余项（新增登记）**：① `C06-C16` 扩展硬约束的逐条判定依据（须待制度侧给出映射，现为 `not_evaluated`）② 群组消息分发功能模块的实通道（185.6 §6.3"经消息分发功能模块"）③ 会话/任务的**生命周期事件流**（`state` 状态机化）

---

*合约 × 国标交互对接规范 V1.1：185.6 三模式 + 四元素（国标字段名）→ 日志（税触发）→ 计税 → **合约族装配（C01~C16 条款核验）** → 存证 → **CLS 结算（净额/定向支付）**；群组/混合参与方权限与 MRCR（ID54）——34 用例全绿（M4 深化 24）｜ 存证: GSEQ-1266*
