// Package scene 实现场景树立项 M2：跨场景互认关系之单父 DAG 特例。
//
// 制度规格（M1 五条，已照准，为实现之硬约束）：
//  ① 场景树 = 跨场景互认关系之**单父** DAG 特例（⛔ N:N 禁，⛔ 不得默示解除）；
//  ② ParentSceneID = **互认路径**（⛔ 非证明继承；⚠️ 无互认则禁止引用）；
//  ③ 「深度」仅"化合深度"一义 —— 本包 MaxSceneDepth 即 D_max 之同一取值，
//     ⛔ 不得引入第二深度参数（并存两值即红灯）；
//  ④ 超深度 fail-closed；
//  ⑤ 场景量化单元沿用 T-011（⛔ 不另立第二口径——本包不定义任何新量化单元类型，
//     量化语义一律回到 T-011 在册口径）。
//
// ⚠️ 本包为设计态实现（SIMULATED 语境），不构成任何「已证明」声称。
// SPDX-License-Identifier: Apache-2.0
package scene

import (
	"errors"
	"fmt"
	"sync"
)

// 错误定义（fail-closed 全家）
var (
	ErrSceneExists           = errors.New("tdca: scene already registered")
	ErrParentNotFound        = errors.New("tdca: parent scene not registered")
	ErrNoMutualRecognition   = errors.New("tdca: no mutual recognition — reference rejected")
	ErrDepthExceeded         = errors.New("tdca: compound depth exceeded (fail-closed)")
	ErrMultiParent           = errors.New("tdca: multi-parent (N:N) forbidden")
	ErrSecondDepthParam      = errors.New("tdca: second depth parameter forbidden")
)

// Scene 场景节点（schema）
type Scene struct {
	SceneID       string `json:"scene_id"`
	ParentSceneID string `json:"parent_scene_id,omitempty"` // 互认路径（⛔ 非证明继承）；空 = 根场景
	Depth         int    `json:"depth"`                     // 化合深度（唯一深度语义，上限 = MaxSceneDepth ≡ D_max）
}

// Tree 场景树（单父 DAG 特例；并发安全）
type Tree struct {
	mu       sync.RWMutex
	scenes   map[string]*Scene
	mutual   map[string]map[string]bool // 互认关系：mutual[a][b] && mutual[b][a] 皆真方为互认
	maxDepth int                        // MaxSceneDepth ≡ D_max（同一取值，全树唯一深度参数）
}

// NewTree 建树。maxDepth 即化合深度上限 D_max —— ⛔ 全树只此一个深度参数。
func NewTree(maxDepth int) (*Tree, error) {
	if maxDepth < 0 {
		return nil, fmt.Errorf("%w: negative maxDepth %d", ErrDepthExceeded, maxDepth)
	}
	return &Tree{
		scenes:   make(map[string]*Scene),
		mutual:   make(map[string]map[string]bool),
		maxDepth: maxDepth,
	}, nil
}

// MaxSceneDepth 全树唯一深度上限（≡ D_max，同一取值）
func (t *Tree) MaxSceneDepth() int { return t.maxDepth }

// DeclareMutual 登记互认关系（双向对称；单边声明不构成互认）
func (t *Tree) DeclareMutual(a, b string) error {
	if a == "" || b == "" || a == b {
		return fmt.Errorf("%w: bad pair (%q,%q)", ErrNoMutualRecognition, a, b)
	}
	t.mu.Lock()
	defer t.mu.Unlock()
	for _, pair := range [][2]string{{a, b}, {b, a}} {
		if t.mutual[pair[0]] == nil {
			t.mutual[pair[0]] = make(map[string]bool)
		}
		t.mutual[pair[0]][pair[1]] = true
	}
	return nil
}

// mutualOK 互认判定（须双向皆真）
func (t *Tree) mutualOK(a, b string) bool {
	return t.mutual[a][b] && t.mutual[b][a]
}

// Register 注册场景——单父 DAG 特例之三道闸：
//
//	闸 1（互认前置）：非根场景与父场景之间须已登记互认，否则 ⛔ 引用被拒；
//	闸 2（深度 fail-closed）：Depth = 父深度 + 1，超 MaxSceneDepth ⟹ 拒绝；
//	闸 3（单父）：同 ID 已注册且带不同父 ⟹ N:N 必拒（⛔ 不得默示解除）。
//
// ⛔ 本函数不提供、也不得以任何形式实现「沿父场景取证明」语义——
// ParentSceneID 仅为互认路径，证明义务不发生继承。
func (t *Tree) Register(s Scene) error {
	if s.SceneID == "" {
		return fmt.Errorf("%w: empty scene id", ErrParentNotFound)
	}
	t.mu.Lock()
	defer t.mu.Unlock()

	if old, dup := t.scenes[s.SceneID]; dup {
		if old.ParentSceneID != s.ParentSceneID {
			return fmt.Errorf("%w: %s already has parent %q", ErrMultiParent, s.SceneID, old.ParentSceneID)
		}
		return fmt.Errorf("%w: %s", ErrSceneExists, s.SceneID)
	}

	depth := 0
	if s.ParentSceneID != "" {
		parent, ok := t.scenes[s.ParentSceneID]
		if !ok {
			return fmt.Errorf("%w: %s", ErrParentNotFound, s.ParentSceneID)
		}
		if !t.mutualOK(s.SceneID, s.ParentSceneID) { // 闸 1
			return fmt.Errorf("%w: %s -/-> %s", ErrNoMutualRecognition, s.SceneID, s.ParentSceneID)
		}
		depth = parent.Depth + 1
	}
	if depth > t.maxDepth { // 闸 2（fail-closed）
		return fmt.Errorf("%w: depth %d > max %d", ErrDepthExceeded, depth, t.maxDepth)
	}
	if s.Depth != 0 && s.Depth != depth { // ⛔ 第二深度取值即红灯
		return fmt.Errorf("%w: declared %d != derived %d", ErrSecondDepthParam, s.Depth, depth)
	}
	node := s
	node.Depth = depth
	t.scenes[s.SceneID] = &node
	return nil
}

// Get 只读取件
func (t *Tree) Get(id string) (*Scene, bool) {
	t.mu.RLock()
	defer t.mu.RUnlock()
	s, ok := t.scenes[id]
	return s, ok
}
