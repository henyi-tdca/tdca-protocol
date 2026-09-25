// credbind-check CLI 测试：A-3 确定性 + 七类样本中的 CLI 类（用法/路径/零扫描/违规/自扫）。
// 注：Run 在 main 包，Go 不允许跨包导入 main，故 CLI 测试与本包同目录（包内测试）。
// SPDX-License-Identifier: Apache-2.0
package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// writeSpec 造样本规格件（t.TempDir() 内）
func writeSpec(t *testing.T, dir, fileName, content string) string {
	t.Helper()
	p := filepath.Join(dir, fileName)
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatalf("write spec: %v", err)
	}
	return p
}

const (
	cleanSpecJSON = `{"name":"clean_tool","inputSchema":{"type":"object","properties":{
		"scene_id":{"type":"string"},"record":{"type":"object"}},"additionalProperties":false}}`
	dirtySpecJSON = `{"name":"evil_tool","inputSchema":{"type":"object","properties":{
		"tenant_id":{"type":"string"}},"additionalProperties":false}}`
)

// ---- 样本1：空输入（Run 无参数）→ exit 2 ----

func TestRunUsageError(t *testing.T) {
	out, code := Run(nil)
	if code != exitUsage {
		t.Fatalf("empty args must exit %d, got %d (out=%q)", exitUsage, code, out)
	}
	if !strings.Contains(out, "usage:") {
		t.Errorf("usage error must print usage, got %q", out)
	}
}

// ---- 样本2：目标路径不存在 → exit 3 ----

func TestRunMissingPath(t *testing.T) {
	out, code := Run([]string{filepath.Join(t.TempDir(), "no-such-dir")})
	if code != exitNoTarget {
		t.Fatalf("missing path must exit %d, got %d (out=%q)", exitNoTarget, code, out)
	}
	if !strings.Contains(out, "not found") {
		t.Errorf("missing path must say not found, got %q", out)
	}
}

// ---- 样本3：零扫描（空目录）→ exit 4 ----

func TestRunZeroScan(t *testing.T) {
	out, code := Run([]string{t.TempDir()})
	if code != exitZeroScan {
		t.Fatalf("zero-scan must exit %d, got %d (out=%q)", exitZeroScan, code, out)
	}
	if !strings.Contains(out, "ZERO-SCAN") {
		t.Errorf("zero-scan must be marked, got %q", out)
	}
	// 目录里只有非规格 JSON → 同样零扫描
	dir := t.TempDir()
	writeSpec(t, dir, "config.json", `{"key":"value"}`)
	_, code = Run([]string{dir})
	if code != exitZeroScan {
		t.Fatalf("non-spec json must count as zero-scan (exit %d), got %d", exitZeroScan, code)
	}
}

// ---- 样本6b：规格含租户标识 → exit 5 ----

func TestRunViolationFail(t *testing.T) {
	dir := t.TempDir()
	writeSpec(t, dir, "evil.json", dirtySpecJSON)
	writeSpec(t, dir, "clean.json", cleanSpecJSON)
	out, code := Run([]string{dir})
	if code != exitCheckFail {
		t.Fatalf("violation must exit %d, got %d (out=%q)", exitCheckFail, code, out)
	}
	if !strings.Contains(out, "VIOLATION") || !strings.Contains(out, "tenant_id") ||
		!strings.Contains(out, "CHECK FAIL") {
		t.Errorf("violation output mismatch: %q", out)
	}
}

// ---- 规格洁净目录 → exit 0 ----

func TestRunCleanPass(t *testing.T) {
	dir := t.TempDir()
	writeSpec(t, dir, "a.json", cleanSpecJSON)
	sub := filepath.Join(dir, "sub")
	if err := os.MkdirAll(sub, 0o755); err != nil {
		t.Fatal(err)
	}
	writeSpec(t, sub, "b.json", cleanSpecJSON) // 递归扫描覆盖子目录
	out, code := Run([]string{dir})
	if code != exitPass {
		t.Fatalf("clean dir must exit %d, got %d (out=%q)", exitPass, code, out)
	}
	if !strings.Contains(out, "scanned 2 tool spec(s)") || !strings.Contains(out, "CHECK PASS") {
		t.Errorf("clean output mismatch: %q", out)
	}
}

// ---- 样本7：自扫 selftest → exit 0 且 0 命中（误伤率闸门）----

func TestRunSelftest(t *testing.T) {
	out, code := Run([]string{"selftest"})
	if code != exitPass {
		t.Fatalf("selftest must exit %d, got %d (out=%q)", exitPass, code, out)
	}
	if !strings.Contains(out, "0 violation(s)") || !strings.Contains(out, "CHECK PASS") {
		t.Errorf("selftest must report 0 violations, got %q", out)
	}
}

// ---- A-3 确定性：同输入连续两遍，输出与退出码逐字节一致 ----

func TestRunDeterministic(t *testing.T) {
	dir := t.TempDir()
	writeSpec(t, dir, "evil.json", dirtySpecJSON)
	writeSpec(t, dir, "clean.json", cleanSpecJSON)
	out1, code1 := Run([]string{dir})
	out2, code2 := Run([]string{dir})
	if code1 != code2 || out1 != out2 {
		t.Fatalf("A-3 determinism violated:\nrun1=(%d,%q)\nrun2=(%d,%q)", code1, out1, code2, out2)
	}
	// selftest 同样逐字节一致
	s1, c1 := Run([]string{"selftest"})
	s2, c2 := Run([]string{"selftest"})
	if c1 != c2 || s1 != s2 {
		t.Fatalf("selftest determinism violated:\nrun1=(%d,%q)\nrun2=(%d,%q)", c1, s1, c2, s2)
	}
}
