# TDCA-FC-SBX-OPS-001 沙盒实验操作空间

> 项目编号: TDCA-FC-SBX-OPS-001 | 状态: M1 核心引擎原型完成（F1+F3+F8）
> 制度锚定: FC-SBX-OPS-001 任务书（FROZEN，NCA-20260810-002）+ TDCA-WORKING-SPEC-001 V1.0
> 前置依赖: TDCA-FC-NS-OPS-001 负空间管理操作空间（M3 已验收冻结）

## 定位

沙盒实验操作空间（SBX-OPS）管理「可以做」的沙盒实验（创新孵化、正和验证、场景配置），
与 NS-OPS（「不可做」负空间约束）构成一体两翼。详见 `TDCA-FC-SBX-OPS-001-任务书.md`。

## 里程碑

| 里程碑 | 内容 | 状态 |
|--------|------|------|
| M0 | 立项签批（人类裁决 A，任务书 FROZEN） | ✅ 2026-08-10 |
| **M1** | **核心引擎原型（F1 CRUD + F3 激活系数 + F8 NCA 存证）** | ✅ 本会话 |
| M2 | 三位一体与正和验证（F2+F6+F5） | ⏳ 待新会话框 |
| M3 | 系统集成与联动（F7 NS-OPS/FlowEngine/PhaseMachine） | ⏳ 待 M2 |
| M4 | 验收交付（F1-F8 全通过） | ⏳ 待 M3 |

## 快速开始

```bash
# 后端（Python 3.12）
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000          # http://127.0.0.1:8000/docs

# 测试（46 项，隔离自动）
python -m pytest -q

# E2E 冒烟（须先启动服务）
python -X utf8 scripts/e2e_smoke.py

# 前端（Node 18+）
cd frontend
npm install
npm run dev                               # http://localhost:5173
```

## 目录结构

```
tdca-sbx-ops/
├── TDCA-FC-SBX-OPS-001-任务书.md      # FROZEN（M0 签批）
├── 会话框规范-S0-M1-20260810.md        # M1 会话框规范（六要素 + 制度基线 8/8 核验）
├── API文档.md                          # REST 契约（F1/F3/F8）
├── 交付报告-M1-20260810.md             # M1 交付记录
├── 交付确认书-M1-20260810.md            # M1 确认书（待三方签批）
├── backend/
│   ├── app/
│   │   ├── sandbox_core.py             # F1 生命周期状态机（Phase0→P0→P1→Exit/Closed）
│   │   ├── activation_engine.py        # F3 激活系数（SV-1 >1.2 硬编码）
│   │   ├── nca_logger.py               # F8 NCA 存证（11 字段链式哈希）
│   │   ├── multisig.py                 # SV-4/SV-6 三方多签门控
│   │   ├── models.py / store.py / main.py / seed.py
│   │   └── routes/                     # sandboxes / activation / nca
│   ├── tests/                          # 46 项测试（conftest 隔离）
│   └── scripts/e2e_smoke.py            # 真实 HTTP 冒烟（9/9）
└── frontend/                           # React/TS 沙盒管理面板
```

## 硬约束落地（SV-1~7）

| 约束 | 落地 |
|------|------|
| SV-1 激活系数 >1.2 出盒必要条件 | `activation_engine.py` 阈值硬编码常量 1.2，出盒 API 校验 |
| SV-2 PUCR 预售须可验证 MOU | `configure` 记录 amount + data_nature（MOU 锚定位 M2 落地） |
| SV-3 触碰负空间即熔断 | 评估 α≤1.0 → 熔断路径；关闭 reason 熔断标记（F7 对接 NS-OPS 留 M3） |
| SV-4 三方任何一方可触发终止 | `close` trigger_role 三选一校验 |
| SV-5 最小化合检查 | `run_iteration` ENG-003 日志预埋（F5 落地完整判定） |
| SV-6 出盒异构三角 ≥3 签名 | `multisig.verify_trinity_signatures` 三方各 ≥1 |
| SV-7 全操作 NCA 存证 | 每操作 `nca_logger` 链式存证 + `/nca/verify` 校验 |
