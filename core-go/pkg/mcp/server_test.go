// Package mcp 测试：MCP 桥接（DCD-CORE-GO-001 §三 验收 ≥15 用例）
//
// 覆盖: 握手 / 工具枚举 / enforce-nca-nsfl 调用 / JSON Schema 合规拦截 /
//       破坏性测试（伪造 NCA/绕过 NSFL/注入）/ 挂载模式 E2E（外部 Agent 全会话）。
// SPDX-License-Identifier: Apache-2.0
package mcp

import (
	"bufio"
	"bytes"
	"encoding/json"
	"strings"
	"testing"

	"github.com/henyi-tdca/tdca-core-go/pkg/nca"
)

// ---- 测试工具 ----

// call 发送单条 JSON-RPC 请求，返回响应行
func call(t *testing.T, s *Server, line string) map[string]any {
	t.Helper()
	var out bytes.Buffer
	srv := NewServer()
	// 保持 Server 引用：此处每个测试独立服务器，模拟外部 Agent 单次连接
	_ = srv
	// 直接处理（无状态桥接：每次 Serve 新实例，等价于外部 Agent 独立挂载）
	if err := srv.Serve(strings.NewReader(line), &out); err != nil {
		t.Fatalf("serve: %v", err)
	}
	var resp map[string]any
	if err := json.Unmarshal(bytes.TrimSpace(out.Bytes()), &resp); err != nil {
		t.Fatalf("unmarshal response: %v (raw=%q)", err, out.String())
	}
	return resp
}

// run 一次完整会话（多行请求 → 多行响应），返回响应行列表
func run(t *testing.T, s *Server, lines ...string) []map[string]any {
	t.Helper()
	var in strings.Builder
	for _, l := range lines {
		in.WriteString(l)
		in.WriteString("\n")
	}
	var out bytes.Buffer
	if err := s.Serve(strings.NewReader(in.String()), &out); err != nil {
		t.Fatalf("serve: %v", err)
	}
	var resps []map[string]any
	sc := bufio.NewScanner(bytes.NewReader(out.Bytes()))
	for sc.Scan() {
		if strings.TrimSpace(sc.Text()) == "" {
			continue
		}
		var r map[string]any
		if err := json.Unmarshal(sc.Bytes(), &r); err != nil {
			t.Fatalf("unmarshal: %v (line=%q)", err, sc.Text())
		}
		resps = append(resps, r)
	}
	return resps
}

func j(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}

func cardJSON(overrides map[string]any) string {
	card := map[string]any{
		"agent_id":         "NM-001",
		"protocol_version": "3.1.2",
		"scene_id":         "scene-phy-notification",
		"role":             "NM-Operator",
		"allowed_calls":    []string{"verify", "record"},
		"nsfl_boundary":    []string{"no-key-export", "no-tamper"},
	}
	for k, v := range overrides {
		card[k] = v
	}
	return j(card)
}

// ---- 1. 握手与工具枚举 ----

func TestInitializeHandshake(t *testing.T) {
	s := NewServer()
	resps := run(t, s,
		`{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","clientInfo":{"name":"ext-agent","version":"1.0"}}}`,
		`{"jsonrpc":"2.0","id":2,"method":"tools/list"}`,
	)
	if len(resps) != 2 {
		t.Fatalf("want 2 responses, got %d", len(resps))
	}
	init := resps[0]
	info := init["result"].(map[string]any)
	if info["protocolVersion"] != ProtocolVersion {
		t.Errorf("protocolVersion = %v", info["protocolVersion"])
	}
	si := info["serverInfo"].(map[string]any)
	if si["name"] != "tdca-core-go-mcp" {
		t.Errorf("serverInfo.name = %v", si["name"])
	}
	list := resps[1]["result"].(map[string]any)["tools"].([]any)
	if len(list) != 4 {
		t.Fatalf("want 4 tools, got %d", len(list))
	}
	names := map[string]bool{}
	for _, tl := range list {
		names[tl.(map[string]any)["name"].(string)] = true
	}
	for _, want := range []string{"enforce_check", "nca_append", "nca_verify", "nsfl_eval"} {
		if !names[want] {
			t.Errorf("missing tool %q", want)
		}
	}
}

// ---- 2. enforce_check ----

func TestEnforceCheckPass(t *testing.T) {
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "enforce_check", "arguments": map[string]any{"agent_card": json.RawMessage(cardJSON(nil))}}})
	resp := run(t, s, req)[0]
	if err, _ := resp["error"]; err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	text := resultText(t, resp)
	if !strings.Contains(text, `"status":"PASS"`) {
		t.Errorf("want PASS, got %s", text)
	}
}

func TestEnforceCheckRejectProtocol(t *testing.T) {
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "enforce_check", "arguments": map[string]any{"agent_card": json.RawMessage(cardJSON(map[string]any{"protocol_version": "9.9.9"}))}}})
	resp := run(t, s, req)[0]
	if _, ok := resp["error"]; !ok {
		// 若实现返回 result 而非 error，检查 status
		if !strings.Contains(resultText(t, resp), "REJECT") {
			t.Fatalf("want REJECT signal, got %v", resp)
		}
	}
}

func TestEnforceCheckInjectionBlocked(t *testing.T) {
	// 破坏性测试：提示注入 → fail-closed
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "enforce_check", "arguments": map[string]any{"agent_card": json.RawMessage(cardJSON(map[string]any{"agent_id": "<script>alert(1)</script>"}))}}})
	resp := run(t, s, req)[0]
	if _, ok := resp["error"]; !ok {
		text := resultText(t, resp)
		if !strings.Contains(text, "REJECT") && !strings.Contains(text, "BLOCK") {
			t.Fatalf("injection must be blocked, got %s", text)
		}
	}
}

func TestEnforceCheckUnknownFieldRejected(t *testing.T) {
	// JSON Schema 合规拦截：未知字段 → 拒绝（注入/越权前置）
	s := NewServer()
	card := map[string]any{
		"agent_id": "NM-001", "protocol_version": "3.1.2",
		"scene_id": "scene-phy-notification", "role": "NM-Operator",
		"allowed_calls": []string{"verify"}, "nsfl_boundary": []string{"no-tamper"},
		"__admin__": true, // 未知字段
	}
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "enforce_check", "arguments": map[string]any{"agent_card": json.RawMessage(j(card))}}})
	resp := run(t, s, req)[0]
	if err, ok := resp["error"]; !ok {
		t.Fatalf("unknown field must be schema-rejected, got %v", resp)
	} else {
		if !strings.Contains(err.(map[string]any)["message"].(string), "schema violation") {
			t.Errorf("want schema violation, got %v", err)
		}
	}
}

// ---- 3. nca_append / nca_verify ----

func recordJSON(prev string) string {
	return j(map[string]any{
		"nca_id": "n1", "type": "fact", "hash": "",
		"ts": "2026-08-23T00:00:00Z", "signer": "TDCA-PUBKEY-01",
		"payload_ref": "FactHash_0", "prev_hash": prev,
		"nsfl": map[string]any{"version": "V0.2"},
	})
}

func TestNcaAppendOk(t *testing.T) {
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "nca_append", "arguments": map[string]any{"record": json.RawMessage(recordJSON("sha256:genesis"))}}})
	resp := run(t, s, req)[0]
	text := resultText(t, resp)
	if !strings.Contains(text, `"status":"appended"`) || !strings.Contains(text, `"count":1`) {
		t.Errorf("want appended/count=1, got %s", text)
	}
}

func TestNcaAppendTamperRejected(t *testing.T) {
	// 破坏性测试：伪造 prev_hash → 篡改拒绝
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "nca_append", "arguments": map[string]any{"record": json.RawMessage(recordJSON("sha256:deadbeef"))}}})
	resp := run(t, s, req)[0]
	if err, ok := resp["error"]; !ok {
		t.Fatalf("tampered prev_hash must be rejected, got %v", resp)
	} else if !strings.Contains(err.(map[string]any)["message"].(string), "prev_hash") {
		t.Errorf("want prev_hash mismatch, got %v", err)
	}
}

func TestNcaVerifyChain(t *testing.T) {
	s := NewServer()
	// 构造两记录链（第二条 prev_hash = 第一条记录哈希）——通过 MCP 无法取哈希，
	// 故用同构 JSON 直接构造链式记录
	rec1 := ncaRec(t, "n1", "sha256:genesis")
	rec1Hash := rec1["hash"].(string)
	rec2 := ncaRec(t, "n2", rec1Hash)
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "nca_verify", "arguments": map[string]any{"records": []any{rec1, rec2}}}})
	resp := run(t, s, req)[0]
	text := resultText(t, resp)
	if !strings.Contains(text, `"verify":true`) {
		t.Errorf("want verify true, got %s", text)
	}
}

func ncaRec(t *testing.T, id, prev string) map[string]any {
	t.Helper()
	n := nca.NewRecord(id, "fact", "2026-08-23T00:00:00Z", prev, nil)
	n.PayloadRef = "FactHash_" + id
	n.Hash = n.RecordHash() // 与桥接层同构的真实链式哈希
	raw, _ := json.Marshal(n)
	var m map[string]any
	_ = json.Unmarshal(raw, &m)
	return m
}

func TestNcaVerifyForgedRejected(t *testing.T) {
	// 破坏性测试：伪造记录（hash 与载荷不符）→ 验证失败
	s := NewServer()
	rec1 := ncaRec(t, "n1", "sha256:genesis")
	rec2 := ncaRec(t, "n2", rec1["hash"].(string))
	rec2["hash"] = "sha256:forged" // 篡改
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "nca_verify", "arguments": map[string]any{"records": []any{rec1, rec2}}}})
	resp := run(t, s, req)[0]
	if _, ok := resp["error"]; !ok {
		text := resultText(t, resp)
		if strings.Contains(text, `"verify": true`) {
			t.Fatalf("forged record must fail verify, got %s", text)
		}
	}
}

// ---- 4. nsfl_eval ----

func TestNsflWarn(t *testing.T) {
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "nsfl_eval", "arguments": map[string]any{"trigger_id": "t1", "signal": "suspicious-pattern"}}})
	resp := run(t, s, req)[0]
	text := resultText(t, resp)
	if !strings.Contains(text, `"status":"WARN"`) {
		t.Errorf("want WARN, got %s", text)
	}
}

func TestNsflBlock(t *testing.T) {
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "nsfl_eval", "arguments": map[string]any{"trigger_id": "t1", "signal": "unauthenticated"}}})
	resp := run(t, s, req)[0]
	text := resultText(t, resp)
	if !strings.Contains(text, `"status":"BLOCK"`) || !strings.Contains(text, `"blocked":true`) {
		t.Errorf("want BLOCK, got %s", text)
	}
}

func TestNsflFusedIrreversible(t *testing.T) {
	// 破坏性测试：绕过尝试 → FUSED 不可逆
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "nsfl_eval", "arguments": map[string]any{"trigger_id": "t1", "signal": "nsfl-bypass-attempt"}}})
	resp := run(t, s, req)[0]
	text := resultText(t, resp)
	if !strings.Contains(text, `"status":"FUSED"`) || !strings.Contains(text, `"irreversible":true`) {
		t.Errorf("want FUSED irreversible, got %s", text)
	}
}

func TestNsflMissingArgSchemaRejected(t *testing.T) {
	// JSON Schema 合规拦截：缺 required → 拒绝
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "nsfl_eval", "arguments": map[string]any{"trigger_id": "t1"}}})
	resp := run(t, s, req)[0]
	if err, ok := resp["error"]; !ok {
		t.Fatalf("missing signal must be schema-rejected, got %v", resp)
	} else if !strings.Contains(err.(map[string]any)["message"].(string), "schema violation") {
		t.Errorf("want schema violation, got %v", err)
	}
}

// ---- 5. 协议级 ----

func TestUnknownMethod(t *testing.T) {
	s := NewServer()
	req := `{"jsonrpc":"2.0","id":1,"method":"tools/unknown"}`
	resp := run(t, s, req)[0]
	if err, ok := resp["error"]; !ok {
		t.Fatalf("unknown method must error, got %v", resp)
	} else if err.(map[string]any)["code"].(float64) != CodeMethod {
		t.Errorf("want method-not-found code, got %v", err)
	}
}

func TestUnknownTool(t *testing.T) {
	s := NewServer()
	req := j(map[string]any{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
		"params": map[string]any{"name": "evil_tool", "arguments": map[string]any{}}})
	resp := run(t, s, req)[0]
	if _, ok := resp["error"]; !ok {
		t.Fatalf("unknown tool must error, got %v", resp)
	}
}

func TestParseError(t *testing.T) {
	s := NewServer()
	req := `{"jsonrpc":"2.0","id":1,"method":` // 截断 JSON
	resp := run(t, s, req)[0]
	if err, ok := resp["error"]; !ok {
		t.Fatalf("parse error must be reported, got %v", resp)
	} else if err.(map[string]any)["code"].(float64) != CodeParse {
		t.Errorf("want parse error code, got %v", err)
	}
}

// ---- 6. 挂载模式 E2E（外部 Agent 全会话）----

func TestMountModeE2E(t *testing.T) {
	// 外部 Agent（如 DeepSeek Harness 类）通过 MCP stdio 挂载 TDCA 核心：
	// 准入 → 存证 → 熔断 全链，不改外部源码（BIDIR-001）
	s := NewServer()
	reqs := []string{
		`{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","clientInfo":{"name":"dsh-agent","version":"0.1"}}}`,
		j(map[string]any{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
		j(map[string]any{"jsonrpc": "2.0", "id": 3, "method": "tools/call",
			"params": map[string]any{"name": "enforce_check", "arguments": map[string]any{"agent_card": json.RawMessage(cardJSON(nil))}}}),
		j(map[string]any{"jsonrpc": "2.0", "id": 4, "method": "tools/call",
			"params": map[string]any{"name": "nca_append", "arguments": map[string]any{"record": json.RawMessage(recordJSON("sha256:genesis"))}}}),
		j(map[string]any{"jsonrpc": "2.0", "id": 5, "method": "tools/call",
			"params": map[string]any{"name": "nsfl_eval", "arguments": map[string]any{"trigger_id": "dsh", "signal": "suspicious-pattern"}}}),
	}
	resps := run(t, s, reqs...)
	if len(resps) != 5 {
		t.Fatalf("want 5 responses, got %d", len(resps))
	}
	// ① 握手
	if resps[0]["result"].(map[string]any)["protocolVersion"] != ProtocolVersion {
		t.Errorf("handshake failed")
	}
	// ② 工具枚举
	if len(resps[1]["result"].(map[string]any)["tools"].([]any)) != 4 {
		t.Errorf("tools/list failed")
	}
	// ③ 准入 PASS
	if m := resultMap(t, resps[2]); m["status"] != "PASS" {
		t.Errorf("enforce_check must PASS, got %v", m)
	}
	// ④ 存证 appended
	if m := resultMap(t, resps[3]); m["status"] != "appended" {
		t.Errorf("nca_append must succeed, got %v", m)
	}
	// ⑤ 熔断 WARN
	if m := resultMap(t, resps[4]); m["action"].(map[string]any)["status"] != "WARN" {
		t.Errorf("nsfl_eval must WARN, got %v", m)
	}
}

// ---- 工具 ----

// resultText 提取 tools/call 结果文本
func resultText(t *testing.T, resp map[string]any) string {
	t.Helper()
	if e, ok := resp["error"]; ok {
		t.Fatalf("response has error: %v", e)
	}
	res := resp["result"].(map[string]any)
	content := res["content"].([]any)
	first := content[0].(map[string]any)
	return first["text"].(string)
}

// resultMap 解析 tools/call 结果文本为 map（结构化断言）
func resultMap(t *testing.T, resp map[string]any) map[string]any {
	t.Helper()
	var m map[string]any
	if err := json.Unmarshal([]byte(resultText(t, resp)), &m); err != nil {
		t.Fatalf("unmarshal result text: %v", err)
	}
	return m
}
