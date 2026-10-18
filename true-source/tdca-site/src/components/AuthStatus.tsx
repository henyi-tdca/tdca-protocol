// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-F2-001 | 目标函数: 登录状态栏（F-2：未登录 → /auth 入口；已登录 → DID + 登出）
// 约束矩阵: FRAMEWORK-001 §四 /auth + F-2 认证上下文；SITE-THREE-FIXES-001-AMEND-1 处3 补搬
// 来源: 旧树 app-shell.tsx AuthStatus（L116~L133）单摘迁入，useAuth 改指新树 @/lib/auth-context
// =============================================================================
import { NavLink } from 'react-router'
import { useAuth } from '@/lib/auth-context'

/** 登录状态栏（F-2）：未登录 → /auth 入口；已登录 → DID + 登出 */
export function AuthStatus() {
  const { isAuthenticated, did, logout } = useAuth()
  if (!isAuthenticated) {
    return (
      <NavLink
        to="/auth"
        data-testid="auth-login-link"
        className="shrink-0 whitespace-nowrap rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs font-medium text-white hover:bg-slate-700"
      >
        登录（DID）
      </NavLink>
    )
  }
  return (
    <span data-testid="auth-status" className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-lg border border-emerald-200 bg-emerald-50 px-2 py-1">
      <span className="text-xs font-medium text-emerald-800">🔐 {did}</span>
      <button data-testid="auth-logout" className="border-0 bg-transparent px-1 py-0 text-[10px] text-emerald-600 underline hover:bg-transparent hover:text-emerald-800" onClick={logout}>
        登出
      </button>
    </span>
  )
}
