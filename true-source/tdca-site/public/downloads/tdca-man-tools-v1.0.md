# ⭐ **TDCA 官方工具 ⭐ 使用手册**（⭐ 总册 ⭐ `V0.1-DRAFT` ⭐ ）

> 件号：**`TDCA-MAN-TOOLS-001`** ｜ 版本：**`V0.1-DRAFT`** ｜ 日期：**`2026-11-05`**（+08）
> 编制：**`Reasonix`**（智库）｜ 操作类型：**`Manual`**
> 性质: ⚠️ **草案 · 待验收 · 拟对外（⛔ 未生效 · ⛔ 未上站）**
> 来处：⭐ 创始人 ⭐ 本框 ⭐ 选定 ——⭐ 形态 ⭐ 乙 ⭐ （⭐ 一本总册 ＋ ⭐ 九页速查 ⭐ ）／⭐ 起草 ⭐ 本侧 ⭐
> 依据：内部缺口评估件（另册，⛔ 对外）§五 十节骨架

---

## 一、⭐ 这是什么（⭐ 九包 ⭐ 一览 ⭐ ）

| ⭐ 包 | ⭐ 一句话 | ⭐ 依赖 | ⭐ 线上 |
|---|---|---|---|
| `tdca-microtax` ⭐ （`A-2` ⭐ ） | ⭐ 微交付税收计算（⭐ 调度税 ⭐ ／⭐ 交易费 ⭐ ／⭐ 净额 ⭐ ） | ⭐ 标准库 ⭐ ＋ ⭐ 同货架 ⭐ `A-3` ⭐ 环境 ⭐ | ✅ `64,278 B` |
| `tdca-nsfl-compiler` ⭐ （`A-3` ⭐ ） | ⭐ 负空间语言词法与编译 | ⭐ 标准库 | ✅ `54,989 B` |
| `tdca-cert-tool` ⭐ （`A-4` ⭐ ） | ⭐ 存证自检工具 | ⭐ 标准库 | ✅ `8,541 B` |
| `tdca-call-rules` ⭐ （`A-5` ⭐ ） | ⭐ 商业调用规则引擎（⭐ 判定 ⭐ ／⭐ 税明细 ⭐ ） | ⭐ 标准库 | ✅ `12,128 B` |
| `tdca-govtools` ⭐ （`A-1` ⭐ ） | ⭐ 治理工具七件（⭐ 见第五节 ⭐ ） | ⭐ 标准库 ⭐ ＋ ⭐ **`PyYAML`** ⭐ | ✅ `35,668 B` |
| `tdca-legal-agent` ⭐ （`A-6` ⭐ ） | ⭐ 法务智能体（⭐ 冲突检测 ⭐ ／⭐ 负空间过滤 ⭐ ） | ⭐ **纯标准库** | ✅ `29,135 B` |
| ⭐ `tdca-mailbox-spec` | ⭐ 信箱协作协议（⭐ 规范 ⭐ ） | ⭐ 无 ⭐ （⭐ 纯文档 ⭐ ） | 📦 ⭐ 已出包待上架 |
| ⭐ `tdca-mailbox-refimpl` | ⭐ 信箱协作参考实现（⭐ 五件 ⭐ ） | ⭐ **纯标准库** | 📦 ⭐ 同上 |
| ⭐ `tdca-mailbox-bundle` | ⭐ 信箱协作一键起盘 | ⭐ **纯标准库** | 📦 ⭐ 同上 |

---

## 二、⭐ 怎么拿到

⭐ 站点 ⭐ 工具货架 ⭐ ：`https://tdca.com.cn/toolshelf` ⭐ ——⭐ 六卡 ⭐ 各带 ⭐ 依赖 ⭐ ／⭐ 下载 ⭐ ／⭐ `sha256` ⭐ ／⭐ 许可 ⭐ ；⭐ 信箱协作 ⭐ 为 ⭐ 独立一卡 ⭐ （⭐ 卡内三分下载 ⭐ ）⭐ 。

---

## 三、⭐ 怎么验真（⭐ 必做 ⭐ ）

⭐ 每个包 ⭐ 卡面 ⭐ 标 ⭐ `sha256` ⭐ **前 `16` 位** ⭐ 。⭐ 下载后 ⭐ 本地复算 ⭐ ：

```
# Linux / macOS
sha256sum tdca-xxx-v1.0.zip | cut -c1-16 | tr 'a-f' 'A-F'
# Windows PowerShell
(Get-FileHash tdca-xxx-v1.0.zip -Algorithm SHA256).Hash.Substring(0,16)
```

⭐ 与卡面 ⭐ 不符 ⭐ ⟹ ⛔ 使用 ⭐ ，⭐ 请回报 ⭐ 。

---

## 四、⭐ 怎么跑（⭐ 通则 ⭐ ）

1. ⭐ 解包 ⭐ ：`unzip tdca-xxx-v1.0.zip`
2. ⭐ 读包内 ⭐ `README.md` ⭐ （⭐ 四要素 ⭐ ）
3. ⭐ 建议 ⭐ 干净 ⭐ `venv` ⭐ ：`python -m venv venv && venv/bin/pip install -r requirements.txt`（⭐ 无 ⭐ `requirements.txt` ⭐ 者 ⭐ 即 ⭐ 零依赖 ⭐ ）
4. ⭐ 按 ⭐ 第五节速查 ⭐ 跑 ⭐ 一行 ⭐

⭐ 注 ⭐ ：⭐ `A-1` ⭐ 需 ⭐ `PyYAML` ⭐ ；⭐ 其余 ⭐ 除 ⭐ `A-2` ⭐ 需与 ⭐ `A-3` ⭐ 同环境 ⭐ 外 ⭐ 皆 ⭐ ⛔ 需三方库 ⭐ 。

---

## 五、⭐ 参数与输出 ⭐ （⭐ 速查 ⭐ · ⭐ 每包 ⭐ 一页 ⭐ 见随包 ⭐ `QUICKREF.md` ⭐ ）

### ⭐ `A-1` ⭐ 治理七件

| ⭐ 工具 | ⭐ 做什么 | ⭐ 典型命令 |
|---|---|---|
| `_nca_chain_verify_v1.py` | ⭐ 存证链完整性核（⭐ 断链 ⭐ ／⭐ 重号 ⭐ ） | `python _nca_chain_verify_v1.py --quiet` |
| `_nca_discipline_check_v5.py` | ⭐ 纪律机验 | `python _nca_discipline_check_v5.py` |
| `_mailbox_ledger_v1.py` | ⭐ 信箱台账（⭐ 对账 ⭐ ／⭐ 认领 ⭐ ） | `python _mailbox_ledger_v1.py --check` |
| `_daily_patrol_v1.py` | ⭐ 日常巡检 | `python _daily_patrol_v1.py --quiet` |
| `_weekly_deep_check_v1.py` | ⭐ 周度深核 | `python _weekly_deep_check_v1.py --quiet` |
| `_ops_daily_v1.py` | ⭐ 运维日报（⭐ 六项核 ⭐ ） | `python _ops_daily_v1.py --mode morning` |
| `_deliver_seal_v1.py` | ⭐ 交付封签（⭐ 自哈希 ⭐ ＋ ⭐ 旁注 ⭐ ） | `python _deliver_seal_v1.py --help` |

⭐ 退出码通则 ⭐ ：⭐ **`0` ⭐ 通过 ⭐ ／⭐ `1` ⭐ 有差 ⭐ ／⭐ `2` ⭐ 读数不可得 ⭐** ⭐ 。

### ⭐ `A-2`~`A-6` ⭐ 一行

```
A-2: from microtax import compute_taxes   # 输出 调度税/交易费/合计/净额
A-3: python -m nsfl_compiler <源文件>     # 词法 token 序列
A-4: python cert_l1.py --help             # selfcheck / endpoint 两参
A-5: python engine/call_rules_engine.py --caller u1 --scene s1 --value 1000 --tax 200
A-6: from legal_agent.interface import LegalAgentInterface
```

### ⭐ 信箱三包

```
bundle: python _mailbox_init_v1.py --root ./mailbox    # 建五夹＋写样例＋自测
refimpl: python _mailbox_ledger_v1.py --check --mailbox-root ./mailbox
         python _mailbox_drop_v1.py --file x.md --to TO-EXEC --mailbox-root ./mailbox
```

---

## 六、⭐ 数据格式

| ⭐ 包 | ⭐ 输入 | ⭐ 样例 |
|---|---|---|
| ⭐ 信箱 | ⭐ 件 ⭐ ＋ ⭐ 同名 ⭐ `.sha256`（⭐ `17 B` ⭐ 单行大写 ⭐ ） | ⭐ 包内 ⭐ `ledger.sample.json`（⭐ 脱敏 ⭐ ） |
| ⭐ `A-2` | ⭐ 金额 ⭐ ／⭐ 场景 ⭐ ／⭐ 税基 | ⭐ 包内 ⭐ `README` ⭐ 示例 |
| ⭐ `A-5` | ⭐ 调用方 ⭐ ／⭐ 场景 ⭐ ／⭐ 价值 ⭐ ／⭐ 税 | ⭐ 同上 |

---

## 七、⭐ 边界（⭐ 要紧 ⭐ · ⭐ 必读 ⭐ ）

| # | ⭐ 条 |
|---|---|
| `1` | ⭐ 信箱协作 ⭐ 现为 ⭐ **半自动** ⭐ ——⭐ 认领 ⭐ ／⭐ 回执 ⭐ ／⭐ 对账 ⭐ 由脚本做 ⭐ ，⭐ **投放 ⭐ 由人决定** ⭐ ；⛔ 全自动档 ⭐ 未上线 ⭐ |
| `2` | ⭐ 工具 ⭐ **⛔ 承载真实资金流** ⭐ ——⭐ 分润 ⭐ 为 ⭐ 模拟态 ⭐ 记账 ⭐ |
| `3` | ⭐ 输出 ⭐ **⛔ 作 ⭐ 司法裁决 ⭐ 或 ⭐ 单独处分依据** ⭐ |
| `4` | ⭐ 税收 ⭐ 计算 ⭐ 依 ⭐ 在册参数 ⭐ ，⭐ **⛔ 替代 ⭐ 法定申报 ⭐** |
| `5` | ⭐ 治理七件 ⭐ 面向 ⭐ 本体系 ⭐ 内部件 ⭐ 格式 ⭐ ；⭐ 异构环境 ⭐ 使用 ⭐ 须 ⭐ 自建数据 ⭐ |
| `6` | ⭐ 所有工具 ⭐ **⛔ 上传任何数据 ⭐ 到外部** ⭐ ；⭐ 全部 ⭐ 本地运行 ⭐ |

---

## 八、⭐ 故障排查（⭐ 常见 ⭐ ）

| ⭐ 现象 | ⭐ 因 | ⭐ 解 |
|---|---|---|
| `ModuleNotFoundError: yaml` | ⭐ `A-1` ⭐ 缺 ⭐ `PyYAML` | `pip install pyyaml` ⭐ ，⭐ 或 ⭐ 用 ⭐ 信箱 ⭐ `JSON` ⭐ 后端 ⭐ |
| ⭐ 退出码 ⭐ `2` | ⭐ 读数不可得 ⭐ （⭐ 数据面 ⭐ 不在 ⭐ ） | ⭐ 检查 ⭐ 数据目录 ⭐ ／⭐ 先 ⭐ 跑 ⭐ 初始化 ⭐ |
| ⭐ `A-2` ⭐ 导入失败 | ⭐ 未与 ⭐ `A-3` ⭐ 同环境 ⭐ | ⭐ 两包 ⭐ 同置 ⭐ 同 ⭐ `venv` |
| ⭐ 信箱 ⭐ 认领失败 | ⭐ `sha256` ⭐ 用了 ⭐ 件头自报值 ⭐ | ⭐ 须用 ⭐ **整件原始字节** ⭐ 哈希 ⭐ |
| ⭐ 中文 ⭐ 乱码 | ⭐ 终端 ⭐ 非 ⭐ `UTF-8` | `PYTHONUTF8=1` ⭐ 或 ⭐ 改 ⭐ 代码页 ⭐ |

---

## 九、⭐ 版本与更新

| ⭐ 项 | ⭐ 说明 |
|---|---|
| ⭐ 版本号 | ⭐ `vX.Y` ⭐ ——⭐ `X` ⭐ 不兼容变更 ⭐ ，⭐ `Y` ⭐ 兼容修订 ⭐ |
| ⭐ 升级 | ⭐ 下新包 ⭐ → ⭐ 验 ⭐ `sha256` ⭐ → ⭐ 替换 ⭐ ；⭐ 数据 ⭐ 格式 ⭐ 变更 ⭐ 于 ⭐ `README` ⭐ 明示 ⭐ |
| ⭐ 通知 | ⭐ 站点 ⭐ 公告栏 ⭐ |

---

## 十、⭐ 许可与责任

| ⭐ 项 | ⭐ 内容 |
|---|---|
| ⭐ 许可 | ⭐ `Apache-2.0` ⭐ （⭐ 各包 ⭐ 附 ⭐ `LICENSE` ⭐ 全文 ⭐ ） |
| ⭐ 免责 | ⭐ 按 ⭐ 「⭐ 现状 ⭐ 」⭐ 提供 ⭐ ，⭐ 无 ⭐ 明示 ⭐ 或 ⭐ 默示 ⭐ 担保 ⭐ |
| ⭐ 分润 ⭐ 声明 | ⭐ 模拟态 ⭐ 记账 ⭐ ，⭐ ⛔ 承诺 ⭐ 现金 ⭐ 兑付 ⭐ |
| ⭐ 品行 ⭐ 声明 | ⭐ ⛔ 声称 ⭐ 与 ⭐ 任何 ⭐ 上游项目 ⭐ 存在 ⭐ 背书 ⭐ 关系 ⭐ |

---

## ⭐ 边界（⭐ 本件 ⭐ 自身 ⭐ ）

- ⚠️ ⭐ 草案 ⭐ · ⭐ 待验收 ⭐ · ⛔ 生效 ⛔ 上站 ⛔ 对外 ⭐。
- ⭐ 九页 ⭐ `QUICKREF.md` ⭐ 与 ⭐ 随包挂载 ⭐ 另批 ⭐（⭐ 本件 ⭐ 只出总册 ⭐ ）⭐ 。

---

*Reasonix · L1-SI-197 · Manual（工具总册 V0.1） · 2026-11-05（+08）*
