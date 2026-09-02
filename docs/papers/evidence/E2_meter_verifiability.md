# E2 · 计量层可验证性（真实运行值）

> 实证编号: E2 ｜ 对应 GSEQ: 0840 / 来源: TDCA-HANDOFF-WORKBUDDY-PAPER-EVIDENCE-001 §二.E2
> 数据性质: **real**（ledger.py --verify 实跑输出，2026-09-01）
> 纪律: 全部为真实 verify 结果；置信度分级如实标注

## 一、哈希链 verify（real）

`ledger.py --verify` 实跑输出（2026-09-01）：

```
[verify] 条目数=20  链式连续=✅  链尾=789b24a5323bc8e5..
[summary] 总条 20 | 事件分布 {'nca_entry': 5, 'mou_anchor': 10, 'settlement': 5} | 关联 Level A 计量 1
```

- **条目数 = 20** ✅
- **链式连续 = ✅**（创世 `0^64` → seq20 完整连续，无断链）
- **链尾哈希 = `789b24a5323bc8e58927fa3b49cddb58a78725315a8243faff9df0c8f4afd0c2`**（论文可引 `789b24a5…`）
- 事件分布：nca_entry 5 / mou_anchor 10 / settlement 5

## 二、tax_integrity 封印（real）

- 全部 **10 条 mou_anchor 条目（seq6–15）均携带 `tax_integrity` 字段**（哈希封印，证明 MOU 税锚未被篡改）。
- 其中 **5 条 REAL 锚定（seq11–15，Phase 2b 官方挂牌价）全部 verify 通过 → 5/5 ✅**（0 errors）。
- SIM 锚定 5 条（seq6–10）同带封印，与 REAL 段独立校验互不影响。

## 三、置信度分级 · Level A 真实记录（real）

- ledger 内 **关联 Level A 真实计量 = 1 条（seq1）**：`NCA-COLDSTART-EXP-20260831-094653`，`linked_meter.confidence="A"`，source=`replay-from-NCA-COLDSTART-EXP-20260831-094653（real 2026-08-31 DeepSeek usage）`。
- MET-001 落实：仅 Level A（真计量+source_hash）可关联入账本；Level B/C 拒入。
- ⚠️ 口径留痕：规范 E2 文本列 Level A 为「seq1/seq4-6/seq11」，但本端 ledger real verify 仅 seq1 带 confidence=A 关联计量；seq4-6 为 Reasonix 裁决条目（linked_meter=null），seq11 为 REAL 税锚条目（非 Level A 计量关联）。**论文引用 Level A 时请以本 real 值（seq1）为准**，seq4-6/seq11 标记建议核实或改为「REAL 税锚条目」。

## 四、来源

| 数据项 | 路径 |
|---|---|
| ledger 20 条 | `docs/cognitive-compiler/coldstart/ledger/ledger.jsonl` |
| verify 脚本 | `docs/cognitive-compiler/coldstart/ledger.py --verify` |
| 链尾 / 封印 | 见 ledger.jsonl seq20（hash）、seq6–15（tax_integrity） |

*E2 完。下接 E3（税收锚定数值链）。*
