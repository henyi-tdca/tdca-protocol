# E3 · 税收锚定落地（真实数值链）

> 实证编号: E3 ｜ 对应 GSEQ: 0840 / 来源: TDCA-HANDOFF-WORKBUDDY-PAPER-EVIDENCE-001 §二.E3
> 数据性质: **real**（ledger seq11 REAL 锚定 + phase3_reconciliation.json）；成本估算部分标 SIMULATED
> 纪律: I-COST/tax/mou_anchor 为 REAL 账本值；cost_nature 区分标注

## 一、数值链（real）

```
I-COST   = tokens × price / 1e6
         = 5122 × 0.44 / 1e6
         = 0.00225368 USD                              ← REAL（DeepSeek 官方定价页 2026-09-01 实抓）

tax_cny  = i_cost_usd × fx_ref × 0.15
         = 0.00225368 × 7.2 × 0.15
         = 0.0024339744 CNY                           ← REAL（ledger seq11, Phase 2b 参考汇率 fx=7.2）

mou_anchor = tax_cny = 0.0024339744                   ← REAL（ID79 税收硬数据地板，非成本倒推）
```

- 账本落点：`ledger/ledger.jsonl` seq11（event_type=mou_anchor-REAL, nca_id=NCA-COLDSTART-EXP-20260831-094653）
- tax_integrity 封印：`b788ca0102c05404e0c259aac768f8250a392c67b8635b5c3b0987aea4328d81` ✅

## 二、数币结算原型对账（real）

`ledger/phase3_reconciliation.json`（2026-09-01T07:01:24Z）：

```
sum_mou_anchor_settled   = 0.0024339744
sum_e_cny_settled        = 0.0024339744
ledger_real_mou_anchor_total = 0.0024339744
balanced_internal = true
balanced_vs_ledger = true
all_balanced = true
fx: rate=6.7197 (live, frankfurter.app, captured 2026-09-01T07:01:22Z)
anchor: e-CNY (ID80) | simulation: true (ID92 不实收)
```

- **三向对账平衡 ✅**：Σmou_anchor ≡ Σe_cny ≡ ledger_REAL_mou_anchor = 0.0024339744
- 结算锚 = 数字人民币 e-CNY（ID80）；模拟态（ID92 不实收，凭账本转实际结算）

## 三、⚠️ 规范文本 FX 值核对（待 Reasonix 裁定）

- 本 handoff E3 原文写 `tax_cny = i_cost_usd × fx 6.7197 × 0.15`，但**真实账本 seq11 用 fx=7.2**（Phase 2b 参考汇率，GSEQ-0821 R7 接受标注非实时）。
- `6.7197` 实为 **Phase 3 结算实时汇率**（frankfurter live，仅用于 e_cny 金额换算），属另一步骤。
- 两值巧合使 tax 结果一致（0.0024339744），但**论文引用时应区分**：税锚用 fx=7.2（REAL 账本），e_cny 用 fx=6.7197（live 结算）。已在此如实标注，建议论文终稿统一表述。

## 四、来源

| 数据项 | 路径 |
|---|---|
| I-COST / tax / mou_anchor | `ledger/ledger.jsonl` seq11 |
| 对账 | `ledger/phase3_reconciliation.json` |
| 成本估算（SIMULATED 标注） | `NCA-COLDSTART-EXP-20260831-094653.json` est_cost_cny=0.005122（cost_nature=SIMULATED 估算） |

*E3 完。*
