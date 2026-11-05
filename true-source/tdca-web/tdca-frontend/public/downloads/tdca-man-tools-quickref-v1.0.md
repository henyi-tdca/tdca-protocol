# ⭐ **TDCA 官方工具 ⭐ 速查页合集**（⭐ 九包 ⭐ 各一节 ⭐ · 随包分发 ⭐ ）

> 件号：**`TDCA-MAN-TOOLS-001-QUICKREF`** ｜ 版本：**`V1.0-DRAFT`** ｜ 日期：**`2026-11-05`**（+08）
> 会话框：**`L1-SI-197`** ｜ 编制：**`Reasonix`**（智库）｜ 操作类型：**`Manual`**
> 性质: ⚠️ **草案 · 待验收 · 拟对外 ⛔ 未上站**
> 上游：⭐ 手册总册 ⭐ `V1.0-FROZEN` ⭐ （⭐ 已签批生效 ⭐ ）＋ ⭐ 机读版 ⭐ `V0.2`
> 用法：⭐ 分发时 ⭐ **按节拆出** ⭐ 对应包 ⭐ 之一页 ⭐ ，⭐ 随包置 ⭐ `QUICKREF.md` ⭐。

---

## ⭐ `A-2` ⭐ 微交付税收 `tdca-microtax`

| ⭐ 项 | ⭐ 内容 |
|---|---|
| ⭐ 做什么 | ⭐ 按在册参数算 ⭐ 一次微交付 ⭐ 之 ⭐ 税负与净额 |
| ⭐ 能力项 | `tax.schedule` ⭐ ／`tax.transaction_fee` ⭐ ／`tax.net_amount` |
| ⭐ 该用 | ⭐ 需算单笔税负 ⭐ ／⭐ 需核对税明细 |
| ⛔ **不该用** | ⭐ 法定申报 ⭐ ／⭐ 真实资金划拨 ⭐ ／⭐ 跨场景聚合计税 ⭐ |
| ⭐ 入口 | ⭐ `from microtax import compute_taxes` |
| ⭐ 入参 | `amount` ⭐ （⭐ 数 ⭐ ）⭐ ／`scene` ⭐ （⭐ 串 ⭐ ）⭐ ／`tax_base` ⭐ （⭐ 数 ⭐ ） |
| ⭐ 出参 | `{schedule, fee, total, net}` |
| ⭐ 边界 | `B-2` ⭐ （⭐ ⛔ 真实资金 ⭐ ）⭐ ／`B-4` ⭐ （⭐ ⛔ 替代法定申报 ⭐ ） |
| ⭐ 依赖 | ⭐ 标准库 ＋ ⭐ 须与 ⭐ `A-3` ⭐ 同环境 ⭐ |

---

## ⭐ `A-3` ⭐ 负空间编译器 `tdca-nsfl-compiler`

| ⭐ 项 | ⭐ 内容 |
|---|---|
| ⭐ 做什么 | ⭐ 把负空间声明 ⭐ 编译为 ⭐ 可机验 ⭐ 词法与结构 |
| ⭐ 能力项 | `nsfl.lex` ⭐ ／`nsfl.compile` |
| ⭐ 该用 | ⭐ 需校验 ⭐ 负空间表达 ⭐ 合式 ⭐ ／⭐ 需转 ⭐ 机读结构 ⭐ |
| ⛔ **不该用** | ⭐ 替代 ⭐ 人工法律判断 |
| ⭐ 入口 | `python -m nsfl_compiler <源文件>` |
| ⭐ 出参 | `{tokens: 列表, ok: 布尔}` |
| ⭐ 边界 | `B-3` ⭐ ／`B-5` |
| ⭐ 依赖 | ⭐ 纯标准库 |

---

## ⭐ `A-4` ⭐ 存证自检 `tdca-cert-tool`

| ⭐ 项 | ⭐ 内容 |
|---|---|
| ⭐ 做什么 | ⭐ 对本机存证 ⭐ 做 ⭐ 结构与哈希自检 |
| ⭐ 能力项 | `attest.selfcheck` ⭐ ／`attest.endpoint_probe` |
| ⭐ 该用 | ⭐ 需确认存证件 ⭐ 未被改写 ⭐ ／⭐ 需探端点可达 |
| ⛔ **不该用** | ⭐ 替代 ⭐ 正式审计 |
| ⭐ 入口 | `python cert_l1.py --help` ⭐ （⭐ 两参：⭐ `selfcheck` ⭐ ／`endpoint` ⭐ ） |
| ⭐ 出参 | `{ok, detail}` |
| ⭐ 边界 | `B-3` |
| ⭐ 依赖 | ⭐ 纯标准库 |

---

## ⭐ `A-5` ⭐ 商业调用规则 `tdca-call-rules`

| ⭐ 项 | ⭐ 内容 |
|---|---|
| ⭐ 做什么 | ⭐ 判定 ⭐ 一次商业调用 ⭐ 是否许可 ⭐ ，⭐ 并给 ⭐ 税明细 |
| ⭐ 能力项 | `rules.evaluate` ⭐ ／`rules.tax_detail` ⭐ ／`rules.verdict` |
| ⭐ 该用 | ⭐ 需判定 ⭐ 调用方 ⭐ 在某场景 ⭐ 是否合规 ⭐ ／⭐ 需模拟态税明细 |
| ⛔ **不该用** | ⭐ 真实结算与划拨 ⭐ ／⭐ 替代合同审查 |
| ⭐ 入口 | `python engine/call_rules_engine.py --caller u1 --scene s1 --value 1000 --tax 200` |
| ⭐ 出参 | `{verdict, tax_detail, simulated: true}` |
| ⭐ 边界 | `B-2` ⭐ ／`B-3` |
| ⭐ 依赖 | ⭐ 纯标准库 |

---

## ⭐ `A-1` ⭐ 治理工具七件 `tdca-govtools`

| ⭐ 件 | ⭐ 做什么 | ⭐ 一行命令 |
|---|---|---|
| `_nca_chain_verify_v1.py` | ⭐ 链完整性核 | `python _nca_chain_verify_v1.py --quiet` |
| `_nca_discipline_check_v5.py` | ⭐ 纪律机验 | `python _nca_discipline_check_v5.py` |
| `_mailbox_ledger_v1.py` | ⭐ 信箱台账 | `python _mailbox_ledger_v1.py --check` |
| `_daily_patrol_v1.py` | ⭐ 日常巡检 | `python _daily_patrol_v1.py --quiet` |
| `_weekly_deep_check_v1.py` | ⭐ 周度深核 | `python _weekly_deep_check_v1.py --quiet` |
| `_ops_daily_v1.py` | ⭐ 运维日报 | `python _ops_daily_v1.py --mode morning` |
| `_deliver_seal_v1.py` | ⭐ 交付封签 | `python _deliver_seal_v1.py --help` |

⭐ 退出码 ⭐ ：`0` ⭐ 通过 ⭐ ／`1` ⭐ 有差 ⭐ ／`2` ⭐ 读数不可得 ⭐ 。
⛔ **不该用** ⭐ ：⭐ 缺 ⭐ 本体系格式 ⭐ 账本 ⭐ ／⭐ 期望 ⭐ 开箱用 ⭐ 他人数据 ⭐ 。
⭐ 边界 ⭐ ：`B-5` ⭐ ／`B-6` ⭐ ；⭐ 依赖 ⭐ 标准库 ＋ ⭐ **`PyYAML`** ⭐ （⭐ 非零依赖 ⭐ ）⭐ 。

---

## ⭐ `A-6` ⭐ 法务智能体 `tdca-legal-agent`

| ⭐ 项 | ⭐ 内容 |
|---|---|
| ⭐ 做什么 | ⭐ 法律素材 ⭐ 冲突检测 ⭐ 与 ⭐ 负空间过滤 |
| ⭐ 能力项 | `legal.conflict_detect` ⭐ ／`legal.nsfl_filter` ⭐ ／`legal.kb_query` |
| ⭐ 该用 | ⭐ 需检查 ⭐ 条文冲突 ⭐ ／⭐ 需过滤 ⭐ 负空间表达 |
| ⛔ **不该用** | ⭐ 出具法律意见 ⭐ ／⭐ 替代律师 |
| ⭐ 入口 | `from legal_agent.interface import LegalAgentInterface` |
| ⭐ 出参 | `{conflicts: 列表, filtered: 串}` |
| ⭐ 边界 | `B-3` ⭐ ／`B-5` |
| ⭐ 依赖 | ⭐ 纯标准库 |

---

## ⭐ `MB-SPEC` ⭐ 信箱协作规范 `tdca-mailbox-spec`

| ⭐ 项 | ⭐ 内容 |
|---|---|
| ⭐ 做什么 | ⭐ 定义 ⭐ 跨终端异构智能体 ⭐ 任务协作协议 |
| ⭐ 能力项 | `mailbox.protocol_spec` |
| ⭐ 该用 | ⭐ 需实现 ⭐ 或 ⭐ 对接 ⭐ 信箱协作 |
| ⛔ **不该用** | ⭐ 需可执行程序 ⭐ （⭐ 用 ⭐ `refimpl` ⭐ ） |
| ⭐ 入口 | ⭐ 读包内 ⭐ `README` ⭐ 与 ⭐ 条例双版本 ⭐ ＋ ⭐ `mailbox-conventions.md` |
| ⭐ 边界 | `B-1` |
| ⭐ 依赖 | ⭐ 无 ⭐ （⭐ 纯文档 ⭐ ） |

---

## ⭐ `MB-REFIMPL` ⭐ 信箱协作参考实现 `tdca-mailbox-refimpl`

| ⭐ 件 | ⭐ 干什么 | ⭐ 一行命令 |
|---|---|---|
| `_mailbox_ledger_v1.py` | ⭐ 台账 ⭐ ＋ ⭐ 认领 | `python _mailbox_ledger_v1.py --check --mailbox-root ./mailbox` |
| `_mailbox_scan.py` | ⭐ 双向扫描 | `python _mailbox_scan.py --mailbox-root ./mailbox` |
| `_mailbox_drop_v1.py` | ⭐ 投放 | `python _mailbox_drop_v1.py --file x.md --to TO-EXEC --mailbox-root ./mailbox` |
| `_l1si159_mailbox_done_v1.py` | ⭐ 归位 ⭐ `DONE` | `python _l1si159_mailbox_done_v1.py` |
| `import_json.py` | ⭐ `JSON` →⭐ `YAML` | `python import_json.py --help` |

⛔ **不该用** ⭐ ：⭐ 期望 ⭐ **全自动托管** ⭐ ——⭐ 现为 ⭐ **半自动**（⭐ 投放 ⭐ 由人决定 ⭐ ）⭐ 。
⭐ 边界 ⭐ ：`B-1` ⭐ ／`B-6` ⭐ ；⭐ 依赖 ⭐ 纯标准库 ⭐ ；⭐ 认领 ⭐ 须用 ⭐ **整件哈希** ⛔ 件头自报值 ⭐ 。

---

## ⭐ `MB-BUNDLE` ⭐ 信箱一键起盘 `tdca-mailbox-bundle`

| ⭐ 项 | ⭐ 内容 |
|---|---|
| ⭐ 做什么 | ⭐ 建五夹 ⭐ ＋ ⭐ 写样例 ⭐ ＋ ⭐ 跑自测 ⭐ ＋ ⭐ 打印 ⭐ 态分布 |
| ⭐ 能力项 | `mailbox.init` ⭐ ／`mailbox.selftest` |
| ⭐ 该用 | ⭐ 首次部署 ⭐ 需快速验证 ⭐ 协议可用 |
| ⛔ **不该用** | ⭐ 生产数据初建 ⭐ （⭐ 须人工核 ⭐ ） |
| ⭐ 入口 | `python _mailbox_init_v1.py --root ./mailbox` |
| ⭐ 出参 | `{dirs, selftest}` |
| ⭐ 边界 | `B-1` |
| ⭐ 依赖 | ⭐ 纯标准库 ⭐ ；⭐ 随包附 ⭐ `ledger.sample.json` ⭐ （⭐ 脱敏 ⭐ ） |

---

## ⭐ 通则（⭐ 九包共用 ⭐ ）

| # | ⭐ 条 |
|---|---|
| `1` | ⭐ 下载后 ⭐ **先验 ⭐ `sha256`** ⭐ 前 `16` 位 ⭐ 与卡面 ⭐ 比对 ⭐ |
| `2` | ⭐ 退出码 ⭐ `0` ⭐ ／`1` ⭐ ／`2` ⭐ 三值 ⭐ 通义 ⭐ |
| `3` | ⭐ 全部 ⭐ **本地运行** ⭐ ，⛔ 上传数据 ⭐ |
| `4` | ⭐ 边界六条 ⭐ 见 ⭐ 总册 ⭐ §七 ⭐ ；⭐ 任一条 ⭐ 违反 ⭐ 即 ⭐ 误用 ⭐ |

---

## ⭐ 边界

- ⚠️ ⭐ 草案 ⭐ 待验收 ⭐ · ⛔ 上站 ⛔ 生效 ⭐。
- ⭐ 随包分发时 ⭐ 按节拆出 ⭐ ，⭐ 包内件名 ⭐ 统一 ⭐ `QUICKREF.md` ⭐。

---

*Reasonix · L1-SI-197 · Manual（速查页合集 V1.0-DRAFT） · 2026-11-05（+08）*
