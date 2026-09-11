// Package mcp 实现 TDCA 核心引擎的 MCP（Model Context Protocol）桥接（DCD-CORE-GO-001 §三）。
//
// 将 enforce/nca/nsfl 三包暴露为 AI 可调用工具（tools/list + tools/call），
// 外部 Agent 通过 MCP stdio 传输挂载调用——只赋能不改码（BIDIR-001），
// JSON Schema 合规拦截（未知字段/非法类型拒绝，fail-closed）。
//
// 协议: MCP JSON-RPC 2.0 over stdio（逐行 JSON），零第三方依赖（ID31 最简机制）。
// 接口熵=0: 工具输出与 tdcad CLI / Python 桥接 JSON 100% 同构。
// 会话层: TDCA-STD-SESSION-001 V0.2-DRAFT-REV2（握手/心跳/断开三段纪律，
// 错误统一 -32000 + "tdca/session:" 前缀，小结经 _meta.tdca.session_summary 载域）。
//
// 制度锚定: DCD-CORE-GO-001 §三（对外 MCP 桥接）｜ TDCA-OPEN-COLLAB-001 §二（挂载模式）｜ BIDIR-001
// SPDX-License-Identifier: Apache-2.0
package mcp

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"strings"
	"sync"
	"time"

	"github.com/henyi-tdca/tdca-core-go/pkg/enforce"
	"github.com/henyi-tdca/tdca-core-go/pkg/nca"
	"github.com/henyi-tdca/tdca-core-go/pkg/nsfl"
)

// ---- MCP 协议常量 ----

const (
	ProtocolVersion = "2025-06-18" // MCP spec 版本（tools 子集；服务端自身版本，协商应答恒回此值）
)

// SupportedProtocolVersions 支持的 MCP 协议版本集（裁定 D-6：按 MCP 标准协商）。
// 客户端版本 ∈ 本集 → 接受，协商结果记入 session_open 事件；∉ 本集或低于最低基线
// → version-incompatible（不静默降级）。具名切片，随生态更新扩充；
// 协商 ≠ 降级：schema / 门禁 / 超时阈值不因协商放宽（规范 §四）。
var SupportedProtocolVersions = []string{"2024-11-05", "2025-03-26", ProtocolVersion, "2025-11-25"}

// versionSupported 客户端协议版本支持集判定
func versionSupported(v string) bool {
	for _, sv := range SupportedProtocolVersions {
		if sv == v {
			return true
		}
	}
	return false
}

// ---- JSON Schema 类型 ----

// Schema JSON Schema 子集（MCP inputSchema 所需）
type Schema struct {
	Type                 string             `json:"type"`
	Description          string             `json:"description,omitempty"`
	Properties           map[string]*Schema `json:"properties,omitempty"`
	Required             []string           `json:"required,omitempty"`
	AdditionalProperties bool               `json:"additionalProperties"`
	Enum                 []string           `json:"enum,omitempty"`
}

// ---- 工具定义 ----

// Tool MCP 工具声明（tools/list 返回项）
type Tool struct {
	Name        string  `json:"name"`
	Description string  `json:"description"`
	InputSchema *Schema `json:"inputSchema"`
}

// ToolHandler 工具实现（返回 JSON 可序列化结果）
type ToolHandler func(args map[string]any) (any, error)

// ---- 服务器 ----

// Server 轻量 MCP 服务器（stdio，逐行 JSON-RPC 2.0）+ 常驻会话层（TDCA-STD-SESSION-001）
type Server struct {
	mu     sync.Mutex
	tools  map[string]ToolHandler
	cards  map[string]*Tool // name -> 声明（tools/list 顺序）

	// ---- 会话层（单会话单主体，max_inflight=1，裁定 D-4A）----
	sesMu    sync.Mutex
	session  *Session       // 当前会话（替换既有单值 s.client；nil = 无会话）
	policy   SessionPolicy  // 会话纪律参数（规范 §七，cmd flag 可覆盖）
	rejected []SessionEvent // session_rejected 事件（握手拒绝不建会话，仍须存证）
	pingSeq  int            // 服务端 ping 序号（ping request id = tdca-ping-N）

	encMu sync.Mutex // 应答写出互斥（心跳 goroutine 与主循环并发写）
}

// NewServer 构造 MCP 服务器（注册 TDCA 核心三件工具；会话参数取规范 §七 默认值）
func NewServer() *Server {
	return NewServerWithPolicy(DefaultSessionPolicy())
}

// NewServerWithPolicy 构造 MCP 服务器（指定会话纪律参数；偏离默认值随会话事件存证）
func NewServerWithPolicy(policy SessionPolicy) *Server {
	s := &Server{
		tools:  map[string]ToolHandler{},
		cards:  map[string]*Tool{},
		policy: policy,
	}
	s.registerCoreTools()
	return s
}

// Session 当前会话（检查点/测试用；可能为 nil）
func (s *Server) Session() *Session {
	s.sesMu.Lock()
	defer s.sesMu.Unlock()
	return s.session
}

// RejectedEvents 握手拒绝事件（session_rejected；内存存证，不落盘）
func (s *Server) RejectedEvents() []SessionEvent {
	s.sesMu.Lock()
	defer s.sesMu.Unlock()
	out := make([]SessionEvent, len(s.rejected))
	copy(out, s.rejected)
	return out
}

// recordRejected 记 session_rejected（含已知要素；永不含 token 值）
func (s *Server) recordRejected(agentID, scene, tokenID, reason string, now time.Time) {
	s.sesMu.Lock()
	defer s.sesMu.Unlock()
	s.rejected = append(s.rejected, SessionEvent{
		Event:      EventSessionRejected,
		RecordType: "service",
		AgentID:    agentID,
		Scene:      scene,
		TokenID:    tokenID,
		Reason:     reason,
		Policy:     s.policy.PolicyJSON(),
		At:         now,
	})
}

// transportBroken 半开检测（规范 §五/§六 + §十三 A9）：写失败/管道破裂 → 立即 ABORTED，
// 记 session_abort(transport-broken)；不等心跳阈值、不等 EOF。
func (s *Server) transportBroken() {
	s.sesMu.Lock()
	defer s.sesMu.Unlock()
	if s.session != nil {
		s.session.OnTransportBroken(time.Now())
	}
}

// Register 注册工具（外部扩展点；重名拒绝——防覆盖注入）
func (s *Server) Register(t Tool, h ToolHandler) error {
	if t.Name == "" || h == nil {
		return fmt.Errorf("mcp: invalid tool registration")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, dup := s.tools[t.Name]; dup {
		return fmt.Errorf("mcp: tool %q already registered", t.Name)
	}
	if t.InputSchema == nil {
		t.InputSchema = &Schema{Type: "object", Properties: map[string]*Schema{}, AdditionalProperties: false}
	}
	s.tools[t.Name] = h
	s.cards[t.Name] = &t
	return nil
}

// registerCoreTools 注册 TDCA 核心三件（enforce/nca/nsfl）为 AI 工具
func (s *Server) registerCoreTools() {
	_ = s.Register(Tool{
		Name:        "enforce_check",
		Description: "TDCA 准入门禁校验（AgentCard）：协议/场景/角色/调用上限/负空间边界检查，注入 fail-closed。返回 PASS|REJECT|BLOCK。",
		InputSchema: &Schema{
			Type: "object",
			Properties: map[string]*Schema{
				"agent_card": {
					Type:        "object",
					Description: "AgentCard 声明（agent_id/protocol_version/scene_id/role/allowed_calls/nsfl_boundary）",
					Properties: map[string]*Schema{
						"agent_id":         {Type: "string"},
						"protocol_version": {Type: "string"},
						"scene_id":         {Type: "string"},
						"role":             {Type: "string"},
						"allowed_calls":    {Type: "array"},
						"nsfl_boundary":    {Type: "array"},
					},
					Required:             []string{"agent_id", "protocol_version", "scene_id", "role", "allowed_calls", "nsfl_boundary"},
					AdditionalProperties: false,
				},
			},
			Required:             []string{"agent_card"},
			AdditionalProperties: false,
		},
	}, s.handlerEnforceCheck)

	_ = s.Register(Tool{
		Name:        "nca_append",
		Description: "NCA 存证链追加（append-only，prev_hash 链式校验，篡改拒绝）。返回 status/count/head。",
		InputSchema: &Schema{
			Type: "object",
			Properties: map[string]*Schema{
				"record": {
					Type:        "object",
					Description: "NcaRecord（nca_id/type/hash/ts/signer/payload_ref/prev_hash/nsfl）",
					Properties: map[string]*Schema{
						"nca_id":      {Type: "string"},
						"type":        {Type: "string", Enum: []string{"fact", "auth", "mou", "state", "service"}},
						"hash":        {Type: "string"},
						"ts":          {Type: "string"},
						"signer":      {Type: "string"},
						"payload_ref": {Type: "string"},
						"prev_hash":   {Type: "string"},
						"nsfl":        {Type: "object"},
					},
					Required:             []string{"nca_id", "type", "prev_hash", "ts", "signer"},
					AdditionalProperties: false,
				},
			},
			Required:             []string{"record"},
			AdditionalProperties: false,
		},
	}, s.handlerNcaAppend)

	_ = s.Register(Tool{
		Name:        "nca_verify",
		Description: "NCA 存证链全链验证（哈希连续 + 篡改检测 + 伪造拒绝）。返回 verify/count。",
		InputSchema: &Schema{
			Type: "object",
			Properties: map[string]*Schema{
				"records": {Type: "array", Description: "NcaRecord 数组（按追加顺序）"},
			},
			Required:             []string{"records"},
			AdditionalProperties: false,
		},
	}, s.handlerNcaVerify)

	_ = s.Register(Tool{
		Name:        "nsfl_eval",
		Description: "NSFL 负空间熔断判定（ALLOW→WARN→BLOCK→FUSED 分级，未知信号 fail-closed BLOCK）。",
		InputSchema: &Schema{
			Type: "object",
			Properties: map[string]*Schema{
				"trigger_id": {Type: "string", Description: "触发主体（如 t1 / agent-id）"},
				"signal":     {Type: "string", Description: "信号（如 unauthenticated / key-export / nsfl-bypass-attempt）"},
			},
			Required:             []string{"trigger_id", "signal"},
			AdditionalProperties: false,
		},
	}, s.handlerNsflEval)
}

// ---- 工具实现（挂载 TDCA 核心三件，输出与 CLI 同构——接口熵=0）----

func (s *Server) handlerEnforceCheck(args map[string]any) (any, error) {
	cardRaw, err := json.Marshal(args["agent_card"])
	if err != nil {
		return nil, fmt.Errorf("enforce: invalid agent_card: %v", err)
	}
	gate := enforce.NewEntryGate()
	res, err := gate.Apply(cardRaw)
	// 接口熵=0：与 tdcad enforce check / Python bridge 输出同构
	return map[string]any{
		"status":   res.Status,
		"reason":   res.Reason,
		"agent_id": res.AgentID,
		"scene_id": res.SceneID,
		"role":     res.Role,
		"checks":   res.Checks,
	}, err
}

func (s *Server) handlerNcaAppend(args map[string]any) (any, error) {
	recMap, ok := args["record"].(map[string]any)
	if !ok {
		return nil, fmt.Errorf("nca: record must be an object")
	}
	raw, err := json.Marshal(recMap)
	if err != nil {
		return nil, fmt.Errorf("nca: invalid record: %v", err)
	}
	var rec nca.NcaRecord
	if err := json.Unmarshal(raw, &rec); err != nil {
		return nil, fmt.Errorf("nca: invalid record: %v", err)
	}
	chain := nca.NewChain()
	if err := chain.Append(&rec); err != nil {
		return nil, err // prev_hash mismatch → 篡改拒绝
	}
	return map[string]any{"status": "appended", "head": chain.Head(), "count": chain.Len()}, nil
}

func (s *Server) handlerNcaVerify(args map[string]any) (any, error) {
	raw, err := json.Marshal(args["records"])
	if err != nil {
		return nil, fmt.Errorf("nca: invalid records: %v", err)
	}
	var recs []nca.NcaRecord
	if err := json.Unmarshal(raw, &recs); err != nil {
		return nil, fmt.Errorf("nca: invalid records: %v", err)
	}
	chain := nca.NewChain()
	for i := range recs {
		if err := chain.Append(&recs[i]); err != nil {
			return nil, err // 伪造 prev_hash → 拒绝
		}
	}
	ok := chain.Verify()
	return map[string]any{"verify": ok, "count": chain.Len()}, nil
}

func (s *Server) handlerNsflEval(args map[string]any) (any, error) {
	trigger, _ := args["trigger_id"].(string)
	signal, _ := args["signal"].(string)
	if trigger == "" || signal == "" {
		return nil, fmt.Errorf("nsfl: trigger_id and signal required")
	}
	engine := nsfl.NewFuseEngine()
	res := engine.Eval(trigger, signal)
	return map[string]any{
		"action": map[string]any{
			"status": res.Action.Status, "type": res.Action.Type,
			"reason": res.Action.Reason, "irreversible": res.Action.Irreversible,
		},
		"trigger_id": res.TriggerID,
		"blocked":    res.Blocked,
		"message":    res.Message,
	}, nil
}

// ---- JSON-RPC 2.0 处理 ----

type rpcRequest struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params,omitempty"`
}

type rpcResponse struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"`
	Result  any             `json:"result,omitempty"`
	Error   *rpcError       `json:"error,omitempty"`
}

type rpcError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// rpcErrorCode MCP/JSON-RPC 错误码
const (
	CodeParse   = -32700
	CodeInvalid = -32600
	CodeMethod  = -32601
	CodeParams  = -32602
	// CodeSession 会话层错误统一码（规范 §九：复用 JSON-RPC -32000，message 前缀 tdca/session:）
	CodeSession   = -32000
	CodeInternal  = -32603
	CodeToolError = -32000 // MCP: 工具执行错误（与会话层同码段，由 message 前缀区分）
)

// pingIDPrefix 服务端 ping request 的 id 前缀（对端 response 据此关联赛活）
const pingIDPrefix = "tdca-ping-"

// Serve 启动 stdio MCP 服务器（逐行读 stdin，逐行写 stdout，直到 EOF / close 通知）
//
// 会话纪律（TDCA-STD-SESSION-001 V0.2-DRAFT-REV2）：
//   - 入站消息先做超时巡检（握手超时 / pong 逾期 / GC，单调时钟）
//   - 服务端心跳 goroutine 按 T_ping 周期发 ping【request】（规范 §五：ping→pong 双向可发）
//   - close 通知 → DRAINING → 回会话小结（_meta.tdca.session_summary）→ CLOSED → 服务退出
//   - 写失败/管道破裂 → 立即 ABORTED（transport-broken，规范 §十三 A9）
func (s *Server) Serve(r io.Reader, w io.Writer) error {
	sc := bufio.NewScanner(r)
	sc.Buffer(make([]byte, 0, 64*1024), 1<<20)
	enc := json.NewEncoder(w)
	// emit 捕获写错误（R-1）：写失败 → 半开检测，会话立即 ABORTED(transport-broken)
	emit := func(v any) error {
		s.encMu.Lock()
		err := enc.Encode(v)
		s.encMu.Unlock()
		if err != nil {
			s.transportBroken()
		}
		return err
	}
	done := make(chan struct{})
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		s.heartbeatLoop(done, emit)
	}()
	defer func() { close(done); wg.Wait() }()

	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var req rpcRequest
		if err := json.Unmarshal([]byte(line), &req); err != nil {
			if err := emit(rpcResponse{JSONRPC: "2.0", ID: nil, Error: &rpcError{Code: CodeParse, Message: "parse error"}}); err != nil {
				return err
			}
			continue
		}
		if req.Method == "" {
			// 无 method 但有 id → 对端 response 帧：对服务端 ping 的 pong 应答（规范 §五）
			if len(req.ID) > 0 && string(req.ID) != "null" {
				if strings.HasPrefix(strings.Trim(string(req.ID), `"`), pingIDPrefix) {
					s.onAlive(time.Now())
				}
				continue
			}
			if err := emit(rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeInvalid, Message: "invalid request"}}); err != nil {
				return err
			}
			continue
		}
		now := time.Now()
		// 超时巡检（握手超时 → 会话不建立，记 session_rejected）
		s.checkSessionTimeouts(now)

		// notification（无 id）不响应（close 回会话小结除外）
		if len(req.ID) == 0 || string(req.ID) == "null" {
			switch req.Method {
			case "notifications/initialized":
				// H3 到位 → 置 ESTABLISHED（原为「忽略」，现推进会话）
				if err := s.handshakeDone(now); err != nil {
					// 握手超时等 → 拒绝存证，会话不建立
				}
			case "close":
				// 断开四步：DRAINING → 排空 → 回会话小结 → CLOSED
				if err := s.closeSession(emit, ReasonNormalClose, now, true); err != nil {
					return err
				}
				return nil
			}
			// 其余通知（含非规范方法集的 ping/pong 通知型）按 fail-closed 忽略
			continue
		}
		if err := emit(s.handle(req, now)); err != nil {
			return err
		}
	}
	// EOF：传输结束。已建立未关闭会话 → 排空 → CLOSED（transport-eof），小结不写出（对端不可达），仅事件存证。
	s.sesMu.Lock()
	sess := s.session
	s.sesMu.Unlock()
	if sess != nil && (sess.State == StateEstablished || sess.State == StateStale || sess.State == StateSuspended || sess.State == StateDraining) {
		eofNow := time.Now()
		_ = s.closeSession(emit, ReasonTransportEOF, eofNow, false)
	}
	return sc.Err()
}

// heartbeatLoop 服务端保活（规范 §五）：会话活跃期按 T_ping 发 ping【request】
//（id = tdca-ping-N；对端须在 T_pong 内回 response=pong）；逾期记 miss（CheckTimeouts）。
// 写失败 → 半开检测（transport-broken）并退出心跳。
func (s *Server) heartbeatLoop(done chan struct{}, emit func(any) error) {
	for {
		s.sesMu.Lock()
		interval := s.policy.TPing
		s.sesMu.Unlock()
		if interval <= 0 {
			interval = 30 * time.Second
		}
		select {
		case <-done:
			return
		case <-time.After(interval):
		}
		var pingID string
		s.sesMu.Lock()
		if sess := s.session; sess != nil &&
			(sess.State == StateEstablished || sess.State == StateStale || sess.State == StateSuspended) {
			now := time.Now()
			_ = sess.CheckTimeouts(now) // pong 逾期 miss / 持权到期 / GC
			if sess.State == StateEstablished || sess.State == StateStale || sess.State == StateSuspended {
				if !sess.awaitingPong {
					s.pingSeq++
					pingID = fmt.Sprintf("%s%d", pingIDPrefix, s.pingSeq)
					sess.awaitingPong = true
					sess.pingSentAt = now
				}
			}
		}
		s.sesMu.Unlock()
		if pingID != "" {
			select {
			case <-done:
				return
			default:
			}
			if err := emit(map[string]any{"jsonrpc": "2.0", "id": pingID, "method": "ping"}); err != nil {
				return // 半开：会话已置 ABORTED(transport-broken)，心跳停止
			}
		}
	}
}

// checkSessionTimeouts 入站消息触发的超时巡检
func (s *Server) checkSessionTimeouts(now time.Time) {
	s.sesMu.Lock()
	defer s.sesMu.Unlock()
	sess := s.session
	if sess == nil {
		return
	}
	if err := sess.CheckTimeouts(now); err != nil {
		if ge, ok := err.(*SessionGateError); ok && ge.Code == ReasonHandshakeTimeout {
			// 握手超时：不建立会话，记 session_rejected
			s.rejected = append(s.rejected, SessionEvent{
				Event: EventSessionRejected, RecordType: "service",
				SessionID: sess.ID, AgentID: sess.AgentID, Scene: sess.Scene,
				TokenID: sess.TokenID, Reason: ReasonHandshakeTimeout,
				Policy: s.policy.PolicyJSON(), At: now,
			})
			s.session = nil
		}
	}
}

// handshakeDone H3 到位推进（notifications/initialized）
func (s *Server) handshakeDone(now time.Time) error {
	s.sesMu.Lock()
	defer s.sesMu.Unlock()
	if s.session == nil {
		return nil // 无在途握手（幂等忽略）
	}
	if err := s.session.HandshakeDone(now); err != nil {
		if ge, ok := err.(*SessionGateError); ok {
			s.rejected = append(s.rejected, SessionEvent{
				Event: EventSessionRejected, RecordType: "service",
				SessionID: s.session.ID, AgentID: s.session.AgentID, Scene: s.session.Scene,
				TokenID: s.session.TokenID, Reason: ge.Code,
				Policy: s.policy.PolicyJSON(), At: now,
			})
		}
		s.session = nil
		return err
	}
	return nil
}

// onAlive 对端存活证明（对端 ping request / 对服务端 ping 的 pong response 入站）
func (s *Server) onAlive(now time.Time) {
	s.sesMu.Lock()
	defer s.sesMu.Unlock()
	if s.session != nil {
		s.session.OnPong(now)
	}
}

// closeSession 断开四步（规范 §六 D1~D4）：DRAINING → 排空 → 回会话小结 → CLOSED
// emitSummary=false 用于 EOF（传输已断，小结不写出，仅事件存证）
func (s *Server) closeSession(emit func(any) error, kind string, now time.Time, emitSummary bool) error {
	s.sesMu.Lock()
	sess := s.session
	if sess == nil {
		s.sesMu.Unlock()
		return nil
	}
	sess.BeginDrain(now)
	sess.Finish(kind, now)
	summary := sess.Summary(now)
	s.sesMu.Unlock()
	if !emitSummary {
		return nil
	}
	// 回会话小结（规范 §六 D3）：经 _meta.tdca.session_summary 载域，
	// 复用规范新增的唯一扩展通知名 close（接口熵优先，不新增通知方法名）
	return emit(map[string]any{
		"jsonrpc": "2.0",
		"method":  "close",
		"params":  map[string]any{"_meta": map[string]any{"tdca": map[string]any{"session_summary": summary}}},
	})
}

// gateToolCall tools/call 会话态闸门（非 ESTABLISHED 一律拒；持权到期 SUSPENDED 拒）
func (s *Server) gateToolCall(tool string, now time.Time) (*Session, *SessionGateError) {
	s.sesMu.Lock()
	defer s.sesMu.Unlock()
	sess := s.session
	if sess == nil {
		return nil, &SessionGateError{Code: ReasonSessionNotEstablished, Detail: "no session: initialize with _meta.tdca first"}
	}
	if err := sess.BeforeToolCall(tool, now); err != nil {
		ge, ok := err.(*SessionGateError)
		if !ok {
			ge = &SessionGateError{Code: ReasonSessionNotEstablished, Detail: err.Error()}
		}
		return nil, ge
	}
	return sess, nil
}

// afterToolCall 在途释放
func (s *Server) afterToolCall(sess *Session) {
	s.sesMu.Lock()
	sess.AfterToolCall()
	s.sesMu.Unlock()
}

func (s *Server) handle(req rpcRequest, now time.Time) rpcResponse {
	switch req.Method {
	case "initialize":
		return s.handleInitialize(req, now)

	case "ping":
		// 双向心跳（规范 §五）：对端 ping request → 应答 pong response；同时计为存活证明
		s.onAlive(now)
		return rpcResponse{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{"pong": true}}

	case "tools/list":
		s.mu.Lock()
		tools := make([]*Tool, 0, len(s.cards))
		for _, t := range s.cards {
			tools = append(tools, t)
		}
		s.mu.Unlock()
		return rpcResponse{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{"tools": tools}}

	case "tools/call":
		var p struct {
			Name      string         `json:"name"`
			Arguments map[string]any `json:"arguments"`
		}
		if len(req.Params) > 0 {
			if err := json.Unmarshal(req.Params, &p); err != nil {
				return rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeParams, Message: "invalid params"}}
			}
		}
		if p.Name == "" {
			return rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeParams, Message: "missing tool name"}}
		}
		// 会话态闸门（规范 §五）：非 ESTABLISHED 一律拒，先于 schema 与工具查找
		sess, gerr := s.gateToolCall(p.Name, now)
		if gerr != nil {
			return rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeSession, Message: gerr.Error()}}
		}
		defer s.afterToolCall(sess)
		s.mu.Lock()
		h, ok := s.tools[p.Name]
		card := s.cards[p.Name]
		s.mu.Unlock()
		if !ok {
			return rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeMethod, Message: "tool not found: " + p.Name}}
		}
		// JSON Schema 合规拦截（fail-closed：非法参数拒绝）
		if err := validateSchema(card.InputSchema, p.Arguments); err != nil {
			return rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeParams, Message: "schema violation: " + err.Error()}}
		}
		result, err := h(p.Arguments)
		if err != nil {
			// 工具执行错误 → MCP error（含 NSFL 熔断/篡改拒绝）
			return rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeToolError, Message: err.Error()}}
		}
		out, _ := json.Marshal(result)
		return rpcResponse{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
			"content": []map[string]any{{"type": "text", "text": string(out)}},
		}}

	default:
		return rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeMethod, Message: "method not found: " + req.Method}}
	}
}

// handleInitialize H1：解析 _meta.tdca（agent_card / pcr_token / scene），
// 校验版本与三要素 → 建会话（HANDSHAKING）；返回 _meta.tdca.session_id 与 session_policy。
// fail-closed：未知字段 → -32602；会话层拒绝 → -32000 + "tdca/session:" 前缀（规范 §九）。
func (s *Server) handleInitialize(req rpcRequest, now time.Time) rpcResponse {
	// 参数/字段级拒绝（schema 纪律，A14 口径）
	rejectParams := func(msg string) rpcResponse {
		return rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeParams, Message: msg}}
	}
	// 会话层拒绝（规范 §九：-32000 + tdca/session: 前缀）
	rejectSession := func(ge *SessionGateError) rpcResponse {
		return rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeSession, Message: ge.Error()}}
	}
	// 单会话：重复 initialize 拒绝（不变量 1：session_id 不跨会话复用，重连须重新握手，D-4A）
	if s.Session() != nil {
		return rejectSession(&SessionGateError{Code: ReasonSessionNotEstablished, Detail: "session already initialized; reconnect to re-handshake"})
	}
	// 顶层参数 fail-closed 解析
	var raw map[string]json.RawMessage
	if len(req.Params) > 0 {
		if err := json.Unmarshal(req.Params, &raw); err != nil {
			return rejectParams("initialize params not an object")
		}
	}
	for k := range raw {
		switch k {
		case "protocolVersion", "clientInfo", "capabilities", "_meta":
		default:
			return rejectParams("unknown initialize field " + strconvQuote(k))
		}
	}
	var p struct {
		ProtocolVersion string `json:"protocolVersion"`
		ClientInfo      struct {
			Name    string `json:"name"`
			Version string `json:"version"`
		} `json:"clientInfo"`
		Meta json.RawMessage `json:"_meta"`
	}
	if len(req.Params) > 0 {
		_ = json.Unmarshal(req.Params, &p)
	}
	// 协议版本：缺失 / 非字符串 → -32602（fail-closed 参数纪律，HANDOFF-002 §六-2）
	pvRaw, ok := raw["protocolVersion"]
	if !ok {
		return rejectParams("missing protocolVersion")
	}
	var clientVersion string
	if err := json.Unmarshal(pvRaw, &clientVersion); err != nil {
		return rejectParams("protocolVersion not a string")
	}
	// 版本协商（裁定 D-6）：客户端版本 ∈ 支持集 → 接受；应答仍回服务端自身版本
	// ProtocolVersion。协商 ≠ 降级：schema / 门禁 / 超时阈值不因协商放宽（规范 §四）。
	if !versionSupported(clientVersion) {
		s.recordRejected(p.ClientInfo.Name, "", "", ReasonVersionIncompatible, now)
		return rejectSession(&SessionGateError{Code: ReasonVersionIncompatible,
			Detail: "client=" + strconvQuote(clientVersion) + " server=" + ProtocolVersion})
	}
	// _meta.tdca 解析（fail-closed：_meta 仅允许 tdca 命名空间）
	var meta *tdcaMeta
	if len(p.Meta) > 0 {
		var metaRaw map[string]json.RawMessage
		if err := json.Unmarshal(p.Meta, &metaRaw); err != nil {
			return rejectParams("_meta not an object")
		}
		for k := range metaRaw {
			if k != "tdca" {
				return rejectParams("unknown _meta namespace " + strconvQuote(k))
			}
		}
		if tdcaRaw, ok := metaRaw["tdca"]; ok {
			strict := json.NewDecoder(strings.NewReader(string(tdcaRaw)))
			strict.DisallowUnknownFields()
			var m tdcaMeta
			if err := strict.Decode(&m); err != nil {
				return rejectParams("_meta.tdca: " + err.Error())
			}
			// pcr_token 内部字段 fail-closed
			if tokRaw, ok := mustRawMap(tdcaRaw)["pcr_token"]; ok {
				strictTok := json.NewDecoder(strings.NewReader(string(tokRaw)))
				strictTok.DisallowUnknownFields()
				var tok pcrToken
				if err := strictTok.Decode(&tok); err != nil {
					return rejectParams("_meta.tdca.pcr_token: " + err.Error())
				}
			}
			meta = &m
		}
	}
	// 三要素校验（主体/场景/持权）→ 不通过则记 session_rejected
	agentID, scene, tokenID, expiresAt, verr := validateHandshake(s.policy, meta, p.ClientInfo.Name, now)
	if verr != nil {
		ge := verr.(*SessionGateError)
		tid := ""
		if meta != nil && meta.PCRToken != nil {
			tid = meta.PCRToken.TokenID
		}
		s.recordRejected(p.ClientInfo.Name, scene, tid, ge.Code, now)
		return rejectSession(ge)
	}
	// H1 通过 → 建会话（HANDSHAKING）；协商结果随会话记入 session_open 事件（裁定 D-6）
	sess := NewSession(s.policy, agentID, scene, tokenID, expiresAt, now)
	sess.negotiatedVersion = clientVersion
	s.sesMu.Lock()
	s.session = sess
	s.sesMu.Unlock()
	return rpcResponse{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
		"protocolVersion": ProtocolVersion,
		"capabilities":    map[string]any{"tools": map[string]any{"listChanged": false}},
		"serverInfo":      map[string]any{"name": "tdca-core-go-mcp", "version": "1.0.0"},
		"_meta": map[string]any{"tdca": map[string]any{
			"session_id":     sess.ID,
			"session_policy": s.policy.PolicyJSON(),
		}},
	}}
}

func strconvQuote(s string) string { return fmt.Sprintf("%q", s) }

// mustRawMap 解析 JSON 对象为 RawMessage map（失败返回空 map）
func mustRawMap(raw json.RawMessage) map[string]json.RawMessage {
	m := map[string]json.RawMessage{}
	_ = json.Unmarshal(raw, &m)
	return m
}

// ---- JSON Schema 合规校验（fail-closed）----

func validateSchema(s *Schema, args map[string]any) error {
	if s == nil {
		return nil
	}
	if args == nil {
		args = map[string]any{}
	}
	// required
	for _, k := range s.Required {
		if _, ok := args[k]; !ok {
			return fmt.Errorf("missing required field %q", k)
		}
	}
	// additionalProperties=false → 未知字段拒绝（注入拦截）
	if s.AdditionalProperties == false && len(s.Properties) > 0 {
		for k := range args {
			if _, known := s.Properties[k]; !known {
				return fmt.Errorf("unknown field %q (additionalProperties=false)", k)
			}
		}
	}
	for k, sub := range s.Properties {
		v, present := args[k]
		if !present {
			continue
		}
		if err := validateValue(sub, v, k); err != nil {
			return err
		}
	}
	return nil
}

func validateValue(s *Schema, v any, path string) error {
	if s == nil {
		return nil
	}
	switch s.Type {
	case "object":
		m, ok := v.(map[string]any)
		if !ok {
			return fmt.Errorf("%s: expected object", path)
		}
		return validateSchema(s, m)
	case "string":
		if _, ok := v.(string); !ok {
			return fmt.Errorf("%s: expected string", path)
		}
	case "array":
		arr, ok := v.([]any)
		if !ok {
			return fmt.Errorf("%s: expected array", path)
		}
		if len(s.Enum) > 0 {
			return nil // array 无 enum 语义
		}
		_ = arr
	}
	if len(s.Enum) > 0 {
		str, ok := v.(string)
		if !ok {
			return fmt.Errorf("%s: expected enum value", path)
		}
		okEnum := false
		for _, e := range s.Enum {
			if str == e {
				okEnum = true
				break
			}
		}
		if !okEnum {
			return fmt.Errorf("%s: value %q not in enum %v", path, str, s.Enum)
		}
	}
	return nil
}
