# 入仓来源说明 · tdca-sbx-ops（ARTIFACT-INCORP-002）

> 本文件为入仓 provenance 说明（TDCA-HANDOFF-EXEC-ARTIFACT-INCORP-002），非制度件。

## 一、来源账

- 来源包：`TDCA-ARTIFACT-PAYLOAD-sbx-ns-ops-20261010.tar.gz`
- 包 sha256：`82911e11aee27bb22c982ab7f662a846dc5449c586a34d29c8703566230063d5`（取件时核验一致）
- 权威逐件账：`TDCA-ARTIFACT-PAYLOAD-sbx-ns-ops-20261010-MANIFEST.sha256`，1,031 行
- 本目录入仓件数：87 件中本包占 48 件，逐件已对清单复核（哈希＋字节）一致

## 二、入仓范围（甲：实现＋测试）

| 路径 | 内容 |
|---|---|
| `backend/app/` | 实现（19 件，FastAPI 应用） |
| `backend/tests/` | 单元／接口测试（18 件） |
| `backend/scripts/` | 本地 e2e 验证脚本（9 件，仅打 127.0.0.1） |
| `backend/pytest.ini` · `backend/requirements.txt` | 测试与运行配置 |

## 三、未入仓部分（乙候选，待创始人点定）

- `backend/data/`（46 件 did_*.json 运行样例数据）
- `backend/nca/`（297 件 NCA 生成记录）
- `frontend/`（前端）
- 顶层文档件：与 `docs/sbx-ops/` 在册件逐件比对，内容一致（仅换行符差异），不重复入仓

## 四、敏感面（入仓前复扫）

- 凭据类命中 2 处，均非真凭据：
  - `backend/app/flow_adapter.py:61` —— `FLOW_CRT_TOKEN` 环境变量读取带硬编码占位默认值，**建议后续专项处理**（本件按"搬不造"原样入仓，保持与交付清单哈希一致）
  - `backend/app/nca_logger.py` —— `config_right_token` 仅为参数名
- IP 仅 127.0.0.1；无人名、无本机路径

## 五、外部依赖与基线

- **外部依赖**：`tdca-flow-orchestrator`（兄弟仓，未随包交付）。`flow_adapter.py`／`phase_adapter.py` 以 `Path(__file__).resolve().parents[4] / "tdca-flow-orchestrator" / "src"` 硬路径加载，缺该仓时 flow／phase 相关路由与 4 个测试件不可用。
- **基线测试**（交付件原样、本机直跑）：151 passed / 17 failed / 20 errors（含上述 4 件收集错误）。失败项未诊断，按"搬不造"原样入仓。
- 联盟链／数字人民币平台等链上部署属外部条件，本轮挂起。
