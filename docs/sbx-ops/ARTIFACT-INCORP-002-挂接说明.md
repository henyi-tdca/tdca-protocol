# ARTIFACT-INCORP-002 挂接说明（实底 ↔ 两件在册制度件互指）

> 本文件为新增挂接件（TDCA-HANDOFF-EXEC-ARTIFACT-INCORP-002 / T-2），**不改任何在册件正文**。
> 互指以本说明为枢纽：本说明与两件制度件同目录（docs/sbx-ops/）相邻存放，提供制度件 → 实底方向的索引；
> 实底 → 制度件方向由各实底目录的 `SOURCE-ARTIFACT-INCORP-002.md` 与本说明的映射表共同承载。

## 一、互指双方

| 角色 | 在册件 / 落位 | 说明 |
|---|---|---|
| 制度件①（语义权威） | `docs/sbx-ops/TDCA-PRINCIPLE-DSA-001-动态安全三空间循环机制.md` | 动态安全三空间循环机制 |
| 制度件②（语义权威） | `docs/sbx-ops/TDCA-DSA-FC-NS-OPS-001-接口规范-V1.0-REVIEW.md` | DSA／负空间全栈接口规范（同族） |
| 实底（实现＋测试，甲范围） | `tdca-sbx-ops/backend/`（PR：`feat/artifact-incorp-impl`，48 件）| 沙盒调度空间实现 |
| 实底（实现＋测试，甲范围） | `tdca-ns-ops/backend/`（PR：`feat/artifact-incorp-impl`，39 件）| 负空间管理操作空间实现 |
| 机读版（T-3） | `docs/sbx-ops/TDCA-DSA-FC-NS-OPS-001-接口规范-V1.0.machine.json` | 接口／状态枚举／触发级；人读件为语义权威 |

两件实底随 PR `feat/artifact-incorp-impl` 入仓；本说明与机读版随 PR `feat/artifact-incorp-link` 入仓，两 PR 相互独立、各自可审。

## 二、映射表（文件名粒度索引）

### 2.1 制度件①（三空间循环）↔ 实底

| 制度件概念 | 实底承载（入仓路径） |
|---|---|
| 状态机（NS-PENDING … EXITED，10 态 21 转换） | `tdca-ns-ops/backend/app/sandbox.py`、`tdca-ns-ops/backend/app/models.py` |
| 沙盒调度器（M2 模块） | `tdca-sbx-ops/backend/app/sandbox_core.py`、`tdca-sbx-ops/backend/app/routes/sandboxes.py` |
| 激活系数 >1.2（SV-1） | `tdca-sbx-ops/backend/app/activation_engine.py`（ACTIVATION_THRESHOLD 单一权威阈值） |
| 正和验证 / ERI / CCI（Utility Genie） | `tdca-sbx-ops/backend/app/utility_genie_adapter.py`、`tdca-sbx-ops/backend/app/routes/genie.py`、`genie_callback.py` |
| 人类门 / 人类裁决 | `tdca-ns-ops/backend/app/human_gate.py`、`tdca-sbx-ops/backend/app/routes/trinity.py`（TRINITY_ROLES） |
| NCA 存证生成 | `tdca-sbx-ops/backend/app/nca_logger.py`、`tdca-sbx-ops/backend/app/routes/nca.py` |
| 多签 | `tdca-sbx-ops/backend/app/multisig.py` |

### 2.2 制度件②（接口规范）↔ 实底

| 规范概念 | 实底承载（入仓路径） |
|---|---|
| 负空间声明校验（IF-001 语义） | `tdca-ns-ops/backend/app/routes/constraints.py`、`views.py` |
| 函数语料六要素 / 审查 | `tdca-ns-ops/backend/app/adjustment_flow.py`、`tdca-sbx-ops/backend/app/routes/chem.py`（六要素评分） |
| 运行时负空间匹配（ECE 语义） | `tdca-sbx-ops/backend/app/dsa_extension.py`、`tdca-sbx-ops/backend/app/routes/dsa.py`、`tdca-ns-ops/backend/app/integration/nsfl_adapter.py` |
| 熔断档位 L1–L5 / 状态联动 | `tdca-sbx-ops/backend/app/routes/cbdc.py`（cbdc_anchor）、`tdca-sbx-ops/backend/app/activation_engine.py`（escalate 语义） |
| 沙盒生命周期（SBX-* 态） | `tdca-sbx-ops/backend/app/routes/phase.py`、`phase_adapter.py`、`flow_adapter.py` |
| 工程端点 /api/v1/*（M3 口径） | `tdca-ns-ops/backend/app/main.py` 及 `routes/`（adjustments、constraints、integration、views） |
| DSA ↔ NS-OPS 适配层 | `tdca-ns-ops/backend/app/integration/`（flow_adapter、identity、sandbox_real） |

> 上表为文件名粒度挂接索引，仅指示「制度概念 → 代码承载」的查找入口；语义权威始终是两件人读制度件，代码行为与制度件冲突时以制度件为准并回报。

## 三、机读版定位与使用约束

- 机读版：`TDCA-DSA-FC-NS-OPS-001-接口规范-V1.0.machine.json`（JSON，可解析）。
- 覆盖范围：状态全集与编码、21 条状态转换、熔断触发级 L1–L5、IF-001…IF-008 接口契约（含规范端点↔M3 工程端点适配映射）、错误码 TDCA-ERR-001…014、事件总线 topic 清单、性能基线。
- 约束：人读件为语义权威；机读版不臆造——规范未详细定义的接口（IF-005/007/008）在机读版中显式标记 `null` + `note`；联盟链智能合约接口（TDCA-DSA-CBDC-001）属外部条件，本轮挂起，不入机读化范围。

## 四、挂接合规声明

- 未改动任何在册件正文（含两件制度件、docs/sbx-ops/ 与 docs/ns-ops/ 全部在册件）。
- 未触碰 host 白名单件（deploy/.env 归创始人自管；freeze-pair-1009.yml、docker-compose.yml(+bak)、nginx、web.conf、portal/index.html、install.sh 均未触及）。
- 本说明为新增件；如需撤销挂接，删除本文件与机读版即可，无在册件耦合。
