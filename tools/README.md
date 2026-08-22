# TDCA Protocol · tools/ 发布包（M1+M2 + 五项目 · 全量）

> 版本: V2.2（2026-08-23，全量 8 包，191 用例发布结构回归）
> 仓库: henyi-tdca/tdca-protocol ｜ 上游: DCD-COG-ALIGN-001 + DCD-UTIL-VALUE-001 + 五项目 DCD（全部 ACCEPT）
> 存证: GSEQ-0345→0359（会话 008 全链）｜ 签批: M1+M2 + 五项目 M1 均 FROZEN（HUMAN-FOUNDER-001）

本目录为 TDCA 开源 tools/ 全量发布包——**增值服务双线（M1+M2）+ 五项目化合贡献**，随 tdca-protocol 仓库发布：

## 目录结构（8 包）

```
tools/
├── tdca_cognitive_distance.py   # 基座：认知距离（定义 3.36/3.37，命题 3.10）
├── tdca_cognitive_state.py      # 基座：五维认知状态向量（ID8）
├── tdca_fuzzy_distance.py       # 基座：模糊数学层（FUZZY_CONFIDENCE）
├── cog_align/                   # 线① 认知对齐评测（M1 + M2 场景包）  43 用例
│   ├── engine/report/notary/api/cli.py + scenarios.py（M2 场景包）
├── util_value/                  # 线② 效用价值评估（M1 + M2 入表）    44 用例
│   ├── engine/report/notary/api/cli.py + accounting.py（M2 入表）
├── value_services/              # 增值服务包统一入口（V2.0-M2）        7 用例
├── maka_nca/                    # 五项目① Maka：Event Log→NCA+正和    23 用例
├── paperclip_nca/               # 五项目② Paperclip：编排→协作编译     18 用例
├── pi_nca/                      # 五项目③ Pi：MIT 层制度编译（Fair Source 隔离） 19 用例
├── cypress_pool/                # 五项目④ Cypress：配置权计量+L2       19 用例
└── thingsboard_pool/            # 五项目⑤ ThingsBoard：IoT 计量+L2    18 用例
（合计 191 用例）
```

## 快速开始

```bash
# 增值服务（M1+M2）
python -m value_services --version                          # V2.0-M2
python -m value_services cog-align measure --a A --state-a <json> --b B --state-b <json>
python -m value_services util-value entry --asset CP-001 --tx <json> --period 2026-08

# 五项目贡献（M1）
python -m maka_nca.cli endtoend --log <json>               # Event Log→NCA+正和
python -m paperclip_nca.cli compile --orch <json>          # 编排→协作语义
python -m pi_nca.cli compile --spec <json>                 # 构建→制度编译（MIT 层）
python -m cypress_pool.cli market --run <json> --price 10  # 测试→计量→L2 订单
python -m thingsboard_pool.cli market --stream <json>      # 设备流→计量→L2 订单

# API 服务（零依赖）
python -m cog_align.api      # :8123
python -m util_value.api     # :8124

# 测试（从本目录运行）
python -m pytest cog_align/tests util_value/tests value_services/tests maka_nca/tests paperclip_nca/tests pi_nca/tests cypress_pool/tests thingsboard_pool/tests
```

## 依赖
- Python ≥ 3.12，仅标准库（零第三方依赖；存证 YAML 优先 pyyaml，无则回退 JSON）
- 基座模块（tdca_cognitive_*.py / tdca_fuzzy_distance.py）与本目录同层——勿移动

## 制度纪律
- **MOU 地板语义**：util_value 只输出可观测下限（U_observed=Σ销项+进项），禁止主观估值；3× 超限熔断锚定 1.5×
- **数据性质标注**（ID92）：SIMULATED 合成数据 / REAL 真实数据按来源标注，绝不冒充
- **NCA 存证**：每次评测/评估自动落链（provenance 标注）
- **NSFL**：非法输入 NSFL-TRIGGER 拒绝
- **Fair Source 管控**（pi_nca）：化合仅限 MIT 层，Fair Source 核心层不内化/不依赖/不传播（许可证边界即化合边界）
- **双向赋能**（BIDIR-001）：五项目贡献独立实现，不修改任何外部项目核心（maka/paperclip/pi/cypress/thingsboard 核心零触碰）
- **版权链纪律**（util_value）：上链为模拟通道（SIMULATED_ONCHAIN），真实上链待司法链接入

## 验收证据
- 发布结构回归：**191 passed**（增值服务 94 + 五项目 97）
- toolchain 全套：300 passed
- 交付报告：TDCA-M1-VALUE-SERVICES-001（M1 FROZEN）+ TDCA-M2-VALUE-SERVICES-001（M2 FROZEN）+ TDCA-M1-FIVE-PROJECTS-001（五项目 M1 FROZEN）

---
SPDX-License-Identifier: TDCA-Internal（随 tdca-protocol 仓库许可发布）
