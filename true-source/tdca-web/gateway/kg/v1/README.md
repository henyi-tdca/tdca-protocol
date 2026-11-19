# TDCA 知识图谱 · 对外结构包（V1.0）

> 本包为 TDCA 官方知识图谱之 ⭐ 对外结构面 ⭐ ：层／类／标题／关系类型。
> ⭐ 不含 ⭐ 内部编号、册内路径、件哈希、原文摘句。缺口账（悬空清单）⛔ 不对外。

## 一、包内有什么

| 文件 | 内容 |
|---|---|
| `manifest.yaml` | 版本、计数、文件哈希、排除项 |
| `nodes.yaml` | 节点：`id` `layer` `layer_name` `type` `type_name` `label` |
| `edges.yaml` | 关系：`id` `type` `source` `target`（指向 `nodes.yaml` 之 `id`） |

计数：节点 1007 ／关系 2587；层：L0 30、L1 288、G 616、L2 73。

## 一之二、怎么验这份包（⛔ 术语，一句话可复现）

- **各文件哈希**：`manifest.yaml` 之 `files.<名>.sha256_16` 与 `bytes` 对 `nodes.yaml`／`edges.yaml` 复算即得。
- **包自身声明哈希**：`manifest.yaml` 之 `self_sha256_16` 采固定占位口径 —— 把该字段值整体替换为 `DEADBEEFDEADBEEF`，再对整份 `manifest.yaml` 取 `sha256` 前 16 位。口径原文写在同文件 `self_sha256_16_method` 字段内，⛔ 依赖任何未成文约定。

## 二、三条调用示例

```python
# 1) 取某层节点
import yaml
d = yaml.safe_load(open("nodes.yaml", encoding="utf-8"))
con = [n for n in d["nodes"] if n["layer"] == "L0"]

# 2) 取某节点的出边与邻接（按 label 看关系）
e = yaml.safe_load(open("edges.yaml", encoding="utf-8"))["edges"]
out = [x for x in e if x["source"] == con[0]["id"]]
labels = dict((n["id"], n["label"]) for n in d["nodes"])
chain = [(labels[x["target"]], x["type"]) for x in out]

# 3) 按关系类型统计（如「实现」类关系）
from collections import Counter
print(Counter(x["type"] for x in e))
```

## 三、边界

- 本包 ⭐ 只读 ⭐ 、可自由引用；⛔ 作对外承诺或评级依据。
- 结构 ⭐ 宁缺毋假 ⭐ ：未确证者不入包。
- 与内部包 ⭐ 同源 ⭐ （同一生成器派生），版本以 `manifest.yaml` 为准。
