# TDCA 工具货架上架填报表 · 第二批 14 件

> 件号：`TDCA-HANDOFF-EXEC-L1SI187-SITE-S2-FILL-001` 块 A 产出 ｜ 日期：2026-11-01（+08）
> 用途：operator 照本表逐条页面注册（本表不含上架动作；一句用途照 SITE-S2-001 令面原文，已过零内部编号／零定价／零凭据核）
> 形态栏「库件 · 无服务入口」（第 5 行）与「须标『调用须授权』」字样照令面逐字填写

| # | 对外名 | 仓内路径 | 形态 | 类目 | 一句用途 | 是否须授权 | 可开性自测方式与结果 |
|---|---|---|---|---|---|---|---|
| 1 | 认知对齐 | `tools/cog_align/` | 服务件（有 `cli.py`） | other | 度量并比对多主体的认知偏差 | false | `python -m cog_align.cli --help` 过（measure/event/convergence/scenario） |
| 2 | 一致性测试套件 | `tools/cts_l1/` | 服务件（`--target` 入口） | other | 对协议实现做一致性测试 | false | `python -m cts_l1 --help` 过（--target 入口） |
| 3 | 跨场景适配 | `tools/cross-scene/` | 库件（无 CLI） | adapter | 跨场景之制度与数据适配 | false | 导入冒烟过（`import cross_scene` OK，库件） |
| 4 | 配置权计量 | `tools/cypress_pool/` | 服务件 ＋ 须标「调用须授权」 | adapter | 计量配置权调用并出账 | true | `python -m cypress_pool.cli --help` 过（meter/market） |
| 5 | 流程编排 | `tools/flow-orchestrator/`（入口在 `src/`） | 库件 · 无服务入口 | other | 编排多环节流程并留痕 | false | 引擎导入冒烟过（`import src` OK，库件口径；服务入口不在本批） |
| 6 | 知识图谱编译器 | `tools/kg-compiler/` | 服务件（`api.py`） | compiler | 将知识图谱编译为可查结构 | false | `python api.py` 起服冒烟过（uvicorn 起进程） |
| 7 | 存证审计 | `tools/maka_nca/` | 服务件 | other | 把事件日志转为可核存证 | false | `python -m maka_nca.cli --help` 过（convert/validate/endtoend） |
| 8 | 通道桥接 | `tools/mcp_bridge/` | 服务件（`stdio`） | adapter | 桥接机器可读通道与外部调用 | false | `python -m mcp_bridge` stdio 起（自标 SIMULATED 就绪） |
| 9 | 商户闭环 | `tools/merchant_loop/` | 服务件 | other | 跑通商户侧闭环并出账 | false | `python -m merchant_loop.cli --help` 过（publish/redeem/roi-report） |
| 10 | 协作编排 | `tools/paperclip_nca/` | 服务件 | compiler | 把协作语义编译为可核步骤 | false | `python -m paperclip_nca.cli --help` 过（compile/summary） |
| 11 | 编码代理 | `tools/pi_nca/` | 服务件 | compiler | 在制度约束下生成与登记代码 | false | `python -m pi_nca.cli --help` 过（compile/guard） |
| 12 | 效用价值评估 | `tools/util_value/` | 服务件 | other | 按制度口径评估资产效用 | false | `python -m util_value.cli --help` 过（assess/entry） |
| 13 | 增值服务包 | `tools/value_services/` | 服务件 ＋ 须标「调用须授权」 | other | 打包对外增值服务能力 | true | `python -m value_services` 入口过（回 usage 提示；件内版本 2.0.0-M2） |
| 14 | 物联计量网关 | `tools/thingsboard_pool/` | 服务件 ＋ 须标「调用须授权」 | adapter | 接入设备数据流并计量 | true | `python -m thingsboard_pool.cli --help` 过（meter/market） |

## 填报备注

- 可开性自测均对**本表所列仓内路径**（canonical 副本）实测；tools/ 与 tdca-toolchain/ 存在双副本、内容有差异，上架与联调以本表路径为准。
- 第 5 行（流程编排）：`src/api.py` 服务入口导入问题**不在本批**（令面块 C.3），入口修复挂站点三期另令；本表按库件·无服务入口填报，一句用途只讲编排引擎能力。
- 既有在架 8 件未动（本表只做新增 14 件）。
