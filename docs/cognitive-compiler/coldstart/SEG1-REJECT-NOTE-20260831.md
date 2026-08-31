# 段1 REJECT 语义说明（NCA-COLDSTART-EXP-20260831-094653）

> 登记: 2026-08-31 ｜ Reasonix 核证 ｜ 关联: TDCA-COLDSTART-FINAL-001 遗留② ｜ 存证: GSEQ-0799

## 事实

段1（准入评估）DeepSeek 输出：REJECT——依据：「双方增量>0 判据不成立：res/BATMA 均为自报且无历史 NCA 链，无法验证真实能力与外部选项，正和增量不可证实」「BATMA 存疑即熔断：不允许以自报值作为缔约依据」；honesty 声明 res/batna 自报=data_provenance:mixed；nsfl_ok=true。

## 语义判定（Reasonix）

1. 段1 REJECT 是模型对自报值不可证实性的诚实评估——与数据诚实纪律一致（如实零态不注水）。
2. 本 COP（第01条-rerun.yaml）的 anchored=true 指外部锚基准实存（麦肯锡 sha8=e8655643 / 三十六计 37 件 / 第01条在库，protocols/tdca-native 实核）——不构成准入通过判定。
3. 冷启动试验整体语义：VB 锚定解除=锚基准可验证性达成；准入通过判定需缔约后真实贡献数据支撑（当前 res/batna 自报段不满足）。

## 处理

- 已如实标注于 NCA-COLDSTART-EXP-20260831-094653（data_provenance=mixed）+ TDCA-COLDSTART-FINAL-001 遗留②
- 可选迭代（非紧急）：段1 增加机验 gate（REJECT 时流程中止并显式标注「准入未过」），避免 REJECT 与后续阶段并存造成语义混淆