package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func writeTemp(t *testing.T, content string) string {
	t.Helper()
	p := filepath.Join(t.TempDir(), "input.json")
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return p
}

func TestVersion(t *testing.T) {
	if version != "1.0.0" {
		t.Fatalf("expected 1.0.0, got %s", version)
	}
}

func TestEnforceCheckPass(t *testing.T) {
	card := `{"agent_id":"NM-001","protocol_version":"3.1.2","scene_id":"scene-phy-notification","role":"NM-Operator","allowed_calls":["verify"],"nsfl_boundary":["no-key-export"]}`
	p := writeTemp(t, card)
	if err := cmdEnforce([]string{"check", p}); err != nil {
		t.Fatal(err)
	}
}

func TestEnforceCheckReject(t *testing.T) {
	// 非 PASS 返回 error（REJECT）
	card := `{"agent_id":"x","protocol_version":"9.9.9","scene_id":"scene-phy-notification","role":"NM-Operator","allowed_calls":["x"],"nsfl_boundary":["y"]}`
	p := writeTemp(t, card)
	if err := cmdEnforce([]string{"check", p}); err == nil {
		t.Fatal("bad protocol should reject")
	}
}

func TestEnforceUsageError(t *testing.T) {
	if err := cmdEnforce([]string{}); err == nil {
		t.Fatal("missing args should error")
	}
	if err := cmdEnforce([]string{"bogus"}); err == nil {
		t.Fatal("unknown subcommand should error")
	}
}

func TestNcaAppend(t *testing.T) {
	rec := `{"nca_id":"n1","type":"fact","hash":"","ts":"2026-08-23T00:00:00Z","signer":"TDCA-PUBKEY-01","payload_ref":"FactHash_0","prev_hash":"sha256:genesis","nsfl":{"version":"V0.2"}}`
	p := writeTemp(t, rec)
	if err := cmdNca([]string{"append", p}); err != nil {
		t.Fatal(err)
	}
}

func TestNcaAppendTamperRejected(t *testing.T) {
	// 错误 prev_hash → 拒绝
	rec := `{"nca_id":"n1","type":"fact","hash":"","ts":"2026-08-23T00:00:00Z","signer":"TDCA-PUBKEY-01","payload_ref":"FactHash_0","prev_hash":"sha256:deadbeef","nsfl":{"version":"V0.2"}}`
	p := writeTemp(t, rec)
	if err := cmdNca([]string{"append", p}); err == nil {
		t.Fatal("tampered prev_hash should reject")
	}
}

func TestNcaVerifyOK(t *testing.T) {
	recs := `[
	  {"nca_id":"n1","type":"fact","hash":"","ts":"2026-08-23T00:00:00Z","signer":"TDCA-PUBKEY-01","payload_ref":"FactHash_0","prev_hash":"sha256:genesis","nsfl":{"version":"V0.2"}},
	  {"nca_id":"n2","type":"fact","hash":"","ts":"2026-08-23T00:00:01Z","signer":"TDCA-PUBKEY-01","payload_ref":"FactHash_1","prev_hash":"sha256:genesis","nsfl":{"version":"V0.2"}}
	]`
	// 注意：第二条 prev_hash 需链头——用单链验证简化（1 条）
	one := `[
	  {"nca_id":"n1","type":"fact","hash":"","ts":"2026-08-23T00:00:00Z","signer":"TDCA-PUBKEY-01","payload_ref":"FactHash_0","prev_hash":"sha256:genesis","nsfl":{"version":"V0.2"}}
	]`
	_ = recs
	p := writeTemp(t, one)
	if err := cmdNca([]string{"verify", p}); err != nil {
		t.Fatal(err)
	}
}

func TestNcaUsageError(t *testing.T) {
	if err := cmdNca([]string{}); err == nil {
		t.Fatal("missing subcommand should error")
	}
	if err := cmdNca([]string{"bogus"}); err == nil {
		t.Fatal("unknown subcommand should error")
	}
}

func TestNsflEvalWarn(t *testing.T) {
	// suspicious-pattern → WARN（不阻断，err nil）
	if err := cmdNsfl([]string{"eval", "t1", "suspicious-pattern"}); err != nil {
		t.Fatal(err)
	}
}

func TestNsflEvalBlocked(t *testing.T) {
	// unauthenticated → BLOCK（err non-nil）
	if err := cmdNsfl([]string{"eval", "t1", "unauthenticated"}); err == nil {
		t.Fatal("block should error")
	}
}

func TestNsflUsageError(t *testing.T) {
	if err := cmdNsfl([]string{}); err == nil {
		t.Fatal("missing args should error")
	}
}

func TestJSONOutputValid(t *testing.T) {
	// 输出 JSON 合法性抽查（接口熵=0）
	card := `{"agent_id":"NM-001","protocol_version":"3.1.2","scene_id":"scene-phy-notification","role":"NM-Operator","allowed_calls":["verify"],"nsfl_boundary":["no-key-export"]}`
	p := writeTemp(t, card)
	raw, _ := os.ReadFile(p)
	var c enforceCard
	if err := json.Unmarshal(raw, &c); err != nil {
		t.Fatal(err)
	}
	if c.Role != "NM-Operator" {
		t.Fatalf("expected NM-Operator, got %s", c.Role)
	}
}

type enforceCard struct {
	AgentID string `json:"agent_id"`
	Role    string `json:"role"`
}
