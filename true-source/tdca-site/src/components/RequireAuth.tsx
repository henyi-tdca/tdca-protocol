// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 追平批B3（L1SI206-PARITY-B3）受护页守卫
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-PARITY-B3-001 §二#1——/authorization/panel 受护
//   （未登录重定向 /auth）；后端同守 401。本件为接缝级新件（新站无 RequireAuth 壳组件，
//   照批3 私域口径由 API 层 fail-closed 把守；本页令面明载「重定向 /auth」，遂补最小守卫）
// =============================================================================
import type { ReactNode } from 'react'
import { Navigate } from 'react-router'
import { useAuth } from '@/lib/auth-context'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/auth" replace />
  return <>{children}</>
}
