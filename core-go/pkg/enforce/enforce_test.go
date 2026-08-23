package enforce

import (
	"encoding/json"
	"strings"
	"testing"
)

func validCard() []byte {
	card := AgentCard{
		AgentID: "NM-001", ProtocolVer: "3.1.2", SceneID: "scene-phy-notification",
		Role: "NM-Operator", AllowedCalls: []string{"verify", "record"},
		NSFLBoundary: []string{"no-key-export", "no-tamper"},
	}
	b, _ := json.Marshal(card)
	return b
}

func TestEntryPass(t *testing.T) {
	g := NewEntryGate()
	res, err := g.Apply(validCard())
	if err != nil || res.Status != "PASS" {
		t.Fatalf("expected PASS, got %s err=%v", res.Status, err)
	}
	if len(res.Checks) != 5 {
		t.Fatalf("expected 5 checks, got %d", len(res.Checks))
	}
}

func TestEntryRejectBadProtocol(t *testing.T) {
	g := NewEntryGate()
	raw := strings.Replace(string(validCard()), "3.1.2", "9.9.9", 1)
	res, err := g.Apply([]byte(raw))
	if err == nil || res.Status != "REJECT" {
		t.Fatalf("expected REJECT, got %s", res.Status)
	}
}

// 破坏性测试：提示注入（越权调用意图）→ fail-closed
func TestEntryInjectionFailClosed(t *testing.T) {
	g := NewEntryGate()
	cases := []string{
		`{"agent_id":"<script>alert(1)</script>","protocol_version":"3.1.2","scene_id":"scene-phy-notification","role":"NM-Operator","allowed_calls":["x"],"nsfl_boundary":["y"]}`,
		`{"agent_id":"DROP TABLE nca;--","protocol_version":"3.1.2","scene_id":"scene-phy-notification","role":"NM-Operator","allowed_calls":["x"],"nsfl_boundary":["y"]}`,
	}
	for _, c := range cases {
		_, err := g.Apply([]byte(c))
		if err == nil {
			t.Fatalf("injection should be rejected: %s", c)
		}
	}
}

// 破坏性测试：未知字段注入（DisallowUnknownFields）→ 拒绝
func TestEntryUnknownFieldRejected(t *testing.T) {
	g := NewEntryGate()
	raw := `{"agent_id":"a","protocol_version":"3.1.2","scene_id":"scene-phy-notification","role":"NM-Operator","allowed_calls":["x"],"nsfl_boundary":["y"],"evil":"pwn"}`
	_, err := g.Apply([]byte(raw))
	if err == nil {
		t.Fatal("unknown field should be rejected")
	}
}

// 破坏性测试：无负空间边界（fail-closed）→ BLOCK
func TestEntryMissingNSFLBlocked(t *testing.T) {
	g := NewEntryGate()
	raw := `{"agent_id":"a","protocol_version":"3.1.2","scene_id":"scene-phy-notification","role":"NM-Operator","allowed_calls":["x"],"nsfl_boundary":[]}`
	res, err := g.Apply([]byte(raw))
	if err == nil || res.Status != "BLOCK" {
		t.Fatalf("expected BLOCK (fail-closed), got %s", res.Status)
	}
}

func TestEntryRejectBadRole(t *testing.T) {
	g := NewEntryGate()
	raw := strings.Replace(string(validCard()), "NM-Operator", "HACKER", 1)
	res, err := g.Apply([]byte(raw))
	if err == nil || res.Status != "REJECT" {
		t.Fatalf("expected REJECT, got %s", res.Status)
	}
}

func TestEntryOversizeRejected(t *testing.T) {
	g := NewEntryGate()
	big := make([]byte, 9000)
	_, err := g.Apply(big)
	if err == nil {
		t.Fatal("oversize should be rejected")
	}
}
