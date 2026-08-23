// Package mcp 实现 TDCA 核心引擎的 MCP（Model Context Protocol）桥接（DCD-CORE-GO-001 §三）。
//
// 将 enforce/nca/nsfl 三包暴露为 AI 可调用工具（tools/list + tools/call），
// 外部 Agent 通过 MCP stdio 传输挂载调用——只赋能不改码（BIDIR-001），
// JSON Schema 合规拦截（未知字段/非法类型拒绝，fail-closed）。
//
// 协议: MCP JSON-RPC 2.0 over stdio（逐行 JSON），零第三方依赖（ID31 最简机制）。
// 接口熵=0: 工具输出与 tdcad CLI / Python 桥接 JSON 100% 同构。
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

	"github.com/henyi-tdca/tdca-core-go/pkg/enforce"
	"github.com/henyi-tdca/tdca-core-go/pkg/nca"
	"github.com/henyi-tdca/tdca-core-go/pkg/nsfl"
)

// ---- MCP 协议常量 ----

const (
	ProtocolVersion = "2025-06-18" // MCP spec 版本（tools 子集）
)

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

// Server 轻量 MCP 服务器（stdio，逐行 JSON-RPC 2.0）
type Server struct {
	mu     sync.Mutex
	tools  map[string]ToolHandler
	cards  map[string]*Tool // name -> 声明（tools/list 顺序）
	client string           // 握手后客户端名
}

// NewServer 构造 MCP 服务器（注册 TDCA 核心三件工具）
func NewServer() *Server {
	s := &Server{
		tools: map[string]ToolHandler{},
		cards: map[string]*Tool{},
	}
	s.registerCoreTools()
	return s
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
						"nca_id":       {Type: "string"},
						"type":         {Type: "string", Enum: []string{"fact", "auth", "mou", "state", "service"}},
						"hash":         {Type: "string"},
						"ts":           {Type: "string"},
						"signer":       {Type: "string"},
						"payload_ref":  {Type: "string"},
						"prev_hash":    {Type: "string"},
						"nsfl":         {Type: "object"},
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
		"status":  res.Status,
		"reason":  res.Reason,
		"agent_id": res.AgentID,
		"scene_id": res.SceneID,
		"role":    res.Role,
		"checks":  res.Checks,
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
	JSONRPC string      `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"`
	Result  any         `json:"result,omitempty"`
	Error   *rpcError   `json:"error,omitempty"`
}

type rpcError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// rpcErrorCode MCP/JSON-RPC 错误码
const (
	CodeParse     = -32700
	CodeInvalid   = -32600
	CodeMethod    = -32601
	CodeParams    = -32602
	CodeInternal  = -32603
	CodeToolError = -32000 // MCP: 工具执行错误
)

// Serve 启动 stdio MCP 服务器（逐行读 stdin，逐行写 stdout，直到 EOF）
func (s *Server) Serve(r io.Reader, w io.Writer) error {
	sc := bufio.NewScanner(r)
	sc.Buffer(make([]byte, 0, 64*1024), 1<<20)
	enc := json.NewEncoder(w)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var req rpcRequest
		if err := json.Unmarshal([]byte(line), &req); err != nil {
			_ = enc.Encode(rpcResponse{JSONRPC: "2.0", ID: nil, Error: &rpcError{Code: CodeParse, Message: "parse error"}})
			continue
		}
		if req.Method == "" {
			_ = enc.Encode(rpcResponse{JSONRPC: "2.0", ID: req.ID, Error: &rpcError{Code: CodeInvalid, Message: "invalid request"}})
			continue
		}
		// notification（无 id）不响应
		if len(req.ID) == 0 || string(req.ID) == "null" {
			if req.Method == "notifications/initialized" {
				continue
			}
			continue
		}
		resp := s.handle(req)
		if err := enc.Encode(resp); err != nil {
			return err
		}
	}
	return sc.Err()
}

func (s *Server) handle(req rpcRequest) rpcResponse {
	switch req.Method {
	case "initialize":
		var p struct {
			ProtocolVersion string `json:"protocolVersion"`
			ClientInfo      struct {
				Name    string `json:"name"`
				Version string `json:"version"`
			} `json:"clientInfo"`
		}
		if len(req.Params) > 0 {
			_ = json.Unmarshal(req.Params, &p)
		}
		s.client = p.ClientInfo.Name
		return rpcResponse{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
			"protocolVersion": ProtocolVersion,
			"capabilities":    map[string]any{"tools": map[string]any{"listChanged": false}},
			"serverInfo":      map[string]any{"name": "tdca-core-go-mcp", "version": "1.0.0"},
		}}

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
