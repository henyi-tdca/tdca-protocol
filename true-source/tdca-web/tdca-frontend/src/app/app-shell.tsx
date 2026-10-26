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
import { ProcessRail } from './process-rail'
import { RightRail } from './right-rail'
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
  /** 在建中角标：内容未完全入站／尚未入站（2026-10-04 创始人明示标注） */
  badge?: string
  /** raw＝站内原始资源（如 /api/v1/selfcheck/spec 机读规格）：<a> 直开，⛔ 不走 SPA 路由（避免 404 兜底吞掉） */
  raw?: boolean
  /** authOnly＝仅登录态渲染（L1SI175-A1-3）：项进公域组但匿名不可见，不进公域匿名导航面 */
  authOnly?: boolean
}

/**
 * 二期改版批2块一：公域顶栏六入口（照终定稿 §二块一）。
 * 公域只留公开栏目；须登录／须角色栏目移入右栏「我的」（PRIVATE_NAV，见 right-rail）；
 * 运维分区（运维端／形式化入站／集群准入闸门／评审）⛔ 不入公共导航，独立入口属块四。
 */
export type NavEntry =
  | { kind: 'link'; to: string; label: string }
  | { kind: 'group'; group: string; items: NavItem[] }

export const APP_NAV: NavEntry[] = [
  { kind: 'link', to: '/', label: '首页' },
  {
    kind: 'group',
    group: '生态',
    items: [
      { to: '/agents', label: '智能体集群' }, // 展示面：官方智能体观测橱窗（照终定稿保留于公域）
      { to: '/agent-shelf', label: '智能体区' }, // 展示面：组二 10 件呈现（呈现≠注册）
      { to: '/toolshelf', label: '工具货架' }, // 展示面：浏览公开
      { to: '/academy', label: '商学院' }, // L1SI152-EDU-PORTAL-001 栏目首入：介绍页＋教材目录页（原文照贴）
    ],
  },
  {
    kind: 'group',
    group: '市场',
    items: [
      { to: '/ownership', label: '所有权' }, // 公开读 / 确权操作须 HUF
      { to: '/market', label: '配置权市场', badge: '在建中' }, // 无真实挂牌（auth_grants=0），SIMULATED 演示
      { to: '/tax', label: '税收' },
      { to: '/sandbox', label: '沙盒' }, // 公开读 / 入盒须 HUF
    ],
  },
  {
    kind: 'group',
    group: '制度与透明',
    items: [
      { to: '/about', label: '关于' },
      { to: '/governance', label: '治理' }, // HUF 强制鉴权（B-4）；操作唤起签批，⛔ 不内嵌凭据面
      { to: '/audit', label: '审计' },
      { to: '/notifier', label: '通知机', badge: '在建中' }, // WS 实时通道令牌未通（4401），仅静态状态页
      { to: '/attestation/history', label: '确权历史' }, // 制度即公开；总览/meta/dynamic 三路在私域「我的」
      { to: '/announcements', label: '公告栏' }, // 对外公告区：空栏为常态，内容须创始人逐次明示后发布
      { to: '/process', label: '流程总览' }, // 二期改版批2块三：14 环逐环四能（tdca-site ProcessOverview 移植）
      { to: '/negativespace', label: '负空间' }, // B5 新增批项一：管「什么不能做」（原则与类别，⛔ 不列禁项词表）
      { to: '/official-assets', label: '官方资产区' }, // B5 新增批项二：官方工具（免费）＋官方产物（付费橱窗），调用暂未开放
      { to: '/nca-guide', label: '存证说明' }, // B5 新增批项三：存证格式制度说明（为什么存/怎么存/谁都要存；⛔ 不展凭据与内部编号）
      { to: '/terms', label: '术语检索', authOnly: true }, // L1SI175-A1-3：进制度与透明组但仅登录态渲染（⛔ 公域匿名导航——匿名开放另候创始人一句）
    ],
  },
  {
    kind: 'group',
    group: '资源',
    items: [
      { to: '/library', label: '文库' },
      { to: '/docs', label: '文档库' }, // 裁点2终定：与文库并存（⛔ 不并线——端点不同、族不同）
      { to: '/rules', label: '制度地图' }, // L1SI162-RULES-MAP-001：56 件制度件五类五态六步（公开读；件正文权限照旧）
      { to: '/anchors', label: '模拟锚' }, // 裁定落地件：SIMULATED 模拟态展示＝官方资源呈现 ➜ 公域（随块二落位）
      { to: '/api/v1/selfcheck/spec', label: '机器可读规格', raw: true }, // D1-002（裁定 6181）：原 /openapi.json 实测 404，改指 selfcheck/spec（200·六关键词齐）；raw 直开保留
    ],
  },
  {
    kind: 'group',
    group: '帮助与联系',
    items: [
      { to: '/start', label: '新手指引' }, // L1SI167-START-ENTRY-001-001：入口置帮助组首位（首页卡片撤回；自我更正：导航表为手写分组，PAGE_META 仅路由）
      { to: '/verify', label: '怎么验证' }, // L1SI175-B1 S1-5：三件自查全路径（匿名面）
      { to: '/help', label: '帮助与联系', badge: '在建中' },
    ], // 薄占位：内容随文档库「帮助」族入站（块二）
  },
]

/** 身份角色切换（H/M/L）：横排原样（2026-10-17 返工：创始人所指为四层架构 LayerIndicator，非本件，撤销误改） */
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
      <button data-testid="auth-logout" className="border-0 bg-transparent px-1 py-0 text-[10px] text-emerald-600 underline hover:bg-transparent hover:text-emerald-800" onClick={logout}>
        登出
      </button>
    </span>
  )
}

function ShellInner() {
  const location = useLocation()
  const navigate = useNavigate()
  const layer = layerForPath(location.pathname)
  // L1SI175-A1-3：authOnly 导航项（登录态可见）过滤用
  const { isAuthenticated } = useAuth()
  // M3 裁定③兜底：会话过期/被踢 → 明确提示横幅；不自动跳转，当前页面未提交内容原样保留
  const [sessionExpiredFrom, setSessionExpiredFrom] = useState<string | null>(null)
  // 二期改版批1：小屏左右栏折叠开关（宽屏恒显）
  const [showLeft, setShowLeft] = useState(false)
  const [showRight, setShowRight] = useState(false)
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
          <span className="text-xs font-semibold text-amber-800">TDCA 官网 · 公域（公开面）／私域（我的）／运维分区（不公开）</span>
          <SimulatedBadge nature="simulated" label="全站模拟态 data_nature=simulated (ID92)" />
        </div>
      </div>
      <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-2">
          <HufBanner />
          <div className="flex flex-wrap items-center gap-2">
            <IntentBar />
            <AuthStatus />
            <DidSwitcher />
            <NotifierBar />
          </div>
        </div>
        <nav data-testid="app-nav" className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-1 px-4 pb-2">
          {APP_NAV.map((entry) =>
            entry.kind === 'link' ? (
              <NavLink
                key={entry.to}
                to={entry.to}
                end={entry.to === '/'}
                className={({ isActive }) =>
                  `text-xs ${isActive ? 'font-semibold text-slate-900 underline underline-offset-4' : 'text-gray-500 hover:text-slate-800'}`
                }
              >
                {entry.label}
              </NavLink>
            ) : (
              <span key={entry.group} className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="text-[10px] font-medium tracking-wide text-gray-400">{entry.group}</span>
                {entry.items
                  .filter((item) => !item.authOnly || isAuthenticated)
                  .map((item) =>
                  item.raw ? (
                    <a
                      key={item.to}
                      href={item.to}
                      target="_blank"
                      rel="noreferrer"
                      data-testid={`nav-raw-${item.to}`}
                      className="text-xs text-gray-500 underline decoration-dotted underline-offset-4 hover:text-slate-800"
                    >
                      {item.label}
                    </a>
                  ) : (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={({ isActive }) =>
                        `text-xs ${isActive ? 'font-semibold text-slate-900 underline underline-offset-4' : 'text-gray-500 hover:text-slate-800'}`
                      }
                    >
                      {item.label}
                      {item.badge && (
                        <span data-testid={`nav-badge-${item.to}`} className="ml-1 rounded bg-amber-100 px-1 py-px text-[9px] font-medium text-amber-700">
                          {item.badge}
                        </span>
                      )}
                    </NavLink>
                  ),
                )}
              </span>
            ),
          )}
        </nav>
      </header>
      <div className="mx-auto mt-3 w-full max-w-7xl px-4">
        <LayerIndicator current={layer} />
      </div>
      {/*
        二期改版批1：三栏版式（左流程栏／中内容／右我的+AI助手）。
        小屏：左右栏默认折叠，点按钮展开为覆盖层（⛔ 不得因改版致移动端不可用）。
      */}
      <div className="mx-auto flex w-full max-w-7xl items-start gap-4 px-4 py-4">
        <button
          data-testid="rail-toggle-left"
          onClick={() => setShowLeft((v) => !v)}
          className="fixed bottom-4 left-4 z-50 rounded-full bg-slate-800 px-3 py-2 text-xs text-white shadow-lg lg:hidden"
        >
          {showLeft ? '收起流程' : '流程'}
        </button>
        <button
          data-testid="rail-toggle-right"
          onClick={() => setShowRight((v) => !v)}
          className="fixed bottom-4 right-4 z-50 rounded-full bg-indigo-600 px-3 py-2 text-xs text-white shadow-lg lg:hidden"
        >
          {showRight ? '收起助手' : '我的·助手'}
        </button>
        <div
          data-testid="rail-left"
          className={`w-60 shrink-0 lg:sticky lg:top-24 lg:block ${
            showLeft ? 'fixed inset-y-0 left-0 z-40 overflow-y-auto bg-gray-50 p-4' : 'hidden'
          }`}
        >
          <ProcessRail />
        </div>
        <main data-testid="main-col" className="min-w-0 flex-1">
          <Outlet />
        </main>
        <div
          data-testid="rail-right"
          className={`w-72 shrink-0 lg:sticky lg:top-24 lg:block ${
            showRight ? 'fixed inset-y-0 right-0 z-40 overflow-y-auto bg-gray-50 p-4' : 'hidden'
          }`}
        >
          <RightRail />
        </div>
      </div>
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
