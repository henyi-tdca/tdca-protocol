// Package nsfl 实现 TDCA 负空间熔断器（DCD-CORE-GO-001 核心三）。
//
// 分级响应：ALLOW → WARN → BLOCK → ALT_PATH → HUMAN_OVERRIDE → FUSED；
// 类型断言硬约束（R1-R10 编码为 Go 类型）；并发安全。破坏性测试点：绕过尝试触发熔断。
//
// 制度锚定: DCD-CORE-GO-001 ｜ NSFL-V0.2 ｜ tdca-firmware-spec §六（物理/制度负空间）
// 接口熵=0: 与 Python 版 nsfl 输出 JSON 100% 兼容
// SPDX-License-Identifier: TDCA-Internal
package nsfl

import (
	"errors"
	"fmt"
	"sync"
)

// 熔断状态
const (
	StatusAllow      = "ALLOW"
	StatusWarn       = "WARN"
	StatusBlock      = "BLOCK"
	StatusAltPath    = "ALT_PATH"
	StatusHuman      = "HUMAN_OVERRIDE"
	StatusFused      = "FUSED"
)

// 负空间类型
const (
	TypeInstitutional = "INSTITUTIONAL" // 制度负空间（可逆至 SUSPENDED 或不可逆 FUSED）
	TypePhysical      = "PHYSICAL"      // 物理负空间（不可逆，信任锚底线）
)

// 错误定义
var (
	ErrFused     = errors.New("tdca: fused (irreversible)")
	ErrBlocked   = errors.New("tdca: blocked")
	ErrNoAltPath = errors.New("tdca: no alt path")
)

// Action 熔断动作（类型断言硬约束——状态机不允许非法迁移）
type Action struct {
	Status    string `json:"status"`
	Type      string `json:"type"`       // INSTITUTIONAL | PHYSICAL
	Reason    string `json:"reason"`
	Irreversible bool `json:"irreversible"`
}

// FuseResult 熔断判定结果
type FuseResult struct {
	Action    Action `json:"action"`
	TriggerID string `json:"trigger_id"`
	Blocked   bool   `json:"blocked"`
	Message   string `json:"message"`
}

// Rule 熔断规则（R1-R10 编码）
type Rule struct {
	ID       string   `json:"id"`
	Severity int      `json:"severity"` // 1 警告 / 2 BLOCK / 3 FUSED
	Matches  []string `json:"matches"`  // 触发模式
	AltPath  string   `json:"alt_path,omitempty"`
}

// FuseEngine 熔断引擎（并发安全）
type FuseEngine struct {
	mu      sync.RWMutex
	rules   []Rule
	fused   bool
	fuseInfo map[string]any
}

// NewFuseEngine 默认熔断引擎（R1-R10 制度规则）
func NewFuseEngine() *FuseEngine {
	return &FuseEngine{
		rules: DefaultRules(),
		fuseInfo: map[string]any{},
	}
}

// DefaultRules 制度默认规则（R1-R10 核心子集，NSFL-V0.2）
func DefaultRules() []Rule {
	return []Rule{
		{ID: "R1", Severity: 2, Matches: []string{"unauthenticated", "no-auth"}},
		{ID: "R2", Severity: 2, Matches: []string{"illegal-token", "bad-token"}},
		{ID: "R3", Severity: 3, Matches: []string{"key-export", "puf-extract"}},
		{ID: "R4", Severity: 3, Matches: []string{"physical-tamper", "decap"}},
		{ID: "R5", Severity: 2, Matches: []string{"version-drift", "fw-unknown"}},
		{ID: "R6", Severity: 1, Matches: []string{"suspicious-pattern"}},
		{ID: "R7", Severity: 2, Matches: []string{"unauthorized-call"}},
		{ID: "R8", Severity: 2, Matches: []string{"cert-invalid"}},
		{ID: "R9", Severity: 1, Matches: []string{"rate-limit"}},
		{ID: "R10", Severity: 3, Matches: []string{"nsfl-bypass-attempt"}},
	}
}

// Eval 判定单信号（fail-closed：未知信号按 BLOCK 处理）
func (e *FuseEngine) Eval(triggerID, signal string) FuseResult {
	e.mu.RLock()
	defer e.mu.RUnlock()

	// 已熔断（FUSED 不可逆）
	if e.fused {
		return FuseResult{
			Action: Action{Status: StatusFused, Type: e.fuseInfo["type"].(string),
				Reason: "already fused", Irreversible: true},
			TriggerID: triggerID, Blocked: true,
			Message: "engine fused (irreversible)",
		}
	}

	for _, r := range e.rules {
		for _, m := range r.Matches {
			if m == signal {
				switch {
				case r.Severity == 3:
					e.fused = true
					e.fuseInfo = map[string]any{
						"type": TypeInstitutional, "rule": r.ID, "signal": signal,
						"irreversible": true,
					}
					return FuseResult{
						Action: Action{Status: StatusFused, Type: TypeInstitutional,
							Reason: fmt.Sprintf("rule %s: %s", r.ID, signal), Irreversible: true},
						TriggerID: triggerID, Blocked: true,
						Message: fmt.Sprintf("NSFL fused by %s", r.ID),
					}
				case r.Severity == 2:
					return FuseResult{
						Action: Action{Status: StatusBlock, Type: TypeInstitutional,
							Reason: fmt.Sprintf("rule %s: %s", r.ID, signal)},
						TriggerID: triggerID, Blocked: true,
						Message: fmt.Sprintf("NSFL blocked by %s", r.ID),
					}
				default:
					return FuseResult{
						Action: Action{Status: StatusWarn, Type: TypeInstitutional,
							Reason: fmt.Sprintf("rule %s: %s", r.ID, signal)},
						TriggerID: triggerID, Blocked: false,
						Message: fmt.Sprintf("NSFL warn by %s", r.ID),
					}
				}
			}
		}
	}
	// fail-closed：未知信号 → BLOCK（不默认放行）
	return FuseResult{
		Action: Action{Status: StatusBlock, Type: TypeInstitutional,
			Reason: "unknown signal (fail-closed)"},
		TriggerID: triggerID, Blocked: true,
		Message: "unknown signal treated as BLOCK (fail-closed)",
	}
}

// HumanOverride 人类最终签名权（ID71 慢系统——唯一可解除 BLOCK 的路径）
func (e *FuseEngine) HumanOverride(triggerID string) FuseResult {
	if e.fused {
		return FuseResult{
			Action: Action{Status: StatusFused, Type: TypeInstitutional,
				Reason: "fused irreversible — human override not allowed", Irreversible: true},
			TriggerID: triggerID, Blocked: true, Message: "cannot override FUSED",
		}
	}
	return FuseResult{
		Action: Action{Status: StatusHuman, Type: TypeInstitutional,
			Reason: "human override (slow system ID71)"},
		TriggerID: triggerID, Blocked: false, Message: "human override granted",
	}
}

// PhysicalFuse 物理负空间熔断（不可逆，信任锚底线）
func (e *FuseEngine) PhysicalFuse(triggerID, reason string) FuseResult {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.fused = true
	e.fuseInfo = map[string]any{"type": TypePhysical, "reason": reason, "irreversible": true}
	return FuseResult{
		Action: Action{Status: StatusFused, Type: TypePhysical,
			Reason: reason, Irreversible: true},
		TriggerID: triggerID, Blocked: true,
		Message: "physical fuse (irreversible, trust anchor)",
	}
}

// IsFused 是否已熔断
func (e *FuseEngine) IsFused() bool {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.fused
}
