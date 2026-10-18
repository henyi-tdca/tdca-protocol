// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-F2-001 | 目标函数: F-2 认证上下文（DID + token 登录态，B-4 联动）
// 约束矩阵: FRAMEWORK-001 §四 /auth（待 F-2 后接）+ BACKEND-REVIEW B-4（TDCA_GATEWAY_AUTH）+ F-4/HUF
// 预期分配: AuthProvider + useAuth（isAuthenticated / did / token / login / logout）
// =============================================================================
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { clearSessionToken, setHufToken } from '@/lib/client'

export interface AuthState {
  isAuthenticated: boolean
  did: string | null
  login: (did: string, token: string) => void
  logout: () => void
}

const STORAGE_DID = 'tdca_auth_did'
const STORAGE_TOKEN = 'tdca_auth_token'

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [did, setDid] = useState<string | null>(() => localStorage.getItem(STORAGE_DID))
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(STORAGE_TOKEN))

  const value = useMemo<AuthState>(
    () => ({
      isAuthenticated: did !== null && token !== null,
      did,
      login: (nextDid, nextToken) => {
        setDid(nextDid)
        setToken(nextToken)
        setHufToken(nextToken) // B-4：写操作 Authorization 联动
        localStorage.setItem(STORAGE_DID, nextDid)
        localStorage.setItem(STORAGE_TOKEN, nextToken)
      },
      logout: () => {
        setDid(null)
        setToken(null)
        localStorage.removeItem(STORAGE_DID)
        localStorage.removeItem(STORAGE_TOKEN)
        // SITE-THREE-FIXES-001-AMEND-1 处3：登出并清 B-4 写令牌（HUF）与会话令牌（TDCA-SES）
        localStorage.removeItem('tdca_huf_token')
        clearSessionToken()
      },
    }),
    [did, token],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth 必须在 AuthProvider 内使用')
  return ctx
}
