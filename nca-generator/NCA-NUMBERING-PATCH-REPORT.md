# NCA 编号机制补丁 · 执行回报报告（WorkBuddy）

> 执行依据：WorkBuddy 执行指令 `NCA 编号机制补丁（选项 B+C，GSEQ-0544）`；编号口径 max+1 裁定 GSEQ-0551；本机 PR 组装 GSEQ-0552
> 执行方：WorkBuddy ｜ 时间：2026-08-27 17:35 ｜ 纪律：产物不推送（待签批走 PR）、NSFL 未触碰、凭证零落盘（本任务无外部 API）

## 一、根因（编号事故 GSEQ-0540 后续）

旧 `nca_generator._seq_file()` 仅维护一个**按天的计数器文件** `.seq-{YYYYMMDD}`，**落盘前从不扫描 `.tdca-nca` 目录**。因此：

- 人工若手工预分配 `TDCA-REASONIX-{date}-155.yaml`（如 M2 编译 NCA），计数器仍从 154→155；
- `generate_nca` 复用 `155` → **覆盖**手工文件，M2 provenance 丢失（即 155 撞号事故）。

根因 = **编号权威来自计数器而非目录**，且**允许手动预分配**。

## 二、补丁内容（选项 B + C 固化）

文件：`.tdca-protocol/nca-generator/nca_generator.py`（重写编号逻辑，其余结构保留）

### 选项 B：落盘前扫盘 + 空闲位顺延（并发安全）
- 移除 `_seq_file()`；新增 `_reserve_free_nca_slot(today)`：
  1. 扫描 `.tdca-nca` 目录当天已有编号集合；
  2. 定位**首个未占用整数**（首空闲语义，满足需求④「中间断号后首个空闲位」）；
  3. 用 `os.open(path, O_CREAT | O_EXCL | O_WRONLY)` **原子预约**占位文件；
  4. 若并发下该位被抢（`FileExistsError`）→ 顺延下一空闲位，循环直至成功。
- 因先预约后写内容，**绝不覆盖已有文件**；写入失败尽力释放空占位（避免孤儿）。
- 计数器文件 `.seq-{today}` 仍更新但**仅作提示，编号权威改为目录扫描**。

### 选项 C：禁止手动预分配编号
- `generate_nca` 新增 `explicit_seq=None` 参数；**任何非 None 值 → `ValueError("禁止手动预分配编号…")`**。编号仅由 `generate_nca` 统一生成，人工仅能通过调用该 API 触发。
- 新增常量 `NCA_NUMBERING_DISCIPLINE` 固化纪律（模块 docstring + 常量）。
- 生成物新增 `Generated-By: nca_generator.generate_nca` 溯源标记。
- 新增 `verify_numbering_discipline(nca_dir, require_marker=True)` lint：检出重复 id / 文件名格式错 / 文件内 NCA-ID 与文件名不符 / 缺 `Generated-By` 标记的「疑似手动预分配」文件（legacy 文件祖父条款：仅报告不删）。

## 三、测试（7 用例，全绿）

文件：`nca-generator/test_nca_numbering.py`（`python test_nca_numbering.py`，unittest，7 passed）

| # | 用例 | 断言 | 结果 |
| - | - | - | - |
| T1 | 占用顺延 + 不覆盖 | 手动占 001 → 顺延 002；001 未被覆盖 | ✅ |
| T1b | 高位手动占用不覆盖（155 事故复现） | 手动占 155 → 返回 156（max+1 顺延），155 未覆盖 | ✅ |
| T2 | 编号选取（中间断号，max+1） | 占 001+003 → 取 004（保留缺口） | ✅ |
| T3 | 链连续性 | 连生成 50 条 → 编号恰为 {1..50}，无重叠无缺口 | ✅ |
| T4 | 手动分配拒绝 | `explicit_seq=5` → `ValueError`，无文件产生 | ✅ |
| T5 | 并发模拟 | 25 线程同生成 → 25 个编号全唯一、文件全存在、占满 1..25 | ✅ |
| T6 | 纪律校验 lint | API 生成过审；手工无标记文件被检出 | ✅ |

## 四、回归

- 全仓库扫描 `explicit_seq`：仅补丁模块与测试文件引用，**无任何现有调用方传该参数** → 向后兼容无破坏（调用方均以关键字传参，签名新增尾参默认 None）。
- `generate_nca` 其余签名/返回 `(nid, npath, nca_dict)` 不变；`list_ncas` / `verify_numbering_discipline` 新增。

## 五、纪律固化与见证

- 纪律：`NCA_NUMBERING_DISCIPLINE` = "编号仅由 generate_nca 统一生成；禁止手动预分配编号。人工获取 NCA 应通过调用 generate_nca（API）触发，不得手工指定编号。"
- 本补丁自身亦经 API 发射见证 NCA（非手工预分配，落点由补丁后 generate_nca 自动选取）：
  - **见证 NCA：`TDCA-REASONIX-20260827-159`**（Operation-Type=`CodePatch`，含 `Generated-By` 标记）
  - 选号过程：真实目录已占 001–158 → 扫盘取 max+1 = **159**（保留缺口，不回填），未覆盖 158。
- 凭证零落盘 / NSFL 未触碰：本任务为纯代码补丁，无外部 API / 凭证 / 算力调用。
- **产物不推送**：`nca_generator.py` 补丁 + `test_nca_numbering.py` + 本报告 + 见证 NCA-159 均落本地，**待签批走 PR** 推送 upstream（遵循归档纪律，本地为权威副本）。

## 六、诚实标注（mixed 口径）

1. **编号口径裁定（GSEQ-0551）**：需求④「中间断号后首个空闲位」原按首空闲（填空）实现；经裁定改为 **max+1 保留缺口**——编号=事实存证时间序，缺口=历史事故/并发痕迹，不可回填（不可篡改精神）。已落地：`_reserve_free_nca_slot` candidate 初值改 `max(existing)+1`（单点改动），测试同步改为 max+1 语义（T2→004、T1b→156）。首空闲方案不再采用。
2. **并发安全边界**：`O_EXCL` 在同一文件系统上跨进程原子；测试以线程模拟近同时触发，25/25 唯一。若跨不同挂载点/网络盘，需额外分布式锁（当前桌面单机场景足够）。
3. 旧计数器文件 `.seq-{today}` 保留仅作兼容提示，编号权威已移至目录扫描。
