# Axiom 6 — Computable Audit-Invertibility（Formal Proof, Published）

> 文档: AXIOM6-PROOF ｜ 版本: V1.0 ｜ 日期: 2026-08-23 ｜ 状态: ✅ 发布（Tier A：已证且稳定）
> 权威全文: `TDCA-CORE-GO-AXIOM6-001`（tdca-thinktank，Reasonix 制度层）｜ 数学基础: `TDCA-MATH-WP-REV-001`（V1.0-FROZEN）
> 实现: `core-go/pkg/enforce/axiom6.go` + `axiom6_verify.go`（Apache-2.0）

---

## 一、公理 6 表述

对于任意合法制度函数 f: X→Y，存在可计算映射 f⁻: Y×X→{0,1} 满足：
1. **验证完备性**: ∀x∈X, f⁻(f(x),x)=1
2. **验证可靠性**: ∀x∈X, ∀y∈Y, f⁻(y,x)=1 ⟹ y=f(x)
3. **可还原性**: ∀y∈Im(f)，存在可计算 g:Y→X 使 f(g(y))=y（右逆，非严格反函数）
4. **复杂度约束**: Complexity(f⁻) ≤ Complexity(Verify_institution)

**排除条款**: 哈希单向函数/黑盒预言机不可审计构造被排除；允许非单射（多对一仍可还原）。

## 二、实例化（enforce 准入门禁）

| 角色 | 定义 | 实现 |
|---|---|---|
| f | f: X→Y，X=AgentCard 有限集，Y=EnforceResult | `EntryGate.Verify` |
| f⁻ | f⁻(y,x)=1 ⟺ 重算 Verify(x) 与 y 三元组全等 | `EntryGate.AuditVerify` |
| g | g(y)=按 (status,reason) 构造最小违规/合规卡片 | `EntryGate.RightInverse` |

## 三、四约束证明要点

| 约束 | 证明 |
|---|---|
| 1 完备性 | AuditVerify 重算 Verify(x)（确定性程序同一输入同输出）→ 三元组全等 → 1 |
| 2 可靠性 | AuditVerify=1 ⟺ 重算与 y 全等 ⟹ y=f(x) |
| 3 可还原性 | RightInverse 枚举 Im(f) 全 6 判定类（PASS/REJECT×4/BLOCK），每类确定性构造 + 归纳验证 f(g(y))=y |
| 4 复杂度 | T(f⁻)=T(Verify)+O(1) ≤ T(Verify_institution)；T(g)=O(1) |

## 四、机器验证（可执行）

```bash
cd core-go && go test ./pkg/enforce/ -run VerifyAxiom6 -v
```

输出 9 项断言（约束 1+3 六判定类 / 约束 2 篡改对抗 / 约束 4 复杂度 / 排除条款）全 PASS。
**机验意义**：证明不再是文档论证——`VerifyAxiom6()` 返回 false 即证明失效（fail-closed）。

## 五、模型假设与适用范围（重要，勿误读）

- **适用范围**：enforce 准入函数（白名单可逆校验）的审计可还原性
- **模型假设**：X=AgentCard 有限集；f 为确定性程序
- **不标"绝对安全"**：本证明覆盖"可审计还原性"，不覆盖密码学安全、部署安全、经济-博弈攻击（后者由制度防线覆盖——见 TDCA-SECURITY-INSTITUTIONAL-001）
- **残余**：SM2 验签为接口预留（哈希级校验）；Lean 证明器版为 P-1 开放问题

## 六、外部贡献

- 证明器移植（Lean/Isabelle）：开放问题 P-1
- 推广到 NCA/NSFL：开放问题 P-3
- 详见 `TDCA-FORMAL-OPEN-PROBLEMS-001`（9 项开放问题）

---

> 本证明为公理 6 实例化发布版（Tier A）；权威全文在 tdca-thinktank，随 core-go 推送。
> 关联: TDCA-MATH-WP-REV-001 ｜ CLAIMS-MATRIX.md ｜ INSTITUTION-HASHES.md
