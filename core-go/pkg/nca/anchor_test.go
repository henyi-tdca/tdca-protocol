// anchor_test.go T-ANCHOR-1 验收单测：
//  ① 三态迁移覆盖（合法迁移 + 全部非法迁移拒绝）
//  ② overruled 记录不可物理删除（删除返回错误）
//  ③ DecayRate 默认 = 1.0（锁定）
//  ④ G-2：上调路径可审计触发条件（样本量下限 + 收敛判据）锁定
// SPDX-License-Identifier: Apache-2.0
package nca

import (
	"errors"
	"testing"
)

func TestAnchorStateMachine_LegalTransitions(t *testing.T) {
	r := NewAnchorRegistry(nil)
	a, err := r.Propose("A1", "sha256:assert-1")
	if err != nil {
		t.Fatalf("propose: %v", err)
	}
	if a.Status != AnchorProposed {
		t.Fatalf("initial status = %s, want proposed", a.Status)
	}
	if _, err := r.Activate("A1"); err != nil {
		t.Fatalf("activate: %v", err)
	}
	if _, err := r.Overrule("A1", "反例证据 C-20260916"); err != nil {
		t.Fatalf("overrule from active: %v", err)
	}
	got, _ := r.Get("A1")
	if got.Status != AnchorOverruled || got.OverruleReason == "" {
		t.Fatalf("overrule not recorded: %+v", got)
	}

	// proposed → overruled 亦合法
	if _, err := r.Propose("A2", "sha256:assert-2"); err != nil {
		t.Fatal(err)
	}
	if _, err := r.Overrule("A2", "提案阶段即被推翻"); err != nil {
		t.Fatalf("overrule from proposed: %v", err)
	}
}

func TestAnchorStateMachine_IllegalTransitions(t *testing.T) {
	r := NewAnchorRegistry(nil)
	must := func(name string, err error) {
		t.Helper()
		if !errors.Is(err, ErrAnchorIllegalTransition) {
			t.Fatalf("%s: err = %v, want ErrAnchorIllegalTransition", name, err)
		}
	}
	_, _ = r.Propose("B1", "sha256:x")
	if _, err := r.Activate("B1"); err != nil {
		t.Fatalf("setup activate: %v", err)
	}
	must("active→active（重复生效）", func() error { _, e := r.Activate("B1"); return e }())
	_, _ = r.Overrule("B1", "r")
	must("overruled→active", func() error { _, e := r.Activate("B1"); return e }())
	must("overruled→overruled（终态再迁移）", func() error { _, e := r.Overrule("B1", "again"); return e }())
	must("空理由推翻", func() error { _, _ = r.Propose("B2", "sha256:y"); _, e := r.Overrule("B2", ""); return e }())
}

func TestAnchor_OverruledCannotBeDeleted(t *testing.T) {
	r := NewAnchorRegistry(nil)
	_, _ = r.Propose("C1", "sha256:z")
	_, _ = r.Activate("C1")
	_, _ = r.Overrule("C1", "反例")
	if err := r.Delete("C1"); !errors.Is(err, ErrAnchorOverruledDelete) {
		t.Fatalf("delete overruled: err = %v, want ErrAnchorOverruledDelete", err)
	}
	if _, ok := r.Get("C1"); !ok {
		t.Fatal("overruled record vanished after refused delete")
	}
	// 非终态可删（对照）
	_, _ = r.Propose("C2", "sha256:z2")
	if err := r.Delete("C2"); err != nil {
		t.Fatalf("delete proposed should pass: %v", err)
	}
}

func TestAnchor_DecayRateDefaultLocked(t *testing.T) {
	r := NewAnchorRegistry(nil)
	a, _ := r.Propose("D1", "sha256:d")
	if a.DecayRate != DefaultDecayRate || DefaultDecayRate != 1.0 {
		t.Fatalf("DecayRate default = %g, want 1.0（不衰减）", a.DecayRate)
	}
}

func TestAnchor_G2_IncreaseRequiresAuditableEvidence(t *testing.T) {
	chain := NewChain()
	r := NewAnchorRegistry(chain)
	_, _ = r.Propose("E1", "sha256:e")
	_, _ = r.Activate("E1")

	// 反例 1：样本量不足
	if _, err := r.IncreaseDecayRate("E1", 1.5, DecayEvidence{SampleSize: MinSampleSizeForIncrease - 1, Converged: true}); !errors.Is(err, ErrAnchorDecayEvidence) {
		t.Fatalf("insufficient sample: err = %v", err)
	}
	// 反例 2：未收敛
	if _, err := r.IncreaseDecayRate("E1", 1.5, DecayEvidence{SampleSize: MinSampleSizeForIncrease, Converged: false}); !errors.Is(err, ErrAnchorDecayEvidence) {
		t.Fatalf("not converged: err = %v", err)
	}
	// 反例 3：不上调（newRate <= current）
	if _, err := r.IncreaseDecayRate("E1", 0.5, DecayEvidence{SampleSize: 100, Converged: true}); !errors.Is(err, ErrAnchorDecayEvidence) {
		t.Fatalf("non-increase: err = %v", err)
	}
	// 反例 4：非 active 态不可调
	_, _ = r.Propose("E2", "sha256:e2")
	if _, err := r.IncreaseDecayRate("E2", 2.0, DecayEvidence{SampleSize: 100, Converged: true}); !errors.Is(err, ErrAnchorIllegalTransition) {
		t.Fatalf("proposed-state adjust: err = %v", err)
	}

	// 正例：证据齐备 ⟹ 生效且上链可验
	before := chain.Len()
	a, err := r.IncreaseDecayRate("E1", 1.5, DecayEvidence{SampleSize: 100, Converged: true, Note: "第 3 观测窗"})
	if err != nil {
		t.Fatalf("evidenced increase: %v", err)
	}
	if a.DecayRate != 1.5 {
		t.Fatalf("DecayRate = %g, want 1.5", a.DecayRate)
	}
	if chain.Len() <= before {
		t.Fatal("evidenced increase not anchored to chain")
	}
	if !chain.Verify() {
		t.Fatal("chain integrity broken after audit append")
	}
}
