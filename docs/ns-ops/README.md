# TDCA NS-OPS 负空间管理操作空间（M1 原型）

> FC: TDCA-FC-NS-OPS-001 | 状态: M1 原型 | 日期: 2026-08-09
> 制度锚定: TDCA-WORKING-SPEC-001 V1.0 | 决策记录: DCD-NS-OPS-001（FROZEN）
> 完整说明见 [会话框规范-S0-20260809.md](会话框规范-S0-20260809.md) 与 [API文档.md](API文档.md)

## 是什么

负空间管理操作空间（Negative Space Operations, NS-OPS）是 TDCA 全周期管理系统 Phase 0 前置的
负空间治理子空间——**人类操作台（慢系统人机界面）**。M1 原型交付三大面板：

| 面板 | 功能 | 制度锚定 |
|------|------|---------|
| 三层负空间视图 | 主体/场景/制度 + 四重底线 + 安全域 | F1 / NS-009 |
| 约束管理 CRUD | 创建/更新/删除，人类签名门 | F1 / BV-3 |
| 调整权操作面板 | NS-011 状态机七步推进（快慢分离） | F2 / BV-3/4/5/6 |
| 声明-行为校验 | 越界实时判定（BLOCK 熔断） | F3 / BV-1 |

## 目录结构

```
tdca-ns-ops/
├── 会话框规范-S0-20260809.md   # 会话框规范（六要素/制度基线/完整性 6/6）
├── API文档.md                  # 完整 API 说明
├── backend/                    # FastAPI 后端（Python 3.12）
│   ├── app/
│   │   ├── main.py             # 入口（uvicorn）
│   │   ├── models.py           # Pydantic 数据模型（FNSCM/NSI 合并）
│   │   ├── store.py            # JSON 存储 + NCA 引擎（MEMO-006 附录 C）
│   │   ├── human_gate.py       # BV-3 人类写权限门
│   │   ├── sandbox.py          # BV-4 三层沙盒引擎
│   │   ├── adjustment_flow.py  # NS-011 调整权状态机
│   │   ├── seed.py             # 种子数据（三层 6 条）
│   │   └── routes/             # constraints / views / adjustments
│   └── tests/test_api.py       # pytest 14 用例
└── frontend/                   # React 19 + TS + Vite（对齐 edu-simulator 模式）
    ├── src/pages/              # 三层面板 4 页
    ├── src/api/                # 客户端 + 类型契约（接口熵=0）
    └── src/test/               # vitest 3 用例
```

## 快速运行

### 后端（端口 8123）

```bash
cd backend
pip install -r requirements.txt
python -c "from app.seed import seed_if_empty; seed_if_empty()"   # 可选：预置种子
uvicorn app.main:app --host 127.0.0.1 --port 8123
```

### 前端（端口 5173，代理 /api → 8123）

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`。人类签名默认 `HUMAN-FOUNDER-001`（可在顶部切换）。

### 测试

```bash
cd backend  && python -m pytest tests/ -v      # 14 passed
cd frontend && npm run test                     # 3 passed
cd frontend && npm run build                    # tsc + vite build ✅
```

## 制度要点（BV-1~7 落地）

- **BV-3 硬隔离**：所有写操作（约束 CRUD / 调整推进）必须携带在册人类签名；AI 签名 `403`。
- **BV-4 先沙盒**：调整进入确定态前强制三层沙盒（技术/经济/社会）+ 层级吞噬防护。
- **BV-5 全存证**：每次写操作自动生成 NCA（`.tdca-nca/`，11 字段）。
- **BV-6 快慢分离**：面板=慢系统（人类操作）→ API=快系统（刚性态执行）分离建模。
- **BV-7 空窗处置**：确定态带生效时间与回滚版本（红队返修项）。

## 数据存储

- 约束/调整台账: `backend/data/*.json`（原子写入，临时文件+rename）
- NCA 存证: `<workspace>/.tdca-nca/NCA-TDCA-REASONIX-{date}-{seq}.yaml`
- 清理演示数据: 删除 `backend/data/` 后重启（种子幂等重建）
