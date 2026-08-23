package nsfl

import (
	"sync"
	"testing"
)

func TestEvalAllowPath(t *testing.T) {
	// 无匹配信号 → fail-closed BLOCK（不默认放行）
	e := NewFuseEngine()
	res := e.Eval("t1", "benign-signal")
	if !res.Blocked {
		t.Fatalf("unknown signal should block (fail-closed), got %s", res.Action.Status)
	}
}

// 破坏性测试：绕过尝试（nsfl-bypass-attempt，R10 severity 3）→ FUSED 不可逆
func TestEvalBypassFused(t *testing.T) {
	e := NewFuseEngine()
	res := e.Eval("t1", "nsfl-bypass-attempt")
	if res.Action.Status != StatusFused || !res.Action.Irreversible {
		t.Fatalf("bypass attempt should FUSE (irreversible), got %s", res.Action.Status)
	}
	if !e.IsFused() {
		t.Fatal("engine should be fused")
	}
}

// 破坏性测试：密钥导出尝试（R3 severity 3）→ FUSED
func TestEvalKeyExportFused(t *testing.T) {
	e := NewFuseEngine()
	res := e.Eval("t1", "key-export")
	if res.Action.Status != StatusFused {
		t.Fatalf("key-export should fuse, got %s", res.Action.Status)
	}
}

// 破坏性测试：物理拆解（R4 severity 3）→ PHYSICAL 不可逆
func TestPhysicalFuse(t *testing.T) {
	e := NewFuseEngine()
	res := e.PhysicalFuse("t1", "physical tamper detected")
	if res.Action.Type != TypePhysical || !res.Action.Irreversible {
		t.Fatalf("physical fuse should be PHYSICAL irreversible")
	}
}

// BLOCK 分级（R1 severity 2）→ BLOCK，可被 HumanOverride 解除
func TestEvalBlockAndHumanOverride(t *testing.T) {
	e := NewFuseEngine()
	res := e.Eval("t1", "unauthenticated")
	if res.Action.Status != StatusBlock || !res.Blocked {
		t.Fatalf("unauthenticated should BLOCK, got %s", res.Action.Status)
	}
	override := e.HumanOverride("t1")
	if override.Action.Status != StatusHuman {
		t.Fatalf("human override should grant, got %s", override.Action.Status)
	}
}

// 破坏性测试：FUSED 后不可 HumanOverride
func TestFusedNoHumanOverride(t *testing.T) {
	e := NewFuseEngine()
	_ = e.Eval("t1", "nsfl-bypass-attempt")
	res := e.HumanOverride("t1")
	if res.Action.Status != StatusFused {
		t.Fatalf("fused engine must not allow override, got %s", res.Action.Status)
	}
}

// WARN 分级（R6 severity 1）→ 不阻断
func TestEvalWarn(t *testing.T) {
	e := NewFuseEngine()
	res := e.Eval("t1", "suspicious-pattern")
	if res.Action.Status != StatusWarn || res.Blocked {
		t.Fatalf("suspicious-pattern should WARN (non-blocking), got %s", res.Action.Status)
	}
}

// 破坏性测试：并发熔断判定（十万级）→ 无死锁/无数据竞争
func TestEvalConcurrent(t *testing.T) {
	e := NewFuseEngine()
	const n = 20000
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < n; j++ {
				_ = e.Eval("t", "unauthenticated")
				_ = e.IsFused()
			}
		}()
	}
	wg.Wait()
}

func TestEvalAfterFuseStillBlocked(t *testing.T) {
	e := NewFuseEngine()
	_ = e.Eval("t1", "nsfl-bypass-attempt")
	res := e.Eval("t2", "whatever")
	if !res.Blocked || res.Action.Status != StatusFused {
		t.Fatalf("post-fuse eval should remain FUSED/blocked")
	}
}
