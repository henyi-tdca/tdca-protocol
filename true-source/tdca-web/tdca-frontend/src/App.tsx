// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 + F-2 | 目标函数: 16 路由（含 /auth F-2 落地）+ 受保护路由守卫
// 约束矩阵: FRAMEWORK-001 §四（权限表）+ BACKEND-REVIEW B-4 + F-4/HUF
// 预期分配: App（AuthProvider + AppShell 布局 + 16 路由 + RequireAuth 保护 + NotFound）
// =============================================================================
import { Navigate, Route, Routes } from 'react-router'
import { AppShell } from '@/app/app-shell'
import { AuthProvider } from '@/app/auth-context'
import { RequireAuth } from '@/app/route-guard'
import { PAGE_META, NotFoundPage, renderPage, DocsIndexPage, DocDetailPage } from '@/pages/pages'

/** 受保护路由（FRAMEWORK-001 §四：须登录 DID + HUF 鉴权）——未登录重定向 /auth */
const PROTECTED = new Set([
  '/agents',
  '/studio',
  '/governance',
  '/attestation',
  '/attestation/meta',
  '/attestation/dynamic',
  '/attestation/history',
  '/me',
  '/me/appeal',
])

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<AppShell />}>
          {PAGE_META.map((meta) => (
            <Route
              key={meta.path}
              path={meta.path}
              element={PROTECTED.has(meta.path) ? <RequireAuth>{renderPage(meta)}</RequireAuth> : renderPage(meta)}
            />
          ))}
          {/* 二期改版批2块一：/channel/* 五路保留为极简入口（重定向，⛔ 不裁撤——删路由＝公开面 404 风险；内容已融入新壳导航） */}
          <Route path="/channel/portal" element={<Navigate to="/" replace />} />
          <Route path="/channel/agents" element={<Navigate to="/agents" replace />} />
          <Route path="/channel/registry" element={<Navigate to="/ownership-registry" replace />} />
          <Route path="/channel/market" element={<Navigate to="/market" replace />} />
          <Route path="/channel/tools" element={<Navigate to="/toolshelf" replace />} />
          {/* 二期改版批2块二：文档库两路参数路由（族列表／详情；首页 /docs 走 PAGE_META） */}
          <Route path="/docs/:family" element={<DocsIndexPage />} />
          <Route path="/docs/:family/:slug" element={<DocDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
