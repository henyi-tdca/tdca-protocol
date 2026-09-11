// 会话层：tdcad mcp serve 常驻会话生命周期（TDCA-STD-SESSION-001 V0.2-DRAFT-REV2）。
//
// 三段纪律：握手（H1 initialize → H2 响应 → H3 notifications/initialized）/
// 心跳（ping request → pong response，miss ≥N_stale → STALE，≥N_abort → ABORTED）/
// 断开（close → DRAINING ≤T_drain → CLOSED / 排空超时 CLOSED(drain-timeout+残余标记)）。
//
// 硬约束落实：
//   - 凭据纪律：pcr_token 只记 token_id，永不记 token 值（结构体无 token 字段）。
//   - 无持久副作用（裁定 D-1A/D-3A）：会话事件仅内存累积，不落盘、不进 NCA 链。
//   - 单调时钟（规范 §五）：心跳/超时一律 time.Time.Sub（单调分量），不用 wall-clock 差值。
//   - fail-closed（规范 §九）：未知状态/方法/字段/子码一律拒绝，不为「保持会话」放宽。
//   - 单会话单主体 + max_inflight=1（裁定 D-4A）。
//   - 错误码（规范 §九）：会话层错误统一 JSON-RPC -32000，message 前缀 "tdca/session:"。
//
// SPDX-License-Identifier: Apache-2.0
package mcp

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/henyi-tdca/tdca-core-go/pkg/enforce"
)

// ---- 会话状态常量（规范 §三，一一对应）----

const (
	StateIdle        = "IDLE"
	StateHandshaking = "HANDSHAKING"
	StateEstablished = "ESTABLISHED"
	StateStale       = "STALE"
	StateSuspended   = "SUSPENDED"
	StateDraining    = "DRAINING"
	StateClosed      = "CLOSED"
	StateAborted     = "ABORTED"
)

// ---- 拒绝 / 结束子码（规范 §九；随 error message 与事件存证）----

const (
	ReasonVersionIncompatible    = "version-incompatible"
	ReasonHandshakeTimeout       = "handshake-timeout"
	ReasonEntryRejected          = "entry-rejected"
	ReasonTokenMissing           = "token-missing"
	ReasonTokenScopeInsufficient = "token-scope-insufficient" // 含握手期过期（规范 §十三 A4）
	ReasonSessionNotEstablished  = "session-not-established"
	ReasonSessionStale           = "session-stale"
	ReasonTokenExpired           = "token-expired" // 会话期到期（裁定 D-2A）
	ReasonMaxInflightExceeded    = "max-inflight-exceeded"
	ReasonDrainTimeout           = "drain-timeout"
	ReasonGCTimeout              = "gc-timeout"
	ReasonHeartbeatTimeout       = "heartbeat-timeout" // 规范 §六/§九：miss ≥N_abort
	ReasonTransportBroken        = "transport-broken"  // 规范 §六：写失败/管道破裂 → 立即 ABORTED
	ReasonNormalClose            = "normal-close"
	ReasonTransportEOF           = "transport-eof"
)

// SessionErrPrefix 会话层错误 message 前缀（规范 §九：统一 -32000 + 前缀 tdca/session:）
const SessionErrPrefix = "tdca/session:"

// ---- 会话事件（规范 §八；record_type=service；默认不落盘，裁定 D-3A）----

const (
	EventSessionOpen     = "session_open"
	EventSessionClose    = "session_close"
	EventSessionAbort    = "session_abort"
	EventSessionRejected = "session_rejected"
)

// SessionEvent 生命周期事件（内存累积；心跳不入事件；永不含 token 值）
type SessionEvent struct {
	Event             string         `json:"event"`              // session_open / session_close / session_abort / session_rejected
	RecordType        string         `json:"record_type"`        // 恒为 "service"
	SessionID         string         `json:"session_id"`         // PCS-{token_id}；拒绝事件可为 ""
	AgentID           string         `json:"agent_id"`           // 主体
	Scene             string         `json:"scene"`              // 场景
	TokenID           string         `json:"token_id"`           // 只记 ID
	Anonymous         bool           `json:"anonymous"`          // 匿名会话标记（裁定 D-7：匿名只读可复算）
	NegotiatedVersion string         `json:"negotiated_version"` // 协商定案的客户端协议版本（裁定 D-6；session_open 记录）
	Reason            string         `json:"reason"`             // 结束/拒绝子码
	DurationMs        int64          `json:"duration_ms"`        // 会话时长（毫秒）
	RequestCount      int            `json:"request_count"`      // 请求数
	ToolCounts        map[string]int `json:"tool_counts"`        // 工具计数
	RejectCount       int            `json:"reject_count"`       // 拒绝数
	ResidualInflight  int            `json:"residual_inflight"`  // 在途残余数（drain-timeout 标记；规范 §六）
	Policy            map[string]any `json:"policy"`             // 生效参数快照（偏离默认值随事件存证，规范 §七）
	At                time.Time      `json:"at"`
}

// ---- 会话参数（规范 §七 默认表；可被 cmd flag 覆盖）----

// SessionPolicy 会话纪律参数
type SessionPolicy struct {
	THandshake  time.Duration // 握手超时 10s
	TPing       time.Duration // 服务端 ping 周期 30s
	TPong       time.Duration // pong 等待上限 15s
	NStale      int           // miss 降级阈值 2
	NAbort      int           // miss 中止阈值 3
	TDrain      time.Duration // 排空上限 5s
	TGC         time.Duration // 残留会话回收 60s（STALE/SUSPENDED/DRAINING 同适用，规范 §六 REV2）
	AllowAnon   bool          // 匿名准入（默认 true=匿名只读，裁定 D-7；false=持权必需，握手即拒）
	MaxInflight int           // 在途请求上限 1
}

// DefaultSessionPolicy 规范 §七 默认值（allow_anonymous 默认 true=匿名只读，裁定 D-7）
func DefaultSessionPolicy() SessionPolicy {
	return SessionPolicy{
		THandshake:  10 * time.Second,
		TPing:       30 * time.Second,
		TPong:       15 * time.Second,
		NStale:      2,
		NAbort:      3,
		TDrain:      5 * time.Second,
		TGC:         60 * time.Second,
		AllowAnon:   true,
		MaxInflight: 1,
	}
}

// PolicyJSON 参数快照（随 _meta.tdca.session_policy 与会话事件存证）
func (p SessionPolicy) PolicyJSON() map[string]any {
	return map[string]any{
		"t_handshake":     p.THandshake.String(),
		"t_ping":          p.TPing.String(),
		"t_pong":          p.TPong.String(),
		"n_stale":         p.NStale,
		"n_abort":         p.NAbort,
		"t_drain":         p.TDrain.String(),
		"t_gc":            p.TGC.String(),
		"allow_anonymous": p.AllowAnon,
		"max_inflight":    p.MaxInflight,
	}
}

// ---- 会话闸门错误 ----

// SessionGateError 会话层拒绝（携带规范子码；message 前缀 tdca/session:，规范 §九）
type SessionGateError struct {
	Code   string // 子码（如 session-not-established）
	Detail string
}

func (e *SessionGateError) Error() string {
	if e.Detail == "" {
		return SessionErrPrefix + e.Code
	}
	return SessionErrPrefix + e.Code + ": " + e.Detail
}

// ---- 会话 ----

// Session 单会话（会话标识 = PCS-{token_id}；单会话单主体，裁定 D-4A）
type Session struct {
	ID        string         // "PCS-"+tokenID
	AgentID   string         // 主体
	Scene     string         // 场景
	TokenID   string         // 只记 ID，永不记 token 值
	State     string         // 状态机当前态
	MissCount int            // 心跳 miss 计数
	Inflight  int            // 在途请求数
	Events    []SessionEvent // 内存累积（默认不落盘，裁定 D-3A）
	StartedAt time.Time      // 建立时刻（单调时钟）

	policy            SessionPolicy
	tokenExpiresAt    time.Time // 持权到期（wall-clock 语义，仅用于到期比较）
	tokenExpired      bool      // 已置 SUSPENDED 标记
	negotiatedVersion string    // 协商定案的客户端协议版本（裁定 D-6；记入 session_open 事件）
	handshakeAt       time.Time // H1 时刻（单调）
	stateAt        time.Time // 最近一次状态迁移（单调）
	lastPong       time.Time // 最近一次存活证明（单调）
	awaitingPong   bool      // 服务端 ping 已发未收 pong
	pingSentAt     time.Time // 最近一次服务端 ping 时刻（单调）
	requestCount   int
	rejectCount    int
	toolCounts     map[string]int
	endReason      string
	drainAt        time.Time
}

// NewSession 建立会话（H1）：主体/场景/持权已校验通过后置 HANDSHAKING。
// 校验本身由 Server.handleInitialize 完成（失败走 session_rejected，不建会话）。
func NewSession(policy SessionPolicy, agentID, scene, tokenID string, tokenExpiresAt time.Time, now time.Time) *Session {
	if tokenID == "" {
		tokenID = "anon"
	}
	return &Session{
		ID:             "PCS-" + tokenID,
		AgentID:        agentID,
		Scene:          scene,
		TokenID:        tokenID,
		State:          StateHandshaking,
		StartedAt:      now,
		handshakeAt:    now,
		stateAt:        now,
		lastPong:       now,
		policy:         policy,
		tokenExpiresAt: tokenExpiresAt,
		toolCounts:     map[string]int{},
	}
}

// transition 状态迁移（内部；记录迁移时刻）
func (s *Session) transition(state string, now time.Time) {
	s.State = state
	s.stateAt = now
}

// HandshakeDone H3 到位（notifications/initialized）→ ESTABLISHED，记 session_open（规范 §四）。
// 三要素齐备性已在 H1 校验；此处只验超时与状态。
func (s *Session) HandshakeDone(now time.Time) error {
	if s.State != StateHandshaking {
		return &SessionGateError{Code: ReasonSessionNotEstablished, Detail: "initialized out of order (state=" + s.State + ")"}
	}
	if now.Sub(s.handshakeAt) > s.policy.THandshake {
		return &SessionGateError{Code: ReasonHandshakeTimeout, Detail: "H3 not received within " + s.policy.THandshake.String()}
	}
	s.transition(StateEstablished, now)
	s.lastPong = now
	s.Events = append(s.Events, s.event(EventSessionOpen, "established", now))
	return nil
}

// writeTools 写类工具集（裁定 D-7 匿名只读判据）：匿名会话永不获得写权限。
// nca_append 的 schema fail-closed 与握手 scope 判据（须含 "mcp"）原样保留，写路径安全不降。
var writeTools = map[string]bool{"nca_append": true}

// BeforeToolCall 会话态闸门（规范 §五/§三 不变量 2）：非 ESTABLISHED 一律拒。
// 通过则在途 +1、请求数/工具计数累计；调用方完成后须 AfterToolCall。
func (s *Session) BeforeToolCall(tool string, now time.Time) error {
	// 持权到期（裁定 D-2A）：ESTABLISHED/STALE → SUSPENDED，拒 tools/call，心跳继续，不断开
	if !s.tokenExpiresAt.IsZero() && now.After(s.tokenExpiresAt) {
		s.OnTokenExpired(now)
	}
	switch s.State {
	case StateEstablished:
		// pass
	case StateStale:
		s.rejectCount++
		return &SessionGateError{Code: ReasonSessionStale, Detail: "heartbeat misses=" + fmt.Sprint(s.MissCount)}
	case StateSuspended:
		s.rejectCount++
		return &SessionGateError{Code: ReasonTokenExpired, Detail: "credential expired; session suspended (heartbeat continues)"}
	default:
		s.rejectCount++
		return &SessionGateError{Code: ReasonSessionNotEstablished, Detail: "state=" + s.State}
	}
	// 匿名只读（裁定 D-7）：匿名会话（PCS-anon）仅放行只读工具
	// （enforce_check / nca_verify / nsfl_eval）；写类工具拒 token-missing
	if s.TokenID == "anon" && writeTools[tool] {
		s.rejectCount++
		return &SessionGateError{Code: ReasonTokenMissing, Detail: "anonymous read-only session: " + tool + " requires credential"}
	}
	if s.Inflight >= s.policy.MaxInflight {
		s.rejectCount++
		return &SessionGateError{Code: ReasonMaxInflightExceeded, Detail: fmt.Sprintf("inflight=%d max=%d", s.Inflight, s.policy.MaxInflight)}
	}
	s.Inflight++
	s.requestCount++
	s.toolCounts[tool]++
	return nil
}

// AfterToolCall 在途 -1（与 BeforeToolCall 成对）
func (s *Session) AfterToolCall() {
	if s.Inflight > 0 {
		s.Inflight--
	}
}

// OnPing 收到对端 ping：视为存活证明（同 OnPong），调用方负责应答 pong（response）。
func (s *Session) OnPing(now time.Time) {
	s.onAlive(now)
}

// OnPong 收到对端 pong（对服务端 ping 的 response）：miss 清零；STALE 恢复 ESTABLISHED
// （持权失效则回 SUSPENDED，规范 §五）。
func (s *Session) OnPong(now time.Time) {
	s.onAlive(now)
}

func (s *Session) onAlive(now time.Time) {
	s.lastPong = now
	s.awaitingPong = false
	s.MissCount = 0
	if s.State == StateStale {
		if s.tokenExpired {
			s.transition(StateSuspended, now)
		} else {
			s.transition(StateEstablished, now)
		}
	}
}

// OnMiss 心跳 miss：≥N_stale → STALE；≥N_abort → ABORTED（heartbeat-timeout，记 session_abort）。
func (s *Session) OnMiss(now time.Time) {
	s.MissCount++
	if s.MissCount >= s.policy.NAbort {
		if s.State != StateAborted {
			s.transition(StateAborted, now)
			s.endReason = ReasonHeartbeatTimeout
			s.Events = append(s.Events, s.event(EventSessionAbort, ReasonHeartbeatTimeout, now))
		}
		return
	}
	if s.MissCount >= s.policy.NStale && s.State == StateEstablished {
		s.transition(StateStale, now)
	}
}

// OnTransportBroken 半开检测（规范 §五/§六 + §九）：stdout 写失败 / 管道破裂 →
// 立即 ABORTED（transport-broken），不等心跳阈值、不等 EOF。
func (s *Session) OnTransportBroken(now time.Time) {
	if s.State == StateClosed || s.State == StateAborted {
		return
	}
	s.transition(StateAborted, now)
	s.endReason = ReasonTransportBroken
	s.Events = append(s.Events, s.event(EventSessionAbort, ReasonTransportBroken, now))
}

// OnTokenExpired 持权到期（裁定 D-2A）：→ SUSPENDED；拒 tools/call=token-expired；心跳继续；不断开。
func (s *Session) OnTokenExpired(now time.Time) {
	if s.tokenExpired {
		return
	}
	s.tokenExpired = true
	if s.State == StateEstablished || s.State == StateStale {
		s.transition(StateSuspended, now)
	}
}

// CheckTimeouts 超时巡检（每次入站消息与心跳 tick 调用；单调时钟）：
//   - HANDSHAKING 超 T_handshake → 拒（handshake-timeout，会话不建立，由调用方记 session_rejected）
//   - awaitingPong 超 T_pong → OnMiss
//   - STALE/SUSPENDED 超 T_gc → ABORTED（gc-timeout）
//   - DRAINING 超 T_gc 未收尾 → 强制回收 ABORTED（gc-timeout）（规范 §六 REV2，裁定 D-2 处置）
func (s *Session) CheckTimeouts(now time.Time) error {
	switch s.State {
	case StateHandshaking:
		if now.Sub(s.handshakeAt) > s.policy.THandshake {
			return &SessionGateError{Code: ReasonHandshakeTimeout, Detail: "H3 not received within " + s.policy.THandshake.String()}
		}
	case StateEstablished, StateStale, StateSuspended:
		// 持权到期巡检（D-2A）
		if !s.tokenExpiresAt.IsZero() && now.After(s.tokenExpiresAt) {
			s.OnTokenExpired(now)
		}
		// pong 逾期 → miss（进入下一 ping 周期）
		if s.awaitingPong && now.Sub(s.pingSentAt) > s.policy.TPong {
			s.OnMiss(now)
			s.awaitingPong = false
		}
		// GC：陈旧/挂起会话超 TGC 回收（中止）
		if (s.State == StateStale || s.State == StateSuspended) && now.Sub(s.stateAt) > s.policy.TGC {
			s.transition(StateAborted, now)
			s.endReason = ReasonGCTimeout
			s.Events = append(s.Events, s.event(EventSessionAbort, ReasonGCTimeout, now))
		}
	case StateDraining:
		// GC：DRAINING 超 T_gc 未收尾 → 强制回收（规范 §六 REV2：与 STALE/SUSPENDED 同适用）
		if now.Sub(s.stateAt) > s.policy.TGC {
			s.transition(StateAborted, now)
			s.endReason = ReasonGCTimeout
			s.Events = append(s.Events, s.event(EventSessionAbort, ReasonGCTimeout, now))
		}
	}
	return nil
}

// BeginDrain 断开第一步（规范 §六 D2）：→ DRAINING（停收新请求，≤T_drain 排空）。
func (s *Session) BeginDrain(now time.Time) {
	if s.State == StateClosed || s.State == StateAborted {
		return
	}
	s.transition(StateDraining, now)
	s.drainAt = now
}

// Finish 断开收尾（规范 §六 D3/D4 + 异常断开表）：
//   - 在途排空 → CLOSED（记 session_close）
//   - 超 T_drain 仍在途 → CLOSED（endReason=drain-timeout，在途残余数经 residual_inflight 标记）
//
// kind 为期望终态触发源（normal-close / transport-eof）。
func (s *Session) Finish(kind string, now time.Time) string {
	if s.State == StateClosed || s.State == StateAborted {
		return s.State
	}
	if s.Inflight > 0 && now.Sub(s.drainAt) > s.policy.TDrain {
		// 排空超时：终态 = CLOSED（非 ABORTED，规范 §六/§十三 A11），标记在途残余数
		s.transition(StateClosed, now)
		s.endReason = ReasonDrainTimeout
		s.Events = append(s.Events, s.event(EventSessionClose, ReasonDrainTimeout, now))
		return s.State
	}
	s.transition(StateClosed, now)
	s.endReason = kind
	s.Events = append(s.Events, s.event(EventSessionClose, kind, now))
	return s.State
}

// Summary 会话小结（规范 §六 D3）：session_id / 时长 / 请求数 / 工具计数 / 拒绝数 / 结束原因
// + 在途残余数（drain-timeout 标记）。
func (s *Session) Summary(now time.Time) map[string]any {
	return map[string]any{
		"session_id":        s.ID,
		"agent_id":          s.AgentID,
		"scene":             s.Scene,
		"token_id":          s.TokenID,
		"state":             s.State,
		"duration_ms":       now.Sub(s.StartedAt).Milliseconds(),
		"request_count":     s.requestCount,
		"tool_counts":       s.toolCounts,
		"reject_count":      s.rejectCount,
		"end_reason":        s.endReason,
		"residual_inflight": s.Inflight,
	}
}

// event 构造事件（最小集字段 + 在途残余 + 参数快照；心跳不入事件；永不记 token 值）
func (s *Session) event(kind, reason string, now time.Time) SessionEvent {
	tc := make(map[string]int, len(s.toolCounts))
	for k, v := range s.toolCounts {
		tc[k] = v
	}
	return SessionEvent{
		Event:             kind,
		RecordType:        "service",
		SessionID:         s.ID,
		AgentID:           s.AgentID,
		Scene:             s.Scene,
		TokenID:           s.TokenID,
		Anonymous:         s.TokenID == "anon",
		NegotiatedVersion: s.negotiatedVersion,
		Reason:            reason,
		DurationMs:        now.Sub(s.StartedAt).Milliseconds(),
		RequestCount:      s.requestCount,
		ToolCounts:        tc,
		RejectCount:       s.rejectCount,
		ResidualInflight:  s.Inflight,
		Policy:            s.policy.PolicyJSON(),
		At:                now,
	}
}

// ---- 握手入参解析（_meta.tdca，fail-closed）----

// tdcaMeta initialize params._meta.tdca（仅允许下列字段；未知字段拒绝）
type tdcaMeta struct {
	AgentCard map[string]any `json:"agent_card"`
	PCRToken  *pcrToken      `json:"pcr_token"`
	Scene     string         `json:"scene"`
}

// pcrToken 持权声明（只取 token_id/scope/expires_at；token 值本体永不进入本结构）
type pcrToken struct {
	TokenID   string   `json:"token_id"`
	Scope     []string `json:"scope"`
	ExpiresAt string   `json:"expires_at"` // RFC3339(Nano)；空 = 无到期
}

// validateHandshake 校验握手三要素（主体/场景/持权），失败返回 *SessionGateError（不建会话）。
// 通过则返回可建会话的要素。fail-closed：任何一项不满足即拒，不静默降级。
//
// 如实登记（整改指令 R-4 / R-5）：
//   - scope 语义为【临时最小定义：须含字面量 "mcp"】，规范 §二 指向 SRIGHT-001 §三
//     scope_covers（须覆盖工具边界）——规范补充条款另批处理（D-3 待裁定），本轮不改实现。
//   - expires_at 解析失败归【token-missing】分支（R-5 选定：保留现行为；若规范侧采纳
//     token-malformed 子码，后续批次切换）。
func validateHandshake(policy SessionPolicy, meta *tdcaMeta, clientName string, now time.Time) (agentID, scene, tokenID string, expiresAt time.Time, err error) {
	agentID = clientName
	// 主体校验：agent_card 过 enforce 门禁（entry-rejected）
	if meta != nil && meta.AgentCard != nil {
		res, gerr := gateAgentCard(meta.AgentCard)
		if gerr != nil {
			return "", "", "", time.Time{}, &SessionGateError{Code: ReasonEntryRejected, Detail: "agent_card invalid: " + gerr.Error()}
		}
		if res.Status != "PASS" {
			return "", "", "", time.Time{}, &SessionGateError{Code: ReasonEntryRejected, Detail: "enforce " + res.Status + ": " + res.Reason}
		}
		agentID = res.AgentID
		scene = res.SceneID
	}
	// 场景：显式 scene 优先补齐
	if meta != nil && meta.Scene != "" {
		scene = meta.Scene
	}
	// 持权校验（AllowAnon=false 时握手即拒；默认 true 时建匿名只读会话 PCS-anon，裁定 D-7）
	if meta == nil || meta.PCRToken == nil || meta.PCRToken.TokenID == "" {
		if !policy.AllowAnon {
			return "", "", "", time.Time{}, &SessionGateError{Code: ReasonTokenMissing, Detail: "_meta.tdca.pcr_token.token_id required"}
		}
		return agentID, scene, "", time.Time{}, nil
	}
	tok := meta.PCRToken
	// 作用域：临时最小定义（须含字面量 "mcp"；D-3 待裁定，见函数头注释 R-4）
	okScope := false
	for _, sc := range tok.Scope {
		if sc == "mcp" {
			okScope = true
			break
		}
	}
	if !okScope {
		return "", "", "", time.Time{}, &SessionGateError{Code: ReasonTokenScopeInsufficient, Detail: "scope must include \"mcp\""}
	}
	// 到期：握手期过期 → token-scope-insufficient（规范 §十三 A4：越界/握手期过期同子码；
	// 会话期到期另走 token-expired → SUSPENDED，见 BeforeToolCall/CheckTimeouts）
	if tok.ExpiresAt != "" {
		exp, perr := time.Parse(time.RFC3339Nano, tok.ExpiresAt)
		if perr != nil {
			// R-5 选定分支：解析失败归 token-missing
			return "", "", "", time.Time{}, &SessionGateError{Code: ReasonTokenMissing, Detail: "expires_at not RFC3339: " + perr.Error()}
		}
		if now.After(exp) {
			return "", "", "", time.Time{}, &SessionGateError{Code: ReasonTokenScopeInsufficient, Detail: "credential already expired at handshake"}
		}
		expiresAt = exp
	}
	return agentID, scene, tok.TokenID, expiresAt, nil
}

// gateAgentCard 复用 enforce 门禁校验握手主体（与工具语义同源，不改判定语义）
func gateAgentCard(card map[string]any) (enforceResult, error) {
	raw, err := json.Marshal(card)
	if err != nil {
		return enforceResult{}, err
	}
	gate := enforce.NewEntryGate()
	res, err := gate.Apply(raw)
	if err != nil {
		return enforceResult{}, err
	}
	return enforceResult{Status: res.Status, Reason: res.Reason, AgentID: res.AgentID, SceneID: res.SceneID}, nil
}

// enforceResult enforce 门禁结果投影（避免暴露内部类型到会话层 API）
type enforceResult struct {
	Status  string
	Reason  string
	AgentID string
	SceneID string
}
