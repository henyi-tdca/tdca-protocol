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
  { path: '/academy', title: '知识学院', layer: 'L0', dataSource: 'A-6 + /api/edu/*（bridge）', permission: '公开', description: '商学院教材 + 教学模拟器 + 考核测评（E-EDU 生态）。' },
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
  { path: '/library', title: '内容区文库（白皮书 · 论文 · 产物库 · 制度规范）', layer: 'L0', dataSource: 'A-22 GET /api/v1/library/*（docs 表只读面）', permission: '登录 DID', description: '内容区只读索引＋正文阅读：whitepapers/papers/cop-library/regulations；以在册仓库为唯一权威源。' },
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
  // B5 新增批项一：负空间栏（公域新增，讲「什么不能做」——只讲原则与类别，⛔ 不列禁项词表）
  { path: '/negativespace', title: '负空间 · 什么不能做', layer: 'L0', dataSource: '静态文案（站内审定口径）', permission: '公开', description: 'TDCA 三空间之一：负空间管「什么不能做」——原则与类别级说明，拒绝清单的公众说明面。' },
  // B5 新增批项二：官方资产区（公域新增——工具在上（免费）‧ 产物在下（付费橱窗）；调用未开放态，⛔ 零支付集成）
  { path: '/official-assets', title: '官方资产区（官方工具 · 官方产物）', layer: 'L0', dataSource: '静态文案（站内审定口径）＋ 文库产物库只读面', permission: '公开', description: '官方资源同区并陈：官方工具九类（免费，官智与用户皆可用）在上；官方产物（付费取用，0.01 元/次计价）在下——取用入口暂未开放，仅橱窗与说明面。' },
  // B5 新增批项三：存证（NCA）说明栏（公域新增——为什么存/怎么存/谁都要存；⛔ 栏内不展实际凭据或内部编号）
  { path: '/nca-guide', title: '存证（NCA）说明', layer: 'L0', dataSource: '静态文案（站内审定口径，依在册 NCA 格式标准）', permission: '公开', description: 'NCA 存证格式＝全站唯一标准：每一场景皆存、官方与用户一致、人类与智能体一致——十三字段／带链／义务块六键／合规六条之公众说明面。' },
  // B5 新增批项四：运维「我的」（运维独立站点内 /ops 域新增——六栏只读占位；⛔ 不复用用户 /me 组件、不共路由）
  // 乙案 P2：运维日志表单与列表（TDCA-TPL-OPS-LOG-001-MACHINE 表单化；V-1~V-8 服务端校验）
  { path: '/ops/logs', title: '运维日志（每日填写）', layer: 'L0', dataSource: '/api/v1/ops/logs（POST/GET）＋ /today（红点）', permission: 'operator/founder（运维门内）', description: '六组 A~F 照机读版模板键名；异常三段（发现→处置→闭合）结构化成三格；未闭合必填下一步＋时限；⛔ 不含凭据字段。' },
  { path: '/ops/logs/list', title: '运维日志列表', layer: 'L0', dataSource: '/api/v1/ops/logs（区间）＋ /export（CSV）', permission: 'operator/founder（运维门内）', description: '区间筛选＋行内查看＋导出 CSV（周汇总/月报）；保留 12 个月不删行。' },
  // INACCOUNT-DEPLOY 块 2：手册接口化站内直读（在册七件按角色出件；撤 /ops/files/ 静态门后唯一取件口）
  { path: '/ops/manual', title: '运维手册与制度（点击直接阅读）', layer: 'L0', dataSource: '/api/v1/ops/files（清单＋按名出件）', permission: 'operator/founder（运维门内）', description: '在册七件站内直读：运维手册／运维制度／日志模板／入站留痕制度；白名单防穿越，⛔ 不再输口令。' },
  { path: '/ops/me', title: '运维我的（站与服务的）', layer: 'L0', dataSource: '静态占位（六栏只读；功能面随运维制度分批接通）', permission: '登录 DID（运维身份；沿运维独立入口 tdca-ops 鉴权）', description: '运维管理员的「我的」：管站与服务的事——站务／服务／治理操作／审计与留痕／应急／账户六栏只读占位，与用户「我的」两套独立。' },
  // 二期改版批2块四：评审队列（裁点3 归运维分区，⛔ 不入公共导航；审核人标识＋写令牌只存本次会话）
  { path: '/review', title: '评审（缔约审核）', layer: 'L0', dataSource: '/api/site/join/*（只读队列＋审核写端点）', permission: '须登录＋审核身份（写令牌校验）', description: '缔约申请评审队列：放行／谢绝留痕；每次放行复核敏感词清单，触负即 409 拦截并留痕。' },
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
import { AcademyPage } from './academy'
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
export { DocsIndexPage, DocDetailPage }
import type { ComponentType } from 'react'

export const PAGE_COMPONENTS: Record<string, ComponentType> = {
  '/about': AboutPage,
  '/': HomePage,
  '/ownership': OwnershipPage,
  '/market': MarketPage,
  '/sandbox': SandboxPage,
  '/tax': TaxPage,
  '/academy': AcademyPage,
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
}

export function renderPage(meta: PageMeta) {
  const Page = PAGE_COMPONENTS[meta.path]
  if (Page) return <Page />
  return (
    <PageShell title={meta.title} dataSource={meta.dataSource} permission={meta.permission} description={meta.description} />
  )
}
