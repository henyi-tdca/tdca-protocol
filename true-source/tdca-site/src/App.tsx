import { Routes, Route } from 'react-router'
import Home from './pages/Home'
import DocsHome, { DocsIndex, DocDetail } from './pages/Docs'
import Review from './pages/Review'
// FRONTEND-MERGE 批1（骨架与门户）：旧版 home/about/pages/announcements 四面迁入
import { OverviewPage } from './pages/Overview'
import { AboutPage } from './pages/About'
import { PagesIndexPage, NotFoundPage } from './pages/PagesIndex'
import { AnnouncementsPage } from './pages/Announcements'
// FRONTEND-MERGE 批2（身份与缔约）：register/auth/me 三面迁入＋AuthProvider 最小接线
import { AuthProvider } from './lib/auth-context'
import { RegisterPage } from './pages/Register'
import { AuthPage } from './pages/AuthLogin'
import { MePage } from './pages/MeConsole'
import { MeAppealPage } from './pages/MeAppealPage'
import { MainChainGuide } from './pages/MainChainGuide'
// FRONTEND-MERGE 批3（智能体面）：agents/agent-dashboard/agent-shelf/studio/workbuddy 五面迁入
import { AgentsPage } from './pages/AgentsCluster'
import { AgentDashboardPage } from './pages/AgentDashboard'
import { AgentShelfPage } from './pages/AgentShelfPage'
import { StudioPage } from './pages/StudioPage'
import { WorkbuddyPage } from './pages/WorkbuddyPage'
// FRONTEND-MERGE 批4（登记与存证面）：五面迁入（attestation 一件四面 → 四路）
import { OwnershipPage } from './pages/OwnershipPage'
import { OwnershipRegistryPage } from './pages/OwnershipRegistryPage'
import { AuthorizationRegistryPage } from './pages/AuthorizationRegistryPage'
import { AttestationOverviewPage, AttestationMetaPage, AttestationDynamicPage, AttestationHistoryPage } from './pages/AttestationPage'
import { AnchorsPage } from './pages/AnchorsPage'
import { AuditPage } from './pages/AuditPage'
import { GovernancePage } from './pages/GovernancePage'
import { FormalPage } from './pages/FormalPage'
import { ClusterPage } from './pages/ClusterPage'
import { MarketPage } from './pages/MarketPage'
import { MarketSimPage } from './pages/MarketSimPage'
import { TaxPage } from './pages/TaxPage'
import { LibraryPage } from './pages/LibraryPage'
import { AcademyPage } from './pages/AcademyPage'
import { ToolshelfPage } from './pages/ToolshelfPage'
import { NotifierPage } from './pages/NotifierPage'
import { SandboxPage } from './pages/SandboxPage'
// 用组批（L1SI206-USE-GROUP-B1）：「用」组两面迁入（U-1 交素材＋U-2 代办登记，旧版权直拷·接缝仅适配）；
// 两面为登录动作面——照 /auth /register 动作页豁免口径 ⛔ 入栏目检索索引（脚本 COLUMN_EXCLUDE 同步）
// 追平批B1（L1SI206-PARITY-B1）：制度地图／帮助与联系／负空间／教材目录四面迁入（旧版权直拷·公开栏目面）
import { RulesMapPage } from './pages/rules/rules'
import { HelpPage } from './pages/HelpPage'
import { NegativeSpacePage } from './pages/NegativeSpacePage'
import { AcademyOutlinePage } from './pages/academy/AcademyOutlinePage'
// 追平批B2（L1SI206-PARITY-B2）：五序资产／官方资产／系统健康／术语检索四面＋运维日志两件（旧版权直拷·接缝仅适配）
// 四面为公开栏目面入索引；ops/logs 两件为运维私域面——⛔ 入栏目检索索引
import { FiveOrdersPage } from './pages/FiveOrdersPage'
import { OfficialAssetsPage } from './pages/OfficialAssetsPage'
import { StatusPage } from './pages/StatusPage'
import { TermsPage } from './pages/TermsPage'
import { OpsLogsPage } from './pages/OpsLogsPage'
import { OpsLogsListPage } from './pages/OpsLogsListPage'
// 追平批B3（L1SI206-PARITY-B3）：授权配置面板（受护）／三问向导／运维我的 三件直拷＋RequireAuth 最小守卫
// （授权面板与 ops/me 为私域/受护面 ⛔ 入公域栏目索引；三问向导公开入册）
import { AuthorizationPanelPage } from './pages/AuthorizationPanelPage'
import { ThreeQuestionsPage } from './pages/ThreeQuestionsPage'
import { OpsMePage } from './pages/OpsMePage'
import { RequireAuth } from './components/RequireAuth'
import { UseUploadPage } from './pages/use/UseUploadPage'
import { UseAgentPage } from './pages/use/UseAgentPage'
import { OpsPage } from './pages/OpsPage'
// MIGRATE 批5（L1SI206）：运维手册三界面（README/OPS/CHANGELOG）——运维私域内路由（须鉴权取件）；
// ⛔ 不入公开导航／⛔ 不入检索索引（索引唯一权威源＝public_docs_ops.py 在册公开清单，本批未动）
import { OpsReadmePage } from './pages/OpsReadmePage'
import { OpsOpsPage } from './pages/OpsOpsPage'
import { OpsChangelogPage } from './pages/OpsChangelogPage'
// MIGRATE 批6（L1SI206）：入门与指南四件（同栈直拷·start-map.yaml 数据件原字节随批·公开面入册）
import { StartPage } from './pages/start/start'
import { NcaGuidePage } from './pages/NcaGuidePage'
// 批 2 骨架：全局壳（两轴）＋频道首页五件——仅加包裹层与新路由，现有路径不动
import { SiteLayout } from './components/SiteLayout'
import { ChannelHome } from './pages/ChannelHome'
// 批 3：协作流程汇总页（/process）——新增路由，现有路径不动
import { ProcessOverviewPage } from './pages/ProcessOverview'
// REGISTRY-PAGE-001：公域登记查询页（/registrations——匿名只读公域区，新增路由，现有路径不动）
import { RegistrationsPage } from './pages/RegistrationsPage'
// MIGRATE 批1：全站检索页（/search——检索整块迁产线，新增路由，现有路径不动）
import { SearchPage } from './pages/SearchPage'
// MIGRATE 批2：智能体通道两面迁入（我的通道＋通道登记，新增路由，现有路径不动；
// 登记面改挂 /channel/register——旧路 /channel/registry 在新版已居「登记与存证」频道首页，⛔ 动他面）
import { ChannelMyPage } from './pages/ChannelMy'
import { AgentChannelRegisterPage } from './pages/AgentChannelRegister'
// MIGRATE 批3（L1SI206）：严选与节点八面 ＋ 补 /channel 总入口（批2 令面漏项补做，九面新增路由，
// 现有路径不动；权限字段照 route-parity.md 原栏——私域两面由 API 层 401/403 fail-closed 把守）
import { ChannelPortalPage } from './pages/ChannelPortal'
import { CurationPoolPage } from './pages/Curation'
import { ContributePage } from './pages/Contribute'
import { PublicFacePage } from './pages/PublicFace'
import { PrivateDomainPage } from './pages/PrivateDomain'
import { NodeNetPage } from './pages/NodeNet'
import { MeNodePage } from './pages/MeNode'
import { MeNodeNetPage } from './pages/MeNodeNet'
import { NodeDisclosurePage } from './pages/NodeDisclosure'
import { LabPage } from './pages/Lab'
import { DemoPage } from './pages/Demo'

export default function App() {
  return (
    <AuthProvider>
      <SiteLayout>
      <Routes>
        {/* MIGRATE 批7：主链导轨挂载（主链八环在册实路由） */}
        {/* 追平批B3（PARITY-B3-001 §二#5）：/five-orders＝主链第二环「五序资产」补挂导轨；
            「新版尚无路由，⛔不挂」之旧注记已失效（该面批B2 已迁入），本件更替 */}
        <Route path="/" element={<><MainChainGuide /><Home /></>} />
        {/* 批 2：频道首页五路（新增，不改现有路径） */}
        <Route path="/channel/portal" element={<ChannelHome channel="portal" />} />
        <Route path="/channel/agents" element={<ChannelHome channel="agents" />} />
        <Route path="/channel/registry" element={<ChannelHome channel="registry" />} />
        <Route path="/channel/market" element={<ChannelHome channel="market" />} />
        <Route path="/channel/tools" element={<ChannelHome channel="tools" />} />
        {/* 批 3：协作流程汇总页（新增，不改现有路径） */}
        <Route path="/process" element={<ProcessOverviewPage />} />
        {/* REGISTRY-PAGE-001：公域登记查询（匿名只读；零新后端，三端点全匿名 GET） */}
        <Route path="/registrations" element={<RegistrationsPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/me" element={<MePage />} />
        {/* MIGRATE 批7：申诉面（旧版权 me-appeal 直拷，受理通道随制度入站开通） */}
        <Route path="/me/appeal" element={<MeAppealPage />} />
        <Route path="/review" element={<Review />} />
        <Route path="/docs" element={<DocsHome />} />
        <Route path="/docs/:family" element={<DocsIndex />} />
        <Route path="/docs/:family/:slug" element={<DocDetail />} />
        {/* MIGRATE 批1：全站检索（静态索引＋本地排序，无后端） */}
        <Route path="/search" element={<SearchPage />} />
        {/* MIGRATE 批2：智能体通道两面（私域门槛由 API 层 401/403 fail-closed 把守，照批3核可口径直挂） */}
        <Route path="/channel/my" element={<ChannelMyPage />} />
        <Route path="/channel/register" element={<AgentChannelRegisterPage />} />
        {/* MIGRATE 批3：/channel 总入口（批2 漏项补做）＋严选与节点八面（九面新增） */}
        <Route path="/channel" element={<><MainChainGuide /><ChannelPortalPage /></>} />
        <Route path="/curation" element={<CurationPoolPage />} />
        <Route path="/contribute" element={<ContributePage />} />
        <Route path="/public-face" element={<PublicFacePage />} />
        <Route path="/private" element={<PrivateDomainPage />} />
        <Route path="/nodes" element={<NodeNetPage />} />
        <Route path="/me/node" element={<MeNodePage />} />
        <Route path="/me/node/net" element={<MeNodeNetPage />} />
        <Route path="/disclosure" element={<NodeDisclosurePage />} />
        <Route path="/overview" element={<OverviewPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/pages" element={<PagesIndexPage />} />
        <Route path="/announcements" element={<AnnouncementsPage />} />
        {/* FRONTEND-MERGE 批3：智能体面五路（路由照存；不设登录门槛——照本批核可口径） */}
        <Route path="/agents" element={<><MainChainGuide /><AgentsPage /></>} />
        <Route path="/agents/:id" element={<AgentDashboardPage />} />
        <Route path="/agent-shelf" element={<AgentShelfPage />} />
        <Route path="/studio" element={<StudioPage />} />
        <Route path="/workbuddy" element={<WorkbuddyPage />} />
        {/* FRONTEND-MERGE 批4：登记与存证面八路（attestation 一件四面 → 四路；照复核件更正补 /anchors） */}
        <Route path="/ownership" element={<OwnershipPage />} />
        <Route path="/ownership-registry" element={<OwnershipRegistryPage />} />
        <Route path="/authorization-registry" element={<><MainChainGuide /><AuthorizationRegistryPage /></>} />
        <Route path="/attestation" element={<><MainChainGuide /><AttestationOverviewPage /></>} />
        <Route path="/attestation/meta" element={<AttestationMetaPage />} />
        <Route path="/attestation/dynamic" element={<AttestationDynamicPage />} />
        <Route path="/attestation/history" element={<AttestationHistoryPage />} />
        <Route path="/anchors" element={<AnchorsPage />} />
        <Route path="/audit" element={<><MainChainGuide /><AuditPage /></>} />
        <Route path="/governance" element={<GovernancePage />} />
        <Route path="/formal" element={<FormalPage />} />
        <Route path="/cluster" element={<ClusterPage />} />
        <Route path="/market" element={<><MainChainGuide /><MarketPage /></>} />
        <Route path="/market-sim" element={<MarketSimPage />} />
        <Route path="/tax" element={<TaxPage />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/academy" element={<AcademyPage />} />
        <Route path="/toolshelf" element={<ToolshelfPage />} />
        <Route path="/notifier" element={<NotifierPage />} />
        <Route path="/sandbox" element={<SandboxPage />} />
        <Route path="/ops" element={<OpsPage />} />
        {/* MIGRATE 批5（L1SI206）：运维手册三界面（同栈直拷 ops-manual 一路·内容=在册白名单源件直读·只进运维私域） */}
        <Route path="/ops/readme" element={<OpsReadmePage />} />
        <Route path="/ops/ops" element={<OpsOpsPage />} />
        <Route path="/ops/changelog" element={<OpsChangelogPage />} />
        {/* MIGRATE 批4（L1SI206）：演练与实验两面（同栈直拷·场景数8不缩·仅人） */}
        <Route path="/lab" element={<LabPage />} />
        <Route path="/demo" element={<DemoPage />} />
        {/* MIGRATE 批6（L1SI206）：入门与指南——/start 六步指引（yaml 单一事实源直拷）＋/nca-guide 存证说明 */}
        <Route path="/start" element={<StartPage />} />
        <Route path="/nca-guide" element={<NcaGuidePage />} />
        {/* 用组批（L1SI206-USE-GROUP-B1）：U-1 交素材（上传一件）→ U-2 代办登记（?u= 串接，两页互链） */}
        {/* 追平批B1：四面新增路由（现有路径不动） */}
        <Route path="/rules" element={<RulesMapPage />} />
        <Route path="/help" element={<HelpPage />} />
        <Route path="/negativespace" element={<NegativeSpacePage />} />
        <Route path="/academy/outline" element={<AcademyOutlinePage />} />
        <Route path="/use/upload" element={<UseUploadPage />} />
        <Route path="/use/agent" element={<UseAgentPage />} />
        {/* 追平批B2（L1SI206-PARITY-B2）：五序资产／官方资产／系统健康／术语检索四面（旧版权直拷·接缝仅适配） */}
        {/* 追平批B3：/five-orders＝主链第二环，补挂 MainChainGuide（导轨裁示·八环之内皆挂） */}
        <Route path="/five-orders" element={<><MainChainGuide /><FiveOrdersPage /></>} />
        <Route path="/official-assets" element={<OfficialAssetsPage />} />
        <Route path="/status" element={<StatusPage />} />
        <Route path="/terms" element={<TermsPage />} />
        {/* 追平批B2：运维日志两件（填写＋列表导出）——运维私域内路由（须鉴权取件）；⛔ 不入公开导航／⛔ 不入检索索引 */}
        <Route path="/ops/logs" element={<OpsLogsPage />} />
        <Route path="/ops/logs/list" element={<OpsLogsListPage />} />
        {/* 追平批B3（L1SI206-PARITY-B3）：授权配置面板（受护·RequireAuth 未登录重定向 /auth）＋三问向导（公开·同批接通悬空链接）＋运维我的（私域） */}
        <Route path="/authorization/panel" element={<RequireAuth><AuthorizationPanelPage /></RequireAuth>} />
        <Route path="/start/three-questions" element={<ThreeQuestionsPage />} />
        <Route path="/ops/me" element={<OpsMePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      </SiteLayout>
    </AuthProvider>
  )
}
