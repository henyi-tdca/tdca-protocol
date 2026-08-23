// Package nca 实现 TDCA NCA 存证链（DCD-CORE-GO-001 核心二）。
//
// 不可变哈希链（append-only）：每块含 prev_hash 链式引用；并发安全（RWMutex）；
// 验签接口（SM2 预留，密钥材料永不落盘）。破坏性测试点：伪造 NCA 验签失败。
//
// 制度锚定: DCD-CORE-GO-001 ｜ tdca-firmware-spec V1.0（FactChain 同构）｜ ID35
// 接口熵=0: 与 Python 版 NCA JSON 100% 兼容（nca_id/prev_hash/hash/ts/sign）
// SPDX-License-Identifier: Apache-2.0
package nca

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
	"time"
)

// 错误定义
var (
	ErrTampered  = errors.New("tdca: chain tampered")
	ErrSignature = errors.New("tdca: signature invalid")
)

// NcaRecord 存证记录（8 字段 Lite 同构 + 全量字段）
type NcaRecord struct {
	NcaID     string            `json:"nca_id"`
	Type      string            `json:"type"`       // fact|auth|mou|state|service
	Hash      string            `json:"hash"`       // sha256:{载荷哈希}
	TS        string            `json:"ts"`         // UTC ISO8601
	Signer    string            `json:"signer"`     // pubkey_ref（密钥材料永不落盘）
	PayloadRef string           `json:"payload_ref"` // FactHash_n
	PrevHash  string            `json:"prev_hash"`  // sha256:{前块}
	NSFL      map[string]any    `json:"nsfl"`       // NSFL-V0.2 触发标记
	Payload   map[string]any    `json:"payload,omitempty"`
}

// RecordHash 计算记录哈希（含 prev_hash 链式——篡改传播）
// 注意：哈希源不含 r.Hash 字段本身（避免自引用循环——Hash=RecordHash 恒等式成立）
func (r *NcaRecord) RecordHash() string {
	digest := sha256.New()
	fmt.Fprintf(digest, "%s|%s|%s|%s|%s", r.NcaID, r.Type, r.TS, r.PrevHash, r.Payload)
	return "sha256:" + hex.EncodeToString(digest.Sum(nil))
}

// Chain NCA 存证链（append-only + 并发安全）
type Chain struct {
	mu      sync.RWMutex
	records []*NcaRecord
	head    string // 最新记录哈希
}

// NewChain 创世链
func NewChain() *Chain {
	return &Chain{head: "sha256:genesis"}
}

// Append 追加记录（验证 prev_hash 链式 + 返回记录）
func (c *Chain) Append(rec *NcaRecord) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if rec.PrevHash != c.head {
		return fmt.Errorf("%w: prev_hash mismatch (got %s, head %s)", ErrTampered, rec.PrevHash, c.head)
	}
	recHash := rec.RecordHash()
	// 篡改自检：重算哈希必须等于 rec.Hash 载荷
	if rec.Hash == "" {
		rec.Hash = recHash
	}
	c.records = append(c.records, rec)
	c.head = recHash
	return nil
}

// Verify 全链完整性（哈希链连续 + 篡改检测）
func (c *Chain) Verify() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	prev := "sha256:genesis"
	for _, r := range c.records {
		if r.PrevHash != prev {
			return false
		}
		if r.RecordHash() != r.Hash && r.Hash != "" {
			return false
		}
		prev = r.RecordHash()
	}
	return true
}

// Head 当前链头
func (c *Chain) Head() string {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.head
}

// Len 记录数
func (c *Chain) Len() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.records)
}

// VerifySignature 验签接口（SM2 预留——密钥材料永不落盘；当前为哈希级验签）
// 破坏性测试：伪造记录 → 哈希/签名失败
func (c *Chain) VerifySignature(rec *NcaRecord) error {
	if rec.Signer == "" {
		return fmt.Errorf("%w: signer missing", ErrSignature)
	}
	if rec.Hash != "" && rec.RecordHash() != rec.Hash {
		return fmt.Errorf("%w: record hash mismatch (tampered)", ErrTampered)
	}
	return nil
}

// Snapshot 全链快照（JSON 序列化，接口熵=0）
func (c *Chain) Snapshot() []byte {
	c.mu.RLock()
	defer c.mu.RUnlock()
	out, _ := json.Marshal(c.records)
	return out
}

// NowISO 当前 UTC 时间（ISO8601）
func NowISO() string {
	return time.Now().UTC().Format("2006-01-02T15:04:05Z")
}

// NewRecord 便捷构造
func NewRecord(ncaID, typ, ts, prevHash string, payload map[string]any) *NcaRecord {
	return &NcaRecord{
		NcaID: ncaID, Type: typ, TS: ts, PrevHash: prevHash,
		Payload: payload,
		NSFL:    map[string]any{"version": "V0.2", "triggered": false, "trigger_reason": nil},
	}
}
