# TDCA MCP · A2A 接口预留（标准互操作）

> 文档: TDCA-CORE-GO-M2-A2A-001 ｜ 状态: **接口定义就绪（预留，不强制实现）** ｜ 依据: TDCA-HANDOFF-M2-001 线 1 #3
> 定位: MCP 桥接（挂载模式）之上，为 Agent-to-Agent 标准互操作（Google A2A 协议）预留接口面——**AgentCard 发现 + tasks/sendMessage 消息传递（SSE）**。
> 纪律: 只赋能不改码（BIDIR-001）；对外口径零算力提及（TDCA-PUBLIC-COMPUTE-001）；接口熵=0（JSON 与核心引擎同构）。

---

## 一、A2A 角色模型

```
外部 Agent A ──(MCP stdio)──> tdca-core-go（enforce/nca/nsfl 工具）
      │                                  │
      └────(A2A tasks/sendMessage, SSE)──┴──> Agent B（TDCA 协议伙伴）
                     （预留：跨 Agent 消息面）
```

- **MCP 面**（已实现）：Agent → TDCA 核心工具调用（准入/存证/熔断）
- **A2A 面**（预留）：Agent ↔ Agent 的消息传递 + 能力发现（AgentCard）

## 二、AgentCard（能力发现，JSON Schema）

```json
{
  "name": "tdca-core-go",
  "description": "TDCA 核心引擎（enforce/nca/nsfl）——制度即代码，挂载/化合双轨协作",
  "url": "https://github.com/henyi-tdca/tdca-protocol",
  "version": "1.0.0",
  "capabilities": {
    "skills": ["enforce_check", "nca_append", "nca_verify", "nsfl_eval"],
    "card": {
      "protocolVersion": "3.1.2",
      "scene_id": "scene-phy-notification",
      "role": "TDCA-Core"
    }
  },
  "authentication": {
    "schemes": ["bearer"],
    "credentials": "TDCA-PUBKEY-01（密钥材料永不落盘）"
  },
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain"]
}
```

**约束**：AgentCard 中 `capabilities.card` 与 `enforce.AgentCard` 结构同构（接口熵=0）；
发现后外部 Agent 可校验 TDCA 能力范围（只读，不触发状态变更）。

## 三、tasks/sendMessage（消息传递，SSE 定义）

A2A 消息面预留——跨 Agent 事件（邀请/声明/分润对账）经 SSE 推送：

```
POST /a2a/tasks/sendMessage
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "a2a-001",
  "method": "tasks/sendMessage",
  "params": {
    "taskId": "invite-dsh-001",
    "message": {
      "role": "agent",
      "parts": [
        {"kind": "text", "text": "TDCA 挂载邀请（TIER-A）：动态分润 15%，只赋能不改码……"},
        {"kind": "nca", "ref": "NCA-ECOSCAN-20260823-INV-…"}
      ],
      "context": {"mode": "mount", "tier": "A"}
    }
  }
}

响应（SSE）:
event: message
data: {"jsonrpc":"2.0","id":"a2a-001","result":{"messageId":"m-001","status":"accepted"}}
```

**预留语义**：
- `tasks/sendMessage`：Agent → Agent 消息（与 ECOSCAN inviter 邀请函同构，邀请即分润登记）
- SSE 通道：服务端推送（长连接）；HTTP 兜底轮询
- 验收（M2 不强制实现）：接口定义就绪即可，实现随 M3 生态邀请联动落地

## 四、与 MCP 桥接的衔接

| 面 | 协议 | 状态 | 作用 |
|---|---|---|---|
| MCP | JSON-RPC 2.0 over stdio | ✅ 已实现（M2） | Agent → TDCA 核心工具调用 |
| A2A | AgentCard + tasks/sendMessage（SSE） | 🔶 预留（M2 定义） | Agent ↔ Agent 互操作 |

衔接点：`enforce_check` 通过后，Agent 获得 A2A 会话凭据（role/capability 快照）——
慢系统（TCN/人类签批 ID71）不承载于芯片端或桥接层，仅裁决层可见。

## 五、实现清单（预留，后续 M3 触发）

- [ ] AgentCard 端点（`GET /.well-known/agentcard.json`）
- [ ] SSE 通道（`GET /a2a/tasks/{id}` + `POST /a2a/tasks/sendMessage`）
- [ ] A2A↔MCP 会话绑定（enforce 通过 → A2A 会话快照）

---

> 本接口面为 A2A 标准互操作预留（AgentCard 发现 + tasks/sendMessage/SSE），M2 交付定义即就绪；实现随生态邀请（线 2）M3 联动。
> 关联: DCD-CORE-GO-001 ｜ TDCA-OPEN-COLLAB-001 ｜ TDCA-HANDOFF-M2-001 ｜ tdca_mcp_bridge.py
