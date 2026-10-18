# TDCA-FOS REPO-003 生产部署手册

> **FC-ID：** TDCA-FC-20260804-006-M4
> **版本：** TDCA-FC-20260804-006-M4
> **状态：** 生产就绪（Production Ready）
> **制度锚定：** TDCA-KG-001 §6.1 / TDCA-ENV-001 / TypeSystem-Confirmation-001 §2.1
> **SPDX-License-Identifier：** TDCA-Internal

---

## 一、快速启动

```bash
# 1. 克隆仓库
git clone <repo> && cd tdca-fos

# 2. 启动全栈（Neo4j + PostgreSQL + Milvus + Redis + gRPC + Pipeline）
docker-compose -f deploy/docker-compose.yml up -d

# 3. 验证健康
curl http://localhost:50051/health
```

### 服务矩阵

| 服务 | 端口 | 说明 |
|------|------|------|
| tdca-kg（Neo4j 5） | 7474 / 7687 | 五维图数据库 |
| tdca-kb（PostgreSQL 15） | 5432 | 知识库结构化存储 |
| tdca-vector（Milvus 2.3） | 19530 | 语义相似度向量库 |
| tdca-redis（Redis 7） | 6379 | 热缓存 |
| tdca-gateway（gRPC） | 50051 | 六 RPC 查询网关 |
| tdca-pipeline | — | 七库联动管道 |

### 初始化

```bash
# 初始化五维图 Schema（节点/边/索引）
python -m tdca_graph.schema.init_schema

# 初始化 KB 表结构（PostgreSQL）
python -m tdca_kb.db.init_db

# 加载本体论
python -m tdca_graph.core.ontology
```

---

## 二、运维 Playbook

### 场景 1：NCA 上链延迟过高

```bash
# 检查批量队列
docker logs tdca-pipeline | grep "batch_submit"

# 手动触发刷新（达到批量阈值自动上链；延迟高时可手动）
curl -X POST http://localhost:50051/admin/flush-nca-batch
```

### 场景 2：慢系统工单堆积

```bash
# 查看待办
curl http://localhost:50051/admin/slow-system/pending

# 人类签名（宪法级变更 / CRITICAL 熔断 / 负空间事件）
curl -X POST http://localhost:50051/admin/slow-system/sign \
  -d '{"ticket_id": "SLOW-xxx", "signature": "HUMAN-SIG"}'

# 签批后反馈到快系统（approve_slow_update 创建并激活版本）
```

### 场景 3：版本回滚

```bash
# 回滚到指定版本（必须人类签名；NSFL：回滚不可逆，不自动前滚）
curl -X POST http://localhost:50051/admin/ota/rollback \
  -d '{"target_version": "v1.0.0", "human_signature": "HUMAN-SIG"}'
```

### 场景 4：监控指标

```bash
# Prometheus 指标端点（NCA 速率 / 熔断器 / 跨库延迟 / MOU 健康度）
curl http://localhost:50051/metrics
```

---

## 三、灾难恢复

| 场景 | 恢复策略 |
|------|----------|
| **图数据库损坏** | 从最近 Merkle Root 验证的版本快照恢复（OTA 版本谱系） |
| **NCA 链断裂** | 暂停跨库调用，人工审计后重建链（verify_chain 定位断裂点） |
| **LEGAL 负空间误触发** | 检查 NSFL 规则配置，联系法律团队评估后修正 Δ 修正案 |
| **PostgreSQL 丢失** | 从备份恢复 knowledge_units 表 + 重建向量索引 |
| **版本回滚错误** | 回滚后旧数据不可自动前滚，必须重新提案（NSFL 约束） |

### 备份策略

```bash
# 每日备份 Neo4j
docker exec tdca-neo4j neo4j-admin dump --to=/backups/neo4j-$(date +%F).dump

# 每日备份 PostgreSQL
docker exec tdca-postgres pg_dump -U tdca tdca_kb > /backups/kb-$(date +%F).sql

# NCA 存证链（不可篡改，定期上链）
# 由 tdca_adapters/chain_adapter.py 批量上链（batch_size=100）
```

---

## 四、制度运维约束（NSFL）

1. **性能优化不可绕过制度约束**：缓存/批处理/异步不得跳过 NCA 生成、NSFL 检查或 MOU 锚定。
2. **监控数据不可伪造**：Prometheus 指标必须基于真实系统状态，禁止模拟指标数据。
3. **生产回滚不可逆**：版本回滚一旦执行，旧版本数据不可自动"前滚"，必须重新提案。
4. **宪法级变更必须慢系统签名**（ID71）；**不可升级锚点不可修改**（TypeSystem §9.3）。
