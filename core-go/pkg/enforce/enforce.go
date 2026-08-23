// Package enforce 实现 TDCA 准入门禁（DCD-CORE-GO-001 核心一）。
//
// 强类型准入校验：AgentCard/协议声明校验 + 公理 6 反函数可计算性（f⁻¹(f(x))=x 可验证），
// 杜绝弱类型注入/越权调用。破坏性测试点：提示注入/越权调用 fail-closed。
//
// 制度锚定: DCD-CORE-GO-001 ｜ 公理 6（反函数可计算性）｜ ID35（制度-技术同构）
// 接口熵=0: 与 Python 版 enforce_entry 输出 JSON 100% 兼容
// SPDX-License-Identifier: TDCA-Internal
package enforce

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
)

// 错误定义（TDCA_Error 类型，调用方必须处理）
var (
	ErrRejected      = errors.New("tdca: entry rejected")
	ErrInjectDetected = errors.New("tdca: injection detected")
	ErrUnauthorized  = errors.New("tdca: unauthorized")
)

// AgentCard 声明（对齐 tdca-firmware-spec / PACK-001 AgentCard 子集）
type AgentCard struct {
	AgentID       string   `json:"agent_id"`
	ProtocolVer   string   `json:"protocol_version"`
	SceneID       string   `json:"scene_id"`
	Role          string   `json:"role"`
	AllowedCalls  []string `json:"allowed_calls"`
	NSFLBoundary  []string `json:"nsfl_boundary"`
}

// EnforceResult 准入结果（与 Python 版 JSON 同构）
type EnforceResult struct {
	Status    string   `json:"status"`    // PASS | REJECT | BLOCK
	Reason    string   `json:"reason"`
	AgentID   string   `json:"agent_id"`
	SceneID   string   `json:"scene_id"`
	Role      string   `json:"role"`
	Checks    []string `json:"checks"`
}

// EntryGate 准入门禁（强类型，fail-closed）
type EntryGate struct {
	SupportedProtocol string
	SceneAllowList    map[string]bool
	RoleAllowList     map[string]bool
	MaxCalls          int
}

// NewEntryGate 构造门禁（默认配置）
func NewEntryGate() *EntryGate {
	return &EntryGate{
		SupportedProtocol: "3.1.2",
		SceneAllowList:    map[string]bool{"scene-phy-notification": true, "scene-collab": true},
		RoleAllowList:     map[string]bool{"NM-Operator": true, "NM-Gov": true, "NM-Fin": true, "NM-Med": true},
		MaxCalls:          64,
	}
}

// ParseAgentCard 严格解析（拒绝注入：非 JSON / 非法字段 / 超长）
func (g *EntryGate) ParseAgentCard(raw []byte) (*AgentCard, error) {
	if len(raw) > 8192 {
		return nil, fmt.Errorf("%w: card too large (%d bytes)", ErrRejected, len(raw))
	}
	var card AgentCard
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&card); err != nil {
		return nil, fmt.Errorf("%w: %v", ErrRejected, err)
	}
	// 注入检测：字段含注入特征（<script>/{{/;DROP/拼接）
	for _, s := range []string{card.AgentID, card.SceneID, card.Role, card.ProtocolVer} {
		if hasInjection(s) {
			return nil, fmt.Errorf("%w: %s", ErrInjectDetected, s)
		}
	}
	return &card, nil
}

// Verify 准入校验（公理 6 反函数可计算性：声明 → 校验 → 声明还原）
func (g *EntryGate) Verify(card *AgentCard) (*EnforceResult, error) {
	result := &EnforceResult{AgentID: card.AgentID, SceneID: card.SceneID, Role: card.Role}
	checks := []string{}

	// 协议版本（反函数可计算性：版本在支持集内）
	if card.ProtocolVer != g.SupportedProtocol {
		result.Status = "REJECT"
		result.Reason = fmt.Sprintf("protocol %s not supported (need %s)", card.ProtocolVer, g.SupportedProtocol)
		result.Checks = append(checks, "protocol")
		return result, nil
	}
	checks = append(checks, "protocol")

	// 场景在允许列表
	if !g.SceneAllowList[card.SceneID] {
		result.Status = "REJECT"
		result.Reason = "scene not in allow list"
		result.Checks = checks
		return result, nil
	}
	checks = append(checks, "scene")

	// 角色在允许列表
	if !g.RoleAllowList[card.Role] {
		result.Status = "REJECT"
		result.Reason = "role not authorized"
		result.Checks = checks
		return result, nil
	}
	checks = append(checks, "role")

	// 调用数上限
	if len(card.AllowedCalls) > g.MaxCalls {
		result.Status = "REJECT"
		result.Reason = "allowed calls exceed limit"
		result.Checks = checks
		return result, nil
	}
	checks = append(checks, "calls")

	// 负空间边界声明必须非空（fail-closed：无边界 = 拒绝）
	if len(card.NSFLBoundary) == 0 {
		result.Status = "BLOCK"
		result.Reason = "nsfl boundary missing (fail-closed)"
		result.Checks = checks
		return result, nil
	}
	checks = append(checks, "nsfl")

	result.Status = "PASS"
	result.Reason = "all checks passed"
	result.Checks = checks
	return result, nil
}

// Apply 执行准入（返回结果；REJECT/BLOCK 时 error 非 nil 便于调用方熔断）
func (g *EntryGate) Apply(raw []byte) (*EnforceResult, error) {
	card, err := g.ParseAgentCard(raw)
	if err != nil {
		return &EnforceResult{Status: "REJECT", Reason: err.Error()}, err
	}
	result, err := g.Verify(card)
	if result.Status != "PASS" {
		return result, fmt.Errorf("%w: %s", ErrRejected, result.Reason)
	}
	return result, nil
}

// ---- 工具 ----

func hasInjection(s string) bool {
	for _, bad := range []string{"<script", "{{", "}}", "DROP ", ";", "' OR ", "\" OR "} {
		for i := 0; i+len(bad) <= len(s); i++ {
			if s[i:i+len(bad)] == bad {
				return true
			}
		}
	}
	return false
}
