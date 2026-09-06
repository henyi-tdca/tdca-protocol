# TDCA-CONTRACTS-TEMPLATES-001 · 智能合约模板集公开页（草案）

> SPDX-License-Identifier: Apache-2.0
> 状态: DRAFT（TDCA 制度层起草，2026-09-06，供门户「智能合约 C01–C16」卡解锁推送）｜ 落位候选: docs/contracts/
> 制度锚: REPO-004 合约库 ｜ TDCA-CONST-v3.1.2（宪法）｜ TERMS-001 §2.1 ｜ 许可: Apache-2.0（仓库根 LICENSE 覆盖）

## 一、定位

TDCA 智能合约模板集——将**宪法条款与经济模型编码为合约硬约束**的规范模板（制度即代码）：每条宪法条款/经济规则对应合约函数与约束检查，**逐条映射制度依据**（条款→函数→约束），杜绝无制度依据的合约。

## 二、模板清单（contract-templates-v1.0.yaml）

| 模板 | 类型 | 用途 |
|---|---|---|
| CONST-ENFORCE-001 | 宪法强制执行 | 宪法十六条编码为硬约束（ConstitutionalChecker：任一违反 fail-closed） |
| MOU-ANCHOR-001 | MOU 税收锚定 | MOU = 进项+出项 + 税收真实性校验 + 验证窗口 + 熔断 |
| NSFL-FUSE-001 | 负空间熔断 | 负空间命中（R<0/无锚/越权）→ 强制归零 + 暂停 |
| CONFIG-RIGHT-SCHEDULE-001 | 配置权调度 | Shapley 分配 + P_C = ψ(ERI, MOU, Shapley, irreplaceability) |
| DCEP-MOU-001 | 数字人民币对接 | MOU_ANCHOR 合约执行 + 结算（e-CNY 法偿锚） |

## 三、C01-C16 条款编号架构（CONST-ENFORCE-001）

| 编号 | 条款 | 约束 |
|---|---|---|
| C01 | 可观测性 | check_observability |
| C02 | 正和聚合 | check_positive_sum（Shapley > 0） |
| C03 | 自证性 | check_self_evidence |
| C04 | 配置权第三极 | check_ownership_isolation |
| C05 | 刚需线保护 | check_substance_line |
| C06–C16 | 扩展硬约束 | 后续条款按同一架构编码扩展 |

> C06–C16 逐条合约函数为**扩展编码位**（模板架构预留，按条款扩展逐条产出）——模板集已定义编号/名称/约束检查架构；逐条代码经编码智能体按模板产出。

## 四、配套

- 编码智能体（合约工程师）：按本模板集将宪法/经济模型产出合约代码 + 制度映射表（机器可读接口随官方智能体集群）
- 试点件：gRPC 集成设计 / 传统文化内容授权合约 / MOU 合约试点（tdca-contract-output 区）

## 五、门户卡口径

「智能合约 C01–C16」= 合约模板集（CONST-ENFORCE/MOU-ANCHOR/NSFL-FUSE/配置权调度/DCEP 五模板 + C01-C16 条款编号架构），制度即代码硬约束规范，Apache-2.0。
