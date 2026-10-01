import { Routes, Route } from 'react-router'
import Home from './pages/Home'
import Join from './pages/Join'
import DocsHome, { DocsIndex, DocDetail } from './pages/Docs'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/join" element={<Join />} />
      <Route path="/docs" element={<DocsHome />} />
      <Route path="/docs/:family" element={<DocsIndex />} />
      <Route path="/docs/:family/:slug" element={<DocDetail />} />
    </Routes>
  )
}
