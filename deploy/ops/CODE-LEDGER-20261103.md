# 代码改动登记册 · CODE-LEDGER-20261103（public_docs_ops.py 扩族留痕）

> 件号：`TDCA-CODE-LEDGER-20261103` ｜ 版本：`V1.0` ｜ 日期：`2026-11-03`（+08）
> 会话框：`L1-SI-192` ｜ 依据令：`TDCA-HANDOFF-EXEC-L1SI192-OPSGUIDE-004` 段 B（代码改动入册·只登记）
> 性质：⚠️ 内部件 · ⛔ 非对外 ｜ 本册为**账**，运行时不读

---

## 登记五行（逐行照令）

1. `public_docs_ops.py` 改前哈希 `393A8E7358C8DD3A`（41,389 B）／改后 `b63393cd34b5a812`（42,094 B）（据 EXEC-DAILY-OPS-20261103-024，本侧复算一致）。
2. 站机备份名：`/root/tdca-site/gateway-channel-cc0c5fd/public_docs_ops.py.bak-opsguide003-20261103`（⛔ 未删）。
3. 时点：`2026-11-03 18:47`（+08，站机钟）。
4. 合并提交：`9a598416`（MR !398，双父真合并；主仓基准，三端树同 `362405E7DF61AA1C`）。
5. 该目录（`/root/tdca-site/gateway-channel-cc0c5fd/`）**无 `git`** ⟹ 本册为**唯一留痕**。

## 改动内容一句

`_FAMILY_DIRS` 增 `"ops-guides": "ops-guides"`；`_PUBLIC_DOCS` 增 `"ops-guides": (三件白名单件名)`——共两行扩族，带在册依据位注释（见主仓 `true-source/tdca-web/gateway/public_docs_ops.py`）。

## 边界

⛔ 本册不改 channel 目录任何件；⛔ 不删 `.bak-*`；只新建本册。

---

*执行侧 · L1-SI-192 · 2026-11-03（+08）*
