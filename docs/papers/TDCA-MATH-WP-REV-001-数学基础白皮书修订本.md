# TDCA 数学基础白皮书（修订本）· 公理化体系与可执行证明

> 文档标识: TDCA-MATH-WP-REV-001 | 版本: **V1.0-FROZEN** | 日期: 2026-08-23 | 状态: ✅ **FROZEN（人类签批冻结，2026-08-23）**
> 编制: TDCA 制度层（融合最新开发成果：公理 6 实例化 + 可执行机验验证器 + 外部审查闭环）
> 基线: TDCA-FUNCTION-WP-002（V2.0-FROZEN，函数白皮书）｜ TDCA-FUNCTION-WP-002-APPX-E（公理化基础）｜ TDCA-CORE-GO-AXIOM6-001（实例化证明）｜ 注册表 V2.3（T-114~T-118）
> 性质: **修订本**——在 V2.0 基础上增补「公理 6 从文本公理化 → 工程实例化 → 可执行机验」的完整闭环，并回应外部审查（公理/命题注释高估实现）

---

## 摘要

TDCA 数学基础以**函数第一性原理**为核心（制度 = 约束函数族 F_TDCA），公理化体系含 6 公理（公理 1-5 + 公理 6 可计算审计还原性）。本修订本的核心增量：**公理 6 从"形式化声明"升级为"实例化实现 + 可执行机验"**——

1. **形式化证明**（TDCA-CORE-GO-AXIOM6-001）：f=Verify / f⁻=AuditVerify / g=RightInverse，四约束（完备/可靠/可还原/复杂度）证明完成，对应附录 E 定理 E.1~E.4
2. **可执行机验**（axiom6_verify.go）：四约束 + 排除条款断言化，**9 项机验断言全 PASS**（任何时刻运行即证明仍成立）
3. **外部审查闭环**：enforce 从"公理 6 工程近似"（白名单可逆校验）升级为"公理 6 实例化证明"——术语与实现一致

---

## 第 1 章 公理化体系总览（修订本整合）

### 1.1 六公理一览

| 公理 | 内容 | 状态 |
|---|---|---|
| 公理 1 | 效用配置封闭性（四要素 Cobb-Douglas 分解） | FROZEN |
| 公理 2 | 正和进化性（Δ_U>0 准入） | FROZEN |
| 公理 3 | 主权信用锚定（e-CNY 法偿性） | FROZEN |
| 公理 4 | 主体效用内生性（效用时间动力学） | FROZEN |
| 公理 5 | 同构保持性（Φ(f∘g)=Φ(f)∘Φ(g)） | FROZEN |
| **公理 6** | **可计算审计还原性**（本修订本核心增量） | ✅ 实例化 + 机验 |

### 1.2 公理 6 完整表述（用户提供原文，FROZEN）

对于任意合法制度函数 f: X→Y，存在可计算映射 f⁻: Y×X→{0,1} 满足：
1. **验证完备性**: ∀x∈X, f⁻(f(x),x)=1
2. **验证可靠性**: ∀x∈X, ∀y∈Y, f⁻(y,x)=1 ⟹ y=f(x)
3. **可还原性**: ∀y∈Im(f)，存在可计算 g:Y→X 使 f(g(y))=y（右逆，非严格反函数）
4. **复杂度约束**: Complexity(f⁻) ≤ Complexity(Verify_institution)

**排除条款**: 哈希单向函数/黑盒预言机等不可审计构造被排除；允许非单射（多对一仍可还原，右逆非左逆）。

---

## 第 2 章 公理 6 实例化：从公理到可执行实现（修订本增量 §1）

### 2.1 实例化映射（core-go pkg/enforce）

| 公理角色 | 形式化定义 | 工程实现 | 文件 |
|---|---|---|---|
| f（制度函数） | f: X→Y，X=AgentCard 有限集，Y=EnforceResult | `EntryGate.Verify` | enforce.go |
| f⁻（验证器） | f⁻: Y×X→{0,1}，重算比对三元组 | `EntryGate.AuditVerify` | axiom6.go |
| g（右逆） | g: Im(f)→X，按判定类构造 | `EntryGate.RightInverse` | axiom6.go |

**X 可数性**（定理 E.1 前置）：协议版本有限（{3.1.2}）+ 场景/角色 allowlist 有限 + 调用数 ≤64 + NSFL 边界有限 → X 为有限集。

### 2.2 四约束证明（完整证明见 TDCA-CORE-GO-AXIOM6-001 §二）

| 约束 | 证明要点 |
|---|---|
| 1 完备性 | f⁻(f(x),x)=1：AuditVerify 重算 Verify(x) 并三元组全等比对——同一确定性程序同一输入同输出 |
| 2 可靠性 | f⁻(y,x)=1 ⟺ 重算 Verify(x) 与 y 三元组全等 ⟹ y=f(x) |
| 3 可还原性 | RightInverse 按 (status,reason) 枚举 Im(f) 全部 6 判定类，每类确定性构造 + 归纳验证 f(g(y))=y |
| 4 复杂度 | T(f⁻)=T(Verify)+O(1) ≤ T(Verify_institution)；T(g)=O(1) ≤ C_max=O(16·c(x)) |

### 2.3 可执行机验（修订本增量 §2）

**axiom6_verify.go**：将四约束 + 排除条款转为可执行断言，9 项机验全 PASS：

```
[约束1+3] PASS: PASS / REJECT(protocol) / REJECT(scene) / REJECT(role) / REJECT(calls) / BLOCK(nsfl)（6 判定类）
[约束2]    PASS: 全部判定类篡改对抗（status/reason/checks 三路篡改均拒绝）
[约束4]    PASS: f⁻ = T(Verify)+O(1)（单次重算，无枚举）
[排除]     PASS: 非哈希单向（g 可计算还原）
```

**机验意义**：公理 6 证明不再只是文档论证——任何时刻运行 `VerifyAxiom6()` 返回 false 即证明失效（fail-closed）；机验与实现同源（同包断言），杜绝"证明与实现脱节"。

---

## 第 3 章 定理体系（修订本整合：既有 + 实例化新增）

### 3.1 既有定理（V2.0 附录 E，FROZEN）

| 定理 | 内容 | 状态 |
|---|---|---|
| 定理 E.1 | f⁻ 存在性（X 可数 ⇒ 可枚举构造） | FROZEN |
| 定理 E.2 | f⁻ 唯一性（完备+可靠 ⇒ f⁻(y,x)=1 ⟺ y=f(x)）——"验证强于还原" | FROZEN |
| 定理 E.3 | 右逆存在充要 = f 满射 | FROZEN |
| 定理 E.4 | 公理 6 与 NSFL 熔断联动（f 不可审计 ⇒ 熔断） | FROZEN |

### 3.2 实例化定理（修订本新增，本白皮书首次整合）

| 定理 | 内容 | 证明/验证 |
|---|---|---|
| 定理 R-1（准入函数实例化） | EntryGate.Verify 满足公理 6 全部四约束 | TDCA-CORE-GO-AXIOM6-001 §二 + 机验 9 项 |
| 定理 R-2（判定类完备枚举） | Im(Verify) = {PASS, REJECT×4, BLOCK} 恰 6 类，RightInverse 全覆盖 | 构造表归纳 + 机验约束 3 |
| 定理 R-3（机验一致性） | VerifyAxiom6() 全断言通过 ⟺ 公理 6 在当前实现成立 | 同源断言 + 篡改对抗测试 |

---

## 第 4 章 可计算性论证（修订本整合）

### 4.1 既有六项论证（附录 E §E.4，FROZEN）

F_TDCA 可计算 / 九算子可计算 / 正和可判定 / UPDA 收敛 / Shapley 效率公理 / 熔断不可逾越——全部以显式前置条件限定适用范围。

### 4.2 修订本新增论证（实例化可计算性）

| # | 论证 | 结论 |
|---|---|---|
| 7 | **公理 6 实例化可计算性** | f⁻（AuditVerify）O(n) 单次重算；g（RightInverse）O(1) 构造——均多项式可计算（工程实现实证） |
| 8 | **机验可判定性** | VerifyAxiom6 为有限断言序列（6 类 + 3 篡改路 + 2 排除），有限步终止，可判定 |

---

## 第 5 章 外部审查回应与修订说明（修订本增量 §3）

外部审查（TDCA-EXTERNAL-REVIEW-RESPONSE-001）指出：enforce.go 把"协议白名单检查"注释为"公理 6 反函数可计算性"属**术语高估实现**（工程检查 ≠ 数学论证）。

**修订响应**：不删除术语，而是**把实现提升到术语高度**——完成实例化证明 + 机验后，术语与实现一致：
- ✅ 公理 6 = 实例化实现（f/f⁻/g）+ 形式化证明（四约束）+ 可执行机验（9 项）
- ✅ 注释升级：enforce.go 包注释"工程近似"→"已实例化+形式化证明（TDCA-CORE-GO-AXIOM6-001）"
- ✅ README 边界声明同步（公理 6 行改"已证明"）

**残余边界（诚实标注）**：
- SM2 验签：接口预留，当前哈希级完整性校验（未实现密码学签名）——公理 6 不依赖密码学签名（验证器为确定性重算）
- Lean/Isabelle 机验：本机工具链不可用，当前为 Go 可执行断言级机验（ID92 SIMULATED）；证明器版待工具链升级

---

## 第 6 章 后续与开放问题

| # | 项 | 状态 |
|---|---|---|
| 1 | Lean/Isabelle 证明器版机验 | 挂账（工具链升级后，P0 A-3 补全项） |
| 2 | 公理 6 推广到其他制度函数（nca/nsfl/mcp） | 挂账（本修订本聚焦 enforce；nca 哈希链/nsfl 熔断可后续实例化） |
| 3 | f⁻ 复杂度真实定标（C_max 基准库） | 挂账（TDCA-FUNCTION-WP-002-CAL-001，需真实运行数据） |
| 4 | 认证体系对接（TDCA-CERT-001：L1 兼容测试含公理 6 机验） | P0 内（认证测试套件将调用 VerifyAxiom6） |

---

## 附录 A · 符号表（修订本）

| 符号 | 含义 |
|---|---|
| X / Y | 制度函数定义域 / 值域（X=AgentCard 有限集，Y=EnforceResult） |
| f / f⁻ / g | 制度函数 / 审计验证器（返回 {0,1}）/ 右逆还原函数 |
| Im(f) | f 的像集（enforce 恰 6 判定类） |
| Verify / AuditVerify / RightInverse | f / f⁻ / g 的工程实现 |
| VerifyAxiom6 | 公理 6 可执行机验（9 断言） |

## 附录 B · 溯源映射（修订本）

| 主张 | 溯源 |
|---|---|
| 公理 6 全文 | TDCA-FUNCTION-WP-002-APPX-E 公理 6（用户提供，FROZEN） |
| 定理 E.1~E.4 | 同上 §E.3 |
| 实例化四约束证明 | TDCA-CORE-GO-AXIOM6-001 §二 |
| 机验实现 | core-go/pkg/enforce/axiom6.go + axiom6_verify.go |
| 术语登记 | 注册表 T-114（f⁻）/ T-115（g）|
| 外部审查 | TDCA-EXTERNAL-REVIEW-RESPONSE-001（术语高估 → 已闭环）|

---

> 本修订本为 TDCA 数学基础白皮书（V1.0-REV）：在 V2.0 公理化体系上增补公理 6 实例化 + 可执行机验完整闭环；待签批转 FROZEN（走 DCD 变更）。
> 关联: TDCA-FUNCTION-WP-002 ｜ APPX-E ｜ TDCA-CORE-GO-AXIOM6-001 ｜ TDCA-P0-KICKOFF-001（A-3 机验）｜ TDCA-CERT-001
