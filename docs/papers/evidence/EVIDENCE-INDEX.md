# 论文实证数据包 · INDEX（六实证真实值）

> 包路径: `docs/cognitive-compiler/coldstart/paper-evidence-20260901/`
> 指令: GSEQ-0840（NCA-TDCA-REASONIX-20260901-041 Handoff, TDCA-HANDOFF-WORKBUDDY-PAPER-EVIDENCE-001）
> 采集方: WorkBuddy ｜ 采集时间: 2026-09-01 ｜ 状态: ✅ 本地落盘，**不发布**（论文定稿用）
> 纪律: **真实值零容忍示意** —— 每值含来源（文件/GSEQ）+ 时间戳 + `real`/`SIMULATED` 标注；已有产物直接采集，未重跑 LLM 耗额度

## 一、六实证清单（E1–E6）

| 实证 | 文件 | 关键真实值 |
|---|---|---|
| **E1 跨模型一致性** | `E1_cross_model_consistency.md` | GLM/混元/DeepSeek 真实编译；三十六计 36/36 六要素 PASS；样本 COP SHA256 `e45a9a31…`（GSEQ-0841 纠正，原 73ae0afd… 失效）；周易双卦 sha256_16 `910fa1a9…`/`7bc18e9b…`（GSEQ-0841 纠正，原 410a0533…/232abf49… 失效）；麦肯锡基准 sha8 `e8655643`；冷启动 5122 tok |
| **E2 计量可验证** | `E2_meter_verifiability.md` | ledger 20 条 verify PASS ✅；链尾 `789b24a5…`；tax_integrity 10 条全封印（5 REAL 5/5）；Level A 关联 1（seq1） |
| **E3 税收锚定** | `E3_tax_anchor.md` | I-COST `0.00225368` USD → tax `0.0024339744` CNY → mou_anchor `0.0024339744`；三向对账平衡 ✅ |
| **E4 双层核验** | `E4_dual_layer_interception.md` | GSEQ-0781 假存证拦截 + GSEQ-0809 冒名核证识别纠正（registry 锚点实盘核验） |
| **E5 外部锚定** | `E5_external_anchor_vb.md` | NCA-COLDSTART-EXP 真实 5122 tok；VB 锚实核（麦肯锡 sha8 e8655643 / 三十六计 37 / 第01条在库）；anchored=true |
| **E6 模型无关性** | `E6_model_independence.md` | 双实证（三十六计/周易 GLM→混元 行为一致）+ 纯本地编译（周易 63/64 零 LLM，模型不在回路） |

## 二、真实值来源映射（文件 / GSEQ）

| 数据 | 来源 |
|---|---|
| 三十六计 36 COP | `TDCA-MEMO-006-Workspace/.tdca-protocol/cognitive-compiler/stratagems/*.yaml` |
| 周易 2 COP + 进度 | `protocols/tdca-native/iching/第01卦-乾.yaml`、`第02卦-坤.yaml`、`progress.yaml` |
| 冷启动真实台账 | `docs/cognitive-compiler/coldstart/NCA-COLDSTART-EXP-20260831-094653.json` |
| ledger 20 条 + verify | `ledger/ledger.jsonl` + `ledger.py --verify` |
| 对账 | `ledger/phase3_reconciliation.json` |
| 0809 案例 | `tdca-thinktank/governance/decisions/TDCA-METER-NSFL-CORRECT-001-冒名核证报告识别与纠正.md` |
| 0781 案例事实 | TDCA-HANDOFF-WORKBUDDY-PAPER-EVIDENCE-001 §二.E4（Reasonix handoff） |
| 规范框架 | TDCA-PAPER-REVIEW-001（GSEQ-0837）、TDCA-METER-FINAL-001（GSEQ-0824） |

## 三、待验证 / 待裁定项（pending-verify，已诚实标注，不虚构）

| 项 | 状态 |
|---|---|
| **E1 KIMI 行编译单元格** | N/A（KIMI 角色=发布/联络线，本证据集未编译 COP）；若需 KIMI 编译实证须待其实编译后补采 |
| **E1 GLM 规范精确耗时** | pending（仅知 2026-08 编写，精确耗时未采集，标注 pending） |
| **E2 Level A 编号口径** | 规范列 seq1/seq4-6/seq11，real verify 仅 seq1 关联 Level A 计量；建议论文以 seq1（real）为准，seq4-6/seq11 改述「REAL 税锚条目」 |
| **E3 FX 值口径** | 规范写 fx 6.7197，real 账本 seq11 用 fx=7.2（Phase 2b 参考汇率）；6.7197 为 Phase 3 结算 live FX。建议论文区分：税锚 fx=7.2 / e_cny fx=6.7197 |
| **0781 案例细节文档** | 本端无独立 0781 案例文档，事实取自 Reasonix handoff（GSEQ-0781）；如需完整事件叙述待 Reasonix 补登记 |

## 四、数据包文件清单

```
paper-evidence-20260901/
├── INDEX.md                          # 本文件
├── E1_cross_model_consistency.md
├── E2_meter_verifiability.md
├── E3_tax_anchor.md
├── E4_dual_layer_interception.md
├── E5_external_anchor_vb.md
├── E6_model_independence.md
└── artifact_hashes.json              # 36 三十六计 + 2 周易 COP 真实 SHA256（可重算验证）
```

*六实证真实数据：跨模型一致性 / 计量可验证 / 税收锚定 / 双层核验 / 外部锚定 / 模型无关性 —— 示意值零容忍，供论文实证章节引用。*
