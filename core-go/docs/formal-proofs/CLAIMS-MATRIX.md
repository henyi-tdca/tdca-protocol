# TDCA Claims–Proof Matrix（声称-证明对照清单）

> 文档: TDCA-CLAIMS-MATRIX-001 ｜ 版本: V1.0 ｜ 日期: 2026-08-23 ｜ 状态: ✅ 发布（分层开源 Tier A/B/C 标注）
> 用途: 全仓"公理/命题/定理"声称逐项绑定证明文件或 [proof: pending] 标注——消除"声称超前于证据"（外部核查项）
> 纪律: 任何新增声称必须在本表登记（Tier + 证明引用）；未登记声称视为无效

---

## 一、Tier A · 已证且稳定（证明文件同库）

| # | 声称 | 证明文件 | 机验 | 模型假设/适用范围 |
|---|---|---|---|---|
| A-1 | 公理 6 可计算审计还原性（enforce 实例化：f=Verify / f⁻=AuditVerify / g=RightInverse） | `TDCA-CORE-GO-AXIOM6-001` + `pkg/enforce/axiom6.go` | ✅ `VerifyAxiom6()` 9 断言全 PASS | X=AgentCard 有限集；模型假设：白名单可逆校验（非形式化数学证明的替代——见数学基础白皮书 §2）；**不标"绝对安全"** |
| A-2 | 定理 E.1~E.4（存在性/唯一性/右逆充要/NSFL 联动） | `TDCA-FUNCTION-WP-002-APPX-E`（FROZEN） | 框架级（机验待 P-1） | 集合论标准框架；X 可数前置 |

## 二、Tier B · 已证但边界待定（证明 + 适用边界声明）

| # | 声称 | 证明文件 | 状态 |
|---|---|---|---|
| B-1 | 命题 3.10 认知距离不对称（d_cognitive(a,b) ≠ d_cognitive(b,a)） | 权威锚 AUTHORITY-CONSTITUTION L2582-2585（定义引用） | 🔶 无独立证明文件——**P-5 开放问题**（吸引专家） |
| B-2 | 定理 2.2 配置权右逆（φ(g(φ(x)))=φ(x)） | TDCA-FUNCTION-WP-002 §2（证明框架） | 🔶 框架级，未机验 |

## 三、Tier C · 进行中/未定稿（[proof: pending]，不挂公理名）

| # | 声称 | 状态 |
|---|---|---|
| C-1 | 公理 6 推广到 NCA 哈希链 / NSFL 熔断器 | [proof: pending] —— **P-3 开放问题** |
| C-2 | f⁻ 复杂度 C_max 真实定标（T-118） | [proof: pending] —— **P-4 开放问题**（SIMULATED 候选） |
| C-3 | Lean/Isabelle 证明器版机验 | [proof: pending] —— **P-1 开放问题**（工具链受限） |
| C-4 | 五可充要性定理 8.8 完整证明 | [proof: pending] —— **P-7 开放问题** |
| C-5 | 宪法十六条全函数化形式化 | [proof: pending] —— **P-8 开放问题** |
| C-6 | 三锚（e-CNY/税收/版权链）验证框架 | [proof: pending] —— **P-9 开放问题**（SIMULATED ID92） |

## 四、规则

1. **声称必须可溯源**：Tier A/B 绑定证明文件；Tier C 标 [proof: pending]（不挂公理名）
2. **不标"绝对安全"**：A/B 均附模型假设 + 适用范围
3. **同步纪律**：证明随代码演进走 DCD 变更；机验（VerifyAxiom6）自动检测失效
4. 外部贡献：新增声称/证明走开源协作宣言 + DCD 门禁

---

> 本矩阵为分层开源 Tier 标注依据（A 已证 / B 边界待定 / C pending）；随推送发布，社区可独立核验。
> 关联: TDCA-MATH-WP-REV-001 ｜ TDCA-FORMAL-OPEN-PROBLEMS-001 ｜ TDCA-STRATEGY-FORMAL-OPEN-002
