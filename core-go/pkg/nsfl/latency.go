// latency.go 实现 T-ANCHOR 批 1 之 T-ANCHOR-3′：延迟契约。
//
// max_latency 声明须存证（上链可验）；超时路径强制返回 BLOCKED（终局性），
// ⛔ 不得挂起、不得静默放行。
//
// ⚠️ 契约数值为工程目标值，就地标 SIMULATED，待实测校准。
// SPDX-License-Identifier: Apache-2.0
package nsfl

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"time"

	"github.com/henyi-tdca/tdca-core-go/pkg/nca"
)

// ErrLatencyUndeclared 未声明延迟契约即启用超时判定
var ErrLatencyUndeclared = errors.New("tdca: latency contract not declared")

// LatencyContract 延迟契约（T-ANCHOR-3′）
type LatencyContract struct {
	ContractID    string `json:"contract_id"`
	MaxLatencyMS  int64  `json:"max_latency_ms"` // ⚠️ SIMULATED 工程目标值，待实测校准
	DeclaredAt    string `json:"declared_at"`    // UTC ISO8601
	DeclHash      string `json:"decl_hash"`      // 声明内容哈希（存证载荷引用）
}

// ContractHash 声明内容哈希（上链可验之锚）
func (c *LatencyContract) ContractHash() string {
	digest := sha256.New()
	fmt.Fprintf(digest, "%s|%d|%s", c.ContractID, c.MaxLatencyMS, c.DeclaredAt)
	return "sha256:" + hex.EncodeToString(digest.Sum(nil))
}

// DeclareLatencyContract 声明延迟契约（声明即存证：返回契约，其 DeclHash 可写入存证链核验）
func DeclareLatencyContract(contractID string, maxLatency time.Duration) (*LatencyContract, error) {
	if contractID == "" || maxLatency <= 0 {
		return nil, fmt.Errorf("%w: bad contract (id=%q, max=%s)", ErrLatencyUndeclared, contractID, maxLatency)
	}
	c := &LatencyContract{
		ContractID:   contractID,
		MaxLatencyMS: maxLatency.Milliseconds(),
		DeclaredAt:   time.Now().UTC().Format(time.RFC3339),
	}
	c.DeclHash = c.ContractHash()
	return c, nil
}

// AnchorDeclaration 声明存证上链（可验）：把 DeclHash 写入 NCA 存证链，
// 事后可由链上载荷重算 ContractHash 比对——声明不可抵赖、不可篡改。
func AnchorDeclaration(c *LatencyContract, chain interface {
	Head() string
	Append(rec *nca.NcaRecord) error
}) error {
	if c == nil || c.DeclHash == "" {
		return ErrLatencyUndeclared
	}
	if chain == nil {
		return fmt.Errorf("%w: nil chain", ErrLatencyUndeclared)
	}
	rec := &nca.NcaRecord{
		NcaID:    "LATENCY-DECL-" + c.ContractID,
		Type:     "latency_contract",
		TS:       c.DeclaredAt,
		Signer:   "latency-contract-registry",
		PrevHash: chain.Head(),
		Payload: map[string]any{
			"contract_id":    c.ContractID,
			"max_latency_ms": c.MaxLatencyMS,
			"decl_hash":      c.DeclHash,
		},
	}
	rec.PayloadRef = rec.RecordHash()
	return chain.Append(rec)
}

// CheckLatency 超时判定——⭐ 超时强制返回 BLOCKED（终局性，非挂起）
func (c *LatencyContract) CheckLatency(elapsed time.Duration, triggerID string) (*FuseResult, error) {
	if c == nil || c.DeclHash == "" {
		return nil, ErrLatencyUndeclared
	}
	if elapsed.Milliseconds() > c.MaxLatencyMS {
		return &FuseResult{
			Action: Action{
				Status:       StatusBlock,
				Type:         TypeInstitutional,
				Reason:       fmt.Sprintf("latency %dms exceeded contract %s max %dms", elapsed.Milliseconds(), c.ContractID, c.MaxLatencyMS),
				Irreversible: false,
			},
			TriggerID: triggerID,
			Blocked:   true,
			Message:   "BLOCKED: latency contract violated (final, no pending state)",
		}, nil
	}
	return &FuseResult{
		Action:    Action{Status: StatusAllow, Type: TypeInstitutional, Reason: "within latency contract"},
		TriggerID: triggerID,
		Blocked:   false,
	}, nil
}
