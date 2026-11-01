# TDCA 形式化结论上架填报表 · Tier A 第二批 10 条

> 件号：`TDCA-HANDOFF-EXEC-L1SI187-SITE-S2-FILL-001` 块 B 产出 ｜ 日期：2026-11-01（+08）
> 候选源：仓内 `core-go/docs/formal-proofs/CLAIMS-MATRIX.md` Tier A 全部 10 条（线上现 14 条皆 Tier C 实验线，与本批零重叠，已逐条比对）
> 纪律：结论文字与适用范围均**矩阵原文移录**（⛔放宽／⛔删减／⛔合并）；一律不标「绝对安全」；N-4／N-5／N-7 之「接口层 conditional」限定在限定标注栏原文保留

| # | 结论文字（矩阵原文） | 证明文件仓内路径 | 机验结论 | 适用范围与模型假设（原文） | 数据性质 | 限定标注 |
|---|---|---|---|---|---|---|
| 1 | 公理 6 可计算审计还原性（enforce 实例化：f=Verify / f⁻=AuditVerify / g=RightInverse） | `core-go/pkg/enforce/axiom6.go` | ✅ `VerifyAxiom6()` 9 断言全 PASS | X=AgentCard 有限集；模型假设：白名单可逆校验（非形式化数学证明的替代——见数学基础白皮书 §2）；**不标"绝对安全"** | real | 无条目级附加限定（通用纪律：不标绝对安全） |
| 2 | 命题 P4a：C < q(1−p)R ⟹ T_process 严格占优（原 B-3） | `core-go/docs/formal-proofs/lean/TDCA/ExPostTrust.lean` | ✅ `lake env lean` 零 error（PR #127 / 机验通道） | 模型假设：单次协作、C 由 A 承担；**不标"绝对安全"** | real | 无条目级附加限定（通用纪律：不标绝对安全） |
| 3 | 推论 2：α ↑ ⟹ e_B* ↓（攫取问题的比较静态，原 B-4） | `core-go/docs/formal-proofs/lean/TDCA/ExPostTrust.lean` | ✅ `lake env lean` 零 error + `sorry` = 0（PR #128 后机验） | 模型假设与适用范围见件头；**不标"绝对安全"** | real | 无条目级附加限定（通用纪律：不标绝对安全） |
| 4 | N-1 失效半径有界性：信任链单点失效向下传导、向上隔离，不全局重置，既有记录不失效 | `core-go/docs/formal-proofs/lean-tdca/TDCA/FailureRadius.lean` | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（lean-verify.yml `lean-tdca` job，首跑未跑） | 模型假设：A1 信任链＝分支有限集合、向下传导＝分支内位置序号增大方向；A2 失效事件带在链证据（无链外失效）；A3/A4 affected／survives 定义即刻画；A5 不建模跨分支共享状态；适用范围＝抽象骨架层，密钥轮换／重锚等动态属工程层；**不标"绝对安全"** | real | 无条目级附加限定（通用纪律：不标绝对安全） |
| 5 | N-2 信任根分级 ↔ 场景密级：接入判定 fail-closed（层级不达标即拒），放行集对密级向下封闭 | `core-go/docs/formal-proofs/lean-tdca/TDCA/Admission.lean` | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上） | 模型假设：B1 信任根四级与场景密级均为 ℕ 全序离散梯级；B2 层级只表信任强度不表身份；B3 requiredLevel 单调不减（恒等实现，任何单调实现可替换）；B4 fail-closed 无「告警后放行」；B5 判定只依赖（密级，根层级）两参；**不标"绝对安全"** | real | 无条目级附加限定（通用纪律：不标绝对安全） |
| 6 | N-3 制度准入状态机（七态）：迁移封闭刻画、非熔断态出边完备、熔断为终态、降级/暂停出边受限、入 certified 必附编译通过证据 | `core-go/docs/formal-proofs/lean-tdca/TDCA/Admission.lean` | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上） | 模型假设：A1 态为裸枚举无身份载荷；A2 certified ⟺ 准入编译通过证据；A3 迁移由归纳定义封闭列出（未列出即非法）；A4 熔断终态、回出＝重走注册流程（治理动作，不在机内）；适用范围＝协议层准入守卫抽象骨架；**不标"绝对安全"** | real | 无条目级附加限定（通用纪律：不标绝对安全；「终态」为状态机 terminal 术语） |
| 7 | N-4 版本对齐 fail-closed：制度版本与检查器版本失配 ⟹ 拒；缺信息 ⟹ 拒；发布门＝版本门 ∧ 工件断言门（与「先工件后制度」同一根） | `core-go/docs/formal-proofs/lean-tdca/TDCA/VersionAlignment.lean` | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上） | 模型假设：A1 两版本均以 ℕ 承载可比可判等；A2 失配判据 decide 形态可计算；A3 缺信息（none）即 false 无默认放行；A4 发布门单一合取；A5 真实 CI 接线属工程层、接口层结论判 conditional（SIMULATED 现状不可核）；**不标"绝对安全"** | real | **接口层结论判 conditional（SIMULATED 现状不可核）**（原文保留，⛔删） |
| 8 | N-5 双锚一致性：分配效力 ⟺ 格式锚过 ∧ 效用锚定；可连不可分；双锚相互独立（见证态机验）；效用锚硬下限不可伪造 | `core-go/docs/formal-proofs/lean-tdca/TDCA/DualAnchor.lean` | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上） | 模型假设：A1 格式锚＝内核可检 Bool 通过位、效用锚定 ⟺ floor ≤ declared；A2 stdFloor=1（零/负声明不得锚定）；A3 allocatable 与 connectable 为不同谓词不得互推；A4 独立性以 formatOnly／utilityOnly 见证态机验；A5 真实效用接口 SIMULATED，接口层结论判 conditional；**不标"绝对安全"** | real | **接口层结论判 conditional（SIMULATED）**（照矩阵原文：「真实效用接口 SIMULATED，接口层结论判 conditional」，⛔删） |
| 9 | N-6 负空间（底线）迁移不变量：底线只增不减；迁移不删除（出处有落）；迁移须签批留痕；登记簿良态在再修订下保持 | `core-go/docs/formal-proofs/lean-tdca/TDCA/NegativeSpace.lean` | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上） | 模型假设：A1 三域 State、条目裸 id 无身份语义；A2 底线＝负空间投影 ∪ sc ∪ pr、迁移以「同 id 换状态标记」留痕不减；A3 合法修订封闭列出（迁移须 approved=true ∧ precedent>0）；A4 签批权归属属治理层不入件；A5 不建模时间与并发；A6 不假设 id 唯一；**不标"绝对安全"** | real | 无条目级附加限定（通用纪律：不标绝对安全） |
| 10 | N-7 快慢接口存在性：合法快系统必有异常上报与人类介入口子；缺上报口子 ⟹ 异常可被压制（可被劫持）；快慢为合法性分工、非性能分工 | `core-go/docs/formal-proofs/lean-tdca/TDCA/FastSlow.lean` | ✅ 本机已机验（Lean 4.34.0-rc2，sorry=0）；CI 机验通道落地中（同上） | 模型假设：A1 本件不含任何性能字段／性能声明；A2 快系统＝上报通道清单＋人类介入通道清单；A3 legit ⟺ 两清单均非空；A4 suppressible ⟺ 上报通道为空；A5 真实裁决接口属工程层、接口层结论判 conditional（SIMULATED 现状不可核）；**不标"绝对安全"** | real | **接口层结论判 conditional（SIMULATED 现状不可核）**（原文保留，⛔删） |

## 填报备注

- 证明文件路径照智库直核清单填写，10 件（含 `core-go/pkg/enforce/axiom6.go`）全部实测在仓。
- 第 1 条矩阵证明文件栏另载 `TDCA-CORE-GO-AXIOM6-001`（设计件号），仓内机验载体为 `core-go/pkg/enforce/axiom6.go`；Lean 侧 `Axiom6.lean` 增列证明器通道（抽象层，不重复 Go 通道结论）。
- 第 2／3 条矩阵证明文件栏另载研究侧引用件（P4a Candidate V1.2），按矩阵自述「不入库」，仓内机验载体为 `lean/TDCA/ExPostTrust.lean`。
- 本表只供 operator 注册与智库复核引用；入站仍走「本侧复核＋operator 上架」，上架后另令核证。
