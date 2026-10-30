// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-2 15 路由页面元数据（骨架）
// 约束矩阵: FRAMEWORK-001 §四（15 路由表）+ REV-002（确权 4 + 认证 1）
// 预期分配: PAGE_META（path/title/layer/dataSource/permission/description）+ 页面组件表
// =============================================================================
import type { LayerKey } from '@/app/layer-indicator'
import { PageShell } from './PageShell'

export interface PageMeta {
  path: string
  title: string
  layer: LayerKey
  dataSource: string
  permission: string
  description: string
}

/** 15 路由骨架元数据（FRAMEWORK-001 §四；F1~F5 逐阶段接线） */
export const PAGE_META: PageMeta[] = [
  { path: '/about', title: '关于 · 一页看懂 TDCA', layer: 'L0', dataSource: '静态文案（TDCA-PLAIN-001）', permission: '公开', description: '智能体世界的规则、账本与信任——面向普通读者的一页通俗说明。' },
  { path: '/', title: 'TDCA 三体可视化中心', layer: 'L0', dataSource: 'A-1 GET /api/v1/system/overview + /health', permission: '公开', description: '正版门户首页：三体／合规前置三阶／双通道缔约／机器可读通道＋四层架构制度总览区并入。' },
  { path: '/ownership', title: '所有权市场（L1 法定确权层）', layer: 'L1', dataSource: '法定交易中心接口（外部）+ 登记簿只读', permission: '公开读 / 确权操作须 HUF', description: '所有权不得在协议网络内流转：确权路径向导 / 转让 / 登记簿公开查询。' },
  { path: '/market', title: '配置权市场（L2）', layer: 'L2', dataSource: 'A-3 POST /api/v1/config-right/call + A-4 GET /api/v1/assets/five-orders', permission: '公开读 / 调用须 DID', description: '配置权协议化流转市场——使用权/配置权可流转，所有权不流转（防混淆）。' },
  { path: '/sandbox', title: '沙盒准入（L2 前置反应釜）', layer: 'SANDBOX', dataSource: 'A-5 GET /api/v1/sandbox/sea-status + /cross-scene/*', permission: '公开读 / 入盒须 HUF', description: '沙盒 = 制度化学反应釜（CHEM-001~004）：SEA 五要件 + 激活系数 &gt;1.2 验证。' },
  { path: '/tax', title: '税收仪表盘（L3 效用计量）', layer: 'L3', dataSource: 'A-2 GET /api/v1/tax/mou/{agent_id} + WS tax_mou', permission: '公开（只读）', description: '每次调用产生 MOU 税收锚定：计税/预缴/MOU 归零只读看板。' },
  { path: '/academy', title: 'TDCA 商学院', layer: 'L0', dataSource: '静态文案（照贴）', permission: '公开', description: 'TDCA 商学院介绍：学院定位、培养对象、教学方式与课程体系。' },
  { path: '/academy/outline', title: '教材目录（纲要）', layer: 'L0', dataSource: '静态文案（照贴）', permission: '公开', description: '商学院教材目录（纲要）：五卷 35 册编排，正文不入站。' },
  { path: '/audit', title: '审计透明', layer: 'L0', dataSource: 'A-7 GET /api/v1/audit/ledger-public + /nca/chain', permission: '公开（制度即公开）', description: 'NCA 存证链 + 熔断历史 + 哈希审计（宪法第十六条 可观测）。' },
  { path: '/governance', title: '治理中心', layer: 'L0', dataSource: 'A-8 POST /api/v1/governance/huf-sign + emergency-fuse', permission: 'HUF 强制鉴权（B-4）', description: '四大治理操作：HUF 签批 / 动态确权队列 / 紧急熔断 / OTA。' },
  { path: '/agents', title: '智能体集群观测', layer: 'L0', dataSource: 'A-10 + WS handshake + 拓扑（tdca-topology-ui）', permission: '登录 DID', description: '五大智能体面板（Trainer/Executor/Auditor/Service/Genie）+ 确权状态灯 + 协作拓扑。' },
  { path: '/notifier', title: '通知机状态页', layer: 'L0', dataSource: 'A-9 GET /api/v1/notifier/mrcr-status + WS notifier', permission: '公开', description: '物理-数字坐标变换可视化：四角色灯 + MOU 汇总 + DUAL 校验 + 确权请求推送。' },
  { path: '/studio', title: '作业（智能体全生命周期）', layer: 'STUDIO', dataSource: '全生命周期 API + HUF 签批通道', permission: '登录 DID + HUF 签批', description: '智能体全生命周期：诞生→教育→沙盒→出盒终裁（/attestation/meta）→市场→化合衍生。' },
  { path: '/attestation', title: '确权中心总览', layer: 'L0', dataSource: '确权 API（A-11 待补）+ WS attestation', permission: '登录 DID + HUF', description: '待审队列 + 最近事件 + 确权统计（元函数/动态/历史入口）。' },
  { path: '/attestation/meta', title: '元函数初始确权（出盒终裁）', layer: 'L0', dataSource: '确权 API + 沙盒验证报告', permission: 'HUF 强制', description: '沙盒验证后、进入配置权市场前的人类确权（先验证后背书，REV-002 修正）。' },
  { path: '/attestation/dynamic', title: '动态确权请求队列', layer: 'L0', dataSource: '确权 API + WS', permission: '登录 DID + HUF', description: '五类动态确权请求（场景扩展/认知演化/化合授权/负空间逼近/目标修正）紧急度排序。' },
  { path: '/attestation/history', title: '确权历史（NCA 链跨代）', layer: 'L0', dataSource: '确权 API', permission: '公开（制度即公开）', description: 'Meta-Attestation-NCA 跨代追溯 + 拒绝事件高亮 + 延迟分析。' },
  { path: '/auth', title: '登录（DID）', layer: 'L0', dataSource: 'B-4 鉴权中间件（TDCA_GATEWAY_AUTH=1 启用时强制）', permission: '公开', description: '统一 DID 认证入口（F-2 落地）：token 持有 + 受保护路由守卫。' },
  { path: '/register', title: '注册（人类账号）', layer: 'L0', dataSource: 'M4 POST /api/v1/auth/register', permission: '公开', description: '注册即 viewer 只读账号（人机面）；注册存证落 NCA 链，成功自动登录进个人后台。' },
  { path: '/me', title: '个人后台（我的）', layer: 'L0', dataSource: 'M5 GET /api/v1/me/dashboard', permission: '须登录（谁的数据谁可见）', description: '我的智能体 / 签批待办 / 我批过的 / 沙盒申请 / 治理操作，一屏聚合。' },
  { path: '/agents/:id', title: '智能体后台', layer: 'L0', dataSource: 'M5 GET /api/v1/agents/{id}/dashboard', permission: '公开读（归属人脱敏）', description: '每一只智能体的画像 / MOU 计量 / 税单 / 签章记录 / NCA 存证，一页看全。' },
  { path: '/workbuddy', title: '人机协作工作台', layer: 'L0', dataSource: 'A-12 /api/v1/workbuddy/*（P5 引擎 + DB 持久化 + NCA 落链）', permission: '登录 DID（执行须人类签名）', description: '跨场景工作流：创建 → 签名门禁执行 → 状态/NCA 全链可查；智能体不得代签。' },
  { path: '/cluster', title: '集群编排与准入闸门（P2）', layer: 'L0', dataSource: 'A-13 /api/v1/cluster/*（授权件四要件机验 + 谱系账本）', permission: '登录 DID（登记须法律主体签名）', description: '授权件登记与多层转授链；配置类调用须凭有效授权件——可信联通 ≠ 可信协作，仅握手不成立。' },
  { path: '/formal', title: '形式化与实验线结论入站（P3）', layer: 'L0', dataSource: 'A-14 /api/v1/formal/*（只做结论面）', permission: '登录 DID', description: '只收结论面：不转公式、不引数值、不带内部编号；数据性质显式标注；入站 ≠ 入主仓 ≠ 对外。' },
  { path: '/toolshelf', title: '工具货架（P4）', layer: 'L0', dataSource: 'A-15 /api/v1/toolshelf/*（工具/模板目录）', permission: '登录 DID（上架须 operator）', description: '站内工具与模板目录：编译器、适配器等；配置类工具须凭授权件过准入闸门。' },
  { path: '/anchors', title: '模拟外部锚与版权事件（P6）', layer: 'L0', dataSource: 'A-17 /api/v1/anchor/*（三锚 SIMULATED；事件落 NCA 链）', permission: '登录 DID', description: '版权链（NCA 链）／结算（站内积分）／税务（金税四期功能）全站内模拟；版权事件＝登记／变更／注销。' },
  { path: '/ops', title: '站点运维端（P7）', layer: 'L0', dataSource: 'A-18 /api/v1/ops/*（红线八项分类器；NCA 存证＋对账）', permission: '登录 DID（操作须 operator）', description: '应用测试期运维工作台：反馈→红线分类→提案→沙盒→上线；触碰根本制度即升 DCD，运维端无权处置。' },
  { path: '/ownership-registry', title: '权属登记管理（P8a）', layer: 'L0', dataSource: 'A-19 /api/v1/ownership/*（登记／变更／注销／查询）', permission: '登录 DID', description: '登记二分之权属侧：凡具表达形式者皆可登记；须载生成来源谱系；场景非必须；法域四支仅索引；四条不公开负空间 fail-closed。' },
  { path: '/market-sim', title: '规范索引与沙盒最小链（P9）', layer: 'L0', dataSource: 'A-20 /api/v1/regulations/* + A-21 /api/v1/market-sim/*', permission: '登录 DID', description: '规范索引入口（版本读件内不硬编码）＋最小链：发布→准入→撮合→结算，全程 SIMULATED，NCA 全链留痕。' },
  { path: '/library', title: '内容区文库（白皮书 · 论文 · 产物库 · 制度规范 · 法律原文 · 适用说明）', layer: 'L0', dataSource: 'A-22 GET /api/v1/library/*（docs 表只读面）', permission: '法律原文与适用说明匿名可读；其余族登录 DID', description: '内容区只读索引＋正文阅读：whitepapers/papers/cop-library/regulations/laws/law-notes；以在册仓库为唯一权威源。' },
  { path: '/agent-shelf', title: '智能体区（组二 10 件呈现）', layer: 'L0', dataSource: '静态呈现面（呈现 ≠ 注册）', permission: '登录 DID', description: '组二 10 件以智能体形态呈现：每条只列名称／一句用途／形态；注册与准入另走在册流程，本区不代办。' },
  { path: '/announcements', title: '公告栏', layer: 'L0', dataSource: 'A-23 GET /api/v1/announcements/list（公开读）', permission: '公开', description: '站点对外公告区：公告内容经创始人明示后由运营发布；空栏为常态，不预置内容。' },
  { path: '/authorization-registry', title: '授权登记管理（P8b）', layer: 'L0', dataSource: 'A-24 /api/v1/authorization/*（登记／变更／注销／查询／操作＋公开查）', permission: '登录 DID（公开查免会话）', description: '登记二分之授权侧：四要件缺一即拒；签名须本人、智能体不代持代填；公开面四字段；四条不公开负空间 fail-closed。' },
  // 二期改版批2块一：公域顶栏第六入口「帮助与联系」——薄占位，内容随文档库「帮助」族入站（块二），联系块同批补入
  { path: '/help', title: '帮助与联系', layer: 'L0', dataSource: '静态占位（帮助族入站前）', permission: '公开', description: '站点帮助与官方联系入口。帮助内容随文档库「帮助」族入站（块二）；论坛暂不落栏，先定位。' },
  // 二期改版批2块二：文档库（裁点2终定：与文库并存，⛔ 不并线——端点不同、族不同）
  { path: '/docs', title: '文档库', layer: 'L0', dataSource: 'GET /api/site/docs/{family}（只读面）', permission: '公开', description: '制度／帮助二族：文档库＝怎么做；理论／白皮书等走知识库（/library）。' },
  // 二期改版批2块三：流程总览（tdca-site ProcessOverview 移植，⛔ 不改语义零内部编号）
  { path: '/process', title: '流程总览（协作流程 14 环）', layer: 'L0', dataSource: '静态文案（站内审定口径）', permission: '公开', description: '14 环逐环四能（是什么／如何行动／规则／后果）；承办呈现面＝站内已有服务/频道名，如实标注。' },
  // 二期改版批2块三：申诉端薄占位（无令载细则，⛔ 不编造受理表单/渠道；受理面随制度入站开通）
  { path: '/me/appeal', title: '申诉', layer: 'L0', dataSource: '—（受理面在建）', permission: '须登录（谁的事谁可见）', description: '惩罚三态申诉受理面：受理通道随制度入站开通，开通前不预置表单与渠道。' },
  // L1SI178-SITE-PRIVATE-ZONE-002（甲案）：私域三空间独立页 /me/node（⛔ 不入公共导航；/me 内挂入口链接）＋公域披露页 /disclosure（匿名可查）
  { path: '/me/node', title: '场景节点管理区（私域三空间）', layer: 'L0', dataSource: '纯前端样例态（页内状态）；零接口调用、零后端写入', permission: '须登录（谁的数据谁可见）', description: '私域三空间：负空间／沙盒出盒／正空间；不披露不可启用；六项硬核只读锁定；示例节点与条目均为虚构样例。' },
  { path: '/disclosure', title: '规则披露公示 · 按节点查阅', layer: 'L0', dataSource: '纯前端样例态（虚构示例条目）；零接口调用', permission: '公开（匿名可读）', description: '私域条目的对外披露面：匿名可查、无需登录，含版本历史；公示才公信。' },
  // B5 新增批项一：负空间栏（公域新增，讲「什么不能做」——只讲原则与类别，⛔ 不列禁项词表）
  { path: '/negativespace', title: '负空间 · 什么不能做', layer: 'L0', dataSource: '静态文案（站内审定口径）', permission: '公开', description: 'TDCA 三空间之一：负空间管「什么不能做」——原则与类别级说明，拒绝清单的公众说明面。' },
  // B5 新增批项二：官方资产区（公域新增——工具在上（免费）‧ 产物在下（付费橱窗）；调用未开放态，⛔ 零支付集成）
  { path: '/official-assets', title: '官方资产区（官方工具 · 官方产物）', layer: 'L0', dataSource: '静态文案（站内审定口径）＋ 文库产物库只读面', permission: '公开', description: '官方资源同区并陈：官方工具九类（免费，官智与用户皆可用）在上；官方产物（付费取用，0.01 元/次计价）在下——取用入口暂未开放，仅橱窗与说明面。' },
  // B5 新增批项三：存证（NCA）说明栏（公域新增——为什么存/怎么存/谁都要存；⛔ 栏内不展实际凭据或内部编号）
  { path: '/nca-guide', title: '存证（NCA）说明', layer: 'L0', dataSource: '静态文案（站内审定口径，依在册 NCA 格式标准）', permission: '公开', description: 'NCA 存证格式＝全站唯一标准：每一场景皆存、官方与用户一致、人类与智能体一致——十三字段／带链／义务块六键／合规六条之公众说明面。' },
  // B5 新增批项四：运维「我的」（运维独立站点内 /ops 域新增——六栏只读占位；⛔ 不复用用户 /me 组件、不共路由）
  // 乙案 P2：运维日志表单与列表（TDCA-TPL-OPS-LOG-001-MACHINE 表单化；V-1~V-8 服务端校验）
  { path: '/ops/logs', title: '运维日志（每日填写）', layer: 'L0', dataSource: '/api/v1/ops/logs（POST/GET）＋ /today（红点）', permission: 'operator/founder（运维门内）', description: '六组 A~F 照机读版模板键名；异常三段（发现→处置→闭合）结构化成三格；未闭合必填下一步＋时限；不含凭据字段。' },
  { path: '/ops/logs/list', title: '运维日志列表', layer: 'L0', dataSource: '/api/v1/ops/logs（区间）＋ /export（CSV）', permission: 'operator/founder（运维门内）', description: '区间筛选＋行内查看＋导出 CSV（周汇总/月报）；保留 12 个月不删行。' },
  // INACCOUNT-DEPLOY 块 2：手册接口化站内直读（在册七件按角色出件；撤 /ops/files/ 静态门后唯一取件口）
  { path: '/ops/manual', title: '运维手册与制度（点击直接阅读）', layer: 'L0', dataSource: '/api/v1/ops/files（清单＋按名出件）', permission: 'operator/founder（运维门内）', description: '在册七件站内直读：运维手册／运维制度／日志模板／入站留痕制度；白名单防穿越，不再输口令。' },
  { path: '/ops/me', title: '运维我的（站与服务的）', layer: 'L0', dataSource: '静态占位（六栏只读；功能面随运维制度分批接通）', permission: '登录 DID（运维身份；沿运维独立入口 tdca-ops 鉴权）', description: '运维管理员的「我的」：管站与服务的事——站务／服务／治理操作／审计与留痕／应急／账户六栏只读占位，与用户「我的」两套独立。' },
  // 二期改版批2块四：评审队列（裁点3 归运维分区，⛔ 不入公共导航；审核人标识＋写令牌只存本次会话）
  { path: '/review', title: '评审（缔约审核）', layer: 'L0', dataSource: '/api/site/join/*（只读队列＋审核写端点）', permission: '须登录＋审核身份（写令牌校验）', description: '缔约申请评审队列：放行／谢绝留痕；每次放行复核敏感词清单，触负即 409 拦截并留痕。' },
  // L1SI162-RULES-MAP-001：制度地图（56 件五类五态六步·页面与检索共读随件机读表 V6.1·0C0FE95560264A8E）
  { path: '/rules', title: '制度地图', layer: 'L0', dataSource: '机读表 _DOC-MAP-RULES-20261021-V6.1-FINAL（仓内单源·?raw 进包）', permission: '公开', description: '56 件制度件按五类分组、五态如实标、S1~S6 六步导航；历史草案折入折叠区，以生效版为准。' },
  // L1SI163-START-001：新手指引（六步＋目录筛四维＋147 术语检索·页面与检索共读 _START-MAP-20261021-V1·0CE5C89A957B6B60）
  { path: '/start', title: '新手指引 · 六步上手 TDCA', layer: 'L0', dataSource: '_START-MAP 三表（单一事实源·仓内单源 ?raw 进包）', permission: '公开', description: 'S1~S6 六步了解 TDCA：每步挂接该步制度件，缺口步如实标「待补」；目录四维筛选与 147 条术语检索同读 _START-MAP 三表。' },
  // L1SI175-B1 S1-5：怎么验证常设页（三件自查全路径，匿名面）
  { path: '/verify', title: '怎么验证 · 5 分钟三件自查', layer: 'L0', dataSource: '匿名只读三件：/api/v1/audit/ledger-public ＋ /api/v1/ci/badge ＋ /api/v1/formal/conclusion/catalog', permission: '公开', description: '不注册 5 分钟三件自查全路径：公开账本 → 机验徽章 → 形式化清单；三个端点匿名只读，任何第三方可复算。' },
  // L1SI175-A1-2：术语检索页（登录可见；服务端 ?q= 过滤；⛔ 匿名开放未授权）
  { path: '/terms', title: '术语检索', layer: 'L0', dataSource: 'A-6 GET /api/v1/knowledge/terms?q=（服务端过滤）', permission: '登录 DID', description: '站内术语注册表检索：词与释义两列，关键词走服务端过滤；登录可见全量，匿名返回已脱敏内部编号。' },
  { path: '/assets', title: '五序资产总览', layer: 'L0', dataSource: 'GET /api/v1/assets/five-orders（DB 实读）', permission: '公开', description: '五序资产池总览：名称、说明与在册数量；真实资产待生态接入，只读展示，不含交易入口。' },
  { path: '/status', title: '系统健康', layer: 'L0', dataSource: 'GET /api/v1/system/overview ＋ /api/v1/ci/badge ＋ /api/v1/eios/cluster-status', permission: '公开', description: '运行指标、机验徽章与集群状态三合一健康面；模块状态以「已冻结」呈现，税率仅为在册演示值。' },
  { path: '/start/three-questions', title: '三问向导 · 贡献前自述', layer: 'L0', dataSource: '纯前端表单（零接口调用）；提交功能待后端就绪', permission: '公开', description: '交素材前的三问：原创吗／用过 AI 吗／用在什么场景。系统只汇总成自述草稿，⛔ 代判；提交功能在建，如实标注。' },
  { path: '/contribute', title: '我要贡献 · 三级台阶', layer: 'L0', dataSource: '纯前端指路页（零接口调用）；指向既有登记端点', permission: '公开', description: 'viewer→贡献者→节点方三级台阶：每阶写什么件、走哪条路、什么算成。只指路不代办，⛔ 承诺时限必过。' },
  { path: '/private', title: '私域与边界 · 公域守门人', layer: 'L0', dataSource: '纯前端说明页（零接口调用）；口径与体系结构说明一致', permission: '公开', description: '公域与私域的分工、两权闸门、三条铁句；起一个节点之前先读这页。' },
  { path: '/demo', title: '体验期与模拟演示', layer: 'L0', dataSource: '纯前端演示值（页内状态）；零接口调用、零后端写入', permission: '公开', description: '四块模拟（虚拟积分／钱包／结算中心／交付税收）＋免责三条；全部演示值，真实功能在三期。' },
  { path: '/lab', title: '模拟演练区', layer: 'L0', dataSource: '纯前端演练值（页内状态）；零接口调用、零后端写入', permission: '公开', description: '与 /demo 分工：demo 看懂、lab 走一遍。五张模拟卡＋一张流水表；积分面额照设计件 6146，演练值不入账、不留存。' },
  // NODE-NET-A-001 私域两卡（⛔ 不动三空间与六项硬核——另立须登录面）
  { path: '/me/node/net', title: '我的节点 · 条例与契约', layer: 'L0', dataSource: '在册条例 V1.0 与本机节点配置（配置未设处如实标「未设置／待复算」）', permission: '登录 DID', description: '私域节点面：卡一「我的节点」只读本人配置（无真值如实标）；卡二「条例与契约」挂在册条例与九类接口清单。' },
  // NODE-NET-A-001 公域四块（可视图只画已披露真节点·状态以最后心跳与截至时刻为准）
  { path: '/nodes', title: '节点网络', layer: 'L0', dataSource: '在册条例 V1.0 与节点现状（真值缺失处如实标「未设置／待复算／尚无」）', permission: '公开', description: '业务端节点接入公开面：可视图只画已披露真节点；状态栏只给最后心跳与数据截至时刻；接口未实现一律不开放。' },
  // L1SI181-USE-U1-001 U-1c：朴素上传页（⛔ 拖拽/进度/多语言/批量；文件＋文件名头直传报文）
  { path: '/use/upload', title: '交素材（上传一件）', layer: 'L0', dataSource: 'POST /api/v1/use/upload ＋ GET /api/v1/use/upload/{id}', permission: '登录 DID', description: '登录后交一件素材：选择文件上传，系统回收件编号与哈希；受理清单内收、清单外给人话理由；同一人传同一文件只留一条（幂等）。' },
  // L1SI182-USE-U2-001 U-2 代办机器人（五步：收件→只问缺项→草稿→本人在场签→出号；复用上传与权属登记端点，草稿仅本地态不落库）
  { path: '/use/agent', title: '代办登记（机器人只跑腿）', layer: 'L0', dataSource: 'GET /api/v1/use/upload/{id} ＋ POST /api/v1/ownership/register（OR- 号沿用）', permission: '登录 DID（须本人确认，未确认不出号）', description: '上传成功后接着办登记：机器人只问缺项、出草稿（不落库不出号）；本人看过草稿、显式点确认才出登记号；机器人不代签、不代判、不对外承诺。' },
]

export const ROUTE_PATHS = PAGE_META.map((m) => m.path)

export function NotFoundPage() {
  return (
    <PageShell
      title="404 · 路由未找到"
      dataSource="—"
      permission="公开"
      description="未知路由 404 兜底（hash 路由）。请从导航选择有效页面。"
    />
  )
}

// F1 页面组件分发（PAGE_META 元数据 + 具体页面内容）
import { AboutPage } from './about'
import { HomePage } from './home'
import { OwnershipPage } from './ownership'
import { MarketPage } from './market'
import { SandboxPage } from './sandbox'
import { TaxPage } from './tax'
// L1SI152-EDU-PORTAL-001：商学院栏目两页（介绍＋教材目录，原文照贴件）；AcademyPage（术语检索）组件保留在册、本栏改指后不再路由
import { BizSchoolIntroPage, BizSchoolOutlinePage } from './academy/biz-school'
import { AuditPage } from './audit'
import { GovernancePage } from './governance'
import { AgentsPage } from './agents'
import { StudioPage } from './studio'
import { NotifierPage } from './notifier'
import { AttestationOverviewPage, AttestationMetaPage, AttestationDynamicPage, AttestationHistoryPage } from './attestation'
import { AuthPage } from './auth'
import { MePage } from './me'
import { RegisterPage } from './register'
import { AgentDashboardPage } from './agent-dashboard'
import { WorkbuddyPage } from './workbuddy'
import { ClusterPage } from './cluster'
import { FormalPage } from './formal'
import { ToolshelfPage } from './toolshelf'
import { AnchorsPage } from './anchors'
import { OpsPage } from './ops'
import { OwnershipRegistryPage } from './ownership-registry'
import { MarketSimPage } from './market-sim'
import { LibraryPage } from './library'
import { AgentShelfPage } from './agent-shelf'
import { AnnouncementsPage } from './announcements'
import { AuthorizationRegistryPage } from './authorization-registry'
import { HelpPage } from './help'
import { DocsHomePage, DocsIndexPage, DocDetailPage } from './docs'
import { ProcessOverviewPage } from './process'
import { NegativeSpacePage } from './negativespace'
import { OfficialAssetsPage } from './official-assets'
import { NcaGuidePage } from './nca-guide'
import { OpsMePage } from './ops-me'
import { OpsLogsPage } from './ops-logs'
import { OpsLogsListPage } from './ops-logs-list'
import { OpsManualPage } from './ops-manual'
import { MeAppealPage } from './me-appeal'
import { ReviewPage } from './review'
// L1SI162-RULES-MAP-001：制度地图 /rules（五类五态六步·机读表单一源）
import { RulesMapPage } from './rules/rules'
// L1SI163-START-001：新手指引 /start（六步＋检索批3·_START-MAP 单一事实源）
import { StartPage } from './start/start'
// L1SI175-B1 S1-5：怎么验证 /verify（三件自查全路径·匿名面）
import { VerifyPage } from './verify'
// L1SI175-A1-2：术语检索 /terms（登录可见·服务端 ?q= 过滤）
import { TermsPage } from './terms'
// L1SI175-B1-1/2/3：五序资产 /assets＋系统健康 /status（匿名可见·集群并入）
import { AssetsPage } from './assets'
import { StatusPage } from './status'
// L1SI175-B2 前三包（6182 拆批裁定·6183 施工令）：三问向导／我要贡献／私域与边界（纯前端）
import { ThreeQuestionsPage } from './three-questions'
import { ContributePage } from './contribute'
import { PrivateDomainPage } from './private-domain'
// L1SI175-B25（6188 拆解裁定·6189 施工令）：体验期与模拟演示一页（四块模拟·纯前端演示值）
import { DemoPage } from './demo'
// L1SI175-B26（6194 拆批裁定·施工令）：模拟演练区一页（五卡＋流水表·纯前端演练值）
import { LabPage } from './lab'
// L1SI178-SITE-PRIVATE-ZONE-002（甲案）：私域三空间 /me/node＋公域披露页 /disclosure
import { MeNodePage } from './me-node'
import { NodeDisclosurePage } from './node-disclosure'
// NODE-NET-A-001：私域两卡 /me/node/net＋公域四块 /nodes（三处同源 node-net-data.ts）
import { MeNodeNetPage } from './me-node-net'
import { NodeNetPage } from './node-net'
// L1SI181-USE-U1-001 U-1c：朴素上传页（⛔ 拖拽/进度/多语言/批量）
import { UseUploadPage } from './use-upload'
import { UseAgentPage } from './use-agent'
export { DocsIndexPage, DocDetailPage }
import type { ComponentType } from 'react'

export const PAGE_COMPONENTS: Record<string, ComponentType> = {
  '/about': AboutPage,
  '/': HomePage,
  '/ownership': OwnershipPage,
  '/market': MarketPage,
  '/sandbox': SandboxPage,
  '/tax': TaxPage,
  '/academy': BizSchoolIntroPage,
  '/academy/outline': BizSchoolOutlinePage,
  '/audit': AuditPage,
  '/governance': GovernancePage,
  '/agents': AgentsPage,
  '/studio': StudioPage,
  '/notifier': NotifierPage,
  '/attestation': AttestationOverviewPage,
  '/attestation/meta': AttestationMetaPage,
  '/attestation/dynamic': AttestationDynamicPage,
  '/attestation/history': AttestationHistoryPage,
  '/auth': AuthPage,
  '/register': RegisterPage,
  '/me': MePage,
  '/agents/:id': AgentDashboardPage,
  '/workbuddy': WorkbuddyPage,
  '/cluster': ClusterPage,
  '/formal': FormalPage,
  '/toolshelf': ToolshelfPage,
  '/anchors': AnchorsPage,
  '/ops': OpsPage,
  '/ownership-registry': OwnershipRegistryPage,
  '/market-sim': MarketSimPage,
  '/library': LibraryPage,
  '/agent-shelf': AgentShelfPage,
  '/announcements': AnnouncementsPage,
  '/authorization-registry': AuthorizationRegistryPage,
  '/help': HelpPage,
  '/docs': DocsHomePage,
  '/process': ProcessOverviewPage,
  '/negativespace': NegativeSpacePage,
  '/official-assets': OfficialAssetsPage,
  '/nca-guide': NcaGuidePage,
  '/ops/me': OpsMePage,
  '/ops/logs': OpsLogsPage,
  '/ops/logs/list': OpsLogsListPage,
  '/ops/manual': OpsManualPage,
  '/me/appeal': MeAppealPage,
  '/review': ReviewPage,
  '/rules': RulesMapPage,
  '/start': StartPage,
  '/verify': VerifyPage,
  '/terms': TermsPage,
  '/assets': AssetsPage,
  '/status': StatusPage,
  '/start/three-questions': ThreeQuestionsPage,
  '/contribute': ContributePage,
  '/private': PrivateDomainPage,
  '/demo': DemoPage,
  '/lab': LabPage,
  '/me/node': MeNodePage,
  '/disclosure': NodeDisclosurePage,
  '/me/node/net': MeNodeNetPage,
  '/nodes': NodeNetPage,
  '/use/upload': UseUploadPage,
  '/use/agent': UseAgentPage,
}

export function renderPage(meta: PageMeta) {
  const Page = PAGE_COMPONENTS[meta.path]
  if (Page) return <Page />
  return (
    <PageShell title={meta.title} dataSource={meta.dataSource} permission={meta.permission} description={meta.description} />
  )
}
