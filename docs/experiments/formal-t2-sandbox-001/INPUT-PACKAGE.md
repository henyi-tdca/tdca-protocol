# TDCA-PLAN-EXP-FORMAL-T2 · 输入包（INPUT PACKAGE）

> 实验：T2 支三沙盒实验 —— 判定「无叙事不经数据升入正空间」。
> 设计件：TDCA-PLAN-EXP-FORMAL-T2-DESIGN-001（V1.0）。
> 定位句（照在册）：加载核心是入场券，沙盒验证是合格证，没有合格证不能出盒；沙盒＝宪法法院，非测试环境。
> 数据性质：本包内合成内容全部标 SIMULATED；在册 17 正例之证据为在册事实（REGISTRY），非合成数据。
> 表述纪律：一切数字仅表述为「给定该场景假设下之差异」，不写成「制度有效」；有限模型不等于一般证明；本通道通过不等于证明器机验通过。

---

## 一、分量取数表（逐分量给在册出处）

### a 命题集（17 登记行＝T1 全批 C-14~C-30）

| 行号 | 命题（摘） | 证明文件（在册） | jobs | 出处 |
|---|---|---|---|---|
| C-14 | COORD-1 协商拓扑计数 | lean-tdca/TDCA/Coord.lean | 922 | CLAIMS-MATRIX.md L55 |
| C-15 | COORD-2 硬阈值误分带 | lean-tdca/TDCA/CoordThreshold.lean | 922 | 同 L56 |
| C-16 | COORD-5 回议发散 | lean-tdca/TDCA/CoordReopen.lean | 922 | 同 L57 |
| C-17 | M-5 负空间不可逾越 | lean-tdca/TDCA/Guard.lean | 923 | 同 L58 |
| C-18 | P-6 熔断可判定性 | 同上（Guard.lean） | 923（同上） | 同 L59 |
| C-19 | P-3 公理 6 推广 | lean-tdca/TDCA/Axiom6General.lean | 924 | 同 L60 |
| C-20 | M-3 化合保持性 | lean-tdca/TDCA/ComposePreserve.lean | 925 | 同 L61 |
| C-21 | M-4 分形归纳主定理 | lean-tdca/TDCA/FractalInduction.lean | 926 | 同 L62 |
| C-22 | P-7 五可充要性 | lean-tdca/TDCA/P7FiveAll.lean | 927 | 同 L63 |
| C-23 | M-7 宪法一致性 | lean-tdca/TDCA/Constitution.lean | 928 | 同 L64 |
| C-24 | P-11 归责映射 | lean-tdca/TDCA/Attribution.lean | 929 | 同 L65 |
| C-25 | M-6 三锚不动点（条件形态） | lean-tdca/TDCA/Anchor.lean | 930 | 同 L66 |
| C-26 | P-5 认知距离不对称 | lean-tdca/TDCA/CogDist.lean | 931 | 同 L67 |
| C-27 | P-13 场景形成机制子集 | lean-tdca/TDCA/SceneScope.lean | 932 | 同 L68 |
| C-28 | COORD-3 协调天花板（条件形态） | lean-tdca/TDCA/CoordCeiling.lean | 933 | 同 L69 |
| C-29 | COORD-4 分层最优性 | lean-tdca/TDCA/CoordLayering.lean | 934 | 同 L70 |
| C-30 | COORD-6 错觉循环不动点（条件形态·离散） | lean-tdca/TDCA/CoordLoop.lean | 935 | 同 L71 |

- 行位：登记行在 `core-go/docs/formal-proofs/CLAIMS-MATRIX.md`；证明文件在 `core-go/docs/formal-proofs/lean-tdca/TDCA/`。
- jobs 链 922→935 逐件 +1 之出处：各件机验回报（lake build 日志，Lean 4.34.0-rc2）；C-14~C-16 之 922 见机验日志 `_build-coord5.log`「Build completed successfully (922 jobs)」。
- blob 出处：入仓 blob＝机验件 blob＝交付件全文逐字（各件合并核证记录），本包由跑法脚本现场以 git blob（sha1）双算。

### b 构造（已出示构造性存在证明所涉对象与算子）

| 构造 | 出处 |
|---|---|
| git blob（sha1，blob {len} NUL 前缀） | 各件合并核证口径「入仓 blob＝机验件 blob＝交付件」之双算方法；脚本内 `git_blob_sha1()` 独立实现 |
| 登记行「同上」承接语义 | 在册原文（C-18 证明文件与机验字段皆「同上」）；脚本显式承接前行 |
| jobs 链完整性判据 | 机验回报逐件「+1 链条吻合」口径 |
| 闸门检查项 G1–G5 | 在册纪律之合成：登记纪律（CLAIMS-MATRIX 头「未登记声称视为无效」）、逐字节一致（合并核证 c 项）、零占位（机验口径）、父提交＝HEAD（合并核证 d 项）、SIMULATED 标（ID92）与禁用措辞（外稿纪律） |

### c 数据（合成数据全部标 SIMULATED）

- 在册 17 正例：证据＝在册事实（文件 bytes、登记行、HEAD c19912a），非合成数据。
- 合成内容（SYNTHETIC）：P2 合法用例（fixtures/SimClaim.lean＋夹具登记簿，叙事含 SIMULATED 标）；负例 N1–N7 与扰动 D1 之攻击构造（变异字段）。负例之叙事沿用基底在册原文（C-30），攻击面在证据与 claim_id，不虚构叙事文本。

### d 指标（该场景假设下之差异量）

- 闸门判定准确性：正例放行率（误伤数）、负例拦截率（失守数）；观测值为布尔判定序列（26 包），期望见三要件。

---

## 二、一票否决清单（自核声明）

| # | 否决条 | 自核结果 |
|---|---|---|
| 1 | 分量来源不可溯 | PASS——17 行逐行给出登记行位与文件路径；blob 现场双算 |
| 2 | 数据性质未标或冒充真实数据 | PASS——合成内容均含 SIMULATED 标（P2 叙事、夹具件、夹具登记簿）；在册事实明示 REGISTRY |
| 3 | 三要件缺任一件 | PASS——见下节三要件（要件一/二已声明，要件三跑后实填于沙盒验证件） |
| 4 | 以实例冒充一般式或越界声称 | PASS——指标仅 26 包场景假设下之判定序列；无「制度有效」表述 |
| 5 | R-1 未办 | PASS——见沙盒验证件附录 R-1：逐分支变化空间核定 |
| 6 | R-2 未办 | PASS——见沙盒验证件附录 R-2：八处自述等价逐句吻合、一处差异登记 |

---

## 三、跑法声明

- 可重复：同输入两次输出逐字节一致（结果记录 results/run1.txt 与 run2.txt 之 sha256 相同）。
- 退出码语义：0＝全绿（误伤 0 且失守 0）；非 0＝失守。
- 误伤：正例与合法用例不得判违规；误伤须 0。
- 规模与扰动档位（执行侧声明）：正例 18（在册 17＋合成合法 1）、负例 7、扰动 1 档（链完整性 off-by-one：jobs−1 陈旧数据），共 26 包。数值扰动之多档位与 T3 之衔接：本件仅声明此 1 档结构性扰动，其余档位留 T3 声明。

## 四、三要件

- 要件一（目标函数与期望值，容忍度与理由）：
  目标函数＝闸门判定准确性。期望：正例放行率 1.0（误伤 0）；负例拦截率 1.0（失守 0）。容忍度：双率均为 0 容差。理由：支三判定「无叙事不经数据升入正空间」为全称布尔命题——任一正例被拒（误伤）即闸门不可用于合法升盒；任一负例被放行（失守）即「叙事不经数据升入正空间」之反例成立、支三失守。fail-closed 之下两向皆 0 容差。
- 要件二（先验＋来源）：
  无制度时（无闸门）：裸叙事与伪数据升入正空间不可被拒——升盒成功率对负例结构性为 1（来源：登记纪律「未登记声称视为无效」之反设；闸门缺位时无执行者）。
  有制度时（本闸门）：按在册判据 G1–G5 执行，升盒成功率对正例 1、对负例 0（来源：判据之合取 fail-closed 语义）。
  本先验为给定场景假设下之判断，不构成「制度有效」表述。
- 要件三（结果-期望比较）：跑后实填，见 SANDBOX-VERIFICATION.md 三要件之③。
