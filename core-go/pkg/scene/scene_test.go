// scene_test.go 场景树 M2 验收单测——⭐ 三条负面用例（M2-4 硬要求）：
//  ① 无互认 ⟹ 引用被拒；② 超深度 ⟹ fail-closed；③ N:N（多父）⟹ 必拒。
// 另：单边声明不构成互认；第二深度参数并存即红灯；量化单元沿用 T-011（审查项，
// 本包不定义任何新量化单元类型——以「不存在第二口径」为锁定方式）。
// SPDX-License-Identifier: Apache-2.0
package scene

import (
	"errors"
	"testing"
)

func mustErr(t *testing.T, want error, err error, ctx string) {
	t.Helper()
	if !errors.Is(err, want) {
		t.Fatalf("%s: err = %v, want %v", ctx, err, want)
	}
}

func TestRegister_RootAndChildWithMutual(t *testing.T) {
	tr, _ := NewTree(3)
	if err := tr.Register(Scene{SceneID: "root"}); err != nil {
		t.Fatalf("root: %v", err)
	}
	if err := tr.DeclareMutual("child", "root"); err != nil {
		t.Fatal(err)
	}
	if err := tr.Register(Scene{SceneID: "child", ParentSceneID: "root"}); err != nil {
		t.Fatalf("child: %v", err)
	}
	got, _ := tr.Get("child")
	if got.Depth != 1 {
		t.Fatalf("child depth = %d, want 1", got.Depth)
	}
}

// 负面用例 ①：无互认 ⟹ 引用被拒（含单边声明不足）
func TestNegative_NoMutualRecognition_Rejected(t *testing.T) {
	tr, _ := NewTree(3)
	_ = tr.Register(Scene{SceneID: "root"})
	// 完全无互认
	mustErr(t, ErrNoMutualRecognition,
		tr.Register(Scene{SceneID: "orphan", ParentSceneID: "root"}), "no mutual")
	// 单边声明（手工只登记一向）不构成互认
	tr.mu.Lock()
	tr.mutual["one-way"] = map[string]bool{"root": true}
	tr.mu.Unlock()
	mustErr(t, ErrNoMutualRecognition,
		tr.Register(Scene{SceneID: "one-way", ParentSceneID: "root"}), "one-way mutual")
	// 父不存在
	mustErr(t, ErrParentNotFound,
		tr.Register(Scene{SceneID: "ghost", ParentSceneID: "nowhere"}), "parent missing")
}

// 负面用例 ②：超深度 ⟹ fail-closed
func TestNegative_DepthExceeded_FailClosed(t *testing.T) {
	tr, _ := NewTree(1) // D_max = 1
	_ = tr.Register(Scene{SceneID: "L0"})
	_ = tr.DeclareMutual("L1", "L0")
	if err := tr.Register(Scene{SceneID: "L1", ParentSceneID: "L0"}); err != nil {
		t.Fatalf("L1: %v", err)
	}
	_ = tr.DeclareMutual("L2", "L1")
	mustErr(t, ErrDepthExceeded,
		tr.Register(Scene{SceneID: "L2", ParentSceneID: "L1"}), "depth 2 > max 1")
	// fail-closed 终局性：被拒节点不得残留
	if _, ok := tr.Get("L2"); ok {
		t.Fatal("rejected scene leaked into tree")
	}
}

// 负面用例 ③：N:N（多父）必拒；⛔ 不得默示解除
func TestNegative_MultiParent_Rejected(t *testing.T) {
	tr, _ := NewTree(3)
	_ = tr.Register(Scene{SceneID: "p1"})
	_ = tr.Register(Scene{SceneID: "p2"})
	_ = tr.DeclareMutual("x", "p1")
	_ = tr.DeclareMutual("x", "p2")
	if err := tr.Register(Scene{SceneID: "x", ParentSceneID: "p1"}); err != nil {
		t.Fatalf("first parent: %v", err)
	}
	// 同 ID 换父 = 多父企图 ⟹ 必拒（⛔ 不默示解除既有父子关系）
	mustErr(t, ErrMultiParent,
		tr.Register(Scene{SceneID: "x", ParentSceneID: "p2"}), "second parent")
	// 同父重复注册亦拒（幂等不等于放行）
	mustErr(t, ErrSceneExists,
		tr.Register(Scene{SceneID: "x", ParentSceneID: "p1"}), "re-register")
}

// 红灯：声明深度与推导深度并存两值 ⟹ ErrSecondDepthParam
func TestSecondDepthValue_RedLight(t *testing.T) {
	tr, _ := NewTree(3)
	_ = tr.Register(Scene{SceneID: "root"})
	_ = tr.DeclareMutual("c", "root")
	mustErr(t, ErrSecondDepthParam,
		tr.Register(Scene{SceneID: "c", ParentSceneID: "root", Depth: 5}), "conflicting depth")
}

// 负 D_max 拒收
func TestNegativeMaxDepth(t *testing.T) {
	if _, err := NewTree(-1); !errors.Is(err, ErrDepthExceeded) {
		t.Fatalf("err = %v", err)
	}
}
