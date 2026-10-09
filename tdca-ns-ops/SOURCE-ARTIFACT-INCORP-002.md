# 入仓来源说明 · tdca-ns-ops（ARTIFACT-INCORP-002）

> 本文件为入仓 provenance 说明（TDCA-HANDOFF-EXEC-ARTIFACT-INCORP-002），非制度件。

## 一、来源账

- 来源包：`TDCA-ARTIFACT-PAYLOAD-sbx-ns-ops-20261010.tar.gz`
- 包 sha256：`82911e11aee27bb22c982ab7f662a846dc5449c586a34d29c8703566230063d5`（取件时核验一致）
- 权威逐件账：`TDCA-ARTIFACT-PAYLOAD-sbx-ns-ops-20261010-MANIFEST.sha256`，1,031 行
- 本目录入仓件数：87 件中本包占 39 件，逐件已对清单复核（哈希＋字节）一致

## 二、入仓范围（甲：实现＋测试）

| 路径 | 内容 |
|---|---|
| `backend/app/` | 实现（含 integration 层，FastAPI 应用） |
| `backend/tests/` | 测试（4 件） |
| `backend/pytest.ini` · `backend/requirements.txt` | 测试与运行配置 |

## 三、未入仓部分（乙候选，待创始人点定）

- `backend/data/`（adjustments.json、constraints.json 运行数据）
- `data_test_m2/` · `data_test_m3/`（测试数据）
- `nca_test_m2/`（441 件）· `nca_test_m3/`（79 件）（NCA 记录）
- `frontend/`（前端）· `docs/`（F5 判定标准文档）
- 顶层文档件：与 `docs/ns-ops/` 在册件逐件比对，内容一致（仅换行符差异），不重复入仓

## 四、敏感面（入仓前复扫）

- 无凭据类命中（nca_test_* 中 "Token: Scope:" 为 NCA 结构字段，非凭据；该目录属乙未入仓）
- IP 仅 127.0.0.1；无人名、无本机路径

## 五、外部依赖与基线

- **外部依赖**：`tdca-flow-orchestrator`（兄弟仓，未随包交付）。`backend/app/integration/flow_adapter.py` 以 `Path(__file__).resolve().parents[4] / "tdca-flow-orchestrator" / "src"` 硬路径加载且在 import 期强制注册，缺该仓时**整个测试套件在 conftest 导入阶段被阻断**，应用路由 integration 视图亦不可用。
- **基线测试**：未跑通（如上，外部依赖所致），按"搬不造"原样入仓。
- 联盟链／数字人民币平台等链上部署属外部条件，本轮挂起。
