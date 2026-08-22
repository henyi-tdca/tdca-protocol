# TDCA Protocol · tools/ 增值服务工具（M1 发布包）

> 版本: V1.0（2026-08-22，M1 FROZEN，HUMAN-FOUNDER-001 签批）
> 仓库: henyi-tdca/tdca-protocol ｜ 上游: DCD-COG-ALIGN-001 + DCD-UTIL-VALUE-001（ACCEPT）
> 存证: GSEQ-0345（NCA-TDCA-REASONIX-20260822-020）+ GSEQ-0348（签批存证）

本目录包含 TDCA 增值服务双线 M1 交付物，随 tdca-protocol 仓库发布：

| 工具 | 功能 | 测试 |
|---|---|---|
| `cog_align/` | 智能体不对称认知对齐评测（API+CLI+报告+NCA 存证） | 27 用例 |
| `util_value/` | 数字版权资产效用价值评估（U_observed 地板+五阶分层+熔断） | 28 用例 |

## 目录结构

```
tools/
├── tdca_cognitive_distance.py   # 基座：认知距离（定义 3.36/3.37，命题 3.10）
├── tdca_cognitive_state.py      # 基座：五维认知状态向量（ID8）
├── tdca_fuzzy_distance.py       # 基座：模糊数学层（FUZZY_CONFIDENCE）
├── cog_align/                   # 线① 认知对齐评测服务
│   ├── engine.py  report.py  notary.py  api.py  cli.py  __init__.py
│   └── tests/test_cog_align.py  (27 passed)
└── util_value/                  # 线② 效用价值评估引擎
    ├── engine.py  report.py  notary.py  api.py  cli.py  __init__.py
    └── tests/test_util_value.py (28 passed)
```

## 快速开始

```bash
# 认知对齐评测（CLI）
python -m cog_align.cli measure --a agent-a --state-a '{"A":0.9,"D":0.9,"L":0.8,"C":0.8,"SC":0.95}' --b agent-b --state-b '{"A":0.15,"D":0.2,"L":0.2,"C":0.15,"SC":0.2}' --notarize

# 效用价值评估（CLI）
python -m util_value.cli assess --asset CP-001 --tx '[{"direction":"output","amount":120,"tier":"ip"},{"direction":"input","amount":50,"tier":"knowledge"}]' --proposed 900 --notarize

# API 服务（零依赖）
python -m cog_align.api      # http://127.0.0.1:8123/api/v1/cog-align/health
python -m util_value.api     # http://127.0.0.1:8124/api/v1/util-value/health

# 测试
python -m pytest cog_align/tests util_value/tests
```

## 依赖

- Python ≥ 3.12，仅标准库（零第三方依赖；存证 YAML 优先 pyyaml，无则回退 JSON）
- 基座模块（tdca_cognitive_*.py / tdca_fuzzy_distance.py）与本目录同层——勿移动

## 制度纪律

- **MOU 地板语义**：util_value 只输出可观测下限（U_observed=Σ销项+进项），禁止主观估值（MEMO-006-Audit）；3× 超限自动熔断锚定 1.5×
- **数据性质标注**（ID92）：SIMULATED 合成数据 / REAL 真实数据按来源标注，绝不冒充
- **NCA 存证**：每次评测/评估自动落链（provenance 标注）；发布到仓库后存证目录为 `tools/.tdca-nca/services/`
- **NSFL**：非法输入（越界/负金额/缺失要素）NSFL-TRIGGER 拒绝

## 验收证据（M1 FROZEN）

- cog_align 27 用例 + util_value 28 用例全绿；回归 164 passed（基线不破）
- CLI 实证：不对称性 d_ab=0.702<d_ba=1.258（命题 3.10）；U_observed=250 + 900→熔断锚定 375
- 交付报告: TDCA-M1-VALUE-SERVICES-001（tdca-thinktank/governance/decisions/）

---
SPDX-License-Identifier: TDCA-Internal（随 tdca-protocol 仓库许可发布）
