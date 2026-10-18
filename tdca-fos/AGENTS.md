# AGENTS.md — TDCA-FOS REPO-003 认知基础设施

TDCA-FOS 七库系统 REPO-003（知识库与知识图谱库）工程实现。制度锚定：TDCA-KG-001 / TDCA-TypeSystem-Confirmation-001。FC 链：TDCA-FC-20260804-006（M1/M2 已完成，M3 进行中）。

## Project

- 位置：`tdca-fos/`（workspace 内），Python 3.12 + SQLAlchemy 2 + neo4j 6 + grpc 1.83
- 交付形态：Python 服务 + YAML 配置 + Protobuf 接口 + Docker Compose 部署包
- 入口：`tdca_gateway/server/grpc_server.py`（gRPC 服务，`serve()` 启动，端口 50051）
- 依赖：`requirements.txt`；测试：`tests/`（pytest）

## Commands

- 测试：`cd tdca-fos && python -m pytest tests -q`（当前 130 passed）
- 接口熵检查（ID82 提交前强制）：`python tdca-fos/checks/interface_entropy.py tdca-fos`（须 0 违例）
- proto 编译：`python -m grpc_tools.protoc -I tdca_gateway/proto --python_out=tdca_gateway/proto --grpc_python_out=tdca_gateway/proto tdca_gateway/proto/dev_governance.proto`
- 运行 gRPC：`serve(graph, kb, tp, nca, nsfl, port=50051)`
- Docker 全栈：`docker compose -f deploy/docker-compose.yml up -d`（需 docker）

## Architecture

- `tdca_graph/` — 五维图核心：`core/ontology.py`（12 节点/9 边枚举+ID56 封印）、`schema/init_schema.py`（12 约束+10 索引）、`query/engine.py`（§3.3/§5.3 查询+ID82 校验）、`version/ota_control.py`（快/慢系统+§9.3 四锚点硬编码）
- `tdca_kb/` — 知识库：`models/knowledge_unit.py`（领域模型）、`db/models.py`（ORM，ARRAY 用 `.with_variant(JSON,"sqlite")` 兼容测试）、`db/store.py`（CRUD+场景查询，PG ANY / SQLite Python 过滤方言分支）
- `tdca_tp/engine/inference_engine.py` — TP 推理机：五规则（ID38/ID82/ID54/ID79/SPEC-002），`execute()` 快慢路径，CRITICAL→NSFL
- `tdca_nsfl/fuse_engine.py` — NSFL 熔断器：LEGAL 绝对熔断（alt_path 强制 None+不可重置+自动上报慢系统）
- `tdca_nca/generator.py` — NCA 生成器：UUID+时间戳+内容哈希封印、追溯链、verify_chain/verify_seal
- `tdca_irp/gateway.py` — IRP 跨库网关（M3 中完整化）
- `tdca_gateway/` — gRPC 网关：`proto/dev_governance.proto`（6 RPC）、`server/grpc_server.py`、`slow_system.py`（慢系统工单）
- `checks/` — 提交前三件套：接口熵检查器、NCA 占位、NSFL 声明

## Conventions

- 所有 `.py`/`.proto`/`.yaml` 文件头部必须含制度锚定注释（`制度锚定:` + 文档编号 + 版本 + 状态 + FC-ID）+ `SPDX-License-Identifier: TDCA-Internal`
- 所有查询/操作/推理必须生成 NCA（ID91）；接口熵=0（ID82）；宪法级变更需人类签名（ID71）
- 测试不连真实 Neo4j/PG：图用 `tests/conftest.py` 的 `InMemoryDriver`（run_single/run_all 语义），KB 用 SQLite 内存库
- 接口熵检查器跳过 `tests/` 目录与 `*_pb2*.py` 自动生成产物
- 依赖注入优先：构造器注入 graph/kb/nca/nsfl 等，便于 Fake 测试
- NSFL：不触碰法律负空间、不修改 §9.3 不可升级锚点、不伪造 MOU 数据
- 开发流程遵循 `TDCA-WORKING-SPEC-001_Reasonix开发工作规范.md`：六要素先行、NCA 审计、负空间熔断、审查闭环、MOU 记录（十项执行清单每次任务勾选）

## Notes

- 工作规范：`TDCA-WORKING-SPEC-001_Reasonix开发工作规范.md`（总纲/会话管理/代码规范/审查/NCA/3L-KB 知识分层/缺口自查/M4 执行清单）
- 硬依赖归档路径见记忆 `project/tdca-repo003-harddeps.md`（KG-001/TypeSystem/session-index 只移不删）
- M4 待办：OTA 接真实图数据库、联动管道生产化、gRPC 接真实后端、MOU 真实税收数据接入
- 交付物落 workspace/tdca-fos/（沙箱限制），NCA 存证在 workspace/.tdca-nca/，打包副本在 workspace/tdca-repo003-delivery/，桌面归档待手动
