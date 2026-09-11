// 会话层测试：TDCA-STD-SESSION-001 V0.2-DRAFT-REV2 §十三 验收 A1~A17
// （R-7：用例名已对齐规范编号，一编号 ↔ 一用例；核证单 GSEQ-1283 §三 映射表为准）
//
// 编号映射（整改前旧名 → 现名）：
//
//	A1  TestA1HandshakeEstablished（不变）
//	A2  TestA2VersionIncompatible（R-11 更新：集合外仍拒 + 缺失/非字符串 → -32602）
//	A3  TestA3TokenMissing（R-12 更新：显式 allow_anonymous=false 下握手即拒）
//	A4  TestA4TokenScopeInsufficient → TestA4TokenScopeOrHandshakeExpiry（补握手期过期分支）
//	A5  TestA7NotEstablished → TestA5NotEstablished（编号归位）
//	A6  TestA10MissStale / TestA10HeartbeatServerDriven → TestA6MissStale / TestA6HeartbeatServerDriven
//	A7  TestA12MissAbort → TestA7MissAbort（子码 heartbeat-timeout）
//	A8  TestA11PongResets → TestA8PongResets
//	A9  新增 TestA9HalfOpenWriteFailure（R-1：写失败 → 立即 ABORTED transport-broken）
//	A10 TestA13CloseDrainClosed → TestA10CloseDrainClosed（小结载域 _meta.tdca.session_summary）
//	A11 TestA14DrainTimeout → TestA11DrainTimeout（终态 CLOSED + residual_inflight，R-2）
//	A12 TestA15GCTimeout → TestA12aGCTimeoutStale + TestA12bGCTimeoutDraining（R-3）
//	A13 新增 TestA13SessionIDReuseRejected（不变量 1）
//	A14 新增 TestA14FailClosed（未知方法/字段 → -32601/-32602 保持）
//	A15 TestV5HeartbeatNotInEvents → TestA15HeartbeatNotInEvents
//	A16 TestV5NoTokenValueInEvents → TestA16NoTokenValueInEvents
//	A17 TestA17TokenExpirySuspended / TestA17TokenExpiryServeDriven（不变）
//	A18 新增 TestA18AnonymousReadOnly（R-12：默认匿名只读；nca_append 拒 token-missing；事件记 anonymous）
//	A19 新增 TestA19VersionNegotiation（R-11：支持集内接受、应答恒回服务端版本、协商结果入事件）
//
// 超额用例（无规范编号，保留为正向补充）：TestEntryRejected / TestHandshakeTimeout /
// TestEstablishedToolCall / TestPingPong / TestHeartbeatPongResponseClearsMiss /
// TestMaxInflightExceeded / TestAllowAnonymousPolicy（R-12 后改测默认放行 + 显式关闭回退）。
//
// SPDX-License-Identifier: Apache-2.0
package mcp

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"strings"
	"testing"
	"time"
)

// ---- 会话测试工具 ----

// tdcaMetaJSON 构造合规 _meta.tdca（三要素齐备：主体/持权/场景）
func tdcaMetaJSON(overrides map[string]any) map[string]any {
	m := map[string]any{
		"agent_card": json.RawMessage(cardJSON(nil)),
		"pcr_token":  map[string]any{"token_id": "tok-test-01", "scope": []string{"mcp"}},
		"scene":      "scene-phy-notification",
	}
	for k, v := range overrides {
		m[k] = v
	}
	return m
}

// initReq 构造 initialize 请求行（meta=nil 表示不带 _meta.tdca）
func initReq(id any, meta map[string]any) string {
	params := map[string]any{
		"protocolVersion": ProtocolVersion,
		"clientInfo":      map[string]any{"name": "sess-test", "version": "0.1"},
	}
	if meta != nil {
		params["_meta"] = map[string]any{"tdca": meta}
	}
	return j(map[string]any{"jsonrpc": "2.0", "id": id, "method": "initialize", "params": params})
}

const initializedNotif = `{"jsonrpc":"2.0","method":"notifications/initialized"}`

// handshakeLines 握手两行（initialize + initialized 通知）
func handshakeLines() []string {
	return []string{initReq("h1", tdcaMetaJSON(nil)), initializedNotif}
}

// runEstablished 完成握手后执行请求，返回请求对应响应（剥除握手响应）
func runEstablished(t *testing.T, s *Server, reqs ...string) []map[string]any {
	t.Helper()
	lines := append(handshakeLines(), reqs...)
	resps := run(t, s, lines...)
	if len(resps) < 1+len(reqs) {
		t.Fatalf("want ≥%d responses, got %d: %v", 1+len(reqs), len(resps), resps)
	}
	if e, ok := resps[0]["error"]; ok {
		t.Fatalf("handshake rejected: %v", e)
	}
	return resps[1 : 1+len(reqs)]
}

func errMsg(t *testing.T, resp map[string]any) string {
	t.Helper()
	e, ok := resp["error"]
	if !ok {
		t.Fatalf("want error, got %v", resp)
	}
	return e.(map[string]any)["message"].(string)
}

func errCode(t *testing.T, resp map[string]any) float64 {
	t.Helper()
	e, ok := resp["error"]
	if !ok {
		t.Fatalf("want error, got %v", resp)
	}
	return e.(map[string]any)["code"].(float64)
}

// unitSession 构造直接可测会话（H1 已过，HANDSHAKING）
func unitSession(p SessionPolicy, tokenID string, expiresAt time.Time, now time.Time) *Session {
	return NewSession(p, "NM-001", "scene-phy-notification", tokenID, expiresAt, now)
}

// serveInteractive 经 io.Pipe 实跑 Serve（逐行写入，wait 后关闭输入），返回会话与全部输出
func serveInteractive(t *testing.T, s *Server, wait time.Duration, lines ...string) (*Session, string) {
	t.Helper()
	inR, inW := io.Pipe()
	var out bytes.Buffer
	done := make(chan error, 1)
	go func() { done <- s.Serve(inR, &out) }()
	for _, l := range lines {
		if _, err := fmt.Fprintln(inW, l); err != nil {
			t.Fatalf("write: %v", err)
		}
	}
	time.Sleep(wait)
	_ = inW.Close()
	if err := <-done; err != nil {
		t.Fatalf("serve: %v", err)
	}
	return s.Session(), out.String()
}

// summaryFromClose 从小结通知行提取 _meta.tdca.session_summary
func summaryFromClose(t *testing.T, line map[string]any) map[string]any {
	t.Helper()
	if line["method"] != "close" {
		t.Fatalf("want close notification carrying summary, got %v", line)
	}
	params, ok := line["params"].(map[string]any)
	if !ok {
		t.Fatalf("close notification missing params: %v", line)
	}
	sum, ok := params["_meta"].(map[string]any)["tdca"].(map[string]any)["session_summary"].(map[string]any)
	if !ok {
		t.Fatalf("missing _meta.tdca.session_summary: %v", line)
	}
	return sum
}

// ---- A1 握手四步正常流 ----

func TestA1HandshakeEstablished(t *testing.T) {
	s := NewServer()
	resps := run(t, s, initReq(1, tdcaMetaJSON(nil)), initializedNotif)
	if len(resps) != 1 {
		t.Fatalf("want 1 response (initialize), got %d: %v", len(resps), resps)
	}
	res := resps[0]["result"].(map[string]any)
	meta := res["_meta"].(map[string]any)["tdca"].(map[string]any)
	if meta["session_id"] != "PCS-tok-test-01" {
		t.Errorf("session_id = %v", meta["session_id"])
	}
	pol := meta["session_policy"].(map[string]any)
	if pol["t_handshake"] != "10s" || pol["max_inflight"].(float64) != 1 || pol["allow_anonymous"] != true {
		t.Errorf("session_policy mismatch: %v", pol)
	}
	sess := s.Session()
	if sess == nil {
		t.Fatalf("session missing after handshake")
	}
	if sess.AgentID != "NM-001" || sess.Scene != "scene-phy-notification" || sess.TokenID != "tok-test-01" {
		t.Errorf("session identity mismatch: %+v", sess)
	}
	// session_open 事件（type=service，最小集字段）——H3 到位即记，证明曾置 ESTABLISHED
	if len(sess.Events) < 1 || sess.Events[0].Event != EventSessionOpen || sess.Events[0].RecordType != "service" {
		t.Fatalf("want session_open/service event, got %+v", sess.Events)
	}
	// EOF 收尾纪律：输入结束 = 传输断开 → CLOSED（transport-eof），记 session_close
	if sess.State != StateClosed || sess.endReason != ReasonTransportEOF {
		t.Errorf("EOF must close session (transport-eof), got %s/%s", sess.State, sess.endReason)
	}
}

// ---- A2 版本不相容（无静默降级；-32000 + tdca/session: 前缀；R-11 协商后集合外仍拒）----

func TestA2VersionIncompatible(t *testing.T) {
	s := NewServer()
	bad := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": map[string]any{
		"protocolVersion": "1999-01-01",
		"clientInfo":      map[string]any{"name": "sess-test", "version": "0.1"},
		"_meta":           map[string]any{"tdca": tdcaMetaJSON(nil)},
	}})
	resps := run(t, s, bad)
	if c := errCode(t, resps[0]); c != -32000 {
		t.Errorf("want -32000, got %v", c)
	}
	msg := errMsg(t, resps[0])
	if !strings.Contains(msg, "tdca/session:"+ReasonVersionIncompatible) || !strings.Contains(msg, ProtocolVersion) {
		t.Errorf("want tdca/session:version-incompatible + server version, got %q", msg)
	}
	if s.Session() != nil {
		t.Errorf("session must not be established")
	}
	rej := s.RejectedEvents()
	if len(rej) != 1 || rej[0].Reason != ReasonVersionIncompatible || rej[0].Event != EventSessionRejected {
		t.Errorf("want session_rejected/version-incompatible, got %+v", rej)
	}
	// R-11：protocolVersion 缺失 → -32602（fail-closed 参数纪律，非会话层拒绝）
	s2 := NewServer()
	noVer := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": map[string]any{
		"clientInfo": map[string]any{"name": "sess-test", "version": "0.1"},
		"_meta":      map[string]any{"tdca": tdcaMetaJSON(nil)},
	}})
	if c := errCode(t, run(t, s2, noVer)[0]); c != -32602 {
		t.Errorf("missing protocolVersion must be -32602, got %v", c)
	}
	// R-11：protocolVersion 非字符串 → -32602
	s3 := NewServer()
	numVer := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": map[string]any{
		"protocolVersion": 20250618,
		"clientInfo":      map[string]any{"name": "sess-test", "version": "0.1"},
	}})
	if c := errCode(t, run(t, s3, numVer)[0]); c != -32602 {
		t.Errorf("non-string protocolVersion must be -32602, got %v", c)
	}
}

// ---- A3 缺 PCR-Token（显式 allow_anonymous=false → 握手即拒；R-12 后默认改匿名只读，见 A18）----

func TestA3TokenMissing(t *testing.T) {
	p := DefaultSessionPolicy()
	p.AllowAnon = false // 显式关闭匿名准入（--allow-anonymous=false）
	s := NewServerWithPolicy(p)
	meta := tdcaMetaJSON(nil)
	delete(meta, "pcr_token")
	resps := run(t, s, initReq(1, meta))
	if !strings.Contains(errMsg(t, resps[0]), ReasonTokenMissing) {
		t.Errorf("want token-missing, got %v", resps[0])
	}
	// 完全无 _meta.tdca 同样拒绝
	s2 := NewServerWithPolicy(p)
	resps2 := run(t, s2, initReq(1, nil))
	if !strings.Contains(errMsg(t, resps2[0]), ReasonTokenMissing) {
		t.Errorf("want token-missing (no _meta.tdca), got %v", resps2[0])
	}
}

// ---- A4 token 越界 / 握手期过期（同子码 token-scope-insufficient，规范 §十三 A4）----

func TestA4TokenScopeOrHandshakeExpiry(t *testing.T) {
	// 越界：scope 不含 "mcp"
	s := NewServer()
	meta := tdcaMetaJSON(map[string]any{
		"pcr_token": map[string]any{"token_id": "tok-test-02", "scope": []string{"read-only"}},
	})
	resps := run(t, s, initReq(1, meta))
	if !strings.Contains(errMsg(t, resps[0]), ReasonTokenScopeInsufficient) {
		t.Errorf("want token-scope-insufficient, got %v", resps[0])
	}
	rej := s.RejectedEvents()
	if len(rej) != 1 || rej[0].TokenID != "tok-test-02" {
		t.Errorf("rejected event must record token_id only, got %+v", rej)
	}
	// 握手期过期：expires_at 早于握手时刻 → 同子码
	s2 := NewServer()
	past := time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano)
	meta2 := tdcaMetaJSON(map[string]any{
		"pcr_token": map[string]any{"token_id": "tok-expired-hs", "scope": []string{"mcp"}, "expires_at": past},
	})
	resps2 := run(t, s2, initReq(1, meta2))
	if !strings.Contains(errMsg(t, resps2[0]), ReasonTokenScopeInsufficient) {
		t.Errorf("handshake-time expiry must be token-scope-insufficient, got %v", resps2[0])
	}
	if s2.Session() != nil {
		t.Errorf("session must not be established")
	}
}

// ---- A5 握手期调用 tools/call → session-not-established ----

func TestA5NotEstablished(t *testing.T) {
	s := NewServer()
	// 完全无握手
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "nsfl_eval", "arguments": map[string]any{"trigger_id": "t1", "signal": "suspicious-pattern"}}})
	resps := run(t, s, req)
	if c := errCode(t, resps[0]); c != -32000 {
		t.Errorf("want -32000, got %v", c)
	}
	if !strings.Contains(errMsg(t, resps[0]), "tdca/session:"+ReasonSessionNotEstablished) {
		t.Errorf("want tdca/session:session-not-established, got %v", resps[0])
	}
	// H1 已过但 H3 未到（HANDSHAKING）同样拒绝
	s2 := NewServer()
	resps2 := run(t, s2, initReq(1, tdcaMetaJSON(nil)), req)
	if !strings.Contains(errMsg(t, resps2[1]), ReasonSessionNotEstablished) {
		t.Errorf("HANDSHAKING tools/call must reject, got %v", resps2[1])
	}
}

// ---- A6 心跳 2 miss → STALE，新请求 session-stale ----

func TestA6MissStale(t *testing.T) {
	p := DefaultSessionPolicy() // NStale=2
	now := time.Now()
	sess := unitSession(p, "tok-a6", time.Time{}, now)
	if err := sess.HandshakeDone(now); err != nil {
		t.Fatal(err)
	}
	sess.OnMiss(now.Add(time.Second))
	if sess.State != StateEstablished {
		t.Fatalf("miss=1 must stay ESTABLISHED, got %s", sess.State)
	}
	sess.OnMiss(now.Add(2 * time.Second))
	if sess.State != StateStale {
		t.Fatalf("miss=2 must be STALE, got %s", sess.State)
	}
	err := sess.BeforeToolCall("nsfl_eval", now.Add(2*time.Second))
	ge, ok := err.(*SessionGateError)
	if !ok || ge.Code != ReasonSessionStale {
		t.Fatalf("STALE tools/call must reject session-stale, got %v", err)
	}
}

// A6 实跑补证：服务端按 T_ping 发 ping【request】→ 无 pong → miss 累积 → STALE → ABORTED
func TestA6HeartbeatServerDriven(t *testing.T) {
	p := DefaultSessionPolicy()
	p.TPing, p.TPong = 20*time.Millisecond, 15*time.Millisecond
	s := NewServerWithPolicy(p)
	sess, out := serveInteractive(t, s, 300*time.Millisecond,
		initReq(1, tdcaMetaJSON(nil)), initializedNotif)
	// 服务端确已发出 ping request（保活由服务端定时发出；id = tdca-ping-N）
	if !strings.Contains(out, `"method":"ping"`) || !strings.Contains(out, `"id":"tdca-ping-`) {
		t.Errorf("server must emit ping requests, out=%s", out)
	}
	// 无 pong：miss 累积 → 先 STALE 后 ABORTED（A7 实跑证据同此）
	if sess.State != StateAborted {
		t.Fatalf("want ABORTED after sustained misses, got %s", sess.State)
	}
	var abortEvt *SessionEvent
	for i := range sess.Events {
		if sess.Events[i].Event == EventSessionAbort {
			abortEvt = &sess.Events[i]
		}
	}
	if abortEvt == nil || abortEvt.Reason != ReasonHeartbeatTimeout {
		t.Fatalf("want session_abort/heartbeat-timeout, got %+v", sess.Events)
	}
	// 心跳不入事件：事件中不得出现 ping/pong 类
	for _, ev := range sess.Events {
		if strings.Contains(strings.ToLower(ev.Event), "ping") || strings.Contains(strings.ToLower(ev.Reason), "pong") {
			t.Errorf("heartbeat must not enter events: %+v", ev)
		}
	}
}

// ---- A7 心跳 3 miss → ABORTED + heartbeat-timeout ----

func TestA7MissAbort(t *testing.T) {
	p := DefaultSessionPolicy() // NAbort=3
	now := time.Now()
	sess := unitSession(p, "tok-a7", time.Time{}, now)
	_ = sess.HandshakeDone(now)
	sess.OnMiss(now.Add(time.Second))
	sess.OnMiss(now.Add(2 * time.Second))
	sess.OnMiss(now.Add(3 * time.Second))
	if sess.State != StateAborted {
		t.Fatalf("miss=3 must ABORT, got %s", sess.State)
	}
	last := sess.Events[len(sess.Events)-1]
	if last.Event != EventSessionAbort || last.Reason != ReasonHeartbeatTimeout {
		t.Errorf("want session_abort/heartbeat-timeout, got %+v", last)
	}
	// ABORTED 后工具一律拒
	if err := sess.BeforeToolCall("nsfl_eval", now.Add(4*time.Second)); err == nil {
		t.Errorf("ABORTED must reject tools/call")
	}
	// 实跑证据见 TestA6HeartbeatServerDriven（STALE→ABORTED 全链）
}

// ---- A8 pong 恢复（STALE → ESTABLISHED，计数清零）----

func TestA8PongResets(t *testing.T) {
	p := DefaultSessionPolicy()
	now := time.Now()
	sess := unitSession(p, "tok-a8", time.Time{}, now)
	_ = sess.HandshakeDone(now)
	sess.OnMiss(now.Add(time.Second))
	sess.OnMiss(now.Add(2 * time.Second)) // STALE
	sess.OnPong(now.Add(3 * time.Second))
	if sess.State != StateEstablished || sess.MissCount != 0 {
		t.Fatalf("pong must reset to ESTABLISHED/miss=0, got %s/%d", sess.State, sess.MissCount)
	}
	if err := sess.BeforeToolCall("nsfl_eval", now.Add(3*time.Second)); err != nil {
		t.Fatalf("tools/call must recover after pong: %v", err)
	}
}

// ---- A9 半开（写失败）→ 立即 ABORTED + transport-broken（不等阈值，R-1）----

// failWriter 可注入失败 writer（模拟半开管道：写即败）
type failWriter struct{}

func (failWriter) Write(p []byte) (int, error) {
	return 0, fmt.Errorf("simulated write failure (half-open pipe)")
}

func TestA9HalfOpenWriteFailure(t *testing.T) {
	s := NewServer()
	in := strings.NewReader(initReq(1, tdcaMetaJSON(nil)) + "\n")
	err := s.Serve(in, failWriter{})
	if err == nil {
		t.Fatalf("Serve must return write error")
	}
	sess := s.Session()
	if sess == nil {
		t.Fatalf("session was created at H1; must be present for inspection")
	}
	// 写失败 → 立即 ABORTED（不等心跳阈值、不等 EOF）
	if sess.State != StateAborted {
		t.Fatalf("want ABORTED, got %s", sess.State)
	}
	if sess.endReason != ReasonTransportBroken {
		t.Errorf("endReason = %q, want transport-broken", sess.endReason)
	}
	var abortEvt *SessionEvent
	for i := range sess.Events {
		if sess.Events[i].Event == EventSessionAbort {
			abortEvt = &sess.Events[i]
		}
	}
	if abortEvt == nil || abortEvt.Reason != ReasonTransportBroken {
		t.Fatalf("want session_abort/transport-broken event, got %+v", sess.Events)
	}
	// 中途半开变体：握手成功后写失败（close 小结写不出）→ 同样立即 ABORTED
	s2 := NewServer()
	in2 := strings.NewReader(strings.Join(append(handshakeLines(), `{"jsonrpc":"2.0","method":"close"}`), "\n") + "\n")
	if err := s2.Serve(in2, failWriter{}); err == nil {
		t.Fatalf("Serve must return write error on broken pipe mid-session")
	}
	if s2.Session().State != StateAborted || s2.Session().endReason != ReasonTransportBroken {
		t.Errorf("mid-session write failure must ABORTED/transport-broken, got %s/%s",
			s2.Session().State, s2.Session().endReason)
	}
}

// ---- A10 正常断开 + 在途排空：DRAINING → CLOSED + 小结四项一致 ----

func TestA10CloseDrainClosed(t *testing.T) {
	s := NewServer()
	toolReq := j(map[string]any{"jsonrpc": "2.0", "id": 2, "method": "tools/call",
		"params": map[string]any{"name": "nsfl_eval", "arguments": map[string]any{"trigger_id": "t1", "signal": "suspicious-pattern"}}})
	lines := append(handshakeLines(), toolReq, `{"jsonrpc":"2.0","method":"close"}`)
	resps := run(t, s, lines...)
	// 响应：initialize + tools/call + 会话小结通知（close 载 _meta.tdca.session_summary）
	if len(resps) != 3 {
		t.Fatalf("want 3 lines, got %d: %v", len(resps), resps)
	}
	sum := summaryFromClose(t, resps[2])
	if sum["session_id"] != "PCS-tok-test-01" || sum["state"] != StateClosed || sum["end_reason"] != ReasonNormalClose {
		t.Errorf("summary mismatch: %v", sum)
	}
	if sum["request_count"].(float64) != 1 || sum["tool_counts"].(map[string]any)["nsfl_eval"].(float64) != 1 {
		t.Errorf("summary counters mismatch: %v", sum)
	}
	if sum["residual_inflight"].(float64) != 0 {
		t.Errorf("clean drain must have residual_inflight=0, got %v", sum["residual_inflight"])
	}
	sess := s.Session()
	if sess.State != StateClosed {
		t.Errorf("want CLOSED, got %s", sess.State)
	}
	last := sess.Events[len(sess.Events)-1]
	if last.Event != EventSessionClose || last.Reason != ReasonNormalClose || last.RecordType != "service" {
		t.Errorf("want session_close/normal-close/service, got %+v", last)
	}
}

// ---- A11 排空超时：终态 CLOSED（非 ABORTED）+ drain-timeout + 在途残余数标记（R-2）----

func TestA11DrainTimeout(t *testing.T) {
	p := DefaultSessionPolicy() // TDrain=5s
	now := time.Now()
	sess := unitSession(p, "tok-a11", time.Time{}, now)
	_ = sess.HandshakeDone(now)
	// 构造在途未释放（max_inflight=1 同步模型下的极端挂起）
	if err := sess.BeforeToolCall("nca_append", now); err != nil {
		t.Fatal(err)
	}
	sess.BeginDrain(now.Add(time.Second))
	if sess.State != StateDraining {
		t.Fatalf("want DRAINING, got %s", sess.State)
	}
	final := sess.Finish(ReasonNormalClose, now.Add(7*time.Second)) // 超 TDrain 仍在途
	if final != StateClosed {
		t.Fatalf("drain-timeout terminal must be CLOSED (not ABORTED), got %s", final)
	}
	last := sess.Events[len(sess.Events)-1]
	if last.Event != EventSessionClose || last.Reason != ReasonDrainTimeout {
		t.Errorf("want session_close/drain-timeout, got %+v", last)
	}
	// 在途残余数标记（事件与小结双侧）
	if last.ResidualInflight != 1 {
		t.Errorf("event residual_inflight = %d, want 1", last.ResidualInflight)
	}
	if sum := sess.Summary(now.Add(7 * time.Second)); sum["residual_inflight"].(int) != 1 || sum["end_reason"] != ReasonDrainTimeout {
		t.Errorf("summary must mark residual_inflight=1 / drain-timeout, got %v", sum)
	}
	// 对照：在途排空 → CLOSED / normal-close / 残余 0
	sess2 := unitSession(p, "tok-a11b", time.Time{}, now)
	_ = sess2.HandshakeDone(now)
	sess2.BeginDrain(now.Add(time.Second))
	if final := sess2.Finish(ReasonNormalClose, now.Add(2*time.Second)); final != StateClosed {
		t.Errorf("drained session must CLOSE, got %s", final)
	}
	if sess2.Events[len(sess2.Events)-1].ResidualInflight != 0 {
		t.Errorf("clean drain residual must be 0")
	}
}

// ---- A12 残留会话 GC（T_gc 后回收 + gc-timeout；STALE 与 DRAINING 同适用，R-3）----

func TestA12aGCTimeoutStale(t *testing.T) {
	p := DefaultSessionPolicy() // TGC=60s
	now := time.Now()
	sess := unitSession(p, "tok-a12a", time.Time{}, now)
	_ = sess.HandshakeDone(now)
	tStale := now.Add(time.Second)
	sess.OnMiss(now)
	sess.OnMiss(tStale) // STALE，stateAt=tStale
	if sess.State != StateStale {
		t.Fatalf("want STALE, got %s", sess.State)
	}
	// STALE 超 TGC 未恢复 → GC 回收（ABORTED / gc-timeout）
	if err := sess.CheckTimeouts(tStale.Add(61 * time.Second)); err != nil {
		t.Fatalf("gc path must not error, got %v", err)
	}
	if sess.State != StateAborted {
		t.Fatalf("want ABORTED after GC, got %s", sess.State)
	}
	last := sess.Events[len(sess.Events)-1]
	if last.Event != EventSessionAbort || last.Reason != ReasonGCTimeout {
		t.Errorf("want session_abort/gc-timeout, got %+v", last)
	}
	// 对照：TGC 内不回收
	sess2 := unitSession(p, "tok-a12a2", time.Time{}, now)
	_ = sess2.HandshakeDone(now)
	sess2.OnMiss(now)
	sess2.OnMiss(now.Add(time.Second))
	_ = sess2.CheckTimeouts(now.Add(30 * time.Second))
	if sess2.State != StateStale {
		t.Errorf("within TGC must stay STALE, got %s", sess2.State)
	}
}

// DRAINING 超 T_gc 未收尾 → 强制回收（规范 §六 REV2，裁定 D-2 处置）
func TestA12bGCTimeoutDraining(t *testing.T) {
	p := DefaultSessionPolicy() // TGC=60s
	now := time.Now()
	sess := unitSession(p, "tok-a12b", time.Time{}, now)
	_ = sess.HandshakeDone(now)
	tDrain := now.Add(time.Second)
	sess.BeginDrain(tDrain) // DRAINING，未收尾（无 Finish）
	if sess.State != StateDraining {
		t.Fatalf("want DRAINING, got %s", sess.State)
	}
	// TGC 内：不回收
	_ = sess.CheckTimeouts(tDrain.Add(30 * time.Second))
	if sess.State != StateDraining {
		t.Fatalf("within TGC must stay DRAINING, got %s", sess.State)
	}
	// 超 TGC：强制回收
	_ = sess.CheckTimeouts(tDrain.Add(61 * time.Second))
	if sess.State != StateAborted {
		t.Fatalf("want ABORTED after GC, got %s", sess.State)
	}
	last := sess.Events[len(sess.Events)-1]
	if last.Event != EventSessionAbort || last.Reason != ReasonGCTimeout {
		t.Errorf("want session_abort/gc-timeout, got %+v", last)
	}
}

// ---- A13 session_id 跨会话复用尝试 → 拒绝（不变量 1；重连须重新握手）----

func TestA13SessionIDReuseRejected(t *testing.T) {
	s := NewServer()
	// 已建立会话上重复 initialize → 拒绝，原会话不被替换
	resps := run(t, s, initReq(1, tdcaMetaJSON(nil)), initializedNotif, initReq(2, tdcaMetaJSON(nil)))
	if len(resps) != 2 {
		t.Fatalf("want 2 responses, got %d: %v", len(resps), resps)
	}
	if c := errCode(t, resps[1]); c != -32000 {
		t.Errorf("want -32000, got %v", c)
	}
	if !strings.Contains(errMsg(t, resps[1]), "tdca/session:"+ReasonSessionNotEstablished) {
		t.Errorf("re-initialize must reject, got %v", resps[1])
	}
	sess := s.Session()
	if sess == nil || sess.ID != "PCS-tok-test-01" {
		t.Fatalf("original session must be kept, got %+v", sess)
	}
	// 原会话仍可用（不被复用尝试破坏）
	if sess.State != StateClosed { // EOF 收尾（transport-eof）
		t.Logf("final state %s (%s)", sess.State, sess.endReason)
	}
	if sess.Events[0].Event != EventSessionOpen {
		t.Errorf("original session must remain the established one")
	}
}

// ---- A14 未知方法 / 未知字段：-32601 / -32602 既有 fail-closed 保持 ----

func TestA14FailClosed(t *testing.T) {
	// 未知方法 → -32601
	s1 := NewServer()
	r1 := run(t, s1, `{"jsonrpc":"2.0","id":1,"method":"tools/unknown"}`)[0]
	if errCode(t, r1) != -32601 {
		t.Errorf("unknown method must be -32601, got %v", r1)
	}
	// initialize 顶层未知字段 → -32602
	s2 := NewServer()
	badInit := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": map[string]any{
		"protocolVersion": ProtocolVersion,
		"clientInfo":      map[string]any{"name": "x", "version": "0.1"},
		"__backdoor__":    true,
		"_meta":           map[string]any{"tdca": tdcaMetaJSON(nil)},
	}})
	r2 := run(t, s2, badInit)[0]
	if errCode(t, r2) != -32602 {
		t.Errorf("unknown initialize field must be -32602, got %v", r2)
	}
	// _meta 未知命名空间 → -32602
	s3 := NewServer()
	badMeta := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": map[string]any{
		"protocolVersion": ProtocolVersion,
		"clientInfo":      map[string]any{"name": "x", "version": "0.1"},
		"_meta":           map[string]any{"tdca": tdcaMetaJSON(nil), "evil": map[string]any{}},
	}})
	if errCode(t, run(t, s3, badMeta)[0]) != -32602 {
		t.Errorf("unknown _meta namespace must be -32602")
	}
	// _meta.tdca 未知字段 → -32602
	s4 := NewServer()
	meta := tdcaMetaJSON(nil)
	meta["__admin__"] = true
	if errCode(t, run(t, s4, initReq(1, meta))[0]) != -32602 {
		t.Errorf("unknown _meta.tdca field must be -32602")
	}
	// 工具参数未知字段 → -32602（schema violation，ESTABLISHED 后）
	s5 := NewServer()
	badCall := j(map[string]any{"jsonrpc": "2.0", "id": 2, "method": "tools/call",
		"params": map[string]any{"name": "nsfl_eval", "arguments": map[string]any{"trigger_id": "t1", "signal": "x", "__x__": 1}}})
	r5 := runEstablished(t, s5, badCall)[0]
	if errCode(t, r5) != -32602 || !strings.Contains(errMsg(t, r5), "schema violation") {
		t.Errorf("tool arg unknown field must be -32602 schema violation, got %v", r5)
	}
}

// ---- A15 心跳不入 NCA/事件 ----

func TestA15HeartbeatNotInEvents(t *testing.T) {
	p := DefaultSessionPolicy()
	now := time.Now()
	sess := unitSession(p, "tok-a15", time.Time{}, now)
	_ = sess.HandshakeDone(now)
	n := len(sess.Events) // session_open
	sess.OnPing(now.Add(time.Second))
	sess.OnPong(now.Add(2 * time.Second))
	sess.OnMiss(now.Add(3 * time.Second))
	if len(sess.Events) != n {
		t.Fatalf("heartbeat must not append events, got %+v", sess.Events[n:])
	}
	// 实跑侧证据见 TestA6HeartbeatServerDriven 末尾断言
}

// ---- A16 凭据纪律：事件与日志中无 token 值（仅 token_id）----

func TestA16NoTokenValueInEvents(t *testing.T) {
	// pcr_token 携带未知字段（如 token 值本体）→ fail-closed 拒绝
	s := NewServer()
	meta := tdcaMetaJSON(map[string]any{
		"pcr_token": map[string]any{"token_id": "tok-v5", "scope": []string{"mcp"}, "value": "SECRET-TOKEN-VALUE"},
	})
	resps := run(t, s, initReq(1, meta))
	if _, ok := resps[0]["error"]; !ok {
		t.Fatalf("unknown pcr_token field (token value) must be fail-closed rejected, got %v", resps[0])
	}
	if strings.Contains(resps[0]["error"].(map[string]any)["message"].(string), "SECRET-TOKEN-VALUE") {
		t.Errorf("error must not echo token value")
	}
	// 正常会话事件序列化：仅 token_id，无任何 token 值字段
	s2 := NewServer()
	run(t, s2, initReq(1, tdcaMetaJSON(nil)), initializedNotif, `{"jsonrpc":"2.0","method":"close"}`)
	sess := s2.Session()
	raw, _ := json.Marshal(sess.Events)
	var probe []map[string]any
	_ = json.Unmarshal(raw, &probe)
	for _, ev := range probe {
		for k := range ev {
			lk := strings.ToLower(k)
			if lk == "token" || lk == "token_value" || lk == "pcr_token" || lk == "secret" {
				t.Fatalf("event leaks token field %q: %s", k, raw)
			}
		}
	}
	if !strings.Contains(string(raw), "tok-test-01") {
		t.Errorf("token_id must be recorded (audit), got %s", raw)
	}
}

// ---- A17 会话期 token 到期（裁定 D-2A）→ SUSPENDED ----

func TestA17TokenExpirySuspended(t *testing.T) {
	p := DefaultSessionPolicy()
	now := time.Now()
	exp := now.Add(time.Second)
	sess := unitSession(p, "tok-a17", exp, now)
	_ = sess.HandshakeDone(now)

	// 到期前正常
	if err := sess.BeforeToolCall("nsfl_eval", now); err != nil {
		t.Fatal(err)
	}
	sess.AfterToolCall()

	// 到期后：SUSPENDED，tools/call = token-expired
	err := sess.BeforeToolCall("nsfl_eval", now.Add(2*time.Second))
	ge, ok := err.(*SessionGateError)
	if !ok || ge.Code != ReasonTokenExpired {
		t.Fatalf("want token-expired, got %v", err)
	}
	if sess.State != StateSuspended {
		t.Fatalf("want SUSPENDED, got %s", sess.State)
	}
	// 心跳继续：pong 不报错、状态不回 ESTABLISHED（持权失效）、不断开
	sess.OnPong(now.Add(3 * time.Second))
	if sess.State != StateSuspended {
		t.Errorf("pong under expired token must stay SUSPENDED, got %s", sess.State)
	}
	if sess.State == StateClosed || sess.State == StateAborted {
		t.Errorf("session must not disconnect on token expiry")
	}
	// 仍拒
	if err := sess.BeforeToolCall("nsfl_eval", now.Add(3*time.Second)); err == nil {
		t.Errorf("SUSPENDED must keep rejecting tools/call")
	}
	// 续期方式 = 断开重连重新握手（裁定 D-2bA：不接受 in-band 换 token）——
	// 即新连接新会话（NewServer），本层不提供会话内续期 API。
}

// A17 实跑补证：会话中到期 → tools/call 拒 token-expired；ping 仍应答 pong；close 仍可收尾
func TestA17TokenExpiryServeDriven(t *testing.T) {
	exp := time.Now().Add(400 * time.Millisecond).UTC().Format(time.RFC3339Nano)
	meta := tdcaMetaJSON(map[string]any{
		"pcr_token": map[string]any{"token_id": "tok-a17-live", "scope": []string{"mcp"}, "expires_at": exp},
	})
	s := NewServer()
	inR, inW := io.Pipe()
	var out bytes.Buffer
	done := make(chan error, 1)
	go func() { done <- s.Serve(inR, &out) }()
	fmt.Fprintln(inW, initReq(1, meta))
	fmt.Fprintln(inW, initializedNotif)
	time.Sleep(450 * time.Millisecond) // 会话期 token 到期
	toolReq := j(map[string]any{"jsonrpc": "2.0", "id": 2, "method": "tools/call",
		"params": map[string]any{"name": "nsfl_eval", "arguments": map[string]any{"trigger_id": "t1", "signal": "suspicious-pattern"}}})
	fmt.Fprintln(inW, toolReq)
	fmt.Fprintln(inW, `{"jsonrpc":"2.0","id":3,"method":"ping"}`)
	fmt.Fprintln(inW, `{"jsonrpc":"2.0","method":"close"}`)
	_ = inW.Close()
	if err := <-done; err != nil {
		t.Fatalf("serve: %v", err)
	}
	// 解析输出
	var respTool, respPing map[string]any
	var summary map[string]any
	sc := bufio.NewScanner(bytes.NewReader(out.Bytes()))
	for sc.Scan() {
		var r map[string]any
		if err := json.Unmarshal(sc.Bytes(), &r); err != nil {
			continue
		}
		switch {
		case fmt.Sprint(r["id"]) == "2":
			respTool = r
		case fmt.Sprint(r["id"]) == "3":
			respPing = r
		case r["method"] == "close":
			summary = summaryFromClose(t, r)
		}
	}
	if respTool == nil || !strings.Contains(errMsg(t, respTool), "tdca/session:"+ReasonTokenExpired) {
		t.Errorf("tools/call must reject tdca/session:token-expired, got %v (out=%s)", respTool, out.String())
	}
	if respPing == nil || respPing["result"].(map[string]any)["pong"] != true {
		t.Errorf("ping must still be answered under SUSPENDED, got %v", respPing)
	}
	if summary == nil || summary["state"] != StateClosed {
		t.Errorf("session must close cleanly (不断开 on expiry), got %v", summary)
	}
	sess := s.Session()
	if sess == nil {
		t.Fatalf("session missing (out=%s)", out.String())
	}
	if sess.State != StateClosed {
		t.Errorf("want CLOSED, got %s", sess.State)
	}
}

// ---- A18 匿名只读（R-12：默认 allow_anonymous=true；匿名仅只读工具，写类拒 token-missing；事件记 anonymous）----

func TestA18AnonymousReadOnly(t *testing.T) {
	s := NewServer() // 默认策略（allow_anonymous=true，裁定 D-7）
	resps := run(t, s,
		initReq(1, nil), initializedNotif,
		j(map[string]any{"jsonrpc": "2.0", "id": 2, "method": "tools/call",
			"params": map[string]any{"name": "nsfl_eval", "arguments": map[string]any{"trigger_id": "t1", "signal": "unauthenticated"}}}),
		j(map[string]any{"jsonrpc": "2.0", "id": 3, "method": "tools/call",
			"params": map[string]any{"name": "nca_append", "arguments": map[string]any{"record": json.RawMessage(recordJSON("sha256:genesis"))}}}),
	)
	if len(resps) != 3 {
		t.Fatalf("want 3 responses, got %d: %v", len(resps), resps)
	}
	// 匿名握手通过（session_id=PCS-anon）
	meta := resps[0]["result"].(map[string]any)["_meta"].(map[string]any)["tdca"].(map[string]any)
	if meta["session_id"] != "PCS-anon" {
		t.Fatalf("anonymous session_id = %v", meta["session_id"])
	}
	// 只读工具放行
	if e, ok := resps[1]["error"]; ok {
		t.Fatalf("read-only tool must pass for anonymous, got %v", e)
	}
	// 写类工具（nca_append）拒：-32000 + tdca/session:token-missing
	if c := errCode(t, resps[2]); c != -32000 {
		t.Fatalf("want -32000, got %v", c)
	}
	if msg := errMsg(t, resps[2]); !strings.Contains(msg, "tdca/session:"+ReasonTokenMissing) {
		t.Fatalf("want tdca/session:token-missing, got %q", msg)
	}
	// 拒写不伤会话：无 session_abort 事件；会话正常存活至 EOF 收尾（transport-eof）
	sess := s.Session()
	if sess == nil {
		t.Fatalf("session missing")
	}
	for _, ev := range sess.Events {
		if ev.Event == EventSessionAbort {
			t.Fatalf("rejected write must not abort session, got %+v", sess.Events)
		}
	}
	if sess.endReason != ReasonTransportEOF {
		t.Errorf("want normal EOF close (transport-eof), got %s", sess.endReason)
	}
	if len(sess.Events) < 1 || sess.Events[0].Event != EventSessionOpen || !sess.Events[0].Anonymous {
		t.Fatalf("session_open must record anonymous=true, got %+v", sess.Events)
	}
	if sess.rejectCount != 1 {
		t.Errorf("reject_count = %d, want 1", sess.rejectCount)
	}
	// 持权会话事件记 anonymous=false（可复算对照）
	s2 := NewServer()
	_ = runEstablished(t, s2)
	if ev := s2.Session().Events[0]; ev.Anonymous {
		t.Errorf("credentialed session must record anonymous=false, got %+v", ev)
	}
}

// ---- A19 版本协商（R-11：支持集内接受；应答恒回服务端自身版本；协商结果记入 session_open）----

func TestA19VersionNegotiation(t *testing.T) {
	for _, v := range SupportedProtocolVersions {
		s := NewServer()
		req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": map[string]any{
			"protocolVersion": v,
			"clientInfo":      map[string]any{"name": "sess-test", "version": "0.1"},
			"_meta":           map[string]any{"tdca": tdcaMetaJSON(nil)},
		}})
		resps := run(t, s, req, initializedNotif)
		if e, ok := resps[0]["error"]; ok {
			t.Fatalf("supported version %s must be accepted: %v", v, e)
		}
		// 应答恒回服务端自身版本（协商 ≠ 降级）
		if got := resps[0]["result"].(map[string]any)["protocolVersion"]; got != ProtocolVersion {
			t.Errorf("response protocolVersion = %v, want server version %s", got, ProtocolVersion)
		}
		sess := s.Session()
		if sess == nil {
			t.Fatalf("session missing for version %s", v)
		}
		// 协商结果记入 session_open 事件
		if ev := sess.Events[0]; ev.NegotiatedVersion != v {
			t.Errorf("session_open negotiated_version = %q, want %q", ev.NegotiatedVersion, v)
		}
	}
	// 集合外（近版本越界）→ 保持 -32000 version-incompatible（A2 已覆盖远古版本）
	s := NewServer()
	bad := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": map[string]any{
		"protocolVersion": "2026-01-01",
		"clientInfo":      map[string]any{"name": "sess-test", "version": "0.1"},
		"_meta":           map[string]any{"tdca": tdcaMetaJSON(nil)},
	}})
	resps := run(t, s, bad)
	if c := errCode(t, resps[0]); c != -32000 {
		t.Fatalf("out-of-set version must be -32000, got %v", c)
	}
	if msg := errMsg(t, resps[0]); !strings.Contains(msg, "tdca/session:"+ReasonVersionIncompatible) {
		t.Errorf("want tdca/session:version-incompatible, got %q", msg)
	}
	if s.Session() != nil {
		t.Errorf("session must not be established for out-of-set version")
	}
}

// ---- 超额用例（无规范编号，正向补充保留）----

// 主体不过门禁 → entry-rejected（规范 §九 子码；§十三 未单列）
func TestEntryRejected(t *testing.T) {
	s := NewServer()
	meta := tdcaMetaJSON(map[string]any{
		"agent_card": json.RawMessage(cardJSON(map[string]any{"protocol_version": "9.9.9"})),
	})
	resps := run(t, s, initReq(1, meta))
	if !strings.Contains(errMsg(t, resps[0]), "tdca/session:"+ReasonEntryRejected) {
		t.Errorf("want tdca/session:entry-rejected, got %v", resps[0])
	}
	if s.Session() != nil {
		t.Errorf("session must not be established")
	}
}

// 握手超时（H3 逾期 → handshake-timeout；规范 §九 子码，A 序列未单列）
func TestHandshakeTimeout(t *testing.T) {
	p := DefaultSessionPolicy() // THandshake=10s
	now := time.Now()
	sess := unitSession(p, "tok-hs", time.Time{}, now)
	if sess.State != StateHandshaking {
		t.Fatalf("want HANDSHAKING after H1, got %s", sess.State)
	}
	err := sess.HandshakeDone(now.Add(11 * time.Second)) // 超 THandshake
	ge, ok := err.(*SessionGateError)
	if !ok || ge.Code != ReasonHandshakeTimeout {
		t.Fatalf("want handshake-timeout, got %v", err)
	}
	// 时限内 H3 → 正常推进
	sess2 := unitSession(p, "tok-hs2", time.Time{}, now)
	if err := sess2.HandshakeDone(now.Add(9 * time.Second)); err != nil {
		t.Fatalf("in-time H3 must succeed: %v", err)
	}
	if sess2.State != StateEstablished {
		t.Errorf("want ESTABLISHED, got %s", sess2.State)
	}
}

// ESTABLISHED 后 tools/call 正常 + 计数（A1/A10 的补充断言）
func TestEstablishedToolCall(t *testing.T) {
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 2, "method": "tools/call",
		"params": map[string]any{"name": "enforce_check", "arguments": map[string]any{"agent_card": json.RawMessage(cardJSON(nil))}}})
	resps := runEstablished(t, s, req)
	m := resultMap(t, resps[0])
	if m["status"] != "PASS" {
		t.Errorf("want PASS, got %v", m)
	}
	sess := s.Session()
	if sess.Inflight != 0 {
		t.Errorf("inflight must be released, got %d", sess.Inflight)
	}
	sum := sess.Summary(time.Now())
	if sum["request_count"].(int) != 1 || sum["tool_counts"].(map[string]int)["enforce_check"] != 1 {
		t.Errorf("counters mismatch: %v", sum)
	}
}

// 对端 ping request → pong response（规范 §五 双向可发）
func TestPingPong(t *testing.T) {
	s := NewServer()
	resps := runEstablished(t, s, `{"jsonrpc":"2.0","id":2,"method":"ping"}`)
	res := resps[0]["result"].(map[string]any)
	if res["pong"] != true {
		t.Errorf("want pong, got %v", res)
	}
}

// 对服务端 ping 的 pong【response 帧】清 miss 并恢复受理（规范 §五 ping→pong 对应关系）
func TestHeartbeatPongResponseClearsMiss(t *testing.T) {
	p := DefaultSessionPolicy()
	p.TPing, p.TPong = 30*time.Millisecond, 15*time.Millisecond
	p.NStale, p.NAbort = 5, 8 // 放宽阈值，专注验证 pong response 清零语义
	s := NewServerWithPolicy(p)
	inR, inW := io.Pipe()
	var out bytes.Buffer
	done := make(chan error, 1)
	go func() { done <- s.Serve(inR, &out) }()
	fmt.Fprintln(inW, initReq(1, tdcaMetaJSON(nil)))
	fmt.Fprintln(inW, initializedNotif)
	time.Sleep(200 * time.Millisecond) // 期间 miss 累积（→ STALE）
	// 回 pong response（对 tdca-ping-N 的应答帧；id 前缀匹配即可），随后立即 close
	// （不留额外 tick 窗口，避免清零后新 ping 周期再计 miss 干扰断言）
	fmt.Fprintln(inW, `{"jsonrpc":"2.0","id":"tdca-ping-1","result":{}}`)
	fmt.Fprintln(inW, `{"jsonrpc":"2.0","method":"close"}`)
	_ = inW.Close()
	if err := <-done; err != nil {
		t.Fatalf("serve: %v", err)
	}
	sess := s.Session()
	if sess == nil {
		t.Fatalf("session missing")
	}
	// pong response 到位 → miss 清零（ABORTED 则说明未清零）
	for _, ev := range sess.Events {
		if ev.Event == EventSessionAbort {
			t.Fatalf("pong response must clear misses; got abort: %+v", ev)
		}
	}
	if sess.MissCount != 0 {
		t.Errorf("miss count must reset to 0 after pong response, got %d", sess.MissCount)
	}
	if sess.State != StateClosed {
		t.Errorf("want clean CLOSED, got %s", sess.State)
	}
	if !strings.Contains(out.String(), `"id":"tdca-ping-`) {
		t.Errorf("server ping requests missing, out=%s", out.String())
	}
}

// 在途超限（规范 §九 max-inflight-exceeded；§十三 未单列）
func TestMaxInflightExceeded(t *testing.T) {
	p := DefaultSessionPolicy() // MaxInflight=1
	now := time.Now()
	sess := unitSession(p, "tok-mi", time.Time{}, now)
	_ = sess.HandshakeDone(now)
	if err := sess.BeforeToolCall("nca_append", now); err != nil {
		t.Fatal(err)
	}
	err := sess.BeforeToolCall("nca_append", now)
	ge, ok := err.(*SessionGateError)
	if !ok || ge.Code != ReasonMaxInflightExceeded {
		t.Fatalf("want max-inflight-exceeded, got %v", err)
	}
	sess.AfterToolCall()
	if err := sess.BeforeToolCall("nca_append", now); err != nil {
		t.Fatalf("after release must pass: %v", err)
	}
}

// 匿名准入开关（R-12 后默认 true：无持权建匿名只读会话 PCS-anon；显式 false 回退握手即拒，见 A3）
func TestAllowAnonymousPolicy(t *testing.T) {
	// 默认（--allow-anonymous 缺省 = true）：无持权可建匿名会话
	s := NewServer()
	resps := run(t, s, initReq(1, nil), initializedNotif)
	if e, ok := resps[0]["error"]; ok {
		t.Fatalf("anonymous must be allowed by default: %v", e)
	}
	sess := s.Session()
	if sess == nil || sess.ID != "PCS-anon" {
		t.Fatalf("anonymous session mismatch: %+v", sess)
	}
	// 输入结束（EOF）→ 传输断开收尾 CLOSED；建立证据看 session_open 事件
	if sess.Events[0].Event != EventSessionOpen {
		t.Fatalf("want session_open, got %+v", sess.Events)
	}
	// 生效参数随事件存证（allow_anonymous=true 可见）
	if sess.Events[0].Policy["allow_anonymous"] != true {
		t.Errorf("policy deviation must be evidenced in event: %+v", sess.Events[0].Policy)
	}
}
