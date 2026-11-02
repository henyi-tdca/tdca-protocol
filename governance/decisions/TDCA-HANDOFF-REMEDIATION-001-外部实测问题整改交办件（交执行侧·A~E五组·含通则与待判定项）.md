# TDCA-HANDOFF-REMEDIATION-001 · **外部实测问题整改交办件（交执行侧）**

> 文档编号: **TDCA-HANDOFF-REMEDIATION-001** ｜ 版本: **V1.0** ｜ 日期: **2026-09-25**（+08）
> 会话框: **L1-SI-079** ｜ 编制: **Reasonix**（智库）｜ 性质: **交办件（内部件 · 可直接粘贴 · ⛔ 非司法裁决）**
> **授权（创始人 · 逐字）**: 2026-09-25 ——「**要不要真接入 CI？…请选：①先修命中再接入（推荐）整改交办件给执行侧，守门器零扫描必须 fail"是否升格为通则，已公开件（README 等）勘误走追加制，他说的只有 WINDOWS 路径的问题，也要改**」
> **上游**: 外部实测报告（沙箱 clone main，逐套件实跑）＋ **本侧独立复核**（本机实测，main @ `2672d39`）
> ⛔ 零对外；⛔ 不含凭据值；⛔ 不含人名；**时区 +08** ｜ 存证: **`GSEQ-2739`**

---

## 〇、一句话

⭐ 按创始人裁定：**先修命中、后接入 CI**（阶段 2 须再次明示）；**7 处 Windows 硬编码必改**；**守门器「零扫描必须 fail」升格为通则**；**已公开件勘误走追加制**。执行侧按 **A~E 五组**施工，**逐组独立 PR**，⛔ 未经明示不得合并。

---

## 一、本侧复核结论（实测，非采信）

| # | 项 | 实测结果 |
|---|---|---|
| 1 | README 第 62/70 行称"三律守门（律一/律二 **CI 化**）"／"三律（硬约束，**CI 化守门**）" | ⚠️ `.github/workflows` 6 个文件的 `run:` 步骤中**未见**任何守门步骤（**范围内未观察到**）⟹ "CI 化"当前不实 |
| 2 | README 给的用法 `cd tools && python stance_separation_check.py`（**无参数**） | ⚠️ 实测 **RC=0 且零输出** ⟹ 照 README 跑即"静默通过" |
| 3 | `tools/stance_neutrality.py` | `check` 模式 `sys.exit(0 if total == 0 else 1)`；`scan` 模式（默认分支）**恒 exit 0**；本机 `check` 有**真实命中 1 文件 4 处**（见 §四 待判定）；`compiler` 目标本机扫到 **0 文件** |
| 4 | `tools/stance_separation_check.py:122` | `sys.exit(0 if ok == len(sys.argv) - 1 else 1)` ⟹ **不传文件即 exit 0**（实测 RC=0）——**"空输入即通过"第二例** |
| 5 | Windows 硬编码路径 | 已跟踪 `.py` **304 件中恰 7 件**（与外部报告吻合）；未跟踪面另有同类（⛔ 不属公开面，不在本件范围） |
| 6 | `ecoscan/tests/test_ecoscan.py::test_recent_active` | 硬编码 `pushed="2026-08-20T00:00:00Z"` + `days=30` ⟹ 今日（09-25）超窗必红 |
| 7 | `core-go/bridge/tests/test_bridge.py` | 找 `tdcad.exe`，缺则传 `None` ⟹ 无 Go 工具链者全数报错；README 未写"须先 `go build`" |
| 8 | 打包件 | `pyproject.toml` / `setup.py` / `setup.cfg` **全无**（实测 0 件） |
| 9 | **本侧新增**：`tools/tests` 本机复跑 | **80 passed / 1 failed**（`test_mcp_bridge.py::test_stdio_end_to_end`，`AttributeError: 'NoneType' … .strip()` 伴 UTF-8 解码失败） ⟹ 跨平台（中文 Windows）健壮性缺陷，**外部报告未捕获** |

⚠️ Go／Lean／Docker 三栈：本机同样无工具链 ⟹ **标"待证"，不给分不扣分，如实**。

---

## 二、任务分组（A~E，**逐组独立 PR**）

### A 组 · P0 · 守门器「零扫描/零输入即通过」
- **A1** `tools/stance_neutrality.py`：目标→范围**正确映射**；除既有 `compiler`／`repo` 外，须支持**任意路径**（位置参数或 `--scope`）；路径不存在 ⟹ **报错并非 0 退出**（⛔ 不得静默 0 文件）。
- **A2**（两个守门器）**零扫描/零输入必须 fail**：扫描文件数 `== 0` 或未提供任何扫描目标 ⟹ **exit 非 0**，并**显式打印**：扫描根**绝对路径**、**文件计数**、**命中计数**。`scan` 模式亦须有退出码（当前恒 0）。
- **A3** CI：**本件只授权阶段 1**（修工具与文案，⛔ 不接入 CI）。**阶段 2（新增独立 workflow 并把守门步骤设为门禁）须创始人再次明示**；执行侧可**预备**workflow 草案但⛔ 不得提交启用。

### B 组 · P0 · **7 处 Windows 个人路径硬编码**（创始人明示"也要改"）
清单（本侧实测，已跟踪面共 7 件）：
1. `tools/stance_neutrality.py`（`REPO_CL`）
2. `tools/connector-v2/cop_connector.py`（`WS` → `COP_DIR`）
3. `docs/cognitive-compiler/coldstart/coldstart_mcp_client.py`（解释器绝对路径 `_PY`）
4. `docs/cognitive-compiler/coldstart/run_coldstart_rolling.py`（`REPO`）
5. `docs/cognitive-compiler/coldstart/run_coldstart_rolling_dryrun.py`（`REPO`）
6. `docs/cognitive-compiler/coldstart/run_m1_five_emissary.py`（`UG`）
7. `docs/cognitive-compiler/coldstart/run_m3b_coalition_demo.py`（`REPO`）

改法（统一）：
- 一律 `pathlib.Path` + **仓库根自动探测**（`Path(__file__).resolve().parents[n]`）；
- 加**环境变量覆盖**（建议：`TDCA_REPO_ROOT`／`TDCA_COP_DIR`／`TDCA_WS`／`TDCA_PYTHON`，命名可自定但须回报）；
- 默认值指向**仓库内相对路径**；目标不存在 ⟹ **明确报错**（⛔ 不得静默空跑）；
- README／各目录说明**同步写明**默认值与覆盖方式。

### C 组 · P1 · 文档与事实对齐（**追加制**）
- **C1** README §tools 及 §"三律"两处"CI 化"表述改为如实（如"静态检查（**CI 接入待命**）"）；`core-go/docs/formal-proofs/01-TDCA-PROOF-PROGRAM-META-INVERSE-001-…总纲….md:109` 之"已 CI 化"同改。
  ⚠️ **在册件走追加制**：⛔ 不回改原行，另出**勘误追加件**并在件内指明原文出处（创始人已明示）。
- **C2** `tools/connector-v2` README：标注"实跑结果的环境前提"（原"捕获 267"应为特定环境结果），补环境变量入口。
- **C3** `core-go` README「快速开始」补**前置步骤** `go build -o tdcad ./cmd/tdcad`；或 bridge 测试在缺二进制时 `pytest.skip` 并打印构建指令（**缺二进制 ≠ 测试失败**）。

### D 组 · P2 · 测试健壮性
- **D1** `ecoscan/tests/test_ecoscan.py::test_recent_active`：硬编码日期改**相对当前时间**（`datetime.now(timezone.utc) - timedelta(days=k)`）。
- **D2**（**本侧新增**）`tools/tests/test_mcp_bridge.py::test_stdio_end_to_end`：修 `None`／UTF-8 解码健壮性（中文 Windows 环境），使 `tools/tests` **全绿**。

### E 组 · P2 · 可选（可暂缓）
- **E1** 加 `pyproject.toml`（提供 `pip install -e .` 入口）；或明确"不打包"并在 README 说明消费方式。**二选一，可回报后另议**。

---

## 三、通则（创始人已明示升格）

> **通则·守门器零扫描即失守**：凡以"静态扫描结果"作判定的守门工具，**扫描文件数为 0 或未提供扫描目标时，一律判 fail 并显式报告扫描范围**；⛔ **不得以"没扫到"充当"扫了没有违规"**；输出须可区分「未扫到」与「已扫且无违规」。
> ⭐ 落位建议（**待创始人定**）：并入研发治理包／工作规范之**追加件**，与既有"落地原则"同格。

---

## 四、⚠️ 待判定项（⛔ 执行侧不得自行处置，须回报待裁）

本机 `stance_neutrality.py check repo` **真实命中 1 文件 4 处**：
`docs/cop-library/hundred_schools/sunzi/sunzi_real/build_real_cop.py`（含 `[我方]`／`[敌方]` 类字样）。
- 请执行侧**先回报**：该文件性质（是否属"被扫语料／历史语料"）、4 处逐处上下文、是否真违规、是否需要整改或加白。
- ⛔ **本侧与执行侧均不代裁**（涉制度层语义），由创始人裁定后再动。

---

## 五、硬约束（闸门）

1. ⛔ **逐组独立 PR**，⛔ 不得夹带无关改动；⛔ 不得 force-push；
2. ⛔ **未经创始人明示不得合并**；⛔ **阶段 2（接入 CI）须再次明示**；
3. ⛔ 不回改已登记／FROZEN 件（**追加制**）；
4. ⛔ 不含凭据值／人名；⛔ 零对外；
5. ⛔ 不得放宽既有门禁（只能加严）；涉权限变更 ⟹ **停手回报**。

**停手条件**：S-1 需凭据或权限提升｜S-2 涉 FROZEN／已登记件原行｜S-3 发现本件遗漏面（须回报扩容）｜S-4 与在册口径冲突｜S-5 需代裁制度层语义。

---

## 六、回报项（一并回传）

1. 逐组：改动文件清单 + `git diff --stat` + 关键片段；
2. 复跑证据：`python -m pytest tools/tests -q`、（如可）`dual/tests`、`ecoscan/tests` 全量输出尾段；
3. 守门器新行为实证：`scan/check` 于**有效路径**与**无效路径**的**退出码 + 输出**各一例（含扫描根与文件计数）；
4. 7 处硬编码**改前/改后**逐处对照（含环境变量名与新默认值）；
5. §四 待判定项的逐处回报；
6. 零夹带、零凭据自证。

---

## 七、边界与自查

1. 本件为**交办件**（⛔ 非司法裁决）；**未改任何在册件或工程件**（**追加制**）；⛔ 未推；
2. **本侧实测**：双库一致／账尾／`git ls-files` 计数（已跟踪 304 件中 7 件命中）／守门器退出码／`tools/tests` 复跑（80 passed·1 failed）；
3. ⚠️ **本侧 ⛔ 不可核**：Go／Lean／Docker 三栈（本机无工具链）／外部沙箱执行细节／AtomGit·Gitee 侧；
4. ⛔ 零对外；⛔ 不含凭据值；⛔ 不含人名；**时区 +08**。

---

*TDCA-HANDOFF-REMEDIATION-001 V1.0：**外部实测问题整改交办件（交执行侧）** —— 授权（创始人逐字）｜⭐ 五组任务 **A 守门器零扫描必 fail／B 七处 Windows 硬编码必改／C 文档追加勘误／D 测试健壮性／E 打包可选** ｜⭐ **通则**（守门器零扫描即失守，升格）｜⚠️ **待判定一项**（4 处真实命中性质，须回报待裁）｜⭐ CI：**先修命中、后接入**（阶段 2 须再次明示）｜⭐ 逐组独立 PR·⛔ 未经明示不得合并 ｜ 编制: Reasonix（L1-SI-079）｜ 存证: **`GSEQ-2739`***
