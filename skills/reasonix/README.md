# TDCA Protocol × Reasonix Skills

> TDCA（Thought-driven Compound Architecture，智能体协议体系）的**公开面能力包**，以 Reasonix skill 形态提供——让智能体生态获得「计税 / 结算 / 存证 / 合规」四项制度协议能力。

**状态**: 首批发布候选 V0.1（4 件）｜ 许可: Apache-2.0

## 本包是什么

TDCA 的核心方法论之一是「制度即代码」：把治理规则做成智能体在约束下运行的协议，而不是事后审计。本包把其中四件**公开面能力**做成 Reasonix 可直接安装的 skill：

| skill | 一句话 |
|---|---|
| `tdca-tax-officer` | 微交付税收官——对智能体之间的微交付执行计税/预缴/聚合/结算，发生即存证 |
| `tdca-cls-officer` | 金融闭环结算官——多主体债务网络的环销/净额/定向支付/条件支付闭环结算 |
| `tdca-notary` | 存证官——嵌套认知资产（NCA）生成/链式验证/追溯查询，让动作可存证不可抵赖 |
| `tdca-compliance-auditor` | 制度合规审查官——对照治理规范输出可追溯违规清单，合规即正确 |

## 安装

Reasonix 支持从 URL / GitHub / 本地目录安装 skill。安装本包中的任一 skill 目录（含 `SKILL.md`）即可：

```
# 以本地目录为例
install-capability → 选择本包 skills/<skill-name>/ 目录
# 或从公开仓库安装（发布后）
<skill 仓库 raw/目录 URL>
```

## 使用前提

- 库依赖: `tax-officer` / `cls-officer` 需配套实现库（`tdca-microtax` / `tdca-cls`——公开实现随仓库发布或按接口自适配）
- 知识底座: `compliance-auditor` / `notary` 需宿主提供治理规范权威文档与存证链目录（skill 内路径已参数化为 `<workspace>` / `<kb>` 占位）
- 数据性质: 未接真实资金/申报通道前，一切执行须显式标注 `simulated`（模拟态）

## 反哺条款

本包以开源方式发布。**凡因本包产生的任何收益，默认按 15% 比例分润/捐赠给 Reasonix 项目或其社区基金会**（与 TDCA 开源协作分润口径一致）。

## 声明

- 本包由 TDCA 项目发布，**与 Reasonix 官方无关联、未获其背书**；安装与使用请遵循 Reasonix 自身条款。
- 本包不含任何算力/账单口径信息；内容以公开面方法论文档为准。

## 结构与许可

```
skills/
  tdca-tax-officer/SKILL.md
  tdca-cls-officer/SKILL.md
  tdca-notary/SKILL.md
  tdca-compliance-auditor/SKILL.md
LICENSE（Apache-2.0）
```

---
*TDCA Protocol × Reasonix Skills · 公开面 V0.1（首批 4 件候选，发布前经守门人定稿）*
