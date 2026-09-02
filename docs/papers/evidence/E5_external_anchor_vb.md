# E5 · 外部锚定（VB 锚定解除 · 真实台账）

> 实证编号: E5 ｜ 对应 GSEQ: 0840 / 来源: TDCA-HANDOFF-WORKBUDDY-PAPER-EVIDENCE-001 §二.E5 + NCA-COLDSTART-EXP-20260831-094653
> 数据性质: **real**（冷启动真实 5122 tok 台账 + 实核在库 COP 基准）
> 论证: 「锚定」有真实外部信号，非自证

## 一、VB 锚定解除（real）

来源：`NCA-COLDSTART-EXP-20260831-094653.json`

```json
"vb_anchor": {
  "anchor": "麦肯锡COP编译基准 + 三十六计逐计编译基准（protocols/tdca-native 实存实核）",
  "mckinsey_sha256_8": "e8655643",
  "stratagems_count": 37,
  "coldstart_01_in_library": true,
  "anchored": true
},
"vb_unverified_anchor_removed": true
```

- **真实 5122 tok**（DeepSeek deepseek-v4-flash，2026-08-31T09:46:53Z，三段式准入/沙盒/生产）
- **锚实核**：VB 重定价不再仅依赖组织者主权宣言，而基于可验证外部基准——
  - 麦肯锡 COP 编译基准（sha8 `e8655643`，实存 protocols/tdca-native）
  - 三十六计逐计编译基准（37 件在库）
  - 第01条 COP 已入 protocols/tdca-native
  - ⇒ `anchored=true`
- **[UNVERIFIED]→anchored=true**：初始 VB=200 为组织者主权声明（待校准初始值），外部锚实核后升格为 anchored（可被映射校准，偏差超容差则触发 VB 重定价）。
- `vb_unverified_anchor_removed=true`：未经验证的锚被剥离，仅保留实核锚。

## 二、外部锚定的工程意义

- 冷启动场景「自产自用归因困境」（I-MOU）下，VB 锚定若仅靠自报即落入「自证陷阱」。
- TDCA 解法：**以 protocols/tdca-native 中既有的真实编译产物（麦肯锡/三十六计/周易 COP）作为外部锚基准**，冷启动 VB 重定价 = 与实核基准映射校准，而非组织者独断。
- 此即「外部锚定实证」：锚点来自真实在库产物（SHA 可重算），非声明。

## 三、来源

| 数据项 | 路径 |
|---|---|
| 冷启动真实台账 | `docs/cognitive-compiler/coldstart/NCA-COLDSTART-EXP-20260831-094653.json` |
| 麦肯锡基准 | 同上 `vb_anchor.mckinsey_sha256_8=e8655643` |
| 三十六计/周易在库 | `stratagems/`（36）、`protocols/tdca-native/iching/`（2） |

*E5 完。下接 E6（模型无关性·纯本地编译）。*
