// FRONTEND-PERF-001（L1SI207）路由级分包：页面件全部 React.lazy 动态装载，
// 首屏主包 ≤800KB；vendor-react 由 vite manualChunks 固化长缓存。路由表与路径一字未动。
import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router'
import { AuthProvider } from './lib/auth-context'
import { RequireAuth } from './components/RequireAuth'
import { SiteLayout } from './components/SiteLayout'

const Home = lazy(() => import('./pages/Home'))
const DocsHome = lazy(() => import('./pages/Docs'))
const DocsIndex = lazy(() => import('./pages/Docs').then((m) => ({ default: m.DocsIndex })))
const DocDetail = lazy(() => import('./pages/Docs').then((m) => ({ default: m.DocDetail })))
const Review = lazy(() => import('./pages/Review'))
const OverviewPage = lazy(() => import('./pages/Overview').then((m) => ({ default: m.OverviewPage })))
const AboutPage = lazy(() => import('./pages/About').then((m) => ({ default: m.AboutPage })))
const PagesIndexPage = lazy(() => import('./pages/PagesIndex').then((m) => ({ default: m.PagesIndexPage })))
const NotFoundPage = lazy(() => import('./pages/PagesIndex').then((m) => ({ default: m.NotFoundPage })))
const AnnouncementsPage = lazy(() => import('./pages/Announcements').then((m) => ({ default: m.AnnouncementsPage })))
const RegisterPage = lazy(() => import('./pages/Register').then((m) => ({ default: m.RegisterPage })))
const AuthPage = lazy(() => import('./pages/AuthLogin').then((m) => ({ default: m.AuthPage })))
const MePage = lazy(() => import('./pages/MeConsole').then((m) => ({ default: m.MePage })))
const MeAppealPage = lazy(() => import('./pages/MeAppealPage').then((m) => ({ default: m.MeAppealPage })))
// MYSPACE-PHASE1-001（L1SI207）区 2/5 新建三面＋存证查看（复用现端点，零新后端）
const MeAssetPage = lazy(() => import('./pages/MeAssetPage').then((m) => ({ default: m.MeAssetPage })))
const MeRegistryPage = lazy(() => import('./pages/MeRegistryPage').then((m) => ({ default: m.MeRegistryPage })))
const MeConfigPage = lazy(() => import('./pages/MeConfigPage').then((m) => ({ default: m.MeConfigPage })))
const MeNcaPage = lazy(() => import('./pages/MeNcaPage').then((m) => ({ default: m.MeNcaPage })))
const MainChainGuide = lazy(() => import('./pages/MainChainGuide').then((m) => ({ default: m.MainChainGuide })))
const AgentsPage = lazy(() => import('./pages/AgentsCluster').then((m) => ({ default: m.AgentsPage })))
const AgentDashboardPage = lazy(() => import('./pages/AgentDashboard').then((m) => ({ default: m.AgentDashboardPage })))
const AgentShelfPage = lazy(() => import('./pages/AgentShelfPage').then((m) => ({ default: m.AgentShelfPage })))
const StudioPage = lazy(() => import('./pages/StudioPage').then((m) => ({ default: m.StudioPage })))
const WorkbuddyPage = lazy(() => import('./pages/WorkbuddyPage').then((m) => ({ default: m.WorkbuddyPage })))
const OwnershipPage = lazy(() => import('./pages/OwnershipPage').then((m) => ({ default: m.OwnershipPage })))
const OwnershipRegistryPage = lazy(() => import('./pages/OwnershipRegistryPage').then((m) => ({ default: m.OwnershipRegistryPage })))
const AuthorizationRegistryPage = lazy(() => import('./pages/AuthorizationRegistryPage').then((m) => ({ default: m.AuthorizationRegistryPage })))
const AttestationOverviewPage = lazy(() => import('./pages/AttestationPage').then((m) => ({ default: m.AttestationOverviewPage })))
const AttestationMetaPage = lazy(() => import('./pages/AttestationPage').then((m) => ({ default: m.AttestationMetaPage })))
const AttestationDynamicPage = lazy(() => import('./pages/AttestationPage').then((m) => ({ default: m.AttestationDynamicPage })))
const AttestationHistoryPage = lazy(() => import('./pages/AttestationPage').then((m) => ({ default: m.AttestationHistoryPage })))
const AnchorsPage = lazy(() => import('./pages/AnchorsPage').then((m) => ({ default: m.AnchorsPage })))
const AuditPage = lazy(() => import('./pages/AuditPage').then((m) => ({ default: m.AuditPage })))
const GovernancePage = lazy(() => import('./pages/GovernancePage').then((m) => ({ default: m.GovernancePage })))
const FormalPage = lazy(() => import('./pages/FormalPage').then((m) => ({ default: m.FormalPage })))
const ClusterPage = lazy(() => import('./pages/ClusterPage').then((m) => ({ default: m.ClusterPage })))
const MarketPage = lazy(() => import('./pages/MarketPage').then((m) => ({ default: m.MarketPage })))
const MarketSimPage = lazy(() => import('./pages/MarketSimPage').then((m) => ({ default: m.MarketSimPage })))
const TaxPage = lazy(() => import('./pages/TaxPage').then((m) => ({ default: m.TaxPage })))
const LibraryPage = lazy(() => import('./pages/LibraryPage').then((m) => ({ default: m.LibraryPage })))
const AcademyPage = lazy(() => import('./pages/AcademyPage').then((m) => ({ default: m.AcademyPage })))
const ToolshelfPage = lazy(() => import('./pages/ToolshelfPage').then((m) => ({ default: m.ToolshelfPage })))
const NotifierPage = lazy(() => import('./pages/NotifierPage').then((m) => ({ default: m.NotifierPage })))
const SandboxPage = lazy(() => import('./pages/SandboxPage').then((m) => ({ default: m.SandboxPage })))
const RulesMapPage = lazy(() => import('./pages/rules/rules').then((m) => ({ default: m.RulesMapPage })))
const HelpPage = lazy(() => import('./pages/HelpPage').then((m) => ({ default: m.HelpPage })))
const NegativeSpacePage = lazy(() => import('./pages/NegativeSpacePage').then((m) => ({ default: m.NegativeSpacePage })))
const AcademyOutlinePage = lazy(() => import('./pages/academy/AcademyOutlinePage').then((m) => ({ default: m.AcademyOutlinePage })))
const FiveOrdersPage = lazy(() => import('./pages/FiveOrdersPage').then((m) => ({ default: m.FiveOrdersPage })))
const OfficialAssetsPage = lazy(() => import('./pages/OfficialAssetsPage').then((m) => ({ default: m.OfficialAssetsPage })))
const StatusPage = lazy(() => import('./pages/StatusPage').then((m) => ({ default: m.StatusPage })))
const TermsPage = lazy(() => import('./pages/TermsPage').then((m) => ({ default: m.TermsPage })))
const OpsLogsPage = lazy(() => import('./pages/OpsLogsPage').then((m) => ({ default: m.OpsLogsPage })))
const OpsLogsListPage = lazy(() => import('./pages/OpsLogsListPage').then((m) => ({ default: m.OpsLogsListPage })))
const AuthorizationPanelPage = lazy(() => import('./pages/AuthorizationPanelPage').then((m) => ({ default: m.AuthorizationPanelPage })))
const ThreeQuestionsPage = lazy(() => import('./pages/ThreeQuestionsPage').then((m) => ({ default: m.ThreeQuestionsPage })))
const OpsMePage = lazy(() => import('./pages/OpsMePage').then((m) => ({ default: m.OpsMePage })))
const VerifyPage = lazy(() => import('./pages/VerifyPage').then((m) => ({ default: m.VerifyPage })))
const UseUploadPage = lazy(() => import('./pages/use/UseUploadPage').then((m) => ({ default: m.UseUploadPage })))
const UseAgentPage = lazy(() => import('./pages/use/UseAgentPage').then((m) => ({ default: m.UseAgentPage })))
const OpsPage = lazy(() => import('./pages/OpsPage').then((m) => ({ default: m.OpsPage })))
const OpsReadmePage = lazy(() => import('./pages/OpsReadmePage').then((m) => ({ default: m.OpsReadmePage })))
const OpsOpsPage = lazy(() => import('./pages/OpsOpsPage').then((m) => ({ default: m.OpsOpsPage })))
const OpsChangelogPage = lazy(() => import('./pages/OpsChangelogPage').then((m) => ({ default: m.OpsChangelogPage })))
const StartPage = lazy(() => import('./pages/start/start').then((m) => ({ default: m.StartPage })))
const NcaGuidePage = lazy(() => import('./pages/NcaGuidePage').then((m) => ({ default: m.NcaGuidePage })))
const ChannelHome = lazy(() => import('./pages/ChannelHome').then((m) => ({ default: m.ChannelHome })))
const ProcessOverviewPage = lazy(() => import('./pages/ProcessOverview').then((m) => ({ default: m.ProcessOverviewPage })))
const RegistrationsPage = lazy(() => import('./pages/RegistrationsPage').then((m) => ({ default: m.RegistrationsPage })))
const SearchPage = lazy(() => import('./pages/SearchPage').then((m) => ({ default: m.SearchPage })))
const ChannelMyPage = lazy(() => import('./pages/ChannelMy').then((m) => ({ default: m.ChannelMyPage })))
const AgentChannelRegisterPage = lazy(() => import('./pages/AgentChannelRegister').then((m) => ({ default: m.AgentChannelRegisterPage })))
const ChannelPortalPage = lazy(() => import('./pages/ChannelPortal').then((m) => ({ default: m.ChannelPortalPage })))
const CurationPoolPage = lazy(() => import('./pages/Curation').then((m) => ({ default: m.CurationPoolPage })))
const ContributePage = lazy(() => import('./pages/Contribute').then((m) => ({ default: m.ContributePage })))
const PublicFacePage = lazy(() => import('./pages/PublicFace').then((m) => ({ default: m.PublicFacePage })))
const PrivateDomainPage = lazy(() => import('./pages/PrivateDomain').then((m) => ({ default: m.PrivateDomainPage })))
const NodeNetPage = lazy(() => import('./pages/NodeNet').then((m) => ({ default: m.NodeNetPage })))
const MeNodePage = lazy(() => import('./pages/MeNode').then((m) => ({ default: m.MeNodePage })))
const MeNodeNetPage = lazy(() => import('./pages/MeNodeNet').then((m) => ({ default: m.MeNodeNetPage })))
const NodeDisclosurePage = lazy(() => import('./pages/NodeDisclosure').then((m) => ({ default: m.NodeDisclosurePage })))
const LabPage = lazy(() => import('./pages/Lab').then((m) => ({ default: m.LabPage })))
const DemoPage = lazy(() => import('./pages/Demo').then((m) => ({ default: m.DemoPage })))


export default function App() {
  return (
    <AuthProvider>
      <SiteLayout>
      {/* FRONTEND-PERF-001：路由级分包后的统一挂起兜底（首屏主包 ≤800KB） */}
      <Suspense fallback={<div data-testid="route-loading" className="p-8 text-center text-slate-500">加载中…</div>}>
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
        {/* MYSPACE-PHASE1-001 §一.4 补齐：事由/对象/诉求/附件 最小必填登记＋三态展示（受理通道开通后接账） */}
        <Route path="/me/appeal" element={<MeAppealPage />} />
        {/* MYSPACE-PHASE1-001 §一.2/§一.3：区 2 三新建面＋区 5 存证查看（匿名 PrivateGate 引导登录，零数据渲染） */}
        <Route path="/me/asset" element={<MeAssetPage />} />
        <Route path="/me/registry" element={<MeRegistryPage />} />
        <Route path="/me/config" element={<MeConfigPage />} />
        <Route path="/me/nca" element={<MeNcaPage />} />
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
        {/* 追平批B4（L1SI206-PARITY-B4-001）：/verify 怎么验证·5分钟三件自查（公开面·匿名可达·直拷接缝适配）＋两旧链重定向（旧版逐字同形·不破旧链） */}
        <Route path="/verify" element={<VerifyPage />} />
        <Route path="/assets" element={<Navigate to="/five-orders" replace />} />
        <Route path="/ops/manual" element={<Navigate to="/ops/readme" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      </Suspense>
      </SiteLayout>
    </AuthProvider>
  )
}
