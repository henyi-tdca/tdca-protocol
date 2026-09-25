// 条例《租户与环境作用域凭证绑定条例》进程内断言（交办件
// TDCA-HANDOFF-EXEC-TENANT-CRED-BIND-IMPL-001）：
//   - A-1 规格洁净：Register 拒绝含租户/环境标识字段的规格（含嵌套），洁净规格放行
//   - A-2 来源唯一：scope 授权来源 = 网关绑定；请求 scope 不作授权来源
//   - A-4 单调收窄：收窄放行 / 填宽拒 scope-widening / 冲突以凭证为准
//
// CLI 侧样本（用法/路径/零扫描/违规/自扫/A-3 确定性）见 cmd/credbind-check/main_test.go。
//
// SPDX-License-Identifier: Apache-2.0
package mcp

import (
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func okHandler(args map[string]any) (any, error) { return map[string]any{"ok": true}, nil }

// ---- A-1 规格洁净：租户/环境标识字段 → Register 拒绝装载 ----

func TestCB1SpecCleanRegister(t *testing.T) {
	s := newTestServer()
	// 顶层字段 tenant_id → 拒
	err := s.Register(Tool{
		Name: "evil_tenant",
		InputSchema: &Schema{Type: "object", Properties: map[string]*Schema{
			"tenant_id": {Type: "string"},
		}},
	}, okHandler)
	if err == nil || !strings.Contains(err.Error(), "tenant_id") {
		t.Fatalf("tenant_id spec must be rejected with field path, got %v", err)
	}
	// 嵌套 Properties 命中（驼峰 workspaceId → 词 workspace）→ 拒，报嵌套路径
	err = s.Register(Tool{
		Name: "evil_nested",
		InputSchema: &Schema{Type: "object", Properties: map[string]*Schema{
			"outer": {Type: "object", Properties: map[string]*Schema{
				"workspaceId": {Type: "string"},
			}},
		}},
	}, okHandler)
	if err == nil || !strings.Contains(err.Error(), "outer.workspaceId") {
		t.Fatalf("nested violation must report field path, got %v", err)
	}
	// 被拒工具未装载
	for _, tl := range s.Tools() {
		if tl.Name == "evil_tenant" || tl.Name == "evil_nested" {
			t.Fatalf("rejected tool must not be registered: %s", tl.Name)
		}
	}
	// 洁净规格放行（含既有契约字段 scene_id / record——不误伤）
	err = s.Register(Tool{
		Name: "clean_tool",
		InputSchema: &Schema{Type: "object", Properties: map[string]*Schema{
			"scene_id": {Type: "string"},
			"record":   {Type: "object"},
		}},
	}, okHandler)
	if err != nil {
		t.Fatalf("clean spec must register, got %v", err)
	}
	// 误伤率：4 件核心工具规格无命中（registerCoreTools 全部装载成功）
	names := map[string]bool{}
	for _, tl := range s.Tools() {
		names[tl.Name] = true
	}
	for _, want := range []string{"enforce_check", "nca_append", "nca_verify", "nsfl_eval", "clean_tool"} {
		if !names[want] {
			t.Errorf("tool %q missing after spec-clean gate (false positive?)", want)
		}
	}
}

// CheckSpecClean 单元级：词表命中与切词边界（scene / scene_id / envelope 不误伤）
func TestCB1CheckSpecCleanUnit(t *testing.T) {
	cases := []struct {
		field   string
		wantHit bool
	}{
		{"tenant", true}, {"tenantId", true}, {"TenantID", true}, {"env", true},
		{"environment", true}, {"workspace", true}, {"org", true}, {"organization_id", true},
		{"scene", false}, {"scene_id", false}, {"envelope", false}, {"organizer", false},
		{"record", false}, {"agent_card", false},
	}
	for _, c := range cases {
		s := &Schema{Type: "object", Properties: map[string]*Schema{c.field: {Type: "string"}}}
		err := CheckSpecClean(s)
		if c.wantHit && err == nil {
			t.Errorf("field %q must hit forbidden word", c.field)
		}
		if !c.wantHit && err != nil {
			t.Errorf("field %q must NOT hit (false positive): %v", c.field, err)
		}
	}
}

// ---- A-2 来源唯一：scope 授权来源 = 网关绑定，请求参数永不作授权来源 ----

func TestCB2ScopeFromBindingOnly(t *testing.T) {
	// 样本4·正例：有绑定且请求【不带】scope → 握手建立，Session.Scope == 绑定 Scope（绑定推导放行）
	s := newTestServer() // tok-test-01 绑定 Scope=["mcp"]
	meta := tdcaMetaJSON(map[string]any{
		"pcr_token": map[string]any{"token_id": "tok-test-01"}, // 请求不带 scope
	})
	resps := run(t, s, initReq(1, meta), initializedNotif)
	if e, ok := resps[0]["error"]; ok {
		t.Fatalf("bound credential handshake must pass, got %v", e)
	}
	sess := s.Session()
	if sess == nil || !reflect.DeepEqual(sess.Scope, []string{"mcp"}) {
		t.Fatalf("Session.Scope must equal bound scope [mcp], got %+v", sess)
	}
	// 请求 scope 与绑定不一致但可比收窄（["mcp"] ⊆ ["mcp"]）→ 照常放行（走默认 meta 夹具）
	s1 := newTestServer()
	if e, ok := run(t, s1, initReq(1, tdcaMetaJSON(nil)), initializedNotif)[0]["error"]; ok {
		t.Fatalf("equal scope must pass, got %v", e)
	}
	// 无绑定但请求带 scope ["mcp"]（旧语义的授权来源）→ 拒 credential-unbound（R1 来源唯一）
	s2 := NewServer() // 未注入 GatewayAuthProvider
	meta2 := tdcaMetaJSON(map[string]any{
		"pcr_token": map[string]any{"token_id": "tok-unknown", "scope": []string{"mcp"}},
	})
	resps2 := run(t, s2, initReq(1, meta2))
	if msg := errMsg(t, resps2[0]); !strings.Contains(msg, "tdca/session:"+ReasonCredentialUnbound) {
		t.Fatalf("unbound credential must reject credential-unbound, got %q", msg)
	}
	if s2.Session() != nil {
		t.Errorf("session must not be established")
	}
	rej := s2.RejectedEvents()
	if len(rej) != 1 || rej[0].Reason != ReasonCredentialUnbound || rej[0].TokenID != "tok-unknown" {
		t.Errorf("session_rejected must record credential-unbound + token_id only, got %+v", rej)
	}
	// 已注入 provider 但 token 查无绑定 → 同样 credential-unbound（fail-closed）
	s3 := newTestServer()
	meta3 := tdcaMetaJSON(map[string]any{
		"pcr_token": map[string]any{"token_id": "tok-no-binding", "scope": []string{"mcp"}},
	})
	if msg := errMsg(t, run(t, s3, initReq(1, meta3))[0]); !strings.Contains(msg, ReasonCredentialUnbound) {
		t.Fatalf("missing binding must reject credential-unbound, got %q", msg)
	}
}

// ---- A-4 单调收窄：ResolveScope 单元裁决 ----

func TestCB4ResolveScope(t *testing.T) {
	cred := []string{"mcp", "nca"}
	// 空请求 → 绑定推导
	eff, ge := ResolveScope(cred, nil)
	if ge != nil || !reflect.DeepEqual(eff, []string{"mcp", "nca"}) {
		t.Errorf("empty requested must yield cred scope, got %v/%v", eff, ge)
	}
	// 子集收窄 → 放行且 effective=requested
	eff, ge = ResolveScope(cred, []string{"nca"})
	if ge != nil || !reflect.DeepEqual(eff, []string{"nca"}) {
		t.Errorf("narrowing must pass with effective=requested, got %v/%v", eff, ge)
	}
	// 真超集（填宽）→ 拒 scope-widening
	_, ge = ResolveScope(cred, []string{"mcp", "nca", "admin"})
	if ge == nil || ge.Code != ReasonScopeWidening {
		t.Errorf("widening must reject scope-widening, got %v", ge)
	}
	// 不可比冲突 → 以凭证为准
	eff, ge = ResolveScope(cred, []string{"other"})
	if ge != nil || !reflect.DeepEqual(eff, []string{"mcp", "nca"}) {
		t.Errorf("incomparable conflict must fall back to credential scope, got %v/%v", eff, ge)
	}
	// 排序去重（A-3 确定性）：乱序重复输入 → 稳定输出
	eff, ge = ResolveScope([]string{"nca", "mcp", "mcp"}, []string{"mcp", "nca"})
	if ge != nil || !reflect.DeepEqual(eff, []string{"mcp", "nca"}) {
		t.Errorf("set compare must be sorted+deduped, got %v/%v", eff, ge)
	}
	// 空凭证 + 非空请求 = 填宽（空集 ⊆ 任意集）→ 拒
	if _, ge = ResolveScope(nil, []string{"mcp"}); ge == nil || ge.Code != ReasonScopeWidening {
		t.Errorf("requesting scope over empty binding must reject scope-widening, got %v", ge)
	}
}

// ---- 样本5·参数填宽负例（session 级）：握手请求 scope 填宽 → 拒 scope-widening ----

func TestCB4HandshakeScopeWideningRejected(t *testing.T) {
	s := newTestServer() // tok-test-01 绑定 Scope=["mcp"]
	meta := tdcaMetaJSON(map[string]any{
		"pcr_token": map[string]any{"token_id": "tok-test-01", "scope": []string{"mcp", "admin"}},
	})
	resps := run(t, s, initReq(1, meta))
	if msg := errMsg(t, resps[0]); !strings.Contains(msg, "tdca/session:"+ReasonScopeWidening) {
		t.Fatalf("scope widening at handshake must reject scope-widening, got %q", msg)
	}
	if s.Session() != nil {
		t.Errorf("session must not be established")
	}
	rej := s.RejectedEvents()
	if len(rej) != 1 || rej[0].Reason != ReasonScopeWidening {
		t.Errorf("session_rejected must record scope-widening, got %+v", rej)
	}
}

// ---- GSEQ-2815 本地配置源装载：LoadStaticGatewayAuthFile ----

// writeAuthFile 写临时认证源文件（测试辅助）
func writeAuthFile(t *testing.T, content string) string {
	t.Helper()
	p := filepath.Join(t.TempDir(), "gateway-auth.json")
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return p
}

func TestLoadStaticGatewayAuthFileOK(t *testing.T) {
	// 合法文件加载成功且绑定可查
	p := writeAuthFile(t, `{"bindings":[{"token_id":"ext-agent-demo","tenant_id":"tenant-bridge-test","env":"env-test","scope":["mcp"]}]}`)
	g, err := LoadStaticGatewayAuthFile(p)
	if err != nil {
		t.Fatalf("valid file must load, got %v", err)
	}
	if g.Len() != 1 {
		t.Fatalf("expected 1 binding, got %d", g.Len())
	}
	b, ok := g.Binding("ext-agent-demo")
	if !ok {
		t.Fatal("binding for ext-agent-demo must be found")
	}
	if b.TenantID != "tenant-bridge-test" || b.Env != "env-test" || !reflect.DeepEqual(b.Scope, []string{"mcp"}) {
		t.Fatalf("binding mismatch: %+v", b)
	}
	if _, ok := g.Binding("no-such-token"); ok {
		t.Fatal("unknown token_id must not have a binding")
	}
}

func TestLoadStaticGatewayAuthFileUnknownFieldRejected(t *testing.T) {
	// 未知字段（凭据字面字段 token_value）→ DisallowUnknownFields 结构性拒绝；
	// 错误含字段名，不含文件内容值
	p := writeAuthFile(t, `{"bindings":[{"token_id":"x","tenant_id":"t","env":"e","scope":["mcp"],"token_value":"s3cr3t"}]}`)
	_, err := LoadStaticGatewayAuthFile(p)
	if err == nil || !strings.Contains(err.Error(), "token_value") {
		t.Fatalf("unknown credential-literal field must be rejected with field name, got %v", err)
	}
	if strings.Contains(err.Error(), "s3cr3t") {
		t.Fatalf("error must not echo file content value, got %v", err)
	}
	// 顶层未知字段同样拒
	p2 := writeAuthFile(t, `{"bindings":[],"secret":"x"}`)
	if _, err := LoadStaticGatewayAuthFile(p2); err == nil || !strings.Contains(err.Error(), "secret") {
		t.Fatalf("top-level unknown field must be rejected, got %v", err)
	}
}

func TestLoadStaticGatewayAuthFileNotExist(t *testing.T) {
	_, err := LoadStaticGatewayAuthFile(filepath.Join(t.TempDir(), "no-such-file.json"))
	if err == nil {
		t.Fatal("missing file must error")
	}
}

func TestLoadStaticGatewayAuthFileMalformed(t *testing.T) {
	p := writeAuthFile(t, `{"bindings":[{broken`)
	if _, err := LoadStaticGatewayAuthFile(p); err == nil {
		t.Fatal("malformed JSON must error")
	}
}

func TestLoadStaticGatewayAuthFileValidation(t *testing.T) {
	cases := []struct {
		name    string
		content string
		want    string // 错误信息须含的字段名/序号定位
	}{
		{"token_id empty", `{"bindings":[{"token_id":"","tenant_id":"t","env":"e","scope":["mcp"]}]}`, "bindings[0].token_id"},
		{"scope empty", `{"bindings":[{"token_id":"x","tenant_id":"t","env":"e","scope":[]}]}`, "bindings[0].scope"},
		{"token_id dup", `{"bindings":[{"token_id":"x","tenant_id":"t","env":"e","scope":["mcp"]},{"token_id":"x","tenant_id":"t2","env":"e2","scope":["mcp"]}]}`, "duplicates bindings[0]"},
	}
	for _, c := range cases {
		p := writeAuthFile(t, c.content)
		_, err := LoadStaticGatewayAuthFile(p)
		if err == nil || !strings.Contains(err.Error(), c.want) {
			t.Errorf("%s: must reject with %q in error, got %v", c.name, c.want, err)
		}
	}
}
