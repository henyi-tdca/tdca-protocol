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

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/join" element={<Join />} />
      <Route path="/review" element={<Review />} />
      <Route path="/docs" element={<DocsHome />} />
      <Route path="/docs/:family" element={<DocsIndex />} />
      <Route path="/docs/:family/:slug" element={<DocDetail />} />
      <Route path="/overview" element={<OverviewPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/pages" element={<PagesIndexPage />} />
      <Route path="/announcements" element={<AnnouncementsPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
