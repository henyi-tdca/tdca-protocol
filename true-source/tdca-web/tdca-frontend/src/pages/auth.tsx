// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-F2-001 | 目标函数: F-2 /auth 登录页（DID 选择 + token + B-4 联动）
// 约束矩阵: FRAMEWORK-001 §四 /auth + BACKEND-REVIEW B-4（TDCA_GATEWAY_AUTH）+ ID92
// 预期分配: AuthPage（登录 → 持有 token → 回跳来源路由）
// =============================================================================
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { useAuth } from '@/app/auth-context'
import type { DIDRole } from '@/app/did-context'
import { api, setSessionToken } from '@/api/client'

const DEFAULT_TOKEN = 'TDCA-CRT-demo-2026' // 与 gateway B-4 默认 TDCA_GATEWAY_TOKEN 一致

/** F-2 统一 DID 认证入口：M3 账号密码登录（真实会话）+ 既有 DID 模拟态登录（保留） */
export function AuthPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { from?: string; expired?: boolean } | null
  const from = state?.from ?? '/'
  const expired = state?.expired === true

  const [role, setRole] = useState<DIDRole>('H')
  const [token, setToken] = useState(DEFAULT_TOKEN)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loginMsg, setLoginMsg] = useState<string | null>(null)

  const did = role === 'H' ? 'TDID-H-0001' : role === 'M' ? 'TDID-M-0001' : 'TDID-L-0001'

  // M3 真实登录：POST /api/v1/auth/login → TDCA-SES 会话令牌（sessionStorage，关窗即焚）
  async function submitAccount() {
    setLoginMsg(null)
    const res = await api.post<{ token: string; role: string; expires_at: string }>(
      '/api/v1/auth/login',
      { username: username.trim(), password },
    )
    if (res.ok) {
      setSessionToken(res.data.token)
      login(did, res.data.token) // 登录态上下文联动（受保护路由放行）
      // 整页重载：已挂载页面只在 mount 时取数，SPA 回跳不触发 refetch → 登录后整载保证各页数据新鲜
      const target = from && from.startsWith('/') ? `/#${from}` : '/'
      window.location.assign(target)
    } else {
      setLoginMsg(res.status === 401 ? '用户名或密码错误' : `登录失败（${res.status ?? res.reason}）`)
    }
  }

  function submit() {
    login(did, token.trim() || DEFAULT_TOKEN)
    navigate(from, { replace: true })
  }

  return (
    <PageShell
      title="登录（DID）"
      dataSource="M3 鉴权（users/sessions 表）+ B-4 鉴权中间件（TDCA_GATEWAY_AUTH=1 启用时强制）"
      permission="公开"
      description="统一认证入口（F-2 落地）：账号密码登录持有 TDCA-SES 会话令牌，受保护路由（/agents /studio /attestation* /governance）方可访问。"
    >
      {expired && (
        <div data-testid="auth-expired-notice" className="mb-4 max-w-md rounded border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
          会话已过期或在其他处登录。您之前的页面内容未丢失，重新登录后可返回继续。
        </div>
      )}
      <div data-testid="auth-account-form" className="mb-6 max-w-md space-y-3 rounded border border-gray-200 bg-white p-4">
        <div className="text-xs font-semibold text-gray-700">账号登录（M3 真实会话，2h 有效期）</div>
        <input
          data-testid="auth-username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="用户名"
          className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
        />
        <input
          data-testid="auth-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="密码"
          className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
        />
        {loginMsg && <div data-testid="auth-login-msg" className="text-xs text-red-700">{loginMsg}</div>}
        <button
          data-testid="auth-login-account"
          className="w-full rounded bg-emerald-700 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-800"
          onClick={submitAccount}
        >
          登录（账号密码 → 会话令牌）
        </button>
        {/* 忘记密码指引（件 B0：零后端文案口径——无自助重置通道，人工重置） */}
        <p data-testid="auth-forgot-hint" className="text-[11px] leading-4 text-gray-500">
          忘记密码？本站点无自助重置通道，请携带用户名联系站点管理员人工重置（<a href="mailto:xuantan0703@agent.qq.com" className="text-emerald-700 underline">xuantan0703@agent.qq.com</a>）后重新登录。
        </p>
      </div>
      <div className="mb-2 max-w-md text-[10px] uppercase tracking-wide text-gray-400">降级通道：DID 模拟态登录（保留）</div>
      <div data-testid="auth-form" className="max-w-md space-y-4">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          模拟态登录（ID92）——真实网关鉴权由 B-4 中间件兜底 <SimulatedBadge nature="simulated" />
        </div>
        <div>
          <div className="mb-1 text-xs text-gray-600">DID 身份</div>
          <div className="flex gap-2">
            {(['H', 'M', 'L'] as DIDRole[]).map((r) => (
              <button
                key={r}
                data-testid={`auth-role-${r}`}
                data-active={role === r}
                className={`rounded border px-3 py-1.5 text-xs ${role === r ? 'border-slate-800 bg-slate-800 text-white' : 'border-blue-600 bg-blue-600 text-white hover:bg-blue-700'}`}
                onClick={() => setRole(r)}
              >
                {r} · {r === 'H' ? '人类' : r === 'M' ? '智能体' : '学习体'}
              </button>
            ))}
          </div>
          <div className="mt-1 text-xs text-gray-400" data-testid="auth-did-preview">将登录为：{did}</div>
        </div>
        <div>
          <label className="mb-1 block text-xs text-gray-600">HUF/API Token（B-4）</label>
          <input
            data-testid="auth-token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm font-mono"
          />
        </div>
        <button
          data-testid="auth-submit"
          className="w-full rounded bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
          onClick={submit}
        >
          登录（持有 token → 受保护路由）
        </button>
      </div>
    </PageShell>
  )
}
