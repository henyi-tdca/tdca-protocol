# 日抛型接入最小制度包 · `V1.1-FROZEN`

> **版本**：`V1.1-FROZEN`（生效 `2026-11-16`，创始人签批「按建议办」）｜**替代**：`V1.0-FROZEN`（`2026-11-16T20:35:05+08:00`，⭐ 追加制，⛔ 回改旧版 ⭐ ）
> 会话框：`L1-SI-216` ｜ 时点：`2026-11-16T21:08:06+08:00`（系统实测）
> ⭐ 本版之由 ⭐ ：⭐ 沙盒盲测 ⭐ 走完后出 ⭐ 八处卡点（`K1`~`K8`） ⭐ ，⭐ 本版逐项补正 ⭐ ；⭐ 未受卡点触及之条款 ⭐ 逐字不变 ⭐
> ⭐ 本侧先此认领一处 ⭐ ：⭐ 本侧核证单（`GSEQ-8382`）§四 称「本批已出 `V1.1-DRAFT`」，⭐ 实则未出 ⭐ ——⭐ 说了未做，本件即补 ⭐

---

## 0. 这份文件是什么（读这一段就够）

有人想用一次我们的东西，明天就不用了。这份包回答**四件事**：

1. 你**做哪些事算「接入」**（要守规矩），哪些不算；
2. 你**最少要留什么**（留不住就不许接）；
3. 你的**授权凭证最简长什么样**（一页能填完）；
4. 你走的时候**什么能带走、什么必须留下**。

⭐ **这就是全部**。你不需要再读别的文件就能合规接入一次。
⭐ 唯一例外 ⭐ ：⭐ 首次接入之「**接口要求**」以 ⭐ 站内接口说明为准 ⭐ （见 §5）——⭐ 本包 ⛔ 重抄接口文档 ⭐ 。

---

## 1. 什么算接入，什么不算

| 你做的事 | 算接入吗 | 为什么 |
|---|---|---|
| 浏览公开页面、读公开文档 | ⭐ 不算 ⭐ | 等同游客，只看不写 |
| 只读查询公开接口（不写入、不留痕、不调他人资产） | ⭐ 不算 ⭐ | 无状态、无处置对象 |
| 写入、提交、创建任何记录 | ⭐ 算 ⭐ | 产生了要负责的痕迹 |
| 申请存证、取回执 | ⭐ 算 ⭐ | 进入留痕体系 |
| 调用他人资产（含自动调用） | ⭐ 算 ⭐ | 触他人权利 |
| 代为配置、代为授权 | ⭐ 算 ⭐ | 涉及第三方 |

⭐ 一句话 ⭐ ：**你只要「往外留了东西」或「动了别人的东西」，就算接入。**

⭐ 首次接入建议动作 ⭐ （`K1` 补正）：⭐ 先做一次「创建一条记录」 ⭐ ——⭐ 该动作在任何沙盒位与线上均可走通 ⭐ ；
⭐ 「申请存证」之入口、请求形态与回执形态 ⭐ 见 ⭐ 站内接口说明 ⭐ ，⭐ 本包 ⛔ 展开 ⭐ （⭐ 盲测实证：各环境入口不一，写死必误导 ⭐ ）。

---

## 2. 最少要留什么（七项，缺一不许接）

| # | 留什么 | 怎么说清 | 形态（`K3`／`K8` 补正） |
|---|---|---|---|
| `1` | ⭐ 谁 ⭐ | 主体标识，须可回溯到具体主体 | ⭐ 自然人 ⭐ ：真实姓名；⭐ 机构 ⭐ ：全称；⭐ 智能体 ⭐ ：平台登记号；⭐ 系统内部标识（如 `DID`）由平台分配，⭐ 填平台给的那个 ⭐ |
| `2` | ⭐ 何时 ⭐ | 精确到秒，带时区 | `2026-11-16T21:08:06+08:00` |
| `3` | ⭐ 调了什么 ⭐ | ⭐ 对外名称 ⭐ ，非内部编号 | ⭐ 名称以 ⭐ 站内能力清单页公布者为准 ⭐ ，⛔ 自拟（`K4`） |
| `4` | ⭐ 规模 ⭐ | 条数／字节／次数，择实报 | — |
| `5` | ⭐ 输出去向 ⭐ | 只在自己系统内／给了第三方／公开 | 三选一 |
| `6` | ⭐ 授权依据 ⭐ | 凭哪份授权 | 指向 §3 四空件 |
| `7` | ⭐ 结果 ⭐ | 成功／拒绝／部分成功 | ⭐ 拒绝须带理由码，码表见下 ⭐ |

⭐ 理由码最小表 ⭐ （`K8` 补正） ⭐ ：

| 码 | 义 |
|---|---|
| `OK` | 成功 |
| `DENIED_SCOPE` | 拒绝：超出授权范围 |
| `DENIED_PARAM` | 拒绝：参数不合要求 |
| `DENIED_QUOTA` | 拒绝：超出配额或频次 |

⭐ 平台另有更细码时 ⭐ 以平台为准 ⭐ ；⭐ 四类之外 ⭐ 照平台原文抄 ⭐ ，⛔ 自造码 ⭐ 。

---

## 3. 授权凭证最简样子（四个空，填完即用）

```
授权主体：____________________（谁给的权）
授权对象：____________________（给谁用）
授权范围：____________________（能用什么、用到什么程度）
授权期限：____________________（从何时到何时；可写「本次一次性」）
```

四条**都必须填**，任何一个空着，⭐ 视为未授权 ⭐ 。

### 授权范围写多细（`K5` 补正，三档示例任选其一）

| 档 | 怎么写 | 适合 |
|---|---|---|
| 窄 | ⭐ 仅「创建记录」一项，≤`10` 条 ⭐ | 试一次 |
| 中 | 「创建记录」＋「申请存证」，≤`100` 条，期限 `7` 天 | 小批作业 |
| 宽 | 站内全部公开能力，按平台配额 | 正式接入 |

⭐ 判据 ⭐ ：⭐ 你写下的范围 ⭐ 用得着就行 ⭐ ；⭐ 超出即被拒（`DENIED_SCOPE`） ⭐ ——⭐ 宽窄由你定，⛔ 由平台猜 ⭐ 。

### 签名怎么算数（`K2` 补正）

⭐ 二者择一 ⭐ ：

1. ⭐ 本人手写签署 ⭐ （纸质或电子件上署名）；
2. ⭐ 使用平台签发的授权码 ⭐ 填入（⭐ 一码一次，可设时长 ⭐ ）。

⭐ 要求 ⭐ ：⭐ 须能表明本人意思 ⭐ ；⭐ 智能体 ⛔ 代签 ⛔ 代持 ⛔ 代填 ⭐ 。⭐ 形式类型记入留痕 §2 #6 ⭐ 。
⭐ 协议层不收费 ⭐ ——接入本身不产生费用；资产配置与增值服务另行约定。

---

## 4. 你走的时候：什么能带走，什么留下

| 项 | 能带走 | 必须留下 |
|---|---|---|
| 你的业务数据 | ⭐ 能 ⭐（导出即走） | — |
| 你的授权记录 | ⭐ 能 ⭐（副本） | ⭐ 正本留痕 ⭐（谁也不能删） |
| 你产生的留痕（七项） | — | ⭐ 必须留 ⭐（日后说得清的唯一依据） |
| 我们的公开内容 | 按公开许可 | — |
| 他人资产 | ⛔ 不能 | — |

⭐ 「日抛」只抛两样 ⭐ ：**会话与临时产物**。
⭐ 「日抛」不抛留痕与授权记录 ⭐ ——把它们一起抛掉，等于把责任也抛掉。

---

## 5. 首次接入之接口要求（`K6`／`K7` 补正·只给指向）

⭐ 本包 ⛔ 重抄接口文档 ⭐ 。⭐ 但首次接入须过平台两道体检 ⭐ ，⭐ 提前知道可少试错 ⭐ ：

| # | 平台要件 | 你要准备 |
|---|---|---|
| ⭐ 身份角色 ⭐（`K6`） | 平台按 ⭐ 五类主体 ⭐ 分角色，⭐ 关闭记录时另需「三位一体」角色 ⭐ | ⭐ 先确认自己属哪类 ⭐ （界面会提示） |
| ⭐ 六要素声明 ⭐（`K7`） | ⭐ 目标函数 ⭐ ／⭐ 约束矩阵 ⭐ ／⭐ 先验分布 ⭐ ／⭐ 配置权边界 ⭐ ／⭐ 预期分配 ⭐ ／⭐ 审计轨迹 ⭐ | ⭐ 六项各一句话 ⭐ 即可，⭐ 界面逐项索取 ⭐ |

⭐ 具体字段名、必填规则、报错文案 ⭐ 一律 ⭐ 以站内接口说明为准 ⭐ 。

---

## 6. 三条红线（破一条即停接入）

1. ⭐ 不得以「一次性」为由不填授权四空 ⭐ ；
2. ⭐ 不得把他人资产转手再给第三方 ⭐ ；
3. ⭐ 不得把留痕改掉、删掉或补造 ⭐ 。

---

## 7. 机读块（可程序校验，与上文同义）

```yaml
disposable_access_package:
  version: "1.1-frozen"
  counts_as_access: ["write", "submit", "create_record", "request_attestation",
                     "call_third_party_asset", "configure_for_others", "authorize_for_others"]
  not_access: ["browse_public", "read_public_docs", "readonly_query_stateless"]
  first_action_hint: "create_record"
  attestation_entry: "见站内接口说明（本包不展开）"
  min_trace_fields: ["who", "when", "what", "scale", "output_destination",
                     "authorization_basis", "result"]
  trace_forms:
    who: "自然人真名／机构全称／智能体平台登记号；系统标识用平台分配值"
    when: "ISO8601 含时区，精确到秒"
    what: "站内能力清单页之对外名称，不用内部编号"
  reason_codes_min: {"OK": "成功", "DENIED_SCOPE": "超授权范围",
                     "DENIED_PARAM": "参数不合", "DENIED_QUOTA": "超配额或频次"}
  permit_required_fields: ["grantor", "grantee", "scope", "term"]
  permit_scope_examples: {"narrow": "仅创建记录 ≤10 条", "medium": "创建记录＋申请存证 ≤100 条 7 天",
                          "wide": "站内全部公开能力，按平台配额"}
  permit_signing: ["handwritten_by_principal", "platform_issued_code"]
  permit_signing_rule: "须能表明本人意思；智能体不得代签代持代填"
  protocol_layer_fee: "free"
  platform_intake_hint:
    roles: "五类主体；关闭记录另需三位一体角色"
    six_elements: ["目标函数", "约束矩阵", "先验分布", "配置权边界", "预期分配", "审计轨迹"]
    detail: "以站内接口说明为准"
  on_exit:
    may_take: ["own_business_data", "copy_of_authorization_record"]
    must_keep: ["trace_records", "authorization_record_original"]
    may_not_take: ["third_party_assets"]
  red_lines: ["empty_permit_field_is_unauthorized",
              "no_resale_of_third_party_assets",
              "no_alteration_of_trace_records"]
```

---

## 8. English summary

**Minimum access package — read this and you are compliant for one use.** (`V1.1`)

- **What counts as access**: writing, submitting, creating records, requesting attestation, calling someone else's assets, configuring or authorizing on behalf of others. Browsing public content and stateless read-only queries do **not** count. For a first run, **create one record** — it works in any sandbox and in production.
- **Seven records you must keep**: who, when, what, scale, output destination, authorization basis, result. Use the *display name* from the published capability list for "what". Rejections carry one of four codes: `OK`, `DENIED_SCOPE`, `DENIED_PARAM`, `DENIED_QUOTA`.
- **Permit**: four fields — grantor, grantee, scope, term. Any blank field means **no authorization**. Write the scope as narrow/medium/wide as you need; exceeding it is denied. Signing is either handwritten by the principal or a platform-issued code — an agent may never sign, hold, or fill it on someone's behalf. The protocol layer is **free of charge**.
- **First-time platform checks** (details in the on-site interface guide, not here): five principal roles (closing a record additionally needs a three-in-one role), and a six-element declaration — objective function, constraint matrix, prior distribution, configuration-right boundary, expected allocation, audit trail.
- **On exit**: take your own data and a copy of your authorization record; the trace records and the original authorization record **stay**. "Disposable" disposes of sessions and temporary artifacts — **not** of traces and authorizations.
- **Three red lines**: no empty permit fields, no resale of third-party assets, no altering traces.

---

## 9. 修订对照（`V1.0` → `V1.1`，逐条对卡点）

| 卡点 | `V1.0` 之缺 | ⭐ `V1.1` 之补 ⭐ | 位置 |
|---|---|---|---|
| `K1` | 「申请存证」零指引 | ⭐ 首动建议「创建记录」＋存证入口指向站内 ⭐ | §1 末 |
| `K2` | 签名形式与落点无 | ⭐ 二者择一 ＋ 不得代签代持代填 ⭐ | §3 末 |
| `K3` | 主体标识只给原则 | ⭐ 四类形态逐项示例 ⭐ | §2 `#1` |
| `K4` | 对外能力名无查询处 | ⭐ 以站内能力清单页为准，⛔ 自拟 ⭐ | §2 `#3` |
| `K5` | 范围粒度无示例 | ⭐ 窄／中／宽三档示例 ＋ 超范围即拒 ⭐ | §3 |
| `K6` | 身份角色零覆盖 | ⭐ 一行指引（五类主体＋三位一体） ⭐ | §5 |
| `K7` | 六要素零覆盖 | ⭐ 一行 ＋ 六要素名 ⭐ | §5 |
| `K8` | 理由码无码表 | ⭐ 四码最小表 ⭐ | §2 末 |

⭐ 未列之处 ⭐ 逐字同 `V1.0` ⭐ 。

## 10. 边界

⛔ 回改 `V1.0` · ⛔ 重抄接口文档 · ⛔ 替代在册制度（冲突以在册为准）· ⛔ 以本包充接口合规之证。

---

*Reasonix（智库侧）· `L1-SI-216` · 制度件 `V1.1-FROZEN` · `2026-11-16T21:08:06+08:00`（系统实测）*
