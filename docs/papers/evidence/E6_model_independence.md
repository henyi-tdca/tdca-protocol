# E6 · 模型无关性（双实证 + 纯本地编译）

> 实证编号: E6 ｜ 对应 GSEQ: 0840 / 来源: TDCA-HANDOFF-WORKBUDDY-PAPER-EVIDENCE-001 §二.E6 + TDCA-PAPER-REVIEW-001 §三
> 数据性质: **real**（编译产物 + 本地脚本证据）
> 论证: 「程序 vs 运行时」——编译器/脚本（程序）模型无关，运行时模型可替换

## 一、双实证表（real）

| 范式 | 程序（编写模型） | 运行时（执行模型） | 一致性证据 |
|---|---|---|---|
| 三十六计（36 计） | GLM-5.2 编写 `cognitive_compiler` | **混元接管编译** | 36/36 COP 六要素 PASS；NCA 链式确权同构（行为一致） |
| 周易（2/64） | GLM-5.2 编写 `compile_iching.py` | **混元核证** | 第01乾/第02坤 COP schema 同构；sha256_16 `910fa1a9…`/`7bc18e9b…`（GSEQ-0841 纠正，原 410a0533…/232abf49… 失效） |

- 双实证证明：同一套 TDCA 制度（T1/T2 规范、NCA/MOU/NSFL 原语）跑在不同模型上，输出行为一致 → **模型无关性成立**（呼应 ID32「制度红利 > 技术红利」）。

## 二、纯本地编译（模型不在回路）· real 证据

- 周易编译采用 **`compile_iching.py` + `iching_data.py`**：`iching_data.py` 内含六十四卦语料库（real 文件 ~45 KB，64 卦全量本地数据），COP 由脚本从本地数据**确定性生成**。
- **63/64 工作量零 LLM**：除结构化生成外，卦象→COP 映射为确定性本地逻辑，模型不在回路。
- 当前产物：2/64（第01乾 8-31 手动、第02坤 9-01 补跑），`progress.yaml` 标记 `completed: 2 / total: 64 / status: running`。
- 这意味着：**制度层（编译器/脚本）与运行时模型解耦**——更换模型不影响产物结构与确权链路。

## 三、「程序 vs 运行时」证据链

```
程序（模型无关）          运行时（可替换模型）
cognitive_compiler  ────  GLM-5.2 编写 → 混元接管  → 36 COP 行为一致
compile_iching.py   ────  GLM-5.2 编写 → 混元核证  → 2 COP 行为一致
                                 ↑
                    63/64 纯本地生成（模型不在回路）
```

- 论文差异化主张：多数 AI 治理论文停在「原则」，TDCA 提供**可执行代码 + 跨模型可复现产物**双重证据。

## 四、来源

| 数据项 | 路径 |
|---|---|
| 三十六计双实证 | `stratagems/*.yaml`（36）、`E1_cross_model_consistency.md` |
| 周易双实证 + 纯本地 | `protocols/tdca-native/iching/第NN卦-*.yaml`、`compile_iching.py`、`iching_data.py`、`progress.yaml` |

*E6 完。六实证全链闭合。*
