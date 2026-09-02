# E1 · 跨模型一致性（4 模型对比表 · 真实值）

> 实证编号: E1 ｜ 对应 GSEQ: 0840 / 来源规范: TDCA-PAPER-REVIEW-001（0837）§二.2 + TDCA-HANDOFF-WORKBUDDY-PAPER-EVIDENCE-001（GSEQ-0840）§二.E1
> 数据性质: **real**（编译产物/台账/registry 直接采集，未重跑 LLM）；采集时间 2026-09-01
> 纪律: 真实值零容忍示意；无示意值；KIMI 行编译单元格 N/A（角色=发布/联络线，非编译）

## 一、四模型对比表

| 模型 | 范式 | 编译器/脚本来源 | 真实耗时/时间戳 | COP 六要素验证 | NCA / 哈希锚定 | 来源 |
|---|---|---|---|---|---|---|
| **GLM-5.2** | 麦肯锡 COP（编译规范 T1/T2 基准） | GLM 编写 `cognitive_compiler`（T1+T2 规范） | 规范编写 real（2026-08，*精确耗时待补，标注 pending*） | 基准 schema：soul/primitives/dispatch/decision/negative_space/validation 六键齐全 | 麦肯锡 COP 编译基准 **sha8=e8655643** | `NCA-COLDSTART-EXP-20260831-094653.json` vb_anchor 段 |
| **混元** | 三十六计（36 计） | GLM 编写编译器 → **混元接管编译**（行为一致） | 批量单轮产出 36×2 文件，real 编译日 **2026-08-14** | **36/36 PASS**（36 个 COP 六要素全过） | NCA-REASONIX-20260814-002~037（36 件，registry 锚定）；样本 COP 第01计 SHA256=`e45a9a3198b32ce2507e3fee5b5ec5dd5fbf7602bb9186ca6b1534c798b4a2b9`（GSEQ-0841 复核：原 73ae0afd… 为 GSEQ-0840 采集错误哈希，已按磁盘重算纠正） | `TDCA-MEMO-006-Workspace/.tdca-protocol/cognitive-compiler/stratagems/*.yaml`（36 件） |
| **混元** | 周易（2/64） | GLM 编写脚本 → **混元核证** | 第01乾 8-31 手动 + 第02坤 9-01 补跑，real | COP schema 六要素 PASS | 第01卦-乾 sha256_16=`910fa1a96f1da1c3`；第02卦-坤 sha256_16=`7bc18e9ba19d7e59`（GSEQ-0841 复核：原 410a0533…/232abf49… 为 GSEQ-0840 采集错误哈希，已按磁盘重算纠正） | `protocols/tdca-native/iching/第01卦-乾.yaml`、`第02卦-坤.yaml` + `progress.yaml`（completed 2 / 64, last_compiled 2026-09-01） |
| **DeepSeek** | 冷启动 real rerun | community-ledger 自动化（GSEQ-0785 路径 A） | **5122 tok 真实调用**，real 时间戳 **2026-08-31T09:46:53Z** | 六键齐全 yaml 机验通过（生产段） | NCA-COLDSTART-EXP-20260831-094653（model=deepseek-v4-flash） | `NCA-COLDSTART-EXP-20260831-094653.json` |
| **KIMI** | （发布/联络线，非编译） | — | — | — | Kimi 代发 Weekly-003 / 论丛三篇（GSEQ-0830/0835/0836） | `发布成稿/Weekly-003-素材/` |

> ⚠️ 诚实声明：四模型框架中 **KIMI 在本证据集未执行 COP 编译**（其角色=发布/联络/修复线，见三线协作 GSEQ-0805）。上表 KIMI 行编译单元格标 N/A，未虚构 KIMI 编译产物。若论文需 KIMI 编译实证，须待 Kimi 线实际编译后补采（标注 pending-verify）。

## 二、跨模型一致性结论（real 证据）

- **同一编译器跨模型行为一致**：`cognitive_compiler`（T1/T2 规范）先由 GLM-5.2 编写并编译麦肯锡 COP，后由**混元接管**编译三十六计（36 COP）与周易（2 COP），输出 schema 完全对齐（六要素同构、NCA 链式确权），证明编译行为**与运行时模型无关**。
- **独立第三方模型可接入**：DeepSeek 冷启动 real rerun 以 5122 tok 真实调用，三段式（准入/沙盒/生产）机验通过，VB 锚定结论基于实核在库 COP 基准（非自证）。
- **真实哈希链可复核**：三十六计样本 COP SHA256、周易双卦 sha256_16、麦肯锡基准 sha8 均为直接文件哈希（real，可重算验证），无示意值。

## 三、来源文件映射

| 数据项 | 文件路径 |
|---|---|
| 三十六计 36 COP | `TDCA-MEMO-006-Workspace/.tdca-protocol/cognitive-compiler/stratagems/第NN计-*.yaml` |
| 周易 2 COP + 进度 | `开发会话文件/tdca-protocol/protocols/tdca-native/iching/第01卦-乾.yaml`、`第02卦-坤.yaml`、`progress.yaml` |
| 冷启动真实台账 | `开发会话文件/tdca-protocol/docs/cognitive-compiler/coldstart/NCA-COLDSTART-EXP-20260831-094653.json` |
| 麦肯锡基准 sha8 | 同上 json `vb_anchor.mckinsey_sha256_8=e8655643` |

*E1 完。下接 E6（模型无关性·纯本地编译）。*
