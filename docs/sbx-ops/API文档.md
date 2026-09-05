# TDCA SBX-OPS M1 原型 — API 文档

> FC: TDCA-FC-SBX-OPS-001（M1 核心引擎原型）| 版本: 0.1.0-M1 | 日期: 2026-08-10
> 制度锚定: SV-1（激活系数 >1.2 硬编码）/ SV-2（PUCR 可验证）/ SV-4（三方终止）/ SV-6（异构三角签名）/ SV-7（NCA 存证）
> 规范来源: TDCA-FC-SBX-OPS-001 任务书（FROZEN，NCA-20260810-002）+ KB-ECON-001 §7
> 交互式文档: 后端启动后访问 `http://127.0.0.1:8000/docs`（Swagger UI，OpenAPI 自动生成）

---

## 一、服务概览

| 项 | 值 |
|----|----|
| 服务名 | `tdca-sbx-ops` |
| Base URL | `http://127.0.0.1:8000/api/v1` |
| 技术栈 | Python 3.12 + FastAPI 0.141 + pydantic 2.13 |
| 数据存储 | JSON 文件（`backend/data/*.json`） |
| NCA 存证 | `backend/nca/NCA-{YYYYMMDD}-{seq:03d}.json`（11 字段 + 链式哈希，只追加） |
| 启动 | `cd backend && uvicorn app.main:app --port 8000` |

## 二、沙盒生命周期（F1）

### 2.1 创建沙盒 `POST /sandboxes`

六要素声明强制（工作规范 §2.2），缺失任一要素 → 422。

```json
{
  "name": "零数据企业创新孵化",
  "initiator_did": "did:tdca:INNOVATOR-001",
  "initiator_role": "innovator",
  "six_elements": {
    "目标函数": "零数据企业通过 PUCR 预售产生第一笔硬数据",
    "约束矩阵": "FC-SBX-OPS-001 SV-1~7；宪法十六条",
    "先验分布": "任务书 FROZEN + KB-ECON-001 §7",
    "配置权边界": "L2 层",
    "预期分配": "沙盒实验",
    "审计轨迹": "TDCA-NCA-{YYYYMMDD}-{SEQ}"
  }
}
```

→ `201` + Sandbox（`phase=Phase0`，`nca_ids` 含 `SBX_CREATE` 存证）。

### 2.2 沙盒列表 `GET /sandboxes`

→ `200` + Sandbox 数组（按创建时间升序，含种子演示沙盒）。

### 2.3 沙盒详情 `GET /sandboxes/{sandbox_id}`

→ `200` + Sandbox（含 `activation_logs` / `nca_ids` / `eng003_log`）；不存在 → `404`。

### 2.4 沙盒配置 `POST /sandboxes/{id}/configure`

配置 PUCR 预售/质押（SV-2，amount 必须 >0，data_nature 自动标注 simulated）：

```json
{ "pucr": { "amount": 10000 }, "s_rights": [] }
```

→ `200`；amount ≤ 0 → `422`。

### 2.5 开始实验 `POST /sandboxes/{id}/start`

准入完成 → 实验（Phase0→P0）。→ `200`；非准入期 → `422`。

### 2.6 运行迭代 `POST /sandboxes/{id}/run`

```json
{ "iteration": { "metric": "users", "value": 100 } }
```

实验数据收集 + ENG-003 最小化合检查日志（F5 预埋，开发纪律 5）。仅 P0 → `200`。

### 2.7 沙盒出盒 `POST /sandboxes/{id}/exit`

出盒必要条件（SV-1 α>1.2 硬编码 + SV-6 异构三角 ≥3 签名 + 人类签批）：

```json
{
  "signatures": [
    { "role": "innovator", "did": "did:tdca:INNOVATOR-001", "signature": "s1" },
    { "role": "investor",  "did": "did:tdca:INVESTOR-001",  "signature": "s2" },
    { "role": "government","did": "did:tdca:GOV-001",       "signature": "s3" }
  ],
  "human_signatory": "did:tdca:HUMAN-FOUNDER-001"
}
```

→ `200`（phase=Exit）；α≤1.2 或签名不足 → `422`（detail 列明 SV-1/SV-6 原因）。

### 2.8 沙盒关闭 `POST /sandboxes/{id}/close`

负空间熔断（SV-3）/ 三方终止（SV-4，任意一方可触发），人类裁决：

```json
{ "trigger_role": "government", "reason": "负空间熔断：财政不可持续", "human_signatory": "did:tdca:HUMAN-FOUNDER-001" }
```

reason 含"熔断/负空间"→ NCA `negative_space_check=FUSE`。→ `200`（phase=Closed）。

### 2.9 生命周期状态机

```
Phase0(准入) → P0(实验) → P1(评估) → Exit(出盒)  （SV-1 + SV-6 门控）
   任意非终态 → Closed(关闭·熔断/终止，SV-3/SV-4)
非法转移 → 422；终态不可再操作
```

## 三、激活系数引擎（F3）

### 3.1 评估 `POST /sandboxes/{id}/evaluate`

```json
{ "pcr_input": 100, "tax_revenue": 150, "employment_ss": 20, "data_nature": "simulated" }
```

激活系数 = (tax_revenue + employment_ss) / pcr_input。决策门（SV-1 硬编码 1.2）：

| α | 状态 | 决策 |
|----|------|------|
| > 1.2 | 财政自给性达成 | 政策可复制推广（出盒必要条件，非充分） |
| 1.0 < α ≤ 1.2 | 基本盈亏平衡 | 条件续期 |
| ≤ 1.0 | 财政不可持续 | 负空间熔断 / 资产清算 |

→ `200`（phase=P1，`activation_logs` 追加记录，含 `input_hash` 过程可审计）；
`data_nature` 仅允许 `real|simulated`（开发纪律 1：不可 mock）；pcr≤0 / 负数 → `422`。

## 四、NCA 存证（F8）

| 端点 | 说明 |
|------|------|
| `GET /nca` | 存证列表（按序号升序，审计查询） |
| `GET /nca/{nca_id}` | 存证详情（11 字段 + prev_hash/content_hash） |
| `GET /nca/verify` | 链式完整性校验（篡改/断链检测）→ `{valid, checked, first_broken, errors}` |

NCA 11 字段（MEMO-006 附录 C）：NCA-ID / FC-ID / Operation / Operator / Timestamp /
Pre-State / Post-State / Config-Right-Token / Audit-Trail / Human-Signature / Negative-Space-Check。
每条存证链接链尾 `prev_hash`，`content_hash = sha256(内容)`——只追加、不可篡改（SV-7）。

## 五、错误码约定

| HTTP | 含义 | 触发 |
|------|------|------|
| 404 | 资源不存在 | 沙盒/NCA id 错误 |
| 422 | 校验失败 / 非法状态转移 / 出盒资格不满足 | 六要素缺失、α≤1.2 出盒（SV-1）、签名不足（SV-6）、非法转移 |
| 201/200 | 成功 | — |

## 六、前端

React 19 + Vite 面板（`frontend/`），`npm run dev` 后访问 `http://localhost:5173`
（vite proxy `/api` → `127.0.0.1:8000`）。功能：沙盒列表 / 创建（六要素）/ 生命周期操作 /
激活系数三档着色 / NCA 链校验横幅。
