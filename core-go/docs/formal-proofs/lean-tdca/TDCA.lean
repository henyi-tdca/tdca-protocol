-- Root module for the TDCA library (aggregates submodules).
-- 本工程骨架补齐（M3-b 同期）：外部机验 M1 机验首跑报错 `no such file or directory: TDCA.lean`
-- ——lakefile 的 `@[default_target] lean_lib TDCA` 要求库根模块存在（核证差异回灌）。
-- M3-d 补齐（2026-09-13，缺陷 D-3）：新增 `import TDCA.Induction`
-- ——原版仅 4 个 import，致 `lake build` 默认目标**不覆盖 M3-d 件**（V2 机验暴露；外部执行未擅动、如实登记）。
import TDCA.Basic
import TDCA.MetaInverse
import TDCA.Compose
import TDCA.EpsAdd
import TDCA.Induction
-- M-8 Lean 化（2026-09-14）：新增 `import TDCA.SceneEmergence`
-- ——场景形成机制可机验子集 F-1~F-6（命题 M-8.1~M-8.6）。
import TDCA.SceneEmergence
-- 公理 6 证明器通道（2026-09-14）：新增 `import TDCA.Axiom6`
-- ——四约束形式化（约束 1 / 2 归位自 TDCA.MetaInverse；约束 3 为甲′ 形态，非空前提见该件头注）。
import TDCA.Axiom6
-- 公理 6 · 约束 4 条件形态附录（2026-09-14）：新增 `import TDCA.Axiom6Complexity`
-- ——复杂度以建模参数进入、约束以假设形式给出、结论标 conditional；⛔ 不得读作已从程序推出。
import TDCA.Axiom6Complexity
-- 准入守卫（2026-09-23）：新增 `import TDCA.Admission`
-- ——N-3 制度准入状态机（七态）＋ N-2 信任根分级↔场景密级（fail-closed），共用骨架一次建模双用；
-- 本机机验 exit 0、零 sorry；模型假设与适用范围见件头（A1–A5／B1–B5）。
import TDCA.Admission
-- 失效半径有界性（2026-09-23）：新增 `import TDCA.FailureRadius`
-- ——N-1 信任链分支结构（向下传导、向上隔离；单点失效≠全网重置），零依赖刻画式件；
-- 本机机验 exit 0、零 sorry；模型假设与适用范围见件头（A1–A5）。
import TDCA.FailureRadius
-- 负空间迁移不变量（2026-09-23）：新增 `import TDCA.NegativeSpace`
-- ——N-6 负空间（底线）之修订：底线只增不减、迁移不删除（出处有落）、签批留痕、再修订保持；
-- 本机机验 exit 0、零 sorry；模型假设与适用范围见件头（A1–A6）。
import TDCA.NegativeSpace
-- 双锚一致性（2026-09-23）：新增 `import TDCA.DualAnchor`
-- ——N-5 格式锚＋效用锚：分配效力 ⟺ 双锚齐备（可连不可分），接口层 SIMULATED 判 conditional；
-- 本机机验 exit 0、零 sorry；模型假设与适用范围见件头（A1–A5）。
import TDCA.DualAnchor
-- 版本对齐 fail-closed（2026-09-23）：新增 `import TDCA.VersionAlignment`
-- ——N-4 制度版本＋检查器版本：失配 ⟹ 拒、不确定 ⟹ 拒（fail-closed），与「先工件后制度」同一根；
-- 本机机验 exit 0、零 sorry；模型假设与适用范围见件头（A1–A5）。
import TDCA.VersionAlignment
-- 快慢接口存在性（2026-09-23）：新增 `import TDCA.FastSlow`
-- ——N-7 快系统必有异常上报与人类介入口子（缺口子 ⟹ 可被劫持），合法性分工非性能分工；
-- 本机机验 exit 0、零 sorry；模型假设与适用范围见件头（A1–A5）。
import TDCA.FastSlow
-- 协调原理簇第一批之一（2026-10-02）：新增 `import TDCA.Coord`
-- ——COORD-1 协商拓扑计数（递归计数 ＋ 基线实例 ＋ 单调性 ＋ 下界），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（C1–C3）。
import TDCA.Coord
-- 协调原理簇第一批之二（2026-10-02）：新增 `import TDCA.CoordThreshold`
-- ——COORD-2 硬阈值二分类必存误分带（离散收窄版：阈值带 ＋ 类型翻转），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（D1–D3）。
import TDCA.CoordThreshold
-- 协调原理簇第一批之三（2026-10-02）：新增 `import TDCA.CoordReopen`
-- ——COORD-5 回议发散（构造性必要性方向：重开无界 ⟹ 无静默轮），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（R1–R3）。
import TDCA.CoordReopen
-- 证明总纲 M-5 ＋ 开放问题 P-6（2026-10-02）：新增 `import TDCA.Guard`
-- ——负空间不可逾越（熔断是映射行为）＋ 熔断可判定（fail-closed），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（G1–G4）。
import TDCA.Guard
-- 开放问题 P-3（2026-10-02）：新增 `import TDCA.Axiom6General`
-- ——公理 6 推广（抽象四约束 ＋ NCA 链与 NSFL 熔断器两实例；像集裁剪解张力），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（P3-1–P3-4）。
import TDCA.Axiom6General
-- 证明总纲 M-3（2026-10-02）：新增 `import TDCA.ComposePreserve`
-- ——化合保持性（五可保持 ＋ ε 累积线性上界；承重命题），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（M3-1–M3-3）。
import TDCA.ComposePreserve
-- 证明总纲 M-4（2026-10-02）：新增 `import TDCA.FractalInduction`
-- ——分形归纳主定理（一般归纳骨架：基例 ＋ 保持性 ⟹ 任意深度；含充要形态），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（M4-1–M4-3）。
import TDCA.FractalInduction
-- 开放问题 P-7（2026-10-02）：新增 `import TDCA.P7FiveAll`
-- ——五可充要性（定理 8.8 之机验面）：以 M-3 之五可／化合实例喂入 M-4 之归纳骨架收口
-- （充分／必要／充要 ＋ 缺失面 ＋ 百亿规模面 ＋ 边界引用），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（P7-1–P7-3）。
import TDCA.P7FiveAll
-- 证明总纲 M-7 ＋ 开放问题 P-8（2026-10-02）：新增 import TDCA.Constitution
-- ——宪法一致性与定义域非空（见证构造 ＋ 律一内核性 ＋ 律二注入不改内核 ＋ 一致面），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（C1–C4）。
import TDCA.Constitution
-- 开放问题 P-11（2026-10-02）：新增 import TDCA.Attribution
-- ——归责映射可机验子集（结构面：传递性 ＋ 层级单调 ＋ 方向单向与分层隔离 ＋ 无环），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（A1–A3）。
import TDCA.Attribution
-- 证明总纲 M-6 ＋ 开放问题 P-9（2026-10-02）：新增 import TDCA.Anchor
-- ——三锚不动点（不动子空间 ＋ 可迭代 ＋ 三锚齐备 ＋ 契约必要性；整体条件形态），零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（E1–E4）。
import TDCA.Anchor
-- 开放问题 P-5（2026-10-02）：新增 import TDCA.CogDist
-- ——认知距离不对称（命题 3.10）之机验面：可达性不对称之必要面与充分面 ＋ 不对称传递，零依赖件；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（D1–D4）。
import TDCA.CogDist
-- 开放问题 P-13（2026-10-02）：新增 import TDCA.SceneScope
-- ——场景形成机制可形式化子集之两栏边界与见证方向（零依赖机验面；前件 SceneEmergence 为 M-8 子集）；
-- 本机机验 exit 0、零占位；模型假设与适用范围见件头（S1–S4）。
import TDCA.SceneScope
