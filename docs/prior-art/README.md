# docs/prior-art/ · 防御性公开披露索引

> **声明**：本目录文件为**防御性公开**（defensive publication）资料，旨在使关键机制成为**构成可供审查比对的现有技术资料**。采信与否取决于受理机关；本目录不构成法律意见，不声称任何普遍效力。

## 披露清单（首批 5 件）

| 编号 | 机制 | 披露日期 | 公开仓 commit | 主要代码路径 |
|---|---|---|---|---|
| [PA-001](PA-001-compliance-first-admission.md) | 合规前置准入 | 2026-09-16 | `9c88f98` | `tools/enforce_entry.py` |
| [PA-002](PA-002-nsfl-fuse-compensation.md) | 负空间熔断与补偿协同 | 2026-09-16 | `9c88f98` | `core-go/pkg/nsfl/nsfl.go` |
| [PA-003](PA-003-assertion-anchor-tristate.md) | 断言锚点三态状态机 | 2026-09-16 | `9c88f98` | `core-go/pkg/nca/anchor.go` |
| [PA-004](PA-004-latency-cost-blocking.md) | 延迟代价与超时强制阻断 | 2026-09-16 | `9c88f98` | `core-go/pkg/nsfl/latency.go` |
| [PA-005](PA-005-nca-lifecycle.md) | 存证记录生命周期与追溯阻断线 | 2026-09-16 | `9c88f98` | `core-go/pkg/nca/nca.go` |

## 披露标准（可实现自查 7 项）

每份披露须含：① 技术目的 ② 输入/输出 ③ 触发条件 ④ 执行流程 ⑤ 至少一个实施例（引用公开仓代码路径）⑥ 状态机或流程图 ⑦ 文件头载 Disclosure Date 与公开仓 commit。

## 维护与周期复扫

- **半年复扫**：每六个月对本目录做一次复扫——核对披露与公开仓代码的一致性、评估新增机制的披露必要性，并出巡查记录；
- **清单可扩**：后续已公开机制可按同一标准增补披露（逐件独立 PR）；
- 披露文件只追加更正、不改写历史版本；变更以新披露件或修订件形式进入本目录。
