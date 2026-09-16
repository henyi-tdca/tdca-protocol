// anchor.go 实现 T-ANCHOR 批 1 之 T-ANCHOR-1：断言锚点 schema 与三态状态机。
//
// 三态：proposed（提案）→ active（生效）→ overruled（被推翻，终态）。
// 纪律：
//   - overruled 记录不可物理删除（删除返回错误）——推翻留痕、不可灭迹；
//   - 新锚点 DecayRate 默认 = 1.0（不衰减）；
//   - G-2：默认值上调路径必须携带可审计触发条件（样本量下限 + 收敛判据），
//     否则拒绝；一切经证上调写入存证链（上链可验）。
//
// ⚠️ 阈值（MinSampleSizeForIncrease 等）为工程目标值，就地标 SIMULATED，
// 待实测校准；本文件不构成任何「已证明」声称。
// SPDX-License-Identifier: Apache-2.0
package nca

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"sync"
	"time"
)

// 锚点三态
const (
	AnchorProposed  = "proposed"
	AnchorActive    = "active"
	AnchorOverruled = "overruled"
)

// 错误定义
var (
	ErrAnchorNotFound          = errors.New("tdca: anchor not found")
	ErrAnchorExists            = errors.New("tdca: anchor already exists")
	ErrAnchorIllegalTransition = errors.New("tdca: illegal anchor state transition")
	ErrAnchorOverruledDelete   = errors.New("tdca: overruled anchor cannot be physically deleted")
	ErrAnchorDecayEvidence     = errors.New("tdca: decay-rate increase lacks auditable evidence")
)

// DefaultDecayRate 新锚点默认值（1.0 = 不衰减；测试锁定）
const DefaultDecayRate = 1.0

// MinSampleSizeForIncrease G-2 样本量下限（⚠️ SIMULATED 工程目标值，待实测校准）
const MinSampleSizeForIncrease = 30

// AssertionAnchor 断言锚点 schema（T-ANCHOR-1）
type AssertionAnchor struct {
	AnchorID       string  `json:"anchor_id"`
	AssertionHash  string  `json:"assertion_hash"`  // sha256:{断言载荷}
	Status         string  `json:"status"`          // proposed | active | overruled
	DecayRate      float64 `json:"decay_rate"`      // 默认 1.0（不衰减）
	ProposedAt     string  `json:"proposed_at"`     // UTC ISO8601
	ActivatedAt    string  `json:"activated_at,omitempty"`
	OverruledAt    string  `json:"overruled_at,omitempty"`
	OverruleReason string  `json:"overrule_reason,omitempty"`
}

// AnchorHash 锚点内容哈希（不含状态机时间戳，供存证载荷引用）
func (a *AssertionAnchor) AnchorHash() string {
	digest := sha256.New()
	fmt.Fprintf(digest, "%s|%s|%s|%g", a.AnchorID, a.AssertionHash, a.Status, a.DecayRate)
	return "sha256:" + hex.EncodeToString(digest.Sum(nil))
}

// DecayEvidence G-2 可审计触发条件（上调路径的入场券）
type DecayEvidence struct {
	SampleSize int  `json:"sample_size"` // 观测样本量（下限 MinSampleSizeForIncrease）
	Converged  bool `json:"converged"`   // 收敛判据（观测序列已收敛）
	Note       string `json:"note"`        // 审计附注（人读）
}

// AnchorRegistry 锚点登记表（并发安全；审计事件写入存证链）
type AnchorRegistry struct {
	mu      sync.RWMutex
	anchors map[string]*AssertionAnchor
	chain   *Chain // 审计事件上链（可验）；nil 则仅内存
	auditN  int
}

// NewAnchorRegistry 建表（chain 可为 nil——不强制，但生产路径应上链）
func NewAnchorRegistry(chain *Chain) *AnchorRegistry {
	return &AnchorRegistry{anchors: make(map[string]*AssertionAnchor), chain: chain}
}

// nowUTC 统一时间戳
func nowUTC() string { return time.Now().UTC().Format(time.RFC3339) }

// audit 审计事件上链（type=anchor_audit；chain 为 nil 时跳过）
func (r *AnchorRegistry) audit(event string, a *AssertionAnchor) {
	if r.chain == nil {
		return
	}
	r.auditN++
	rec := &NcaRecord{
		NcaID:     fmt.Sprintf("ANCHOR-AUDIT-%06d", r.auditN),
		Type:      "anchor_audit",
		TS:        nowUTC(),
		Signer:    "anchor-registry",
		PrevHash:  r.chain.Head(),
		Payload:   map[string]any{"event": event, "anchor_id": a.AnchorID, "anchor_hash": a.AnchorHash(), "status": a.Status, "decay_rate": a.DecayRate},
	}
	rec.PayloadRef = rec.RecordHash()
	_ = r.chain.Append(rec) // 链式校验失败不阻断状态机，但审计缺失会在 Verify 暴露
}

// Propose 提案新锚点（初始 proposed，DecayRate 默认 1.0）
func (r *AnchorRegistry) Propose(anchorID, assertionHash string) (*AssertionAnchor, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, dup := r.anchors[anchorID]; dup {
		return nil, fmt.Errorf("%w: %s", ErrAnchorExists, anchorID)
	}
	a := &AssertionAnchor{
		AnchorID:      anchorID,
		AssertionHash: assertionHash,
		Status:        AnchorProposed,
		DecayRate:     DefaultDecayRate,
		ProposedAt:    nowUTC(),
	}
	r.anchors[anchorID] = a
	r.audit("propose", a)
	return a, nil
}

// legalTransition 三态合法迁移表：
// proposed→active、proposed→overruled、active→overruled；其余皆非法。
func legalTransition(from, to string) bool {
	switch from {
	case AnchorProposed:
		return to == AnchorActive || to == AnchorOverruled
	case AnchorActive:
		return to == AnchorOverruled
	default:
		return false // overruled 为终态
	}
}

func (r *AnchorRegistry) transition(id, to string, reason string) (*AssertionAnchor, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	a, ok := r.anchors[id]
	if !ok {
		return nil, fmt.Errorf("%w: %s", ErrAnchorNotFound, id)
	}
	if !legalTransition(a.Status, to) {
		return nil, fmt.Errorf("%w: %s -> %s", ErrAnchorIllegalTransition, a.Status, to)
	}
	a.Status = to
	switch to {
	case AnchorActive:
		a.ActivatedAt = nowUTC()
	case AnchorOverruled:
		a.OverruledAt = nowUTC()
		a.OverruleReason = reason
	}
	r.audit("transition_to_"+to, a)
	return a, nil
}

// Activate 生效（proposed → active）
func (r *AnchorRegistry) Activate(id string) (*AssertionAnchor, error) {
	return r.transition(id, AnchorActive, "")
}

// Overrule 推翻（proposed|active → overruled；须给理由——推翻留痕）
func (r *AnchorRegistry) Overrule(id, reason string) (*AssertionAnchor, error) {
	if reason == "" {
		return nil, fmt.Errorf("%w: overrule requires reason", ErrAnchorIllegalTransition)
	}
	return r.transition(id, AnchorOverruled, reason)
}

// Delete 物理删除——⛔ overruled 记录不可物理删除（返回错误）
func (r *AnchorRegistry) Delete(id string) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	a, ok := r.anchors[id]
	if !ok {
		return fmt.Errorf("%w: %s", ErrAnchorNotFound, id)
	}
	if a.Status == AnchorOverruled {
		return fmt.Errorf("%w: %s", ErrAnchorOverruledDelete, id)
	}
	delete(r.anchors, id)
	return nil
}

// IncreaseDecayRate G-2 默认值上调路径：必须携带可审计触发条件
//（样本量 ≥ 下限 且 收敛判据为真），否则拒绝；经证上调写入存证链。
// ⛔ 不存在无证据的直接赋值入口。
func (r *AnchorRegistry) IncreaseDecayRate(id string, newRate float64, ev DecayEvidence) (*AssertionAnchor, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	a, ok := r.anchors[id]
	if !ok {
		return nil, fmt.Errorf("%w: %s", ErrAnchorNotFound, id)
	}
	if a.Status != AnchorActive {
		return nil, fmt.Errorf("%w: decay-rate adjustable only when active (now %s)", ErrAnchorIllegalTransition, a.Status)
	}
	if newRate <= a.DecayRate {
		return nil, fmt.Errorf("%w: new rate %g not above current %g", ErrAnchorDecayEvidence, newRate, a.DecayRate)
	}
	if ev.SampleSize < MinSampleSizeForIncrease || !ev.Converged {
		return nil, fmt.Errorf("%w: sample %d (min %d), converged=%v",
			ErrAnchorDecayEvidence, ev.SampleSize, MinSampleSizeForIncrease, ev.Converged)
	}
	a.DecayRate = newRate
	r.audit("decay_increase", a)
	return a, nil
}

// Get 只读取件
func (r *AnchorRegistry) Get(id string) (*AssertionAnchor, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	a, ok := r.anchors[id]
	return a, ok
}
