# TDCA Flow Orchestrator · 编排器（FC-012）

> SPDX-License-Identifier: Apache-2.0
> 落位: tools/flow-orchestrator/（门户「编排器」解锁入口）｜ 许可: Apache-2.0
> 制度锚: FC-012（Agent 全生命周期编排）｜ 关联: 分层市场区在线实读 / 沙盒实验室区

## 一、定位

Agent 全生命周期编排器——按 FC-012 设计（9-Phase 状态机）编排智能体从创建、运行、融合到归档的生命周期流程：场景编译、融合适配（Δw 阈值）、MOU 闭环、NCA 存证报告。

## 二、模块（src/）

| 模块 | 职责 |
|---|---|
| `flow_engine.py` | 编排主引擎（FC-012 9-Phase 状态机） |
| `phase_machine.py` | 阶段状态机 |
| `fuse_adapter.py` | 融合适配器（Δw 阈值抑制/释放信号） |
| `mou_closer.py` | MOU 闭环（税收锚定/进项出项） |
| `nca_reporter.py` | NCA 存证报告 |
| `models.py` / `api.py` | 数据模型 / API 入口 |
| `__init__.py` | 包入口 |

## 三、设计文档（design/）

- FC-012-PRES-001（预研框架）
- FC-012-DESIGN-002（9-Phase 状态机详细设计）
- FC-012-DESIGN-003（Agent 创建全生命周期编排规格草案）

## 四、测试

```bash
python -m pytest tests/
# 当前: 29 用例全部通过（实测 2026-09-06）
```

## 五、使用

```python
from flow_engine import FlowEngine  # src/ 导入或 sys.path 指向本目录
```

## 六、门户卡口径

「编排器」= FC-012 Agent 全生命周期编排器：9-Phase 状态机 + 融合适配 + MOU 闭环 + NCA 报告，Apache-2.0（含设计文档与测试）。
