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
| C-14 | COORD-1 协商拓扑计数（对等式 C(n)=0+1+…+(n−1)；中枢式 n−1；单调性；下界） | lean-tdca/TDCA/Coord.lean（`coord1_base_0` / `coord1_base_1` / `coord1_base_3` / `coord1_base_4` / `pairwiseChannels_mono` / `pairwiseChannels_ge_sub_one` / `coord1_reduction_3` / `coord1_reduction_4` / `coord1_reduction_5`） | 本机机验（920 jobs／EXIT=0／sorry=0） | C1~C3；抽象计数骨架层；不标绝对安全 |
| C-15 | COORD-2 硬阈值二分类必存误分带（离散收窄版：阈值带 ＋ 类型翻转） | lean-tdca/TDCA/CoordThreshold.lean（`coord2_threshold_band_aux` / `coord2_threshold_band` / `coord2_flip` / `coord2_example`） | 本机机验（921 jobs／EXIT=0／sorry=0） | D1~D3；连续版需测度论·另列；不标绝对安全 |
| C-16 | COORD-5 回议发散（构造性必要性方向：重开无界 ⟹ 不存在静默轮） | lean-tdca/TDCA/CoordReopen.lean（`coord5_unbounded_no_silent` / `coord5_beyond_any_round` / `coord5_example`） | 本机机验（922 jobs／EXIT=0／sorry=0） | R1~R3；反方向需排中律／期望发散需概率论；不标绝对安全 |
| C-17 | M-5 负空间不可逾越（触发即不在定义域／熔断是映射行为／化合不剥离合规前置） | lean-tdca/TDCA/Guard.lean（`fuse_excludes_dom` / `fuse_not_bypassable` / `output_implies_not_trigger` / `decideOutput_iff` / `decideOutput_fail_closed` / `decideOutput_decidable` / `compose_guard_not_weaker` / `compose_trigger_blocks` / `guard_example`） | 本机机验（923 jobs／EXIT=0／sorry=0） | G1~G4；真实 C₁₆ 与触发判据属制度与工程层；不标绝对安全 |
| C-18 | P-6 熔断可判定性（判定正确性 ＋ fail-closed ＋ 二值完备） | 同上（Guard.lean）（`fuse_excludes_dom` / `fuse_not_bypassable` / `output_implies_not_trigger` / `decideOutput_iff` / `decideOutput_fail_closed` / `decideOutput_decidable` / `compose_guard_not_weaker` / `compose_trigger_blocks` / `guard_example`） | 同上 | 同上 |
| C-19 | P-3 公理 6 推广：抽象三约束（完备／可靠／右逆）⟹ 审计通过 ⟺ 记录在像内（且域内）；NCA 链（只增不减）与 NSFL 熔断器（像集裁剪）两实例同形 | lean-tdca/TDCA/Axiom6General.lean（`audit_iff_image_dom` / `restore_on_image` / `nca_append_mono` / `nca_audit_iff` / `fuse_complete_only_on_live` / `fuse_audit_iff` / `fuse_none_not_live` / `axiom6_general_two_instances`） | 本机机验（924 jobs／EXIT=0／sorry=0） | P3-1~P3-3；两实例为零依赖简化载体（非真实实现）；⚠️ 复杂度约束（第 4 条）不本件（照 C-12 属 conditional）；不标绝对安全 |
| C-20 | M-3 化合保持性：五可保持（＋可迭代归纳面）与 ε 累积线性上界（ε(n) = n·ε） | lean-tdca/TDCA/ComposePreserve.lean（`five_all_preserved` / `five_all_preserved_iter` / `epsAccum_eq` / `epsAccum_mono` / `epsAccum_le_linear` / `eps_example`） | 本机机验（925 jobs／EXIT=0／sorry=0） | M3-1~M3-3；⚠️ ε 以 Nat 承载（零依赖简化载体，真数版另列）；阈值／权重属策略层；不标绝对安全 |
| C-21 | M-4 分形归纳主定理（一般骨架）：可持续 ⟺ （基例 ∧ 各步） | lean-tdca/TDCA/FractalInduction.lean（`m4_induction` / `m4_sustainable` / `m4_sustainable_base` / `m4_sustainable_step` / `m4_sustainable_iff` / `m4_example`） | 本机机验（926 jobs／EXIT=0／sorry=0） | M4-1~M4-3；条件于 ID-96（以一般形态承载，其内容另件）；⚠️ L4 宏观层为 conditional 扩展·不绑入；不标绝对安全 |
| C-22 | P-7 五可充要性（定理 8.8 之机验面）：层内规模可持续 ⟺ （基元五可 ∧ 各步复合五可）；任一支缺失 ⟹ 不可持续；10^10 层仍五可 | lean-tdca/TDCA/P7FiveAll.lean（引用 M-3／M-4）（`iterCompose_eq_iterOp` / `p7_sufficient` / `p7_necessary` / `p7_necessary_obs` / `p7_necessary_met` / `p7_necessary_cfg` / `p7_necessary_aud` / `p7_necessary_fus` / `p7_step_preserved` / `p7_iff` / `p7_missing_unsustainable` / `p7_missing_obs` / `p7_missing_met` / `p7_missing_cfg` / `p7_missing_aud` / `p7_missing_fus` / `p7_at_scale` / `p7_scale_10b` / `p7_accum_bound` / `p7_accum_linear` / `p7_example` / `p7_example_gap` / `noFuse_iter_fus` / `p7_example_gap_scale`） | 本机机验（927 jobs／EXIT=0／sorry=0） | P7-1~P7-3；抽象归纳与化合骨架层（不承载制度层规模口径与阈值）；⚠️「熵增坍缩」取判定形态（非物理熵主张·照 C-11）；不标绝对安全 |
| C-23 | M-7 宪法一致性与定义域非空（兼 P-8 机验面）：C16 可满足 ⟹ 定义域非空；C16 在化合下保持（可迭代）；场景注入不改内核（双向）；同一见证满足各支 ⟹ 无内部冲突 | lean-tdca/TDCA/Constitution.lean（`m7_satisfiable` / `m7_dom_nonempty` / `m7_dom_of_sat` / `m7_kernel_compose` / `m7_kernel_iter` / `m7_inject_preserves` / `m7_inject_iter_preserves` / `m7_witness` / `m7_conj_consistent` / `m7_conj_consistent_iff` / `m7_example_sat` / `m7_example_dom` / `m7_example_kernel` / `m7_example_consistent`） | 本机机验（928 jobs／EXIT=0／sorry=0） | C1–C4；抽象一致性骨架层（不代拟宪法十六条逐条内容·属制度层）；不标绝对安全 |
| C-24 | P-11 归责映射之可形式化子集（结构面）：可上溯关系传递；上溯不降层；责任方向单向（上级不可回达下级）与分层隔离（平层不可互达）；无环（不存在自证责任循环） | lean-tdca/TDCA/Attribution.lean（`reaches_trans` / `reaches_pos_to_reaches` / `up_level_lt` / `reaches_level_le` / `reaches_pos_level_lt` / `no_downward` / `same_level_no_reach` / `p11_no_cycle` / `first_node_up` / `root_iff` / `root_no_reach` / `p11_example_leveled` / `p11_example_reaches` / `p11_example_pos` / `p11_example_no_cycle` / `p11_example_same_level` / `p11_example_first_node`） | 本机机验（929 jobs／EXIT=0／sorry=0） | A1–A3；抽象归责结构骨架层（不涉事实归责、不涉制度层判据与责任比例）；与 B-5 模型层预判相区分；不标绝对安全 |
| C-25 | M-6 三锚不动点（条件形态）：若锚映射与化合交换，则不动点集在化合下封闭（含任意深度），三锚齐备时其不动集为化合之不动子空间；契约不成立则复合面不可由契约保证 | lean-tdca/TDCA/Anchor.lean（`m6_fixed_closed` / `m6_fixed_subspace` / `m6_fixed_iter` / `m6_fixed_anchor` / `m6_commutes_needed` / `m6_comp_commutes` / `m6_triple_fixed` / `m6_example_commutes` / `m6_example_fixed` / `m6_example_closed` / `m6_example_iter`） | 本机机验（930 jobs／EXIT=0／sorry=0） | E1–E4；前提为接口交换契约（模拟态）故整体 conditional；抽象接口不变量骨架层；不涉真实结算／税收／版权链数据；不标绝对安全 |
| C-26 | P-5 认知距离不对称（命题 3.10）之机验面：认知结构对称 ⟹ 可达对称（不存在单向不对称）；存在单向边且反向不可达 ⟹ 可达性不对称；不对称可传递 | lean-tdca/TDCA/CogDist.lean（`reach_trans` / `reach_of_edge` / `reach_sym_of_symm` / `p5_no_asym_in_symm` / `p5_reach_iff_of_symm` / `p5_asym_of_oneway` / `p5_asym_trans` / `chainE_reach_le` / `p5_example_asym` / `symE_symm` / `p5_example_symm_reach` / `p5_example_no_asym`） | 本机机验（931 jobs／EXIT=0／sorry=0） | D1–D4；抽象认知图骨架层（以可达性承载不对称面；距离取值与 exp 形态另件）；不涉真实认知度量数据；不标绝对安全 |
| C-27 | P-13 场景形成机制可形式化子集之两栏边界与见证方向：退化域与判定域互补；结构面结论不得越栏（缺见证不可断言制度层结论）；给出见证即存在见证并可传递与合成；单调链之复合（含三段链） | lean-tdca/TDCA/SceneScope.lean（与前件 SceneEmergence.lean 同族）（`scope_degenerate_iff` / `scope_two_column` / `scope_no_cross` / `scope_witness_suffices` / `scope_witness_trans` / `scope_witness_chain` / `scope_monotone_comp` / `scope_monotone_comp3` / `scope_example_dc` / `scope_example_degenerate` / `scope_example_witness` / `scope_example_monotone_comp`） | 本机机验（932 jobs／EXIT=0／sorry=0） | S1–S4；抽象判定域与见证骨架层；阈值取值／意义本体／效用来源语义／否定方向半判定性／收敛性留制度与业务层；不标绝对安全 |
| C-28 | COORD-3 协调天花板（条件形态）：H1（每步严格递增）⟹ 起点增益为正；H2（凹性 · 增益递减）＋ 某处增益非正 ⟹ 该处起增益恒非正（天花板）；H1 ⟹ 任意处增益不为非正（无天花板） | lean-tdca/TDCA/CoordCeiling.lean（`coord3_start_positive` / `coord3_ceiling_step` / `coord3_ceiling_aux` / `coord3_ceiling` / `coord3_no_ceiling` / `coord3_dichotomy` / `coord3_example_const` / `coord3_example_strict` / `coord3_example_concave`） | 本机机验（934 jobs／EXIT=0／sorry=0） | C3-1–C3-4（离散载体；实数与导数形态另议）；离散版 H3 为开放问题·本件不涉；抽象序列骨架层；不标绝对安全 |
| C-29 | COORD-4 分层最优性（条件形态）：层数上限内必有一层成本最小（最优层数存在）；每层固定切换成本 ⟹ k 层累积至少 k·c（分层非免费）；存在层数其总成本不高于基准 ⟺ 分层可行 | lean-tdca/TDCA/CoordLayering.lean（`coord4_optimal_exists` / `coord4_switch_linear` / `coord4_layering_beneficial` / `coord4_layering_not_beneficial` / `coord4_example_optimal` / `coord4_example_switch` / `coord4_example_beneficial`） | 本机机验（934 jobs／EXIT=0／sorry=0） | C4-1–C4-4（离散载体；缩减因子与实数形态另议）；层数上限取值属策略层；抽象成本骨架层；不标绝对安全 |
| C-30 | COORD-6 错觉循环不动点（离散有界情形 · 条件形态）：自增强（未达不动点则每步严格减）⟹ 一致压缩率（c = 1）；迭代单调不增；有限步到达不动点；不动点唯一；全局收敛形态 | lean-tdca/TDCA/CoordLoop.lean（`coord6_self_implies_uniform` / `coord6_contract_one` / `coord6_iter_le` / `coord6_reaches_zero` / `coord6_unique_fixed` / `coord6_global_convergence` / `coord6_example_self` / `coord6_example_uniform` / `coord6_example_zero_fixed` / `coord6_example_converge`） | 本机机验（935 jobs／EXIT=0／sorry=0） | C6-1–C6-4（自然数承载；实数与连续情形另件另议，本件不冒充 Banach 不动点定理）；抽象迭代骨架层；不标绝对安全 |
| C-31 | 三空间真值 L1（互斥／合取封闭／无补） | lean-tdca/TDCA/TruthSpace.lean（`tri_mutex_pos_neg` / `tri_mutex_neg_und` / `tri_mutex_pos_und` / `pos_meet_closed` / `neg_excluded_middle_fails` / `und_excluded_middle_fails` / `pos_excluded_middle_holds` / `tri_exhaustive_or_anchor` / `excluded_middle_not_universal`） | 本机机验通过 · CI 待开 | T-1~T-4＋辅证 A-1~A-3；四点链离散可判定载体（⛔ 非完整海廷代数主张）；不标绝对安全 |
| C-32 | 成本正定性（条件化） | lean-tdca/TDCA/EconEmbed.lean（`cost_pos_of_erase` / `erase_zero_of_cost_zero`） | 本机机验通过 · CI 待开 | E-1~E-3；⭐ 条件化命题（正性公理为显式假设，⛔ 非「生成必有成本」）；ℕ 离散承载（ℚ 形态另件）；不标绝对安全 |

> 附注（归级偏离说明）：初拟时曾考虑新增 Tier B 条目；按上表纪律，Tier B 须「绑定证明文件 + 适用边界声明」——本批内容**尚待证明器机验**，故**不列 Tier B**，统一归 Tier C。
>
> 附注（**条件形态标注**）：**C-12 为显式 `conditional` 项**——其成立**条件于**建模假设 `L-ε`。依「三态原则」（`proved` / `refuted` / `conditional` 皆合法终态），**标注条件形态本身即为合规终态**，不视为缺陷或未完成。
>
> 附注（**复合并保持性命题的表述边界**）：与「复合」「保持性」相关的命题**已给出形式化陈述与证明尝试**；其中**归纳步骨架**已**通过证明器机验**（`Induction.lean` 占位证明已清零，2026-09-14）。⚠️ **惟**：① 该骨架**只及抽象层**（`Five` 为任意谓词族），**「五可」等制度层语义不在其范围**；② 主定理**仍带 `conditional` 适用范围标注**；③ **存在性前提仍未决**（属设计决策，非本骨架所证）。因此 ⛔ **不得**在任何对外材料中声称「复合与保持性已形式化证明」或任何等价表述；如需引用，**只能**表述为「**已给出形式化陈述，归纳步骨架已通过证明器机验；制度层结论与存在性前提仍待定**」。
>
> 【注】本行机验载 934，系 COORD-3 与 COORD-4 两件合建之记；本件（COORD-3）单件实跑为 933。数照原载不改，仅此注。注记日期 2026-10-02。（C-28 行加注；落点：表下单列，不扰表格列数。）
>
> 【附注 · 实验线支撑件（主张无变更）】以下各行为**实验／复核线**之支撑件号，⛔ 不构成声称之升级、⛔ 不构成证明之替代、⛔ 不改本表任何数值与状态；数据性质：有限模型／SIMULATED（ID92）。
> · C-1（P-3／P-6）：实验支撑（P-3 抽象四约束 ＋ NCA 链与 NSFL 熔断器两实例）。主张不变。
> · C-4（P-7）：结构面支撑（M-4 归纳步 ＋ P-7 结构面）；五可之制度语义面不在该线。主张不变。
> · C-5（P-8）：实验支撑（M-7 宪法一致性与定义域非空）。主张不变。
> · C-6（P-9）：仅设计面（接口不变量设计件）；真实验证依赖外部基础设施。主张不变。
> · C-9／C-12（P-12）：对照面（七命题现状对照增补），⛔ 非新证。主张不变。
> · C-10（P-11／P-13）：实验支撑（归责映射可机验子集 ／ 场景形成机制子集）。主张不变。
> · C-2（P-4）：外部依赖（缺真实基准数据）。主张不变。
> · 协调原理簇（COORD-1~COORD-6）：实验支撑。主张不变。
> 附注日期 2026-10-03；本附注为追加制，⛔ 不回改既有行。

## 四、规则

1. **声称必须可溯源**：Tier A/B 绑定证明文件；Tier C 标 [proof: pending]（不挂公理名）
2. **不标"绝对安全"**：A/B 均附模型假设 + 适用范围
3. **同步纪律**：证明随代码演进走 DCD 变更；机验（VerifyAxiom6）自动检测失效
4. 外部贡献：新增声称/证明走开源协作宣言 + DCD 门禁
5. 条目 ↔ 定理之写法（双向索引）：Tier A/B 各自「证明文件」列、Tier C 之证明列，
   凡涉 Lean 件者，一律按「件路径（定理名1 / 定理名2 / …）」书写：
   ① 件路径为相对仓库根之 POSIX 路径；
   ② 定理名以反引号包裹，多个以「 / 」（前后各一空格）分隔；
   ③ 只列该件承载本条声称之定理，不列无关定理；
   ④ 本条只定写法，不改任何声称、数值、状态与适用范围；
   ⑤ 改名/重构后之核对＝周期性抽查（照 §四 3 同向），不追求实时。

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
