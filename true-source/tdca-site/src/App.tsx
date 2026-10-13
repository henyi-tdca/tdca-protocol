import { Routes, Route } from 'react-router'
import Home from './pages/Home'
import Join from './pages/Join'
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

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/join" element={<Join />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/me" element={<MePage />} />
        <Route path="/review" element={<Review />} />
        <Route path="/docs" element={<DocsHome />} />
        <Route path="/docs/:family" element={<DocsIndex />} />
        <Route path="/docs/:family/:slug" element={<DocDetail />} />
        <Route path="/overview" element={<OverviewPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/pages" element={<PagesIndexPage />} />
        <Route path="/announcements" element={<AnnouncementsPage />} />
        {/* FRONTEND-MERGE 批3：智能体面五路（路由照存；不设登录门槛——照本批核可口径） */}
        <Route path="/agents" element={<AgentsPage />} />
        <Route path="/agents/:id" element={<AgentDashboardPage />} />
        <Route path="/agent-shelf" element={<AgentShelfPage />} />
        <Route path="/studio" element={<StudioPage />} />
        <Route path="/workbuddy" element={<WorkbuddyPage />} />
        {/* FRONTEND-MERGE 批4：登记与存证面八路（attestation 一件四面 → 四路；照复核件更正补 /anchors） */}
        <Route path="/ownership" element={<OwnershipPage />} />
        <Route path="/ownership-registry" element={<OwnershipRegistryPage />} />
        <Route path="/authorization-registry" element={<AuthorizationRegistryPage />} />
        <Route path="/attestation" element={<AttestationOverviewPage />} />
        <Route path="/attestation/meta" element={<AttestationMetaPage />} />
        <Route path="/attestation/dynamic" element={<AttestationDynamicPage />} />
        <Route path="/attestation/history" element={<AttestationHistoryPage />} />
        <Route path="/anchors" element={<AnchorsPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/governance" element={<GovernancePage />} />
        <Route path="/formal" element={<FormalPage />} />
        <Route path="/cluster" element={<ClusterPage />} />
        <Route path="/market" element={<MarketPage />} />
        <Route path="/market-sim" element={<MarketSimPage />} />
        <Route path="/tax" element={<TaxPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AuthProvider>
  )
}
