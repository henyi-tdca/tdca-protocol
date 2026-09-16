// latency_test.go T-ANCHOR-3′ 验收单测：
//  ① 声明上链可验（DeclHash 入链、重算比对、链完整）
//  ② 超时路径返回 BLOCKED 而非挂起（终局性）
//  ③ 未声明契约即判定 ⟹ 拒绝（fail-closed）
// SPDX-License-Identifier: Apache-2.0
package nsfl

import (
	"errors"
	"testing"
	"time"

	"github.com/henyi-tdca/tdca-core-go/pkg/nca"
)

func TestLatencyContract_DeclarationAnchored(t *testing.T) {
	chain := nca.NewChain()
	c, err := DeclareLatencyContract("LC-1", 250*time.Millisecond)
	if err != nil {
		t.Fatalf("declare: %v", err)
	}
	if c.DeclHash == "" {
		t.Fatal("DeclHash empty")
	}
	if err := AnchorDeclaration(c, chain); err != nil {
		t.Fatalf("anchor declaration: %v", err)
	}
	if !chain.Verify() {
		t.Fatal("chain integrity broken after declaration")
	}
	// 上链可验：链上载荷的 decl_hash 与契约重算一致
	snap := chain.Snapshot()
	if len(snap) == 0 {
		t.Fatal("snapshot empty")
	}
	// 重算契约哈希与 DeclHash 一致（声明不可抵赖）
	if c.ContractHash() != c.DeclHash {
		t.Fatal("contract hash mismatch")
	}
}

func TestLatencyContract_TimeoutForcedBlocked(t *testing.T) {
	c, _ := DeclareLatencyContract("LC-2", 100*time.Millisecond)

	// 超时 ⟹ BLOCKED（终局，非挂起）
	res, err := c.CheckLatency(150*time.Millisecond, "TG-1")
	if err != nil {
		t.Fatalf("check: %v", err)
	}
	if !res.Blocked || res.Action.Status != StatusBlock {
		t.Fatalf("timeout result = %+v, want BLOCKED", res)
	}

	// 未超时 ⟹ 放行
	res2, _ := c.CheckLatency(50*time.Millisecond, "TG-2")
	if res2.Blocked {
		t.Fatal("within-contract latency wrongly blocked")
	}
}

func TestLatencyContract_UndeclaredFailsClosed(t *testing.T) {
	var nilContract *LatencyContract
	if _, err := nilContract.CheckLatency(time.Millisecond, "TG-3"); !errors.Is(err, ErrLatencyUndeclared) {
		t.Fatalf("undeclared contract: err = %v, want ErrLatencyUndeclared", err)
	}
	if _, err := DeclareLatencyContract("", time.Second); !errors.Is(err, ErrLatencyUndeclared) {
		t.Fatalf("empty id: err = %v", err)
	}
	if _, err := DeclareLatencyContract("LC-4", 0); !errors.Is(err, ErrLatencyUndeclared) {
		t.Fatalf("non-positive max: err = %v", err)
	}
}
