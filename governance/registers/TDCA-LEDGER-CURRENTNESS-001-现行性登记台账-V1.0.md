# TDCA 现行性登记台账（Currentness Ledger）

> 件号：`TDCA-LEDGER-CURRENTNESS-001` ｜ 版本：**V1.0** ｜ 初立：2026-11-22（+08）
> 依据：`TDCA-RULING-L1SI225-VERSION-001` 之 `V-1`／`V-2`；`TDCA-HANDOFF-EXEC-L1SI225-VERFILL-001`
> 用途：第三人**不看件名、只看本台账**即可判「该件是否现行」。版本判定一律以本台账「依据」栏为准，
> ⛔ 以件名/状态后缀（`-FROZEN`/`-DRAFT`/`-REV`）推断现行性（`FROZEN` 仅表冻结，`DRAFT` 明确非现行）。
> 维护纪律：件换版时**新增一行**（⛔ 覆盖旧行）；每行「有效期起」= 该版生效时刻。

## 栏位说明

| 栏 | 内容 |
|---|---|
| 件（族／件名） | 现行版件之标识（仓内路径） |
| 现行版本号 | 现值（形如 `V1.0`） |
| 依据 | 变更控制记录：签批件号／发布令／提交哈希＋时刻 |
| 有效期起 | 该版生效时刻（+08） |

## 一、本批初登 13 件（VERFILL-001 · P0 · 2026-11-22 补标注入册）

| 件（族／件名） | 现行版本号 | 依据 | 有效期起 |
|---|---|---|---|
| papers／TDCA-MONOGRAPH-COP-001.md | V1.0 | 发布提交 496e4837「思维协议认知论定位论文公开发布」2026-08-26；deid 去内部编号 e5fecf5f 2026-10-01；件头自载 Published 2026-08-26／Status Released | 2026-08-26 |
| papers／TDCA-paper-CN.md | V1.0 | GSEQ-0931 裁决公开入库 579e001f(#81) 2026-09-02「期刊投稿路径作废，转公开仓库发布」；哈希锚定修复 28536afc(#82)（FROZEN 定稿 SHA256 12cbc770…）；对齐 0a05ec03(#202)；deid e5fecf5f | 2026-09-02 |
| papers／TDCA-paper-EN.md | V1.0 | 同上批（FROZEN final SHA256 4323f5c4…）；#81/#82/#202/e5fecf5f | 2026-09-02 |
| papers／从盲推到逆推-一次校验器变更的完整工程闭环.md | V1.0 | PRACHAND-001 入仓进站 75c28c32 2026-11-18（依 TDCA-HANDOFF-EXEC-L1SI218-PRACHAND-001） | 2026-11-18 |
| papers／TDCA-MONOGRAPH-DC-001-REV-1-数字人民币智能体协作-修订版.md | V1.0 | L1SI196-PAPER-REPO-001 件2 现行版入仓 8749ccbd 2026-11-05（39008B·sha256_16 5841D91BDAB964E8）；件头自载归档来源用户上传 2026-08-08。注：件内自述「正式修订版（REV-1）／研究沙盒（审查前）」，台账不据后缀推号，仅记于此 | 2026-11-05 |
| papers／evidence/E1_cross_model_consistency.md | V1.0 | 与主论文同版包：GSEQ-0931 公开入库 579e001f(#81) 2026-09-02；哈希锚定 28536afc(#82)；采集 2026-09-01（TDCA-HANDOFF-WORKBUDDY-PAPER-EVIDENCE-001） | 2026-09-02 |
| papers／evidence/E2_meter_verifiability.md | V1.0 | 同上 | 2026-09-02 |
| papers／evidence/E3_tax_anchor.md | V1.0 | 同上 | 2026-09-02 |
| papers／evidence/E4_dual_layer_interception.md | V1.0 | 同上（另涉 TDCA-METER-NSFL-CORRECT-001 案例源） | 2026-09-02 |
| papers／evidence/E5_external_anchor_vb.md | V1.0 | 同上 | 2026-09-02 |
| papers／evidence/E6_model_independence.md | V1.0 | 同上（另涉 TDCA-PAPER-REVIEW-001 §三） | 2026-09-02 |
| papers／evidence/EVIDENCE-INDEX.md | V1.0 | 同上 | 2026-09-02 |
| help／TDCA-HELP-PATHS-001-帮助·三条路与联系方式指引（同源-help页文字）.md | V1.0 | 立族 8959c246（L1SI188-NAV-FIX-003 段二项3）；去内部编号 9d7ed20b（L1SI197-HELP-ID-001）；/help 实况对齐 8798c62c（L1SI200-USABILITY4-2-1）2026-11-06。文字逐字同源 /help 页 | 2026-11-06 |

## 二、已有 version 件转录（22 件 papers · 现值照站端读数转录，签批细则随批次补登）

| 件 | 现值 | 有效期起（待补签批栏） |
|---|---|---|
| TDCA-FUNCTION-WP-002-函数白皮书.md | V2.0-FROZEN | 2026-08-21（件内自载人类签批 ACCEPT） |
| TDCA-FUNCTION-WP-002-APPX-G-附录G-制度大模型与制度孪生函数化登记.md | V2.0 | 2026-08-26（件内自载签批并入） |
| TDCA-FUNCTION-WP-002-APPX-E-附录E-公理化基础-PUBLISH.md | V2.0 | 随函数白皮书体系 |
| TDCA-MATH-WP-REV-001-数学基础白皮书修订本.md | V1.0-FROZEN | 2026-08-23（件内自载签批） |
| TDCA-MONOGRAPH-IT-001.md | V3.0-FINAL | 件内自述 |
| TDCA-MONOGRAPH-AGENT-001-智能体协作范式跃迁-对外净版….md | V1.0 | 2026-08-08（件内自载） |
| TDCA-MONOGRAPH-COP-002-思维协议的运用-对外净版….md | V1.0 | 件内自述 |
| TDCA-MONOGRAPH-SANDBOX-001-沙盒正反化合机制.md | V1.0 | 件内自述 |
| TDCA-REPORT-U-RUN-FINAL-002-效用线注入实验报告-对外净版….md | V1.0 | 件内自述 |
| TDCA-PAPER-ENGINEERING-PHILOSOPHY-001-工程哲学-中文版-V1.0.md | V1.0 | 件内自述 |
| TDCA-PAPER-ENGINEERING-PHILOSOPHY-001-工程哲学-English-V1.0.md | V1.0 | 件内自述 |
| TDCA-PAPER-PHILOSOPHY-001-制度哲学-中文版-V1.0.md | V1.0 | 件内自述 |
| TDCA-PAPER-PHILOSOPHY-001-制度哲学-English-V1.0.md | V1.0 | 件内自述 |
| TDCA-PAPER-FUNCTIONAL-LM-001.md | V1.1-REV-001 | 件内自述 |
| TDCA-WP-MATERIALISM-001.md | V1.1 | 件内自述 |
| TDCA-TOPIC-AGENT-CREATION-001-智能体创建论专题报告-V1.2-PUBLIC.md | V1.2-PUBLIC | 2026-10-23（件内自载） |
| TDCA-TOPIC-PARADIGM-001-主流智能体构建范式六分法-V1.2-PUBLIC.md | V1.2-PUBLIC | 2026-10-23（件内自载） |
| TDCA-TREATISE-026-REV-002-复核修正版.md | V1.2 | 件内自述 |
| tdca-paper-realtime-001/TDCA-PAPER-REALTIME-001-V1.3-PUBLISH-….md | V1.3-PUBLISH | 件内自述 |
| tdca-proposal-anchor-001/TDCA-PROPOSAL-ANCHOR-001-V1.4-PUBLISH-….md | V1.4-PUBLISH | 件内自述 |
| TDCA-PROTOCOL-CCP-001-V1.0-13章补落版-PUBLISH.md | V1.0 | 件内自述 |
| TDCA-RESEARCH-FULLCYCLE-EXPLICITERM-001-全周期管理×解释项替换研究件-PUBLISH.md | V1.0 | 件内自述 |
| TTRN-001-PUBLISH.md | V0.1-DRAFT | **非现行标注**：DRAFT 明确非现行，现行版待出版批次更新本台账 |

## 三、待登批次（后续令）

- regulation／ops-guides／whitepapers 三族：站端已有 version 值（VERFILL-001 令面「可作起点」），逐件转录＋签批依据补登另批施工。
- cop-library 族：不涉版本（令面 S-4），⛔ 纳入本台账。
