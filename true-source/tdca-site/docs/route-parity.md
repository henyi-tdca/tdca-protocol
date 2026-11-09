# 逐面路由对照表（批 0 基线 · 66 行四栏）

> 件号：TDCA-PARITY-ROUTE-L1SI205-B0 ｜ 批次：迁移批 0 基线固化 ｜ 日期：2026-11-09（+08）
> 来源：执行侧 -188 回报（TDCA-EXEC-DAILY-OPS-20261109-188）实读表照录 ｜ 读点：atomgit/main @ a4f4e222
> 旧版基线：tdca-frontend PAGE_META（66 条，S-1 已自校 ≡66）｜ 新版：tdca-site App.tsx
> 口径：⛔「同族」⛔算在位——多级路径仅当新版有动态段模板可承接（如 /docs/:family）才算「动态段在位」，否则一律「缺」。四要件（①页面在位②匿名可达非空壳③可发现④无在建占位）待各批逐面实读。
> 用法：本表为后续各批之验收基准；每批施工前逐行核「新版对照」栏，批 8 追平判定以此表为准。

| # | 旧版路径 | 题名（旧版） | 权限 | 新版对照 | 判 |
|---|---|---|---|---|---|
| 1 | `/` | TDCA 三体可视化中心 | 公开 | `/overview（或 /，Home 已渲染 OverviewPage）` | 改路径 |
| 2 | `/about` | 关于 · 一页看懂 TDCA | 公开 | `/about` | 同路径在位 |
| 3 | `/academy` | TDCA 商学院 | 公开 | `/academy` | 同路径在位 |
| 4 | `/academy/outline` | 教材目录（纲要） | 公开 | — | 缺 |
| 5 | `/agent-shelf` | 智能体区（组二 10 件呈现） | 登录 DID | `/agent-shelf` | 同路径在位 |
| 6 | `/agents` | 智能体集群观测 | 登录 DID | `/agents` | 同路径在位 |
| 7 | `/agents/:id` | 智能体后台 | 公开读（归属人脱敏） | `/agents/:id` | 同路径在位 |
| 8 | `/anchors` | 模拟外部锚与版权事件（P6） | 登录 DID | `/anchors` | 同路径在位 |
| 9 | `/announcements` | 公告栏 | 公开 | `/announcements` | 同路径在位 |
| 10 | `/attestation` | 确权中心总览 | 登录 DID + HUF | `/attestation` | 同路径在位 |
| 11 | `/attestation/dynamic` | 动态确权请求队列 | 登录 DID + HUF | `/attestation/dynamic` | 同路径在位 |
| 12 | `/attestation/history` | 确权历史 | 公开（制度即公开） | `/attestation/history` | 同路径在位 |
| 13 | `/attestation/meta` | 元函数初始确权（出盒终裁） | HUF 强制 | `/attestation/meta` | 同路径在位 |
| 14 | `/audit` | 审计透明 | 公开（制度即公开） | `/audit` | 同路径在位 |
| 15 | `/auth` | 登录（DID） | 公开 | `/auth` | 同路径在位 |
| 16 | `/authorization-registry` | 合约备案（P8b） | 登录 DID（公开查免会话） | `/authorization-registry` | 同路径在位 |
| 17 | `/authorization/panel` | 授权配置面板（C-1） | 登录 DID（起草／签署／撤回须本人；公开查免会话） | — | 缺 |
| 18 | `/channel` | 智能体通道 | 公开 | — | 缺 |
| 19 | `/cluster` | 集群编排与准入闸门（P2） | 登录 DID（登记须法律主体签名） | `/cluster` | 同路径在位 |
| 20 | `/contribute` | 我要贡献 · 三级台阶 | 公开 | — | 缺 |
| 21 | `/curation` | 严选池 · 精选项目一栏 | 公开（匿名可读） | — | 缺 |
| 22 | `/demo` | 体验期与模拟演示 | 公开 | — | 缺 |
| 23 | `/disclosure` | 节点规则披露登记簿 · 公域可查 | 公开（匿名可读 · 只读） | — | 缺 |
| 24 | `/docs` | 文档库 | 公开 | `/docs` | 同路径在位 |
| 25 | `/five-orders` | 五序资产总览 | 公开 | — | 缺 |
| 26 | `/formal` | 形式化与实验线结论入站（P3） | 登录 DID | `/formal` | 同路径在位 |
| 27 | `/governance` | 治理中心 | HUF 强制鉴权（B-4） | `/governance` | 同路径在位 |
| 28 | `/help` | 帮助与联系 | 公开 | — | 缺 |
| 29 | `/lab` | 模拟演练区 | 公开 | — | 缺 |
| 30 | `/library` | 内容区文库（白皮书 · 论文 · 产物库 · 法律原文 · 适用说明） | 法律原文与适用说明匿名可读；其余族登录 DID | `/library` | 同路径在位 |
| 31 | `/market` | 配置权市场（L2） | 公开读 / 调用须 DID | `/market` | 同路径在位 |
| 32 | `/market-sim` | 规范索引与沙盒最小链（P9） | 登录 DID | `/market-sim` | 同路径在位 |
| 33 | `/me` | 个人后台（我的） | 须登录（谁的数据谁可见） | `/me` | 同路径在位 |
| 34 | `/me/appeal` | 申诉 | 须登录（谁的事谁可见） | — | 缺 |
| 35 | `/me/node` | 场景节点管理区（私域三空间） | 须登录（谁的数据谁可见） | — | 缺 |
| 36 | `/me/node/net` | 我的节点 · 条例与契约 | 登录 DID | — | 缺 |
| 37 | `/nca-guide` | 存证（NCA）说明 | 公开 | — | 缺 |
| 38 | `/negativespace` | 负空间 · 什么不能做 | 公开 | — | 缺 |
| 39 | `/nodes` | 节点网络 | 公开 | — | 缺 |
| 40 | `/notifier` | 通知机状态页 | 公开 | `/notifier` | 同路径在位 |
| 41 | `/official-assets` | 官方资产区（官方工具 · 官方产物） | 公开 | — | 缺 |
| 42 | `/ops` | 站点运维端（P7） | 登录 DID（操作须 operator） | `/ops` | 同路径在位 |
| 43 | `/ops/logs` | 运维日志（每日填写） | operator/founder（运维门内） | — | 缺 |
| 44 | `/ops/logs/list` | 运维日志列表 | operator/founder（运维门内） | — | 缺 |
| 45 | `/ops/manual` | 运维手册与制度（点击直接阅读） | operator/founder（运维门内） | — | 缺 |
| 46 | `/ops/me` | 运维我的（站与服务的） | 登录 DID（运维身份；沿运维独立入口 tdca-ops 鉴权） | — | 缺 |
| 47 | `/ownership` | 所有权市场（L1 法定确权层） | 公开读 / 确权操作须 HUF | `/ownership` | 同路径在位 |
| 48 | `/ownership-registry` | 权属登记管理（P8a） | 登录 DID | `/ownership-registry` | 同路径在位 |
| 49 | `/private` | 私域与边界 · 公域守门人 | 公开 | — | 缺 |
| 50 | `/process` | 流程总览（协作流程 14 环） | 公开 | `/process` | 同路径在位 |
| 51 | `/public-face` | 匿名可见面 | 公开 | — | 缺 |
| 52 | `/register` | 注册（人类账号） | 公开 | `/register` | 同路径在位 |
| 53 | `/review` | 评审（缔约审核） | 须登录＋审核身份（写令牌校验） | `/review` | 同路径在位 |
| 54 | `/rules` | 制度地图 | 公开 | — | 缺 |
| 55 | `/sandbox` | 沙盒准入（L2 前置反应釜） | 公开读 / 入盒须 HUF | `/sandbox` | 同路径在位 |
| 56 | `/start` | 新手指引 · 六步上手 TDCA | 公开 | — | 缺 |
| 57 | `/start/three-questions` | 三问向导 · 贡献前自述 | 公开 | — | 缺 |
| 58 | `/status` | 系统健康 | 公开 | — | 缺 |
| 59 | `/studio` | 作业（智能体全生命周期） | 登录 DID + HUF 签批 | `/studio` | 同路径在位 |
| 60 | `/tax` | 税收仪表盘（L3 效用计量） | 公开（只读） | `/tax` | 同路径在位 |
| 61 | `/terms` | 术语检索 | 登录 DID | — | 缺 |
| 62 | `/toolshelf` | 工具货架（P4） | 登录 DID（上架须 operator） | `/toolshelf` | 同路径在位 |
| 63 | `/use/agent` | 代办登记（机器人只跑腿） | 登录 DID（须本人确认，未确认不出号） | — | 缺 |
| 64 | `/use/upload` | 交素材（上传一件） | 登录 DID | — | 缺 |
| 65 | `/verify` | 怎么验证 · 5 分钟三件自查 | 公开 | — | 缺 |
| 66 | `/workbuddy` | 人机协作工作台 | 登录 DID（执行须人类签名） | `/workbuddy` | 同路径在位 |

**汇总**：旧版 66 面；**缺 31 面**（清单见下）；改路径 1 面；同路径/动态段在位 34 面（四要件待实读）。

**缺面清单**：`/academy/outline`、`/authorization/panel`、`/channel`、`/contribute`、`/curation`、`/demo`、`/disclosure`、`/five-orders`、`/help`、`/lab`、`/me/appeal`、`/me/node`、`/me/node/net`、`/nca-guide`、`/negativespace`、`/nodes`、`/official-assets`、`/ops/logs`、`/ops/logs/list`、`/ops/manual`、`/ops/me`、`/private`、`/public-face`、`/rules`、`/start`、`/start/three-questions`、`/status`、`/terms`、`/use/agent`、`/use/upload`、`/verify`

**新版有而旧版无（备查登记，依 PARITY §五.5）**：`/channel/agents`、`/channel/market`、`/channel/portal`、`/channel/registry`、`/channel/tools`、`/overview`、`/pages`、`/registrations`

**注意**：PARITY 判据件所载「旧版 68 面」系含 NotFoundPage(404) 口径；本表按 PAGE_META 实读 66 条，差 1 系 404 页，⛔矛盾。
