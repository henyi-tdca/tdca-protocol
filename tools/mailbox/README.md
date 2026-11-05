# 信箱工具族 · 形态归一（ENG4-001 块6）

> 件号：`ENG4-MAILBOX-001` ｜ 令：`TDCA-HANDOFF-EXEC-L1SI197-ENG4-001` 块6 ｜ 只施工不部署

## 归一三事

| 项 | 落点 |
|---|---|
| ① 统一入口＋统一参数 | `python -m tools.mailbox.mailbox <action>`；参数：`--mailbox-root`（env `TDCA_MAILBOX_ROOT`）／`--box`／`--file`／`--external`／`--require-mail`／`-v` |
| ② 断言集 | `tools/mailbox/assertions.py`：A1 件数（投递件↔旁注一一对应，内部件无旁注义务）／A2 旁注（17B 值符）／A3 状态机（DRAFT→SEALED，盒内零 DRAFT/MISMATCH/ORPHAN）／Z1~Z4 四零立（零占位残留／零孤儿旁注／零超名>110／零终态字样）＋C 组逐件机验 |
| ③ 三态自测 | `python -m tools.mailbox.mailbox selftest`：正常态（夹具全过）／异常态（五缺陷逐断言 FAIL 可读数）／边界态（空盒·非 MAIL 件不误杀） |

## 用法

```bash
# 单件机验 / 封签（判据 C-01~C-05/C-13/C-18，与 TOOL-SEAL-001 v1.2 同口径）
python -m tools.mailbox.mailbox check --file <件> [--external] [--require-mail]
python -m tools.mailbox.mailbox seal  --file <件> [--require-mail]

# 信箱盒断言集
python -m tools.mailbox.mailbox box --mailbox-root C:/Users/22850/Desktop/TDCA交付取件 --box FROM-EXEC

# 三态自测（夹具·不指向真实信箱）
python -m tools.mailbox.mailbox selftest [-v]
```

## 状态机（A3）

`DRAFT`（MAIL 首行占位未封）→ `SEALED`（字段回填＋旁注符）⇄ `MISMATCH`（字段已封但旁注缺/不符，REFUSE 须人工判定）；`INTERNAL`（非 MAIL 件，不入投递状态机）；旁注无本体记 `ORPHAN`。投递盒（FROM-EXEC）断言要求零 DRAFT／零 MISMATCH／零 ORPHAN。

## 边界

- 机验判据移植自 `_deliver_seal_v1.py`（TOOL-SEAL-001 v1.2），该件继续独立可用；等价性有 committed 测试（`tools/tests/test_mailbox_unified.py`）。
- ⛔ 不改信箱内容与台账历史行；⛔ 不改信箱协议条例原文；⛔ 部署另句。
