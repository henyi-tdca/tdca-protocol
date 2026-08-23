// 公理 6 可执行证明验证器测试（P0 A-3）
// SPDX-License-Identifier: Apache-2.0
package enforce

import "testing"

func TestVerifyAxiom6AllPass(t *testing.T) {
	g := NewEntryGate()
	ok, results := g.VerifyAxiom6()
	if !ok {
		t.Fatalf("公理 6 机验失败:\n%v", results)
	}
	// 断言覆盖四约束 + 排除条款
	if len(results) < 6 {
		t.Fatalf("机验项不足（期望 ≥6 项，got %d）: %v", len(results), results)
	}
	for _, r := range results {
		t.Logf("  %s", r)
	}
}

func TestVerifyAxiom6FailClosedOnMutation(t *testing.T) {
	// 负向验证：若将 RightInverse 判定类破坏（模拟证明失效），机验必须报失败
	// 此处直接验证验证器本身能捕获"不可还原"（Im(f) 之外判定）
	g := NewEntryGate()
	_, okG := g.RightInverse(EnforceResult{Status: "FUSED", Reason: "no-such-outcome"})
	if okG {
		t.Fatal("Im(f) 之外判定不可还原（验证器边界应 fail-closed）")
	}
}
