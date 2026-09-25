# COP 计数清单（count manifest）· 2026-09-13 实扫

> 生成日期：2026-09-13 ｜ 实扫脚本：[`tools/cop_count_scan.py`](../../tools/cop_count_scan.py)（仓库根执行 `python tools/cop_count_scan.py` 可复算）
> 口径：仅统计 **git 跟踪件**（`git ls-files`），不含工作树未跟踪文件；`.yaml` 后缀计，`yml` 不在本口径。
> 原生 / 化合分类：`docs/cop-library/` 下 yaml 文件头部含 `COMPOSED-` 标识者计为**化合**，其余计为**原生**。

## 现状计数（本清单为唯一现状依据）

| 项 | 计数 |
|---|---|
| `docs/cop-library/**/*.yaml` **总数** | **530** |
| 　原生（无 COMPOSED- 标识） | 470 |
| 　化合（含 COMPOSED- 标识） | 60 |
| `protocols/**/*.yaml`（权威源层） | 518 |
| `docs/cop-library/chengyu/`（现行成语库） | 150（根目录 60 + `2026-08-28/` 90） |
| `docs/cognitive-compiler/chengyu/`（旧成语库，历史基库） | 62 文件（60 条 + manifest + 编译脚本） |
| 仓库跟踪件总数 | 1768 |

## 分家族（docs/cop-library/）

| 家族 | yaml 数 |
|---|---|
| chengyu | 150 |
| compositions | 39 |
| emissary | 1 |
| engineering-three | 41 |
| games | 4 |
| hundred_schools | 216 |
| marxism | 16 |
| mechanism_design | 1 |
| microeconomics | 12 |
| scenario | 7 |
| stratagems | 38 |
| tdca_core | 4 |
| 麦肯锡思维协议.yaml（根） | 1 |

## 历史口径（仅备查，不作为现状依据）

- 2026-08-25 编译清单快照：原生 336 + 化合 44（见 `docs/cognitive-compiler/思维协议编译清单_2026-08-25.md`）
- 2026-08-30 全量同步口径：515（原生 455 + 化合 60）
- 早期发布文案：353

> 各历史数字与本次实扫的差异属扫描时点与口径演进（新家族入库、chengyu 2026-08-28 批次 90 件补充）；**现状一律以本清单为准**。
