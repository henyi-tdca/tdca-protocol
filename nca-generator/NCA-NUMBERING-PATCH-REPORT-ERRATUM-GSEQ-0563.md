# NCA 编号补丁报告 · 勘误（GSEQ-0563）

> 本勘误**取代并修正** `NCA-NUMBERING-PATCH-REPORT.md` §六-1 的不实声称。
> 成因：主报告 md 当前被 Word/预览进程排他锁定（`EBUSY`），无法内联编辑；
> 勘误文件为权威修正载体，待锁释放后折回主报告 §六-1。
> 纪律：产物不推送（Kimi 推 PR #21）；凭证零落盘；NSFL 未触碰。

## 一、偏差认定（GSEQ-0563 · 动作 2）

原报告 §六-1 称 max+1 口径「已落地」——**不实**。经 GSEQ-0563 实读核验：

| 对照面 | max+1 状态 | 证据 |
|---|---|---|
| 线上 `main`（= GitHub 已合并 PR #20 真值） | **未落地** | `git show main:nca-generator/nca_generator.py` L74-75 = `candidate = 1` + `while candidate in existing`（首空闲版）；其 `test_T1b` 期望 `001`（grep `-156` 无匹配） |
| 本地 `main` 检出（本地 mainline 真值） | **未落地** | 同上，`main` 与线上同源，首空闲版 |
| 本地分支 `feat/nca-numseq-maxplus1-GSEQ-0551`（HEAD=656e9b6，**未推送**） | **已含修复** | L76 = `candidate = (max(existing) if existing else 0) + 1`；`test_T1b` 期望 156、`test_T2` 期望 004；`python test_nca_numbering.py` = **7/7 OK** |

结论：max+1 修复仅 commit 于**未推送的本地分支**，从未 `push`/`merge` 至 `main`，
故 PR #20 合并的线上与本地 `main` 检出均仍为首空闲版。原 §六-1「已落地」对 mainline 不成立。

## 二、修正后 §六-1（权威文本，待折回主报告）

> **编号口径裁定（GSEQ-0551）— 口径偏差修正（GSEQ-0563）**：需求④「中间断号后首个空闲位」原按首空闲（填空）实现；经裁定改为 **max+1 保留缺口**——编号=事实存证时间序，缺口=历史事故/并发痕迹，不可回填（不可篡改精神）。`_reserve_free_nca_slot` candidate 初值改 `max(existing)+1`（单点改动），测试同步改为 max+1 语义（T2→004、T1b→156），**本地分支 `feat/nca-numseq-maxplus1-GSEQ-0551`（656e9b6）已含此修复且 `python test_nca_numbering.py` 7/7 通过**。**但本项此前版本声称『已落地』不实**：该修复仅 commit 于未推送本地分支，从未 `push`/`merge` 至 `main`，故 PR #20 合并的线上 `main` 与本地 `main` 检出均为首空闲版（`candidate = 1`）。max+1 实际由 **Reasonix 落地**，将经 **Kimi 推 PR #21** 上线（本指令 GSEQ-0563 验收确认）。首空闲方案不再采用。

## 三、三线一致性状态（GSEQ-0563 · 动作 2/3）

1. **报告线**：主报告 §六-1 待 Word 锁释放后折回上述权威文本（本勘误先行承载）。
2. **仓库线**：`main` = 首空闲（未落地）；本地分支 `feat/nca-numseq-maxplus1-GSEQ-0551`（656e9b6）= max+1 已含、7/7 绿；分支已建且与修复一致。
3. **上线线**：GitHub `main` = 首空闲（PR #20 真值）；max+1 待 PR #21（Reasonix 修复，Kimi 推送）上线。

→ 三线口径已对齐为「max+1 在本地分支就绪、mainline 待 PR #21 上线」，偏差如实披露、无掩盖。
