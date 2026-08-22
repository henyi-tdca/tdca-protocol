# TDCA Protocol · tools/ 增值服务工具（M1+M2 发布包）

> 版本: V2.0-M2（2026-08-22，M1+M2 均已 FROZEN，HUMAN-FOUNDER-001 签批）
> 仓库: henyi-tdca/tdca-protocol ｜ 上游: DCD-COG-ALIGN-001 + DCD-UTIL-VALUE-001（ACCEPT）
> 存证: GSEQ-0345（M1）/ GSEQ-0348（M1 签批）/ GSEQ-0349（M2）/ GSEQ-0350（M2 签批）

本目录包含 TDCA 增值服务双线 M1+M2 交付物，随 tdca-protocol 仓库发布：

| 工具 | 功能 | 测试 |
|---|---|---|
| `cog_align/` | 智能体不对称认知对齐评测（M1 API/CLI/报告/存证 + **M2 评测场景包**） | 43 用例 |
| `util_value/` | 数字版权资产效用价值评估（M1 地板+五阶+熔断 + **M2 入表服务**） | 44 用例 |
| `value_services/` | **M2 增值服务包统一入口**（双服务打包） | 7 用例 |

## 目录结构

```
tools/
├── tdca_cognitive_distance.py   # 基座：认知距离（定义 3.36/3.37，命题 3.10）
├── tdca_cognitive_state.py      # 基座：五维认知状态向量（ID8）
├── tdca_fuzzy_distance.py       # 基座：模糊数学层（FUZZY_CONFIDENCE）
├── cog_align/                   # 线① 认知对齐评测（M1 + M2 场景包）
│   ├── engine.py  report.py  notary.py  api.py  cli.py
│   ├── scenarios.py             # M2 场景包（思想病毒防御/认知漂移监测/对齐度分档）
│   └── tests/                   (27 M1 + 16 M2)
├── util_value/                  # 线② 效用价值评估（M1 + M2 入表服务）
│   ├── engine.py  report.py  notary.py  api.py  cli.py
│   ├── accounting.py            # M2 入表服务（会计口径/版权链存证）
│   └── tests/                   (28 M1 + 16 M2)
└── value_services/              # M2 增值服务包统一入口
    ├── __init__.py              # 双服务聚合 CLI（--version / cog-align / util-value）
    └── tests/                   (7)
```

## 快速开始

```bash
# 统一入口（M2 增值服务包）
python -m value_services --version
python -m value_services cog-align measure --a A --state-a '{"A":0.9,"D":0.9,"L":0.8,"C":0.8,"SC":0.95}' --b B --state-b '{"A":0.15,"D":0.2,"L":0.2,"C":0.15,"SC":0.2}' --notarize
python -m value_services util-value entry --asset CP-001 --tx '[{"direction":"output","amount":120,"tier":"ip"}]' --period 2026-08 --notarize

# M2 评测场景包（CLI）
python -m cog_align.cli scenario --scenario thought-virus --subject agent-x --baseline <json> --series '[[t0,<s>],[t1,<s>]]'
python -m cog_align.cli scenario --scenario tiering --a A --state-a <json> --b B --state-b <json>

# M2 入表服务（CLI）
python -m util_value.cli entry --asset CP-001 --tx <json> --period 2026-08 --proposed 900

# API 服务（零依赖）
python -m cog_align.api      # :8123  /api/v1/cog-align/{measure,event,scenarios/*}
python -m util_value.api     # :8124  /api/v1/util-value/{assess,entry}

# 测试（从本目录运行）
python -m pytest cog_align/tests util_value/tests value_services/tests
```

## 依赖

- Python ≥ 3.12，仅标准库（零第三方依赖；存证 YAML 优先 pyyaml，无则回退 JSON）
- 基座模块（tdca_cognitive_*.py / tdca_fuzzy_distance.py）与本目录同层——勿移动

## M2 新增能力

### cog_align（评测产品化）
- **思想病毒防御场景**：认知漂移检测（偏离基准且持续增大 → DRIFT_ALERT，建议人工复核+负空间熔断）
- **认知漂移监测场景**：时间序列收敛/漂移（收敛 → CONVERGING / 放大 → DRIFT_ALERT 协商建议）
- **对齐度分档场景**：高度/中度/低度/不可对齐（含不对称分档矩阵——命题 3.10 产品化）

### util_value（入表服务化）
- **会计入表建议**：U_observed>0 → 资本化入表（无形资产科目）；=0 → 费用化（fail-closed 禁止无锚资本化）
- **版权链存证上链**：SHA-256 确定性哈希 + SIMULATED_ONCHAIN 状态（真实上链需司法链运营方接入——不冒充已上链）
- **完整入表报告**（schema v2.0）：地板 + 五阶分层 + 安全熔断 + 会计入表 + 版权链存证

## 制度纪律

- **MOU 地板语义**：util_value 只输出可观测下限（U_observed=Σ销项+进项），禁止主观估值（MEMO-006-Audit）；3× 超限自动熔断锚定 1.5×
- **数据性质标注**（ID92）：SIMULATED 合成数据 / REAL 真实数据按来源标注，绝不冒充
- **NCA 存证**：每次评测/评估自动落链（provenance 标注）；发布到仓库后存证目录为 `tools/.tdca-nca/services/`
- **NSFL**：非法输入（越界/负金额/缺失要素）NSFL-TRIGGER 拒绝
- **版权链纪律**：上链为模拟通道（SIMULATED_ONCHAIN），真实上链待司法链接入——禁止声称已上链

## 验收证据（M1 FROZEN + M2 交付）

- M1: cog_align 27 + util_value 28 用例全绿；回归 164 passed
- M2: cog_align 16 + util_value 16 + value_services 7 用例全绿；回归 203 passed（toolchain 全套）
- 发布结构: 94 passed（从本目录运行）
- 交付报告: TDCA-M1-VALUE-SERVICES-001（M1 FROZEN）+ TDCA-M2-VALUE-SERVICES-001（M2 交付）

---
SPDX-License-Identifier: TDCA-Internal（随 tdca-protocol 仓库许可发布）
