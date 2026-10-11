# TDCA-G3-IDENTITY-LINK-SYNC-001 · 身份桥接联动交付记录（G3 深化 #18）

> 文档编号: TDCA-G3-IDENTITY-LINK-SYNC-001 ｜ 日期: 2026-09-11（+08）｜ 会话框: **L1-SI-029-3415CF** ｜ 编制: Reasonix
> 存证: **GSEQ-1264**（Delivery）｜ 交接来源: TDCA-SESSION-20260911-FINAL-012 §二-A（深化项余项之首）
> 关联件: **AMEND-2**（GSEQ-1260，法理定性）｜ AMEND-1（GSEQ-1258）｜ #17 无主托管（GSEQ-1256~1261）｜ 身份桥接 M1（GSEQ-1191）｜ 身份管理第二册（GSEQ-1186）

---

## 一、任务与制度锚点

**任务（FINAL-012 §二-A）**：G3 #18 —— 与身份桥接联动（**主体消亡 → 链接失效同步 `revoke`**）；落点先读 `tdca-adapters/identity_bridge/identity_bridge.py` 的 `revoke` 接口再设计；**须与 AMEND-2 一致**（主体消亡的认定若涉争议，仍按司法文件口径）。

| 制度依据 | 位置 | 本项落实 |
|---|---|---|
| **TDCA-STD-AGENT-ID-002 §3.2 R-8**（范围与链接层衔接） | `governance/documents/` | 消亡事实属"走出 TDCA 范围"的法律层输入 → 经 TDID↔OID 链接层对接；TDCA 不替代法律确权（L0 不越级）→ 本模块 `legal_ref` 前置 |
| **TDCA-STD-AGENT-ID-003 §六 / §八-2**（失效联动"令牌失效 → revoke"列为待细化） | 同上 | 本模块即该待细化项之落实（`token-expiry` / 注销 / 终态触发集） |
| **AMEND-2 法理定性**（GSEQ-1260） | `governance/decisions/` | 争议裁决权属司法部门；无司法可验证正式文件前 TDCA 零动作（只能休眠）→ 本模块**争议痕迹 + 无 `judicial_ref` ⇒ 零动作** |
| `estate.report_death`（死亡事实须外部法律文书） | `inheritance/estate.py` | 同口径复用（`legal_ref` 必填、fail-closed） |
| `identity_bridge.revoke`（失效同步既有接口） | `identity_bridge/identity_bridge.py` | 本模块仅**调用**，不改其实现（封板纪律：已交付接口不动） |

## 二、联动规则（五条纪律）

1. **法律事实前置**：`on_demise` 须携 `legal_ref`（外部法律文书引用）；缺失即拒（fail-closed，TDCA 不越级判定消亡）
2. **争议痕迹零动作（AMEND-2）**：存在争议痕迹（未决争议 ∪ 争议史无司法文件结案 ∪ 争议流程存在）且无 `judicial_ref` ⇒ **不得 `revoke`**，只让主体休眠（计时继续）
   - 口径与 `escheat.escheat`（AMEND-2 落点）一致：**TDCA 内部裁决登记不构成司法裁决、不得作为处分依据**——故 `DisputeRegistry` 已 `ADJUDICATED` 仍属"痕迹未凭司法文件结案"
3. **仅终态联动**：`disposition="deregister"`（消亡路径）／`dormancy` DEREGISTERED 终态／权益已托管公共品／令牌日抛失效 方触发；`continue` / `dormant`（休眠中）**零动作**——休眠不失效链接
4. **幂等**：无活跃链接 ⇒ no-op（如实标注 `no-active-link`，不报错；重复同步第二次即此结果）
5. **逐判定留痕**：每次判定（含零动作分支）生成一条 `identity-link-sync` 存证；`revoke` 本身另生成 `identity-unlink`（桥接既有行为）——**零动作亦留痕**，保证"TDCA 未动作"这一事实可审计

**公共品路径例外**：无归属、无争议、满一年 → 社区基金公共品（AMEND-2 第 4 条，善意管理／无因管理）⇒ 该路径**无需任何裁决引用**即可完成终端联动（用例 11 实证 `judicial_ref is None`）。

## 三、实现与接口

**新增模块**：`tdca-adapters/inheritance/identity_link_sync.py`（制度水印 + 六要素 docstring + `_LocalSeal` 兜底）

| 接口 | 语义 |
|---|---|
| `on_demise(tdid, *, disposition, legal_ref, judicial_ref=None)` | 消亡事实路径：`deregister` ⇒ 联动；`continue`/`dormant` ⇒ 零动作；缺 `legal_ref` ⇒ 拒 |
| `sync_terminal(tdid, *, trigger, legal_ref=None, judicial_ref=None)` | 终态路径：`trigger ∈ {dormancy-timeout, escheat-public-goods, token-expiry}`；提供注册表时**实测终态**（未达终态 ⇒ 零动作） |
| `sync_batch(tdids, *, trigger, judicial_ref_of=None)` | 批量终态联动（如 `dormancy.sweep` 后），逐主体独立判定 |
| `pending_links()` | **只读**：仍 ACTIVE 的外部链接（悬挂链接审计视图） |
| `dispute_open(tdid)` / `has_dispute_trace(tdid)` | 只读预检：未决争议 / 争议痕迹 |

**结果对象**：`SyncOutcome`（`action ∈ {revoked, no-active-link, deferred-dispute, not-terminal}` + `reason` + `legal_ref/judicial_ref` + `dispute_open/dispute_trace` + `oid` + `nca_refs` + `simulated`）

**常量**：`DEMISE_TRIGGERS` / `TERMINAL_TRIGGERS` / `SYNC_ACTIONS`；`inheritance/__init__.py` 已导出（#18 段落）。

## 四、验证证据

| 验证 | 命令 | 结果 |
|---|---|---|
| 继承线自检（含新增用例） | `python .tdca-nca/scripts/_inherit_selfcheck.py` | **65 passed / 0 failed**（文件 6 个）= 既有 49 + 新增 16 |
| 继承线 + 身份桥接线（跨模块回归） | `python .tdca-nca/scripts/_inherit_selfcheck.py --with-identity-bridge` | **75 passed / 0 failed**（文件 7 个）＝ 65 + identity_bridge 10 |
| 包内导入与默认构造 | `import inheritance`（`tdca-adapters` 入 sys.path） | OK（`IdentityLinkSync()` 自建 bridge + 存证生成器） |

**用例分布**：`test_estate` 10 ｜ `test_dormancy` 10 ｜ `test_shapley` 9 ｜ `test_royalty` 7 ｜ `test_escheat` 13 ｜ **`test_identity_link_sync` 16** ｜ `test_identity_bridge` 10。
**关键断言**：注销处置 → 双向解析终止 + OID 索引释放 + `REVOKED` + 依据含 `legal_ref`；缺 `legal_ref` → 拒且链接维持；争议未决 + 无司法文件 → `deferred-dispute` 且链接仍在；**内部裁决登记（ADJUDICATED）后仍须司法文件**；凭 `judicial_ref` → 放行；未达终态 → 零动作；**公共品路径无争议无归属 ⇒ 联动且 `judicial_ref is None`**；零动作分支同样产出存证。

## 五、口径与留痕

1. **AMEND-2 一致性（核心）**：本模块"不得有任何动作"体现为 `deferred-dispute`——**不 revoke、不改状态、不改计时**，仅留痕说明"TDCA 未动作"；争议结论一律须 `judicial_ref`（含 ADJUDICATED 后）
2. **工具修正（如实留痕）**：自检驱动 `_inherit_selfcheck.py` 原仅支持**零参数 fixture**——新增用例引入组合 fixture（`sync(bridge, dorm, esc)`）后暴露两处缺陷：① 不支持 fixture 间依赖；② 无同用例实例缓存（组合 fixture 与用例参数各持一份实例 → 断言错位）。已修正为**递归解析 + 同用例缓存**，并新增 `--with-identity-bridge` 跨模块扫描；**既有 49 用例的输出口径与结果不变**（65/75 两档均零失败）
3. **自我更正**：首轮自检 16 条新用例全失败于 fixture 构造（`TypeError: sync() missing 3 required positional arguments`）→ 定位为驱动缺陷而非模块缺陷，修正驱动后全绿；曾临时新建 `_identity_sync_selfcheck.py` 后**删除**（避免工具冗余，修正并入既有驱动）
4. **不改既有交付**：`identity_bridge.py` 与 `estate/dormancy/shapley/royalty/escheat` 均未改动（封板纪律）；本项为**新增**模块 + 测试 + 导出
5. **数据性质**：全链**模拟态 ID92**（OID 为模拟占位、`legal_ref`/`judicial_ref` 为样例文书引用，非真实法律文书）

## 六、余项

- **G3 线全部闭环**：#14~#17（GSEQ-1255~1261）+ **#18（本件）** —— G3 线**零余项**
- **制度提示（非阻断，承接 AMEND-2 §五）**：TDCA 内部「裁决/提案」类登记的**法律定位**宜在制度文本中显式标注「非司法裁决、不得单独作为处分依据」——本模块已在口径上落实，制度文本修订仍待随下次制度件处理
- **待触发（本框 A 块其余项）**：M2 线 5 项 ｜ M4 线 4 项 ｜ **#20** national-format 独立工具包（待裁定是否独立发包）

---

*G3 #18 身份桥接联动：主体消亡（法律事实）／休眠期满注销／公共品托管／令牌失效 → TDID↔OID 链接失效同步；争议痕迹无司法文件 ⇒ 零动作只休眠（AMEND-2）；公共品路径无需裁决引用 ｜ 16 用例全绿（继承线 65 + 桥接线 10 = 75）｜ 存证: GSEQ-1264*
