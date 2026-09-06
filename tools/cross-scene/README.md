# TDCA Cross-Scene Sandbox · 跨场景沙盒

> SPDX-License-Identifier: Apache-2.0
> 落位: tools/cross-scene/（门户「场景沙盒」解锁入口）｜ 许可: Apache-2.0
> 制度锚: TASKBOOK-5CC-P3-SBX（T-P3-001 CrossSceneSandbox）｜ FC-5CC-W3 交付（TDCA-FC-5CC-W3W4-001）

## 一、定位

跨场景沙盒（CrossSceneSandbox）——让智能体在**多个场景同时受约束**下运行验证的沙盒引擎：场景冲突/映射成本显式建模（externality_decay），激活系数跨场景合成，数据隔离（脱敏共享视图），算法哈希上链。

## 二、模块（cross_scene/）

| 模块 | 职责 |
|---|---|
| `sandbox.py` | CrossSceneSandbox：≥3 场景强制 + activation_coefficient_cross_scene（(ΣMOU/ΣPCR)×(1−decay)+benefit）+ externality_decay（冲突/映射成本）+ 数据隔离（脱敏共享视图）+ 算法哈希上链 |
| `zero_data_entry.py` | 零数据冷启动入口（场景初值/默认先验） |
| `__init__.py` | 包入口 |

> P3 HTTP API 网关层（inject/promote 端点，联 D-2 nsfl_union 负空间联合引擎）未随本包发布——随 D-2 联合引擎发布时配套。

## 三、测试

```bash
python -m pytest tests/
# 当前: 测试用例全部通过（实测 2026-09-06，沙盒引擎核心直测）
```

## 四、使用

```python
from cross_scene.sandbox import CrossSceneSandbox  # sys.path 指向本目录

sbx = CrossSceneSandbox()
result = sbx.run(scenes=[...], ...)  # 多场景强制 + 激活系数跨场景合成
```

## 五、门户卡口径

「场景沙盒」= 跨场景沙盒引擎（CrossSceneSandbox）：≥3 场景强制 + 跨场景激活系数（衰减/收益建模）+ 数据隔离 + 哈希上链，Apache-2.0。
