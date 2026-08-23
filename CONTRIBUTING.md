# 参与共建：成为 L1 缔约者

> 制度锚定：TDCA-OPC-COMMUNITY-001（DCD-OPC-COMMUNITY-001 ✅ FROZEN）
> 本社区是**缔约者网络**，不是用户群。进入方式只有一种：签署准入 NCA。

## 准入流程（七步）

**外部开发者（你）：**

1. Fork 本仓库（`tdca-protocol`）
2. 本地运行 `python tools/enforce_entry.py --new` → 交互生成准入 NCA 草稿（`nca-archives/TDCA-ADMIT-<日期>-<序号>.yaml`）
3. 编辑该文件，核对字段（模板见 `pack/templates/admit-nca-template.yaml`）
4. 运行 `python tools/enforce_entry.py --check nca-archives/<你的文件>.yaml` → 自检通过（R1~R10 全过）
5. 提交 PR（含准入 NCA，可附首份贡献）

**维护者（守门人）：**

6. 复跑 `--check` + 人工核对 GitHub ID 与 PR 提交者一致
7. 合并 → 准入 NCA 入库 → 你被列入 `ACKNOWLEDGMENTS.md`

## 校验规则速览（enforce_entry.py）

| 规则 | 内容 |
|---|---|
| R1~R3 | YAML 结构完整、编号格式 `TDCA-ADMIT-YYYYMMDD-NNN` 不冲突、类型为 `AdmissionNCA` |
| R4 | `Contractor.GitHub-ID` 与 `Operator` 一致 |
| R5 | 四项基协议全列且 `Accepted: true` |
| R6 | 红线清单非空且含 NSFL 负空间条款 |
| R7 | `Provenance.Status` 固定 `Simulated`（真实态缔约未开放） |
| R8 | 本人自签署，不可代签 |
| R10 | NSFL 禁词熔断（发币/代币/公售/分红承诺等；红线自述的否定语境豁免；熔断留日志，不静默） |

PR 合并前，GitHub Actions（`admission-check.yml`）会对 `nca-archives/` 新增文件自动复跑全量校验 + 全链 `--verify`。

## 贡献类型与流程

| 类型 | 入口 | 评审 |
|---|---|---|
| 准入缔约（L1） | 上方七步 | admission-check 自动门禁 + 守门人核对 |
| 证明/解答贡献（[OPEN-PROBLEMS](OPEN-PROBLEMS.md) P-1~P-9） | PR 附机器可读验证文件（Lean/Isabelle/Coq 或可执行断言验证器） | ★级走常规 PR；★★/★★★ 级触发 **DCD 门禁**（人类 + 智能体双审 + 公示期）——未附机器验证不进入评审 |
| 工具/文档改进 | 常规 PR | 维护者评审 |

### Tier 标注纪律

- 证明与声称按 Tier A（已证明）/ B（部分）/ C（[proof: pending]）标注；未定稿不挂公理名
- 任何证明附模型假设 + 适用范围；**不标"绝对安全"**
- 对照基线：[`core-go/docs/formal-proofs/CLAIMS-MATRIX.md`](core-go/docs/formal-proofs/CLAIMS-MATRIX.md)

### 署名与确权（NCA）

- 贡献被接收即生成 NCA 存证（链式哈希），贡献者署名入 `ACKNOWLEDGMENTS.md`
- 协作按开源协作宣言（TDCA-OPEN-COLLAB-001）：**动态分润 15% + 开源方优先**；无明确收费约定时按开源规则合法挂载，收益默认支付 15% 版税给贡献方或其社区基金会。分润为模拟态 MOU 计量——真实态落地前以 NCA 确权及 ERI 权重记账，不产生真实现金流
- 挂载/化合双轨：外部项目可 mount（外挂协议层，不改码）或 compound（资产与制度函数化合），拒绝即止（配置权归还）

## 红线（不可绕过）

不发币、不公售、不承诺分红、不代币化、不以积分/凭证变相交易；不拉踩其他协议；数据一律带 simulated/real 性质标注（ID92）。触发 NSFL 负空间条款 → 一票否决。
