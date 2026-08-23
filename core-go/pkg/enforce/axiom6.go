// 公理 6 实例化实现（TDCA-CORE-GO-AXIOM6-001 形式化证明）
//
// 将 pkg/enforce 准入从「白名单工程检查」升级为公理 6（可计算审计还原性）的
// 实例化实现——制度函数 f: X→Y（Verify）配套：
//   - f⁻ 验证器 AuditVerify（完备性+可靠性，返回 {0,1}，非反函数——消歧 T-114）
//   - 右逆 g RightInverse（可还原性，∀y∈Im(f): f(g(y))=y——T-115）
//
// 四约束证明见 TDCA-CORE-GO-AXIOM6-001（对应附录 E 定理 E.1~E.4）。
// 两函数均为纯函数（无副作用、不触碰 gate 状态——并发安全），供 EIOS Auditor /
// NCA 确权审计调用（定理 7.1 / 8.4 绑定）。
// SPDX-License-Identifier: Apache-2.0
package enforce

// AuditVerify 公理 6 验证器 f⁻: Y×X→{0,1}。
//
// 完备性: ∀x∈X, f⁻(f(x),x)=1——重算 Verify(x) 与 y 三元组全等。
// 可靠性: f⁻(y,x)=1 ⟹ y=f(x)——全等比对直接推出。
// 复杂度: T(f⁻) = T(Verify) + O(1) ≤ T(Verify_institution)（约束 4 满足）。
func (g *EntryGate) AuditVerify(y EnforceResult, x AgentCard) bool {
	// 重算 f(x)（确定性程序，同一输入同一输出）
	res, err := g.Verify(&x)
	if err != nil || res == nil {
		return false
	}
	// 三元组（status/reason/checks）全等判定
	return res.Status == y.Status && res.Reason == y.Reason && equalStrings(res.Checks, y.Checks)
}

// RightInverse 公理 6 右逆 g: Im(f)→X（还原函数，非严格反函数）。
//
// ∀y∈Im(f): Verify(g(y)) == y——按 (status, reason) 枚举 Im(f) 判定类，
// 每类确定性构造最小违规/合规卡片（构造表见 TDCA-CORE-GO-AXIOM6-001 §三）。
// 复杂度: O(1) 字段赋值（约束 4 满足）。
func (g *EntryGate) RightInverse(y EnforceResult) (AgentCard, bool) {
	base := AgentCard{
		AgentID:      "NM-001",
		ProtocolVer:  g.SupportedProtocol,
		SceneID:      "scene-phy-notification",
		Role:         "NM-Operator",
		AllowedCalls: []string{"verify"},
		NSFLBoundary: []string{"no-tamper"},
	}
	switch {
	case y.Status == "PASS":
		return base, true
	case y.Status == "REJECT" && y.Reason == "protocol 9.9.9 not supported (need "+g.SupportedProtocol+")":
		base.ProtocolVer = "9.9.9"
		return base, true
	case y.Status == "REJECT" && y.Reason == "scene not in allow list":
		base.SceneID = "scene-unknown"
		return base, true
	case y.Status == "REJECT" && y.Reason == "role not authorized":
		base.Role = "ROLE-UNKNOWN"
		return base, true
	case y.Status == "REJECT" && y.Reason == "allowed calls exceed limit":
		base.AllowedCalls = make([]string, g.MaxCalls+1)
		for i := range base.AllowedCalls {
			base.AllowedCalls[i] = "call"
		}
		return base, true
	case y.Status == "BLOCK" && y.Reason == "nsfl boundary missing (fail-closed)":
		base.NSFLBoundary = []string{}
		return base, true
	default:
		// Im(f) 之外或未覆盖判定——不可还原
		return AgentCard{}, false
	}
}

// equalStrings 有序切片逐元素比对（checks 判定路径有序）。
func equalStrings(a, b []string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}
