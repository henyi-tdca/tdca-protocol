# TDCA Claims–Proof Matrix（声称-证明对照清单）

> 文档: TDCA-CLAIMS-MATRIX-001 ｜ 版本: V1.0 ｜ 日期: 2026-08-23 ｜ 状态: ✅ 发布（分层开源 Tier A/B/C 标注）
> 用途: 全仓"公理/命题/定理"声称逐项绑定证明文件或 [proof: pending] 标注——消除"声称超前于证据"（外部核查项）
> 纪律: 任何新增声称必须在本表登记（Tier + 证明引用）；未登记声称视为无效

---

## 一、Tier A · 已证且稳定（证明文件同库）

| # | 声称 | 证明文件 | 机验 | 模型假设/适用范围 |
|---|---|---|---|---|
| A-1 | 公理 6 可计算审计还原性（enforce 实例化：f=Verify / f⁻=AuditVerify / g=RightInverse） | `TDCA-CORE-GO-AXIOM6-001` + `pkg/enforce/axiom6.go` | ✅ `VerifyAxiom6()` 9 断言全 PASS | X=AgentCard 有限集；模型假设：白名单可逆校验（非形式化数学证明的替代——见数学基础白皮书 §2）；**不标"绝对安全"** |
> 注（证明器通道 · Lean）：上述公理 6 可计算审计还原性，已于证明器侧给出形式化陈述并入库
> —— `lean-tdca/TDCA/Axiom6.lean`：约束 1 完备性（`constraint1_completeness`）／约束 2 可靠性
> （`constraint2_soundness`）／约束 3 可还原性·甲′（`constraint3_right_inverse`，三前提）。
> ⚠️ 适用范围＝抽象层（`D` 为有限类型），⛔ 不重复 Go 通道的制度实例，⛔ 不得据以表述制度层结论；
> ⛔ 本注仅增列证明器通道，不改 Go 通道结论与其适用范围。
| A-2 | 定理 E.1~E.4（存在性/唯一性/右逆充要/NSFL 联动） | `TDCA-FUNCTION-WP-002-APPX-E`（FROZEN） | 框架级（机验待 P-1） | 集合论标准框架；X 可数前置 |
| A-3 | 命题 P4a：C < q(1−p)R ⟹ T_process 严格占优（原 B-3） | `research/papers/formal/TDCA-P4a-Corollary2-Lean4-Candidate-V1.2.lean`（研究侧引用·不入库，与 P-3/P-4「artifacts 不进主仓」同源） + `core-go/docs/formal-proofs/lean/TDCA/ExPostTrust.lean` | ✅ `lake env lean` 零 error（PR #127 / 机验通道）；模型假设：单次协作、C 由 A 承担；**不标"绝对安全"** |
| A-4 | 推论 2：α ↑ ⟹ e_B* ↓（攫取问题的比较静态，原 B-4） | 同上 | ✅ `lake env lean` 零 error + `sorry` = 0（PR #128 后机验）；模型假设与适用范围见件头 |
| A-5 | N-1 失效半径有界性：信任链单点失效向下传导、向上隔离，不全局重置，既有记录不失效 | `lean-tdca/TDCA/FailureRadius.lean`（`isolation` / `no_global_reset` / `downward_reaches` / `prior_records_survive` 等） | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（lean-verify.yml `lean-tdca` job，首跑未跑）；模型假设：A1 信任链＝分支有限集合、向下传导＝分支内位置序号增大方向；A2 失效事件带在链证据（无链外失效）；A3/A4 affected／survives 定义即刻画；A5 不建模跨分支共享状态；适用范围＝抽象骨架层，密钥轮换／重锚等动态属工程层；**不标"绝对安全"** |
| A-6 | N-2 信任根分级 ↔ 场景密级：接入判定 fail-closed（层级不达标即拒），放行集对密级向下封闭 | `lean-tdca/TDCA/Admission.lean`（`requiredLevel_mono` / `admit_iff` / `admit_reject_high_low` / `admit_downward_closed`） | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上）；模型假设：B1 信任根四级与场景密级均为 ℕ 全序离散梯级；B2 层级只表信任强度不表身份；B3 requiredLevel 单调不减（恒等实现，任何单调实现可替换）；B4 fail-closed 无「告警后放行」；B5 判定只依赖（密级，根层级）两参；**不标"绝对安全"** |
| A-7 | N-3 制度准入状态机（七态）：迁移封闭刻画、非熔断态出边完备、熔断为终态、降级/暂停出边受限、入 certified 必附编译通过证据 | `lean-tdca/TDCA/Admission.lean`（`AdmTrans_iff_AdmSucc` / `AdmTrans_complete` / `fused_terminal` / `degraded_out_only` / `suspended_out_only` / `certified_requires_compile`） | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上）；模型假设：A1 态为裸枚举无身份载荷；A2 certified ⟺ 准入编译通过证据；A3 迁移由归纳定义封闭列出（未列出即非法）；A4 熔断终态、回出＝重走注册流程（治理动作，不在机内）；适用范围＝协议层准入守卫抽象骨架；**不标"绝对安全"** |
| A-8 | N-4 版本对齐 fail-closed：制度版本与检查器版本失配 ⟹ 拒；缺信息 ⟹ 拒；发布门＝版本门 ∧ 工件断言门（与「先工件后制度」同一根） | `lean-tdca/TDCA/VersionAlignment.lean`（`deny_on_mismatch` / `no_fail_open` / `deny_none_left` / `release_requires_both` 等） | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上）；模型假设：A1 两版本均以 ℕ 承载可比可判等；A2 失配判据 decide 形态可计算；A3 缺信息（none）即 false 无默认放行；A4 发布门单一合取；A5 真实 CI 接线属工程层、接口层结论判 conditional（SIMULATED 现状不可核）；**不标"绝对安全"** |
| A-9 | N-5 双锚一致性：分配效力 ⟺ 格式锚过 ∧ 效用锚定；可连不可分；双锚相互独立（见证态机验）；效用锚硬下限不可伪造 | `lean-tdca/TDCA/DualAnchor.lean`（`alloc_requires_both` / `connect_but_not_alloc` / `connect_not_sufficient` / `anchor_not_sufficient` 等） | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上）；模型假设：A1 格式锚＝内核可检 Bool 通过位、效用锚定 ⟺ floor ≤ declared；A2 stdFloor=1（零/负声明不得锚定）；A3 allocatable 与 connectable 为不同谓词不得互推；A4 独立性以 formatOnly／utilityOnly 见证态机验；A5 真实效用接口 SIMULATED，接口层结论判 conditional；**不标"绝对安全"** |
| A-10 | N-6 负空间（底线）迁移不变量：底线只增不减；迁移不删除（出处有落）；迁移须签批留痕；登记簿良态在再修订下保持 | `lean-tdca/TDCA/NegativeSpace.lean`（`baseline_mono` / `relocate_lands` / `migrate_signed` / `invariant_chain`） | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上）；模型假设：A1 三域 State、条目裸 id 无身份语义；A2 底线＝负空间投影 ∪ sc ∪ pr、迁移以「同 id 换状态标记」留痕不减；A3 合法修订封闭列出（迁移须 approved=true ∧ precedent>0）；A4 签批权归属属治理层不入件；A5 不建模时间与并发；A6 不假设 id 唯一；**不标"绝对安全"** |
| A-11 | N-7 快慢接口存在性：合法快系统必有异常上报与人类介入口子；缺上报口子 ⟹ 异常可被压制（可被劫持）；快慢为合法性分工、非性能分工 | `lean-tdca/TDCA/FastSlow.lean`（`report_channel_exists` / `human_channel_exists` / `gap_implies_hijack` / `no_performance_claims` 等） | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上）；模型假设：A1 本件不含任何性能字段／性能声明；A2 快系统＝上报通道清单＋人类介入通道清单；A3 legit ⟺ 两清单均非空；A4 suppressible ⟺ 上报通道为空；A5 真实裁决接口属工程层、接口层结论判 conditional（SIMULATED 现状不可核）；**不标"绝对安全"** |

## 二、Tier B · 已证但边界待定（证明 + 适用边界声明）

| # | 声称 | 证明文件 | 状态 |
|---|---|---|---|
| B-1 | 命题 3.10 认知距离不对称（d_cognitive(a,b) ≠ d_cognitive(b,a)） | 权威锚 AUTHORITY-CONSTITUTION L2582-2585（定义引用） | 🔶 无独立证明文件——**P-5 开放问题**（吸引专家） |
| B-2 | 定理 2.2 配置权右逆（φ(g(φ(x)))=φ(x)） | TDCA-FUNCTION-WP-002 §2（证明框架） | 🔶 框架级，未机验 |
| B-5 | 分层归责预判：智能体 = 可归责第一节点，委托人 = 最终责任主体（路径三） | WP-MATERIALISM-001 V1.2 §2.2.2 | 🔶 模型层预判，非事实层断言；随 §2.2.2.6 四信号检验，证伪则修订 |

## 三、Tier C · 进行中/未定稿（[proof: pending]，不挂公理名）

| # | 声称 | 状态 |
|---|---|---|
| C-1 | 公理 6 推广到 NCA 哈希链 / NSFL 熔断器 | [proof: pending] —— **P-3 开放问题** |
| C-2 | f⁻ 复杂度 C_max 真实定标（T-118） | [proof: pending] —— **P-4 开放问题**（SIMULATED 候选） |
| C-3 | Lean/Isabelle 证明器版机验 | [proof: pending] —— **P-1 开放问题**（工具链受限） |
| C-4 | 五可充要性定理 8.8 完整证明 | [proof: pending] —— **P-7 开放问题** |
| C-5 | 宪法十六条全函数化形式化 | [proof: pending] —— **P-8 开放问题** |
| C-6 | 三锚（e-CNY/税收/版权链）验证框架 | [proof: pending] —— **P-9 开放问题**（SIMULATED ID92） |
| C-7 | 推论 2 的 α=0 社会最优校验 + FOC 由凹性证出（分析核心） | [proof: pending] —— 见 Lean 文件尾注 checklist [2][3]；**机验通道已建**（`core-go/docs/formal-proofs/lean/`）；**[1] 已由 corollary2 全证覆盖；[2][3] 仍 pending** |
| C-8 | 法律演化四信号（FATF VASP 裁定 / 代理行为可归责立法 / 智能体税务触发节点 / 首份合同获承认） | [proof: pending] —— 外部事实信号，非证明义务；按 EVO-001 可审计等待 |
| C-9 | 元函数可显影定理的基例层（完备性 / 可靠性 / 反射广义逆的存在性，抽象层陈述） | [proof: pending] —— 形式化陈述已备（证明器工程骨架）；**有限模型可执行断言 8/8 PASS**；证明器机验待工具链；**对应 P-12** |
| C-10 | 场景形成机制的形式化子集（含跃迁充分性的**见证方向**判据） | [proof: pending] —— **可形式化子集已显式声明**（可进证明器 / 留在业务与制度层两栏）；**对应 P-13** |
| C-11 | 记录通道熵界：**结构（文法）层**的描述长度增长为对数并趋于饱和；**观测数据**的信息量不受治理影响 | [proof: pending] —— **首轮代理度量**（结构层对数形态 12/12；数据层线性 10/12）；属**模型层**，**非物理定律主张**；样本为合成场景数据（SIMULATED） |
| C-12 | 化合保持性（复合与嵌套下反射广义逆的存在与保持） | [proof: pending] —— **条件于建模假设 `L-ε`（每步耦合误差一致有界）**：**该假设不是数学定理、无法被证明**；若 `L-ε` 不成立，则本项降为**条件形态**（`conditional`）。**不得**读作「无条件成立」；**对应 P-12**（纲领承重分支） |
| C-13 | 通知机（Notification Machine）设计层可形式化性质：① 七状态机：`lean-tdca/TDCA/Admission.lean` 本机已机验（迁移完备／熔断终态／降级·暂停出边受限，sorry=0）；CI 机验通道落地中（lean-verify.yml `lean-tdca` job，首跑未跑）② FactChain（链式哈希单调性 / 不可篡改）③ SE 签名（签名可验证性；与公理 6 的 `f` / `f⁻` 对同构）④ NCA-Lite（轻量存证的完备性 / 一致性） | [proof: pending] —— **SIMULATED**（设计层为模拟态，未见实物实现） |

> 附注（归级偏离说明）：初拟时曾考虑新增 Tier B 条目；按上表纪律，Tier B 须「绑定证明文件 + 适用边界声明」——本批内容**尚待证明器机验**，故**不列 Tier B**，统一归 Tier C。
>
> 附注（**条件形态标注**）：**C-12 为显式 `conditional` 项**——其成立**条件于**建模假设 `L-ε`。依「三态原则」（`proved` / `refuted` / `conditional` 皆合法终态），**标注条件形态本身即为合规终态**，不视为缺陷或未完成。
>
> 附注（**复合并保持性命题的表述边界**）：与「复合」「保持性」相关的命题**已给出形式化陈述与证明尝试**；其中**归纳步骨架**已**通过证明器机验**（`Induction.lean` 占位证明已清零，2026-09-14）。⚠️ **惟**：① 该骨架**只及抽象层**（`Five` 为任意谓词族），**「五可」等制度层语义不在其范围**；② 主定理**仍带 `conditional` 适用范围标注**；③ **存在性前提仍未决**（属设计决策，非本骨架所证）。因此 ⛔ **不得**在任何对外材料中声称「复合与保持性已形式化证明」或任何等价表述；如需引用，**只能**表述为「**已给出形式化陈述，归纳步骨架已通过证明器机验；制度层结论与存在性前提仍待定**」。

## 四、规则

1. **声称必须可溯源**：Tier A/B 绑定证明文件；Tier C 标 [proof: pending]（不挂公理名）
2. **不标"绝对安全"**：A/B 均附模型假设 + 适用范围
3. **同步纪律**：证明随代码演进走 DCD 变更；机验（VerifyAxiom6）自动检测失效
4. 外部贡献：新增声称/证明走开源协作宣言 + DCD 门禁

### §五 三层归档原则（P3 × Tier 映射）

| 层 | 性质 | 归档去向 | "闭环"标准 |
| --- | --- | --- | --- |
| 事实层 | 存在性即正当性，不可辩驳 | 免判据，不入矩阵 Tier | 无需闭环 |
| 模型层 | 有损压缩，可竞争可证伪 | Tier A/B/C，走证明器 | proved / refuted / conditional 三态 |
| 制度层 | 建构物，活规则 | 不入 Tier，走 DCD 存证 | 修订程序闭环，永不走证明器 |

新增声称须先声明所属层，再按该层标准归档；跨层引用须注明层间映射。

---

> 本矩阵为分层开源 Tier 标注依据（A 已证 / B 边界待定 / C pending）；随推送发布，社区可独立核验。
> 关联: TDCA-MATH-WP-REV-001 ｜ TDCA-FORMAL-OPEN-PROBLEMS-001 ｜ TDCA-STRATEGY-FORMAL-OPEN-002
