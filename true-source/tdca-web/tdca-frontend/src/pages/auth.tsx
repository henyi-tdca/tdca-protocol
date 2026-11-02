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

// ── L1SI188-NAV-FIX-004 项4：登录墙三要素（只改文案，⛔ 不改鉴权逻辑/接口名/对外承诺）──
// 六条一级主栏（登录墙 26 路由中的六个一级落地栏，均经 PROTECTED 集与公共导航双重核对）；
// /ops 为页内自闸（非路由守卫重定向），不在六栏之列——第六栏取 /review（缔约评审，导航「我的」组在册入口）。
// 子路归并：/attestation/* → /attestation，/me/* → /me（含 /me/appeal、/me/node、/me/node/net）。
// 「登录后可见」逐条照实（取该栏在册元数据口径），无则写「在建」，⛔ 画饼。
const LOGIN_WALL_COPY: Record<string, { column: string; what: string; visible: string[] }> = {
  '/me': {
    column: '身份与账户（我的）',
    what: '个人私域总栏：本人身份、名下智能体与办理事务的聚合入口。',
    visible: ['我的智能体清单', '签批待办与我批过的', '沙盒申请与治理操作（一屏聚合）'],
  },
  '/studio': {
    column: '工作台（作业）',
    what: '智能体全生命周期作业栏：从诞生到出盒再到市场的办理面。',
    visible: ['智能体全生命周期办理（诞生→教育→沙盒→出盒终裁→市场→化合衍生）', 'HUF 签批通道'],
  },
  '/review': {
    column: '缔约评审',
    what: '缔约申请评审队列栏：申请的放行与谢绝留痕办理面（须登录＋审核身份）。',
    visible: ['缔约申请评审队列', '放行／谢绝留痕操作（写令牌校验）'],
  },
  '/agents': {
    column: '能力与观测（智能体集群）',
    what: '官方智能体运行观测栏：五大智能体的状态与协作拓扑。',
    visible: ['五大智能体面板（Trainer/Executor/Auditor/Service/Genie）', '确权状态灯', '协作拓扑'],
  },
  '/attestation': {
    column: '确权中心',
    what: '确权办理与公开留痕栏：待审、最近事件与历史，全部事件留痕可查。',
    visible: ['待审队列与最近事件', '确权统计', '元函数／动态／历史三个入口'],
  },
  '/governance': {
    column: '治理中心',
    what: '站内治理操作栏：签批、确权队列、紧急熔断与升级（须 HUF）。',
    visible: ['HUF 签批', '动态确权队列', '紧急熔断与 OTA'],
  },
}

/** 登录墙解析：精确命中 → 前缀归并（/attestation/*、/me/*）→ null（非六栏，走原通用口径） */
function resolveLoginWall(from: string): { key: string; copy: (typeof LOGIN_WALL_COPY)[string] } | null {
  const exact = LOGIN_WALL_COPY[from]
  if (exact) return { key: from, copy: exact }
  if (from.startsWith('/attestation')) return { key: '/attestation', copy: LOGIN_WALL_COPY['/attestation'] }
  if (from.startsWith('/me')) return { key: '/me', copy: LOGIN_WALL_COPY['/me'] }
  return null
}

/** F-2 统一 DID 认证入口：M3 账号密码登录（真实会话）+ 既有 DID 模拟态登录（保留） */
export function AuthPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { from?: string; expired?: boolean } | null
  const from = state?.from ?? '/'
  const expired = state?.expired === true
  const wall = from !== '/' ? resolveLoginWall(from) : null

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
      dataSource="账号体系鉴权 ＋ 网关鉴权中间件（启用时强制）"
      permission="公开"
      description="统一认证入口：账号密码登录后获得会话令牌，受保护路由（/agents /studio /attestation* /governance）方可访问。"
    >
      {wall && (
        /* L1SI188-NAV-FIX-004 项4：登录墙三要素（该栏是什么／登录后可见什么／登录入口就地可点） */
        <div data-testid="login-wall" className="mb-6 max-w-md rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div data-testid="login-wall-column" className="mb-1 text-sm font-semibold text-blue-900">
            「{wall.copy.column}」栏需登录
          </div>
          <p data-testid="login-wall-what" className="mb-2 text-xs leading-5 text-blue-800">
            {wall.copy.what}
          </p>
          <ul data-testid="login-wall-visible" className="mb-2 list-disc space-y-0.5 pl-5 text-xs leading-5 text-blue-800">
            {wall.copy.visible.map((v) => (
              <li key={v}>登录后可见：{v}</li>
            ))}
          </ul>
          <a
            href="#auth-account-form"
            data-testid="login-wall-goto-login"
            className="inline-block rounded bg-blue-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-800"
          >
            去登录（下方表单）
          </a>
        </div>
      )}
      {expired && (
        <div data-testid="auth-expired-notice" className="mb-4 max-w-md rounded border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
          会话已过期或在其他处登录。您之前的页面内容未丢失，重新登录后可返回继续。
        </div>
      )}
      <div id="auth-account-form" data-testid="auth-account-form" className="mb-6 max-w-md space-y-3 rounded border border-gray-200 bg-white p-4">
        <div className="text-xs font-semibold text-gray-700">账号登录（真实会话，2h 有效期）</div>
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
          忘记密码？本站点无自助重置通道，请联系站点管理员人工重置（渠道见帮助页）后重新登录。
        </p>
      </div>
      <div className="mb-2 max-w-md text-[10px] uppercase tracking-wide text-gray-400">降级通道：DID 模拟态登录（保留）</div>
      <div data-testid="auth-form" className="max-w-md space-y-4">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          模拟态登录 —— 真实鉴权由网关中间件兜底 <SimulatedBadge nature="simulated" />
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
          <label className="mb-1 block text-xs text-gray-600">HUF/API Token</label>
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
