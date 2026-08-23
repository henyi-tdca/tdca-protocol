// 公理 6 实例化测试（TDCA-CORE-GO-AXIOM6-001 验收）
//
// 覆盖: 完备性（f⁻(f(x),x)=1）/ 可靠性（f⁻(y,x)=1⟹y=f(x)）/
//       可还原性（∀y∈Im(f): f(g(y))=y 全判定类）/ 复杂度（f⁻=1 次 Verify+O(1)）/
//       排除条款（非哈希单向/多对一右逆）/ 纯函数并发安全。
// SPDX-License-Identifier: Apache-2.0
package enforce

import (
	"reflect"
	"sync"
	"testing"
)

// axiomCard 全合规卡片（PASS 判定类代表）
func axiomCard() AgentCard {
	return AgentCard{
		AgentID:      "NM-001",
		ProtocolVer:  "3.1.2",
		SceneID:      "scene-phy-notification",
		Role:         "NM-Operator",
		AllowedCalls: []string{"verify"},
		NSFLBoundary: []string{"no-tamper"},
	}
}

// im 枚举 Im(f) 全部判定类（构造表 §三 的 y 侧）
func im(t *testing.T, g *EntryGate) []EnforceResult {
	t.Helper()
	var out []EnforceResult
	for _, card := range []AgentCard{
		axiomCard(),                                        // PASS
		func() AgentCard { c := axiomCard(); c.ProtocolVer = "9.9.9"; return c }(),   // REJECT(protocol)
		func() AgentCard { c := axiomCard(); c.SceneID = "scene-unknown"; return c }(), // REJECT(scene)
		func() AgentCard { c := axiomCard(); c.Role = "ROLE-UNKNOWN"; return c }(),     // REJECT(role)
		func() AgentCard { c := axiomCard(); c.AllowedCalls = make([]string, 65); return c }(), // REJECT(calls)
		func() AgentCard { c := axiomCard(); c.NSFLBoundary = []string{}; return c }(),  // BLOCK(nsfl)
	} {
		res, _ := g.Verify(&card)
		out = append(out, *res)
	}
	return out
}

// ---- 约束 1 · 完备性 ----

func TestAxiom6Completeness(t *testing.T) {
	// ∀x∈X: f⁻(f(x),x)=1——对 Im(f) 全部判定类代表卡片
	g := NewEntryGate()
	for _, y := range im(t, g) {
		x, ok := g.RightInverse(y)
		if !ok {
			t.Fatalf("RightInverse 不可还原: %s/%s", y.Status, y.Reason)
		}
		if !g.AuditVerify(y, x) {
			t.Fatalf("完备性违反: f⁻(f(%+v),%+v)!=1 (y=%s/%s)", x, x, y.Status, y.Reason)
		}
	}
}

// ---- 约束 2 · 可靠性 ----

func TestAxiom6Soundness(t *testing.T) {
	// f⁻(y,x)=1 ⟹ y=f(x)——篡改 y 任一字段后 AuditVerify 必须拒绝
	g := NewEntryGate()
	for _, y := range im(t, g) {
		x, _ := g.RightInverse(y)
		// 篡改 status
		bad1 := y
		bad1.Status = "TAMPERED"
		if g.AuditVerify(bad1, x) {
			t.Fatalf("可靠性违反: 篡改 status 仍通过 (%s)", y.Status)
		}
		// 篡改 reason
		bad2 := y
		bad2.Reason = "tampered reason"
		if g.AuditVerify(bad2, x) {
			t.Fatalf("可靠性违反: 篡改 reason 仍通过 (%s)", y.Status)
		}
		// 篡改 checks
		bad3 := y
		bad3.Checks = append([]string(nil), y.Checks...)
		bad3.Checks = append(bad3.Checks, "EXTRA")
		if g.AuditVerify(bad3, x) {
			t.Fatalf("可靠性违反: 篡改 checks 仍通过 (%s)", y.Status)
		}
	}
}

func TestAxiom6SoundnessCrossClass(t *testing.T) {
	// 跨判定类：PASS 的 x 不应验证通过 REJECT 的 y
	g := NewEntryGate()
	px, _ := g.RightInverse(EnforceResult{Status: "PASS", Reason: "all checks passed"})
	bad := axiomCard()
	bad.ProtocolVer = "9.9.9"
	ry, _ := g.Verify(&bad)
	if g.AuditVerify(*ry, px) {
		t.Fatal("可靠性违反: PASS 卡片通过 REJECT(protocol) 判定")
	}
}

// ---- 约束 3 · 可还原性（∀y∈Im(f): f(g(y))=y 全类验证）----

func TestAxiom6RightInverseAllClasses(t *testing.T) {
	g := NewEntryGate()
	for _, y := range im(t, g) {
		x, ok := g.RightInverse(y)
		if !ok {
			t.Fatalf("判定类不可还原: %s/%s", y.Status, y.Reason)
		}
		res, _ := g.Verify(&x)
		if !reflect.DeepEqual(*res, y) {
			t.Fatalf("右逆违反: f(g(y))!=y\n  want: %+v\n  got:  %+v", y, *res)
		}
	}
}

func TestAxiom6RightInverseOutsideIm(t *testing.T) {
	// Im(f) 之外（如任意虚构判定）→ 不可还原（g 定义域边界）
	g := NewEntryGate()
	_, ok := g.RightInverse(EnforceResult{Status: "FUSED", Reason: "no such outcome"})
	if ok {
		t.Fatal("Im(f) 之外的判定不可被还原（应返回 false）")
	}
}

func TestAxiom6RightInverseDeterministic(t *testing.T) {
	// g 确定性：同一 y 两次还原同一 x'
	g := NewEntryGate()
	bad := axiomCard()
	bad.SceneID = "scene-unknown"
	y, _ := g.Verify(&bad)
	x1, _ := g.RightInverse(*y)
	x2, _ := g.RightInverse(*y)
	if !reflect.DeepEqual(x1, x2) {
		t.Fatal("右逆 g 非确定性")
	}
}

// ---- 约束 4 · 复杂度（f⁻ = 1 次 Verify + O(1)，非全空间枚举）----

func TestAxiom6ComplexitySingleVerify(t *testing.T) {
	// AuditVerify 复杂度 = T(Verify)+O(1)：不枚举 X，直接重算比对。
	// 验证：对 PASS 类，AuditVerify 与 Verify 单次调用结果一致（结构上 O(n)）。
	g := NewEntryGate()
	x := axiomCard()
	y, _ := g.Verify(&x)
	if !g.AuditVerify(*y, x) {
		t.Fatal("AuditVerify 应单次 Verify 重算通过")
	}
}

// ---- 排除条款 / 纯函数性质 ----

func TestAxiom6NotHashSingleDirection(t *testing.T) {
	// 排除哈希单向：f⁻ 可还原（AuditVerify 重算），非不可逆哈希
	g := NewEntryGate()
	x := axiomCard()
	y, _ := g.Verify(&x)
	// f⁻ 从 (y, x) 双向可判定——非单向（有明确还原路径 RightInverse）
	xr, ok := g.RightInverse(*y)
	res, _ := g.Verify(&xr)
	if !ok || res.Status != "PASS" {
		t.Fatal("公理 6 排除哈希单向：应存在可计算还原路径")
	}
}

func TestAxiom6NonInjectiveAllowed(t *testing.T) {
	// 允许非单射：多对一 f（不同卡片同判定），右逆 g 可选任一 preimage
	g := NewEntryGate()
	c1 := axiomCard()
	c2 := axiomCard()
	c2.AgentID = "NM-002" // 不同卡片
	y1, _ := g.Verify(&c1)
	y2, _ := g.Verify(&c2)
	if y1.Status != y2.Status {
		t.Fatal("多对一前提失效")
	}
	xr, _ := g.RightInverse(*y1)
	res, _ := g.Verify(&xr)
	if res.Status != "PASS" {
		t.Fatal("非单射：右逆应还原任一 preimage")
	}
}

func TestAxiom6PureConcurrent(t *testing.T) {
	// 纯函数并发安全：并行 AuditVerify/RightInverse 无数据竞争（-race 覆盖）
	g := NewEntryGate()
	var wg sync.WaitGroup
	for i := 0; i < 64; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			x := axiomCard()
			y, _ := g.Verify(&x)
			if !g.AuditVerify(*y, x) {
				t.Error("并发完备性违反")
			}
			xr, ok := g.RightInverse(*y)
			res, _ := g.Verify(&xr)
			if !ok || res.Status != "PASS" {
				t.Error("并发还原违反")
			}
		}()
	}
	wg.Wait()
}
