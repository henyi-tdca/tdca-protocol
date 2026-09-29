# tdca-klavis-silent-mount · TDCA × klavis 静默挂载适配器

> **仅模拟态试点 · 未实连上游**（ID92 模拟态标注）
> 本包为静默挂载试点施工产物，依据 `mounts/klavis/`（NCA-MOUNT-20260929-005）登记在案后本地落盘。
> **不宣称已封装可用**——对齐 CATEGORY.md「登记态」语义：只读协议层引用声明 + 存证。

## 挂载登记（已在，先读后建）

| 项 | 值 |
|---|---|
| 目标 | `Klavis-AI/klavis` |
| License（实核） | Apache-2.0 |
| 接口面 | AI 集成平台（MCP 托管面）（服务/API 面） |
| 分类 | `share-enabled`（默认分润类） |
| 分润 | 15% 分润模拟态记账（NCA 确权，非法币承诺，无现金流） |
| 挂载存证 | NCA-MOUNT-20260929-005 |
| 告知函存证 | NCA-ECOACT-20260929-NTC-024 |
| 状态 | registered_only（登记态）· notice_sent（告知函在架，2026-09-29） |

## 六模块结构（仿 tdca-adapters/acps）

| 模块 | 功能 | TDCA 映射 |
|---|---|---|
| `adapter.py` | `full_pipeline()`：配置权坐标映射 → NSFL 预检 → NCA 存证 → MOU 锚定 → 正和放行 | 静默挂载主流程 |
| `nca.py` | NCA 六要素生成（目标/约束/先验/边界/分配/审计）+ 链式水印 | ID56/68 |
| `nsfl.py` | 负空间清单检查 + 熔断（BLOCK/PASS） | ID85/86 |
| `mou.py` | MOU 税收锚定记账（15% 模拟态，无真实现金流） | ID79 |
| `__init__.py` | 导出便捷 API | — |
| `tests/test_adapter.py` | 管道冒烟（NCA 字段齐 / NSFL 边界 / 水印 / 零网络发送） | — |

## 纪律（全强制）

- **静默挂载 = 对方零感知**：`NETWORK_SEND = False`；不真实调用 klavis API、不写上游、不推送、不评论、不发送。
- **不宣称已封装可用**：仅协议层只读引用声明 + 存证；封装评估另批。
- **模拟态**：请求载荷本地构造（`simulate_upstream_payload()`），仅落日志，绝不传输；MOU 15% 分润为 NCA 记账，无真实现金流。
- **外部动作归 Kimi/创始人**：本包任何对外发布/公示动作不在此执行。

## 使用

```python
from tdca_klavis_silent_mount import TdcaKlavisSilentMount

adapter = TdcaKlavisSilentMount()
result = adapter.full_pipeline(
    task="记忆检索增强调用",
    capability_tags=["memory", "agent-runtime"],
)
# result.silent_mount_ok / result.nca / result.mou / result.upstream_notified(=False)
```
