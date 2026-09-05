# TDCA 连接器 v2（cop-connector）

TF-IDF 加权 + 多维语义匹配 + 负空间反向信号的场景 → COP 匹配器。核心算法锚定 S1：`U(c|s) = U₀(c) · SC(s) · A(c,s)`。

> 与门户已链的匹配/距离组件（`tools/tdca_fuzzy_distance.py` / `tools/tdca_cognitive_distance.py`）是**不同件**：后者为适配器实例组件，本目录为连接器 v2 本体。

## 文件

| 文件 | 说明 |
|---|---|
| [cop_connector.py](cop_connector.py) | 连接器 v2 本体：四维特征分离（soul/primitives/decision/negative_space）+ TF-IDF 加权 + 多维加权余弦 + 负空间反向降权 |
| [adapter_matcher.py](adapter_matcher.py) | 适配器 L4 自动化：合规标准条款 → TDCA 原理 ID Top-K 匹配辅助 |

许可：Apache-2.0（SPDX 头在源码内）。

## 实测实例区（2026-09-05 实跑捕获，real 不注水）

- **语法/导入**：两件 `py_compile` 通过（含 Apache-2.0 SPDX 头插入后复验通过）；
- **adapter_matcher 实测**：内置 6 条合规条款演示全量跑通——例：「数据最小化：仅提供任务必需数据，多租户记忆隔离」→ Top-1 **ID90 最小化合原则**（得分 0.088，命中 小化/最小/最小化）；
- **cop_connector 实测**：COP 索引实载 **267 个**思维协议（cop-library 语料），两场景实跑——
  - 沙盒场景（入盒实验：准入校验/负空间熔断/配额/人类签批出盒）Top-1 = **生态准入与可信协作基协议**（A=0.044）；
  - 教育场景（课程协作：分组/角色/调度/公平评价）Top-1 = 最后通牒博弈（A=0.024），Top-2 = 可审计自主决策协议（A=0.019）；
- **tdca-bridge MCP 联动**：本批**未实测**（bridge 侧无存档测试证据）——如实标注，待补。

## 用法

```bash
python adapter_matcher.py            # 内置 6 条款演示
python cop_connector.py              # 需将 COP_DIR 指向本地 cop-library 语料目录
```
