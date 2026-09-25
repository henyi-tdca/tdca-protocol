// 租户与环境作用域凭证绑定（条例《租户与环境作用域凭证绑定条例》落地，
// 交办件 TDCA-HANDOFF-EXEC-TENANT-CRED-BIND-IMPL-001）：
//   - R1 来源唯一：会话作用域授权来源 = 网关认证上下文绑定（按 token_id 取），
//     请求参数 _meta.tdca.pcr_token.scope 永不作授权来源，仅作收窄请求（R3 入参）。
//   - R2 规格洁净：工具 inputSchema 字段名不得含租户/环境标识，命中即拒绝装载。
//   - R3 单调收窄：作用域只收窄放行，填宽一律拒绝（scope-widening），冲突以凭证为准。
//
// fail-closed：未配认证提供者 / 绑定查无 / 不可判一律拒绝。
//
// SPDX-License-Identifier: Apache-2.0
package mcp

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"
	"sync"
	"unicode"
)

// ---- 拒绝子码（条例新增；风格对齐 session.go 常量区，随 error message 与事件存证）----

const (
	ReasonCredentialUnbound = "credential-unbound" // 未配网关认证提供者 / 绑定查无（R1 fail-closed）
	ReasonScopeWidening     = "scope-widening"     // 请求作用域填宽（真超集）一律拒绝（R3）
)

// ---- 凭证绑定（网关认证上下文投影；token 值本体永不入层）----

// CredBinding 网关侧认证上下文中的凭证绑定
type CredBinding struct {
	TenantID string   // 租户标识
	Env      string   // 环境标识
	Scope    []string // 网关绑定的会话作用域（授权唯一来源，R1）
}

// GatewayAuthProvider 网关认证上下文接口（按 token_id 取绑定）
type GatewayAuthProvider interface {
	Binding(tokenID string) (CredBinding, bool)
}

// StaticGatewayAuth 静态绑定表（map 注入实现 GatewayAuthProvider；Serve 前完成注册）
type StaticGatewayAuth struct {
	mu       sync.RWMutex
	bindings map[string]CredBinding
}

// NewStaticGatewayAuth 构造空绑定表
func NewStaticGatewayAuth() *StaticGatewayAuth {
	return &StaticGatewayAuth{bindings: map[string]CredBinding{}}
}

// Bind 注册 token_id → 凭证绑定
func (g *StaticGatewayAuth) Bind(tokenID string, b CredBinding) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.bindings[tokenID] = b
}

// Binding 取绑定（GatewayAuthProvider 实现）
func (g *StaticGatewayAuth) Binding(tokenID string) (CredBinding, bool) {
	g.mu.RLock()
	defer g.mu.RUnlock()
	b, ok := g.bindings[tokenID]
	return b, ok
}

// Len 绑定数（装配日志用；只出计数，不出任何 token_id 或凭据值）
func (g *StaticGatewayAuth) Len() int {
	g.mu.RLock()
	defer g.mu.RUnlock()
	return len(g.bindings)
}

// ---- 本地配置源装载（GSEQ-2815：tdcad 启动时装配认证源）----

// gatewayAuthFile 本地配置源文件格式（严格解析：DisallowUnknownFields，
// 任何额外字段——含 token/secret/value 之类凭据字面字段——结构性拒绝，
// 这是凭据纪律的机械防线：token_id 是标识符，凭据本体永不入码/入仓/入日志）
type gatewayAuthFile struct {
	Bindings []gatewayAuthFileBinding `json:"bindings"`
}

type gatewayAuthFileBinding struct {
	TokenID  string   `json:"token_id"`
	TenantID string   `json:"tenant_id"`
	Env      string   `json:"env"`
	Scope    []string `json:"scope"`
}

// LoadStaticGatewayAuthFile 从本地配置源 JSON 文件装载静态绑定表。
//
// 信任等级标注：本地配置源下，条例 R1 之「已验证」由部署侧保证（非网关侧）——
// 网关侧只负责按 token_id 取绑定并 fail-closed，不验证凭据本体真伪。
//
// 校验（全部 fail-closed，错误信息只报字段名与序号，不回显文件内容值）：
//   - 文件不可读 / JSON 畸形 → 错
//   - token_id 空 → 错；scope 空 → 错；token_id 重复 → 错
//   - 未知字段（含任何凭据字面字段）→ DisallowUnknownFields 结构性拒绝
func LoadStaticGatewayAuthFile(path string) (*StaticGatewayAuth, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("gateway-auth: file unreadable: %v", err)
	}
	defer f.Close()
	dec := json.NewDecoder(f)
	dec.DisallowUnknownFields()
	var doc gatewayAuthFile
	if err := dec.Decode(&doc); err != nil {
		var se *json.SyntaxError
		if errors.As(err, &se) {
			// 语法错只报字节偏移，不回显文件内容
			return nil, fmt.Errorf("gateway-auth: malformed JSON at byte offset %d", se.Offset)
		}
		// 未知字段/类型错：encoding/json 只含字段名与类型，不含值
		return nil, fmt.Errorf("gateway-auth: %v", err)
	}
	if err := dec.Decode(&struct{}{}); err != io.EOF {
		return nil, fmt.Errorf("gateway-auth: malformed JSON: unexpected trailing data")
	}
	g := NewStaticGatewayAuth()
	seen := map[string]int{}
	for i, b := range doc.Bindings {
		if b.TokenID == "" {
			return nil, fmt.Errorf("gateway-auth: bindings[%d].token_id is empty", i)
		}
		if len(b.Scope) == 0 {
			return nil, fmt.Errorf("gateway-auth: bindings[%d].scope is empty", i)
		}
		if first, dup := seen[b.TokenID]; dup {
			return nil, fmt.Errorf("gateway-auth: bindings[%d].token_id duplicates bindings[%d]", i, first)
		}
		seen[b.TokenID] = i
		g.Bind(b.TokenID, CredBinding{TenantID: b.TenantID, Env: b.Env, Scope: b.Scope})
	}
	return g, nil
}

// ---- R2 规格洁净 ----

// specForbiddenWords 规格字段名禁用词表（租户/环境标识；切词后小写化整词比对，
// 既有契约字段 scene / scene_id 不在词表内，不误伤）
var specForbiddenWords = map[string]bool{
	"tenant":       true,
	"env":          true,
	"environment":  true,
	"workspace":    true,
	"org":          true,
	"organization": true,
}

// CheckSpecClean R2 规格洁净检查：递归遍历 inputSchema 的 Properties 键名，
// 键名按非字母字符与驼峰边界切词（小写化比对），命中禁用词表即返回错误（报字段路径）。
// 确定性：每层键名排序后遍历，同输入同输出逐字节一致（A-3）。
func CheckSpecClean(s *Schema) error {
	if s == nil {
		return nil
	}
	return checkSpecClean(s, "")
}

func checkSpecClean(s *Schema, prefix string) error {
	keys := make([]string, 0, len(s.Properties))
	for k := range s.Properties {
		keys = append(keys, k)
	}
	sort.Strings(keys) // map 遍历序不定，排序保证确定性
	for _, k := range keys {
		path := k
		if prefix != "" {
			path = prefix + "." + k
		}
		for _, w := range splitFieldWords(k) {
			if specForbiddenWords[w] {
				return fmt.Errorf("spec-clean: field %q contains tenant/env identifier %q", path, w)
			}
		}
		if err := checkSpecClean(s.Properties[k], path); err != nil {
			return err
		}
	}
	return nil
}

// splitFieldWords 键名切词：非字母字符分界 + 驼峰边界（小写→大写），产物小写化。
// 例：tenant_id → [tenant id]；tenantId → [tenant id]；TenantID → [tenant id]。
func splitFieldWords(name string) []string {
	var words []string
	var cur []rune
	flush := func() {
		if len(cur) > 0 {
			words = append(words, strings.ToLower(string(cur)))
			cur = cur[:0]
		}
	}
	prevLower := false
	for _, r := range name {
		if !unicode.IsLetter(r) {
			flush()
			prevLower = false
			continue
		}
		if unicode.IsUpper(r) && prevLower {
			flush()
		}
		cur = append(cur, r)
		prevLower = unicode.IsLower(r)
	}
	flush()
	return words
}

// ---- R3 单调收窄 ----

// ResolveScope 单调收窄裁决（集合比较均排序去重后判，A-3 确定性）：
//   - requested 为空 → effective = credScope（绑定推导放行）
//   - requested ⊆ credScope → effective = requested（收窄放行）
//   - requested 为 credScope 真超集（含全部元素且有额外，填宽）→ 拒 scope-widening
//   - 其余不可比冲突 → 以凭证（网关绑定）为准，effective = credScope
func ResolveScope(credScope, requested []string) ([]string, *SessionGateError) {
	cred := normScope(credScope)
	req := normScope(requested)
	if len(req) == 0 {
		return cred, nil
	}
	if subsetOf(req, cred) {
		return req, nil
	}
	if subsetOf(cred, req) {
		return nil, &SessionGateError{Code: ReasonScopeWidening,
			Detail: "requested scope widens credential binding (monotonic narrowing only)"}
	}
	return cred, nil
}

// normScope 排序去重（不动入参切片）
func normScope(in []string) []string {
	set := map[string]bool{}
	out := make([]string, 0, len(in))
	for _, s := range in {
		if !set[s] {
			set[s] = true
			out = append(out, s)
		}
	}
	sort.Strings(out)
	return out
}

// subsetOf a ⊆ b（集合语义；空集是任意集子集）
func subsetOf(a, b []string) bool {
	set := make(map[string]bool, len(b))
	for _, x := range b {
		set[x] = true
	}
	for _, x := range a {
		if !set[x] {
			return false
		}
	}
	return true
}

// ---- 规格自扫支撑（credbind-check selftest 用）----

// Tools 已注册工具声明（按名排序，确定性输出；规格自扫/自检用）
func (s *Server) Tools() []Tool {
	s.mu.Lock()
	defer s.mu.Unlock()
	names := make([]string, 0, len(s.cards))
	for n := range s.cards {
		names = append(names, n)
	}
	sort.Strings(names)
	out := make([]Tool, 0, len(names))
	for _, n := range names {
		out = append(out, *s.cards[n])
	}
	return out
}
