# TDCA 知识图谱编译器（FC-005）

> 落位: tools/kg-compiler/（门户「KG 编译器」解锁入口）｜ 许可: Apache-2.0
> **版本：** 1.0.0  
> **制度锚定：** FC-005-SPEC, ID68, ID21, ID91, ID90  
> **Function-Call-ID：** TDCA-FC-20260803-005

## 一、定位

将历史 NCA、外部数据源、领域知识转化为可被 FC-004A 消费的规范化先验分布输入。

## 二、安装

```bash
pip install pyyaml fastapi uvicorn pytest pytest-cov
```

## 三、核心模块

| 模块 | 功能需求 | 覆盖率 |
|------|---------|--------|
| `extractors/nca_extractor.py` | FR-001 历史NCA知识抽取 | 93% |
| `extractors/external_extractor.py` | FR-002 外部数据源接入 | 97% |
| `graph/domain_manager.py` | FR-003 领域知识库管理 | 91% |
| `prior_compilers/prior_compiler.py` | FR-005 先验分布编译 + NecessityChecker(ID90) | 99% |
| `validators/backtest_validator.py` | FR-006 回测验证 | 98% |
| `tdca_kg_compiler.py` | 主类（统一入口） | — |
| `api.py` | FastAPI 服务 | — |

## 四、使用

```python
from tdca_kg_compiler import TDCAKnowledgeGraphCompiler

compiler = TDCAKnowledgeGraphCompiler()

# FR-001: NCA 抽取
result = compiler.build_from_nca({'scenario': '政府采购'})

# FR-005: 先验分布编译
prior = compiler.compile_prior(
    graph_ref='TDCA-KG-001',
    node_selection=[],
    distribution_type='BAYESIAN',
    nodes=result.get('nodes', []),
)

# FR-006: 回测验证
report = compiler.backtest_prior(prior['prior_output'], test_dataset)

# ID90: 最小化合检查
necessity = compiler.necessity_check(
    compound_utility=100.0,
    component_utilities=[20.0, 30.0],
)
```

## 五、API 服务

```bash
# 启动
python api.py  # 或 uvicorn api:app

# 接口（需 Authorization: TDCA-CRT-xxx）
POST /api/v1/kg/build-from-nca   # FR-001
POST /api/v1/kg/compile-prior    # FR-005
GET  /health
```

## 六、与 FC-004A 集成

```
FC-005 输出 prior_distribution:
  type: "COMPILED"
  compiled_ref: "TDCA-PD-{uuid}"
  fallback_type: "EMPIRICAL"
  → 嵌入 FC-004A FunctionSpecRequest.prior_distribution
```

## 七、NSFL 约束

- 知识节点创建必须生成 NCA 存证（FC-001）
- 外部数据接入必须负空间检查（FC-004B）
- 先验编译失败回退均匀分布
- 敏感领域知识需额外审批
- 回测失败即破例信号（ID38）

## 八、测试

```bash
python -m pytest tests/ --cov --cov-report=term
# 当前: 84 用例全部通过（实测 2026-09-06）, 各模块覆盖率 ≥91%
```
