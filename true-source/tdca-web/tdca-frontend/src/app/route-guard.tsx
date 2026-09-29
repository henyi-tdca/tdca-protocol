// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-F2-001 | 目标函数: F-2 路由守卫（受保护路由未登录 → 重定向 /auth）
// 约束矩阵: FRAMEWORK-001 §四（权限表：/agents /studio /attestation* /governance 须登录）+ F-4/HUF
// 预期分配: RequireAuth（未登录 Navigate /auth，记录来源回跳）
// =============================================================================
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { useAuth } from './auth-context'

/** 受保护路由守卫：未登录 → 重定向 /auth（保留来源，登录后回跳） */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace state={{ from: location.pathname }} />
  }
  return <>{children}</>
}
