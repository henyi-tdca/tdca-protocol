# TDCA 核心思维协议库 (tdca_core)

TDCA 生态的**准入与运行基协议库**。用户规则：

> **凡是加入 TDCA 生态的主体，必须加载 TDCA 思维协议。**

## 强制基协议

| COP-ID | 名称 | 强制 | 角色 |
|---|---|---|---|
| `TDCA-CORE-20260815-01` | 生态准入与可信协作基协议 | **是** | 生态宪法/准入门：NCA 确权 + NSFL 护栏 + MOU 正和底线 + 可审计决策 + 可信协作 + 准入门 |
| `TDCA-CORE-20260815-02` | 可审计自主决策协议 | 否 | COP 作为"自主决策源泉层"的方法本体（决策门→状态机→调度→确权→熔断→回滚） |
| `TDCA-CORE-20260815-03` | 正和协作涌现协议 | 否 | 搜索比配引擎的协作方法论本体（互补→缺口→增益→联盟→夏普利→DVP） |

## 编译

```bash
python compile_tdca_core.py
```

生成 `第NN核心-*.yaml` + 发射 NCA（每日序号 `TDCA-REASONIX-20260815-XXX`）。

## 加入生态 = 加载基协议（强制门）

`enforce_entry.py` 把"加入即加载"落地为可执行准入门：

```python
from enforce_entry import require_core_loaded, ecosystem_admit

# 主体已加载基协议 -> 准入
require_core_loaded(["TDCA-CORE-20260815-01", "SCEN-COP-20260814-01"])  # True

# 主体未加载基协议 -> 抛 AdmissionDenied
ecosystem_admit("外部Agent", loaded_ids=[])  # AdmissionDenied
```

运行演示：`python enforce_entry.py`

## 生产接线

任何生态入口都应在协作前调用 `require_core_loaded(agent_loaded_core_ids)`：
- `compose_general`（组合解析前校验双方均已加载基协议）
- 搜索比配引擎 `providers`（加载候选前校验连接器侧已加载基协议）
- 连接器 / MCP 入口（主体接入即加载基协议）

## 与学科/文明库的关系

TDCA 核心库是**生态地基**；兵法 / 博弈论 / 机制设计 / 场景 / 诸子百家 / 辩证实践方法论 / 微观经济学 /
统计学 / 控制论 / 逻辑学 / 数学 等学科与文明源流在其上**化合**（组合第一性），形成开源可调用的思维协议库。

基协议本身也是化合的 operand——例如"辩证实践方法论 = 中国文化 ⊕ 辩证实践方法论"化合时，
父计与解释项都先加载 `TDCA-CORE-20260815-01` 作为可信底座。
