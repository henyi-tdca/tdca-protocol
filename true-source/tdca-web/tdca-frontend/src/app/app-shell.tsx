// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-1 应用壳（DID/HUF Banner/通知机栏/层级指示器 + 导航）
// 约束矩阵: TDCA-TASK-FRONTEND-001（FROZEN）§三 F0-1 + FRAMEWORK-001 §三/§八·C.3
// 预期分配: AppShell（组合 shell 元素 + <Outlet/> + 15 路由导航 + 全站模拟态标注）
// =============================================================================
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router'
import { DIDProvider, ROLE_LABELS, useDID, type DIDRole } from './did-context'
import { HufBanner } from './huf-banner'
import { NotifierBar } from './notifier-bar'
import { LayerIndicator, type LayerKey } from './layer-indicator'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { useAuth } from './auth-context'
import { IntentBar } from './intent-bar'
import { AUTH_REQUIRED_EVENT, SESSION_EXPIRED_EVENT, sessionToken } from '@/api/client'

/** 路由 → 四层架构层级映射（FRAMEWORK-001 §八·C.3） */
export function layerForPath(pathname: string): LayerKey {
  if (pathname.startsWith('/ownership')) return 'L1'
  if (pathname.startsWith('/market')) return 'L2'
  if (pathname.startsWith('/sandbox')) return 'SANDBOX'
  if (pathname.startsWith('/tax')) return 'L3'
  if (pathname.startsWith('/studio')) return 'STUDIO'
  return 'L0'
}

export interface NavItem {
  to: string
  label: string
}
export const APP_NAV: { group: string; items: NavItem[] }[] = [
  {
    group: '橱窗',
    items: [
      { to: '/', label: '首页' },
      { to: '/about', label: '关于' },
      { to: '/ownership', label: '所有权' },
      { to: '/market', label: '配置权市场' },
      { to: '/sandbox', label: '沙盒' },
      { to: '/tax', label: '税收' },
      { to: '/academy', label: '学院' },
      { to: '/audit', label: '审计' },
      { to: '/governance', label: '治理' },
      { to: '/library', label: '文库' },
    ],
  },
  {
    group: '观测',
    items: [
      { to: '/agents', label: '智能体集群' },
      { to: '/notifier', label: '通知机' },
    ],
  },
  { group: '作业', items: [{ to: '/studio', label: 'Agent Studio' }] },
  {
    // 站点一期（P1~P9）：名目照在册 PAGE_META 元数据（pages.tsx），仅挂导航入口，不改制度语义
    group: '站点一期',
    items: [
      { to: '/workbuddy', label: 'WorkBuddy' },
      { to: '/cluster', label: '集群编排' },
      { to: '/formal', label: '形式化入站' },
      { to: '/toolshelf', label: '工具货架' },
      { to: '/anchors', label: '模拟锚' },
      { to: '/ops', label: '运维端' },
      { to: '/ownership-registry', label: '权属登记' },
      { to: '/market-sim', label: '规范与沙盒链' },
    ],
  },
  {
    group: '确权',
    items: [
      { to: '/attestation', label: '确权中心' },
      { to: '/attestation/meta', label: '元函数确权' },
      { to: '/attestation/dynamic', label: '动态确权' },
      { to: '/attestation/history', label: '确权历史' },
    ],
  },
  {
    // 账户（F-2 接缝落地）：名目照在册 PAGE_META 元数据（/auth /register /me）
    group: '账户',
    items: [
      { to: '/auth', label: '登录' },
      { to: '/register', label: '注册' },
      { to: '/me', label: '我的' },
    ],
  },
]

function DidSwitcher() {
  const { role, did, switchRole } = useDID()
  return (
    <div data-testid="did-switcher" className="flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-2 py-1">
      {(['H', 'M', 'L'] as DIDRole[]).map((r) => (
        <button
          key={r}
          data-role={r}
          data-active={role === r}
          className={`rounded px-2 py-0.5 text-xs ${role === r ? 'bg-slate-800 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          onClick={() => switchRole(r)}
        >
          {r}·{ROLE_LABELS[r].split('（')[0]}
        </button>
      ))}
      <span className="ml-1 text-[10px] text-gray-400" data-testid="did-value">{did}</span>
    </div>
  )
}

/** 登录状态栏（F-2）：未登录 → /auth 入口；已登录 → DID + 登出 */
function AuthStatus() {
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
      <button data-testid="auth-logout" className="text-[10px] text-emerald-600 underline hover:text-emerald-800" onClick={logout}>
        登出
      </button>
    </span>
  )
}

function ShellInner() {
  const location = useLocation()
  const navigate = useNavigate()
  const layer = layerForPath(location.pathname)
  // M3 裁定③兜底：会话过期/被踢 → 明确提示横幅；不自动跳转，当前页面未提交内容原样保留
  const [sessionExpiredFrom, setSessionExpiredFrom] = useState<string | null>(null)
  useEffect(() => {
    function onExpired(ev: Event) {
      setSessionExpiredFrom((ev as CustomEvent<{ from?: string }>).detail?.from ?? null)
    }
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired)
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired)
  }, [])
  // 匿名 401/403 引导：未登录访问受保护内容 → 提示条引导登录（不静默空页）；登录成功后隐藏
  const [authRequired, setAuthRequired] = useState(false)
  useEffect(() => {
    function onAuthRequired() {
      setAuthRequired(true)
    }
    window.addEventListener(AUTH_REQUIRED_EVENT, onAuthRequired)
    return () => window.removeEventListener(AUTH_REQUIRED_EVENT, onAuthRequired)
  }, [])
  useEffect(() => {
    // 路由切换时复核：已有会话则收起提示条
    if (authRequired && sessionToken()) setAuthRequired(false)
  }, [location.pathname, authRequired])
  return (
    <div className="flex min-h-screen flex-col bg-gray-50 font-sans">
      {authRequired && !sessionToken() && (
        <div data-testid="auth-required-banner" className="border-b border-blue-200 bg-blue-50">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-1.5">
            <span className="text-xs text-blue-800">
              站点一期各页的制度规则与业务内容需登录后可见（注册即 viewer 只读账号）。
            </span>
            <button
              data-testid="auth-required-login"
              className="rounded bg-blue-700 px-2 py-1 text-[11px] text-white hover:bg-blue-800"
              onClick={() => navigate('/auth', { state: { from: location.pathname } })}
            >
              去登录
            </button>
          </div>
        </div>
      )}
      {sessionExpiredFrom !== null && (
        <div data-testid="session-expired-banner" className="border-b border-red-200 bg-red-50">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-1.5">
            <span className="text-xs text-red-800">
              会话已过期或在其他处登录（来源页面：{sessionExpiredFrom}）。当前页面未提交内容未丢失，请重新登录后再提交。
            </span>
            <button
              data-testid="session-expired-relogin"
              className="rounded bg-red-700 px-2 py-1 text-[11px] text-white hover:bg-red-800"
              onClick={() => {
                setSessionExpiredFrom(null)
                navigate('/auth', { state: { from: sessionExpiredFrom ?? location.pathname, expired: true } })
              }}
            >
              去重新登录
            </button>
          </div>
        </div>
      )}
      <div className="border-b border-amber-200 bg-amber-50/60">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-1.5">
          <span className="text-xs font-semibold text-amber-800">TDCA 官网 · 制度橱窗 / 观测 / 作业</span>
          <SimulatedBadge nature="simulated" label="全站模拟态 data_nature=simulated (ID92)" />
        </div>
      </div>
      <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-2">
          <HufBanner />
          <div className="flex items-center gap-2">
            <IntentBar />
            <AuthStatus />
            <DidSwitcher />
            <NotifierBar />
          </div>
        </div>
        <nav data-testid="app-nav" className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-1 px-4 pb-2">
          {APP_NAV.map(({ group, items }) => (
            <span key={group} className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="text-[10px] font-medium uppercase tracking-wide text-gray-400">{group}</span>
              {items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `text-xs ${isActive ? 'font-semibold text-slate-900 underline underline-offset-4' : 'text-gray-500 hover:text-slate-800'}`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </span>
          ))}
        </nav>
      </header>
      <div className="mx-auto mt-3 w-full max-w-6xl px-4">
        <LayerIndicator current={layer} />
      </div>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>
      <footer className="border-t border-gray-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-3 text-[10px] text-gray-400">
          术语基线：TDCA-TERMINOLOGY-REGISTRY V1.1（G-1）· 制度依据：宪法十六条 + UPDA-v2.0 + NSFL-V0.2 · 后端对接：gateway:8100（仅消费）
        </div>
      </footer>
    </div>
  )
}

export function AppShell() {
  return (
    <DIDProvider>
      <ShellInner />
    </DIDProvider>
  )
}
