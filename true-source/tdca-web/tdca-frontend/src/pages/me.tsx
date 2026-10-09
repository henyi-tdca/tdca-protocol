// =============================================================================
// TDCA 制度水印
// FC-ID: KIMI-WEB-DB-TASK-001-M5 | 目标函数: /me 个人后台（人类用户一屏聚合）
// 约束矩阵: M5-PLAN §三.1（六区块）+ 裁定②（只见自己名下）+ ID92（simulated 标注）
// 预期分配: MePage（会话卡 + 签批待办红签置顶 + 我的智能体 + 我批过的 + 沙盒 + 治理）
// 批 1 扩充（2026-10-09 用户控制台 P1）: 频道直达条 + AI 意图导航 + 权属栏 + 准入判定历史 + 活动产物分页
// 改密入口（2026-10-09 最小实现令）: 账户安全卡（页内改密，调在册 POST /api/v1/me/password；仅本人、NCA 落链）
// =============================================================================
import { useState } from 'react'
import { Link } from 'react-router'
import { api } from '@/api/client'
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface MeData {
  session: { username: string; role: string; expires_at: string; last_register_nca_id?: string | null }
  pending_count: number
  my_agents: { agent_id: string; name: string; five_role: string | null; status: string; attestation_state: string; audit_count: number; data_provenance: string }[]
  my_pending_sign: { request_id: string; agent_id: string; request_type: string; urgency: string | null; reason: string | null; ts: string }[]
  my_decided: { request_id: string; agent_id: string; status: string; ts: string }[]
  my_sandbox: { apply_id: string; result: string | null; sea_snapshot?: string; ts: string }[]
  my_governance: { op: string; fuse_state: string | null; ts: string }[]
  my_assets?: { order_no: number; name: string; description: string | null; asset_count: number; data_provenance: string }[]
  my_grants?: { grant_id: string; subject_agent: string; scene_constraint: string; asset_order: string; status: string; nca_ref: string | null }[]
  my_ownership?: { record_id: string; work_title: string; jurisdiction_branch: string; status: string; nca_ref: string | null; data_provenance: string; created_at: string }[]
  my_config_records?: { run_id: string; result: string; asset_summary: string | null; scene: string | null; price_points: number | null; nca_ref: string | null; ts: string }[]
  my_points?: { balance: number; data_provenance: string; note: string }
  my_nca?: { nca_id: string; action: string; artifact_path: string | null; sha256_8: string | null; ts: string }[]
  note: string
}

const ROLE_LABEL: Record<string, string> = { founder: '创始人', operator: '运营者', viewer: '访客' }
const RESULT_LABEL: Record<string, string> = { admitted: '✅ 已入盒', denied: '❌ 未通过', pending: '⏳ 待审' }
/** 权属状态标注（P8a 既有口径：registered/amended/cancelled） */
const OWNERSHIP_STATUS: Record<string, string> = { registered: '🟢 已登记', amended: '🟡 已变更', cancelled: '⚫ 已注销' }

/** 运营面入口（operator/founder 可见）：直达已在架的运营操作页（2026-10-09 管理员账户配套） */
const OPERATOR_LINKS = [
  { to: '/toolshelf', name: '工具货架', desc: '上架工具（register 面已建，须 operator）' },
  { to: '/ops', name: '运维工单', desc: '建单 / 红线查看（四面已建，须 operator）' },
  { to: '/announcements', name: '公告栏', desc: '公告查看；发布面随用户控制台 P1 排期' },
] as const

/** 频道直达条（批 1 P1）：站内主要频道一键直达（路由以 pages.tsx 注册为准） */
const CHANNEL_LINKS = [
  { to: '/', name: '首页' },
  { to: '/market', name: '市场' },
  { to: '/cluster', name: '集群' },
  { to: '/toolshelf', name: '货架' },
  { to: '/library', name: '文库' },
  { to: '/announcements', name: '公告' },
  { to: '/ops', name: '运维' },
  { to: '/sandbox', name: '沙盒' },
  { to: '/audit', name: '审计' },
] as const

interface IntentResult {
  matched: boolean
  route: string
  title: string
  action: string
  guide: string[]
  alternatives?: { route: string; title: string }[]
}

/** AI 意图导航（批 1 P1）：只接在册 /api/v1/intent 规则表（确定性关键词匹配），零模型外呼、行为可审计 */
function AssistantBox() {
  const [q, setQ] = useState('')
  const [res, setRes] = useState<IntentResult | null>(null)
  const [err, setErr] = useState(false)
  const [busy, setBusy] = useState(false)
  const submit = async () => {
    const query = q.trim()
    if (!query || busy) return
    setBusy(true)
    try {
      const qs = new URLSearchParams({ q: query })
      const r = await api.get<IntentResult>(`/api/v1/intent?${qs}`)
      if (r.ok) {
        setRes(r.data)
        setErr(false)
      } else {
        setErr(true) // fail-closed：不猜测，提示走频道直达条
      }
    } finally {
      setBusy(false)
    }
  }
  return (
    <section data-testid="me-assistant" className="rounded-lg border border-indigo-200 bg-indigo-50 p-4">
      <h3 className="mb-2 text-sm font-semibold text-indigo-900">AI 助手 · 站内导航</h3>
      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && void submit()}
          placeholder="说你要做什么，例如：我要登记权属 / 查我的存证 / 去工具货架"
          data-testid="me-assistant-input"
          className="flex-1 rounded-md border border-indigo-200 bg-white px-3 py-1.5 text-sm"
        />
        <button
          onClick={() => void submit()}
          disabled={busy}
          data-testid="me-assistant-go"
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white disabled:opacity-50"
        >
          {busy ? '匹配中…' : '直达'}
        </button>
      </div>
      <p className="mt-1 text-[11px] text-indigo-700">规则表匹配、零模型外呼、可审计；命中给直达与操作指引。</p>
      {err && <p className="mt-2 text-xs text-amber-700" data-testid="me-assistant-err">意图服务暂不可用，请走上方频道直达条。</p>}
      {res && (
        <div className="mt-2 rounded-md bg-white p-3 text-sm" data-testid="me-assistant-result">
          <div className="font-medium text-gray-800">{res.title}</div>
          <Link to={res.route} data-testid="me-assistant-route" className="mt-1 inline-block text-xs font-medium text-emerald-700 underline">
            直达 {res.route} →
          </Link>
          <ul className="mt-1 list-disc pl-5 text-xs text-gray-600">
            {res.guide.map((g, i) => <li key={i}>{g}</li>)}
          </ul>
          {(res.alternatives ?? []).length > 0 && (
            <div className="mt-1 text-[11px] text-gray-500">
              备选：
              {(res.alternatives ?? []).map((a) => (
                <Link key={a.route} to={a.route} className="ml-2 text-emerald-700 underline">{a.title}</Link>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  )
}

/** 账户安全 · 修改密码（2026-10-09 最小实现令）：页内改密，调在册 POST /api/v1/me/password。
 *  旧密核验/新密强度/吊销本人其它会话/NCA 落链皆在服务端；前端只做入口与提示，不新增依赖。 */
function PasswordChangeCard() {
  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [msg, setMsg] = useState('')
  const [ok, setOk] = useState(false)
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    if (busy) return
    setMsg('')
    setOk(false)
    if (!oldPw || !newPw) { setMsg('旧密码与新密码均不得为空'); return }
    if (newPw.length < 8 || !/[A-Za-z]/.test(newPw) || !/\d/.test(newPw)) {
      setMsg('密码强度不足：至少 8 位且同时包含字母与数字')
      return
    }
    if (newPw !== confirmPw) { setMsg('两次输入的新密码不一致'); return }
    setBusy(true)
    try {
      const r = await api.post<{ changed: boolean; other_sessions_revoked: number; nca_ref: string; note: string }>(
        '/api/v1/me/password', { old_password: oldPw, new_password: newPw })
      if (r.ok) {
        setOk(true)
        setMsg(`密码已更换（本人其它会话已吊销 ${r.data.other_sessions_revoked} 个，当前会话保留）；存证 ${r.data.nca_ref}`)
        setOldPw('')
        setNewPw('')
        setConfirmPw('')
      } else if (r.status === 400) {
        // 前端已先校强度（不通过不发请求）→ 到达服务端的 400 即「旧密码错误」口径（2026-10-09 评估件落地）
        setMsg('旧密码核验未通过（HTTP 400）：请核对当前密码后重试')
      } else if (r.status === 401) {
        setMsg('会话已失效（HTTP 401），请重新登录后再试')
      } else {
        setMsg(`改密失败（HTTP ${r.status ?? '未知'}），请稍后重试`)
      }
    } finally {
      setBusy(false)
    }
  }

  const inputCls = 'rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm'
  return (
    <section data-testid="me-pwd" className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-2 text-sm font-semibold text-gray-800">账户安全 · 修改密码</h3>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
        <input type="password" data-testid="me-pwd-old" value={oldPw} onChange={(e) => setOldPw(e.target.value)}
               placeholder="当前密码" autoComplete="current-password" className={inputCls} />
        <input type="password" data-testid="me-pwd-new" value={newPw} onChange={(e) => setNewPw(e.target.value)}
               placeholder="新密码（至少 8 位，含字母与数字）" autoComplete="new-password" className={inputCls} />
        <input type="password" data-testid="me-pwd-confirm" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)}
               placeholder="再输一遍新密码" autoComplete="new-password" className={inputCls} />
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <button onClick={() => void submit()} disabled={busy} data-testid="me-pwd-submit"
                className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm text-white disabled:opacity-50">
          {busy ? '提交中…' : '更换密码'}
        </button>
        <span className="text-[11px] text-gray-400">仅本人可改本人密码；改后本人其它会话吊销（当前会话保留）；写动作落 NCA 存证链。</span>
      </div>
      {msg && <p data-testid="me-pwd-msg" className={`mt-2 text-xs ${ok ? 'text-emerald-700' : 'text-amber-700'}`}>{msg}</p>}
    </section>
  )
}

/** M5 个人后台：谁的数据谁可见（须登录；未登录自动引导） */
export function MePage() {
  const { status, data } = useApiGet<MeData>('/api/v1/me/dashboard')
  // 活动产物分页（批 1 P1）：dashboard 摘要之外经 /me/nca 追加分页明细，单一口径（按 nca_id 去重保险）
  const [ncaMore, setNcaMore] = useState<NonNullable<MeData['my_nca']>>([])
  const [ncaPage, setNcaPage] = useState(1)
  const [ncaTotal, setNcaTotal] = useState<number | null>(null)
  const [ncaLoading, setNcaLoading] = useState(false)
  const ncaSeen = new Set<string>()
  const ncaItems = [...(data?.my_nca ?? []), ...ncaMore].filter((n) =>
    ncaSeen.has(n.nca_id) ? false : (ncaSeen.add(n.nca_id), true))
  const loadMoreNca = async () => {
    if (ncaLoading) return
    setNcaLoading(true)
    try {
      const r = await api.get<{ total: number; items: NonNullable<MeData['my_nca']> }>(`/api/v1/me/nca?page=${ncaPage + 1}&limit=20`)
      if (r.ok) {
        setNcaMore((prev) => [...prev, ...(r.data.items ?? [])])
        setNcaTotal(typeof r.data.total === 'number' ? r.data.total : null)
        setNcaPage((p) => p + 1)
      }
    } finally {
      setNcaLoading(false)
    }
  }
  // 判定历史（集群准入闸门）：只列 CLUSTER_ADMIT* 三类判定（DENY/SANDBOX/ADMIT）
  const admitItems = (data?.my_nca ?? []).filter((n) => n.action.startsWith('CLUSTER_ADMIT'))
  const admitLabel = (a: string) => (a === 'CLUSTER_ADMIT' ? '✅ 准入' : a.endsWith('_SANDBOX') ? '🧪 沙盒放行' : '❌ 未准入')

  return (
    <PageShell
      title="个人后台（我的）"
      dataSource="M5 GET /api/v1/me/dashboard（六区块一次聚合）"
      permission="须登录（M3 会话，谁的数据谁可见）"
      description="你的智能体、待你签批的请求、你批过的记录、你的沙盒申请与治理操作，一屏看全。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中…</p>}
      {status === 'fail' && (
        <div data-testid="me-login-required" className="max-w-md rounded border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          这里是你自己的后台，需要先登录才能看。
          <Link to="/auth" className="ml-2 font-medium text-emerald-700 underline">去登录 →</Link>
        </div>
      )}
      {status === 'ok' && data && (
        <div className="space-y-5">
          {/* 频道直达条（批 1 P1） */}
          <nav data-testid="me-channels" className="flex flex-wrap gap-2">
            {CHANNEL_LINKS.map((c) => (
              <Link key={c.to} to={c.to} data-testid={`me-ch-${c.to === '/' ? 'home' : c.to.slice(1)}`}
                    className="rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-600 hover:border-emerald-400 hover:text-emerald-700">
                {c.name}
              </Link>
            ))}
          </nav>
          {/* 会话卡 + 红签待办 */}
          <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div data-testid="me-session" className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="text-xs text-gray-500">当前登录</div>
              <div className="mt-1 text-lg font-semibold text-gray-800">
                {data.session.username}
                <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{ROLE_LABEL[data.session.role] ?? data.session.role}</span>
              </div>
              <div className="mt-1 text-xs text-gray-400">会话有效至 {data.session.expires_at.slice(0, 19).replace('T', ' ')}</div>
              {data.session.last_register_nca_id && (
                <div data-testid="me-register-nca" className="mt-1 text-xs text-gray-400">
                  最近缔约存证 <span className="font-mono text-gray-500">{data.session.last_register_nca_id}</span>
                  （注册即缔约已落 NCA 链，可经审计透明页自查在链）
                </div>
              )}
            </div>
            <div data-testid="me-pending-card" className={`rounded-lg border p-4 ${data.pending_count > 0 ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-white'}`}>
              <div className="text-xs text-gray-500">待我签批</div>
              <div className={`mt-1 text-2xl font-bold ${data.pending_count > 0 ? 'text-red-700' : 'text-gray-700'}`}>{data.pending_count} 件</div>
              {data.pending_count > 0 && <Link to="/attestation/dynamic" className="text-xs font-medium text-red-700 underline">去签批 →</Link>}
            </div>
          </section>

          {/* 账户安全 · 修改密码（最小实现令：页内改密入口） */}
          <PasswordChangeCard />

          {/* 运营管理入口（仅 operator/founder 可见；后端闸门照守，前端只是入口） */}
          {(data.session.role === 'operator' || data.session.role === 'founder') && (
            <section data-testid="me-operator" className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
              <h3 className="mb-2 text-sm font-semibold text-emerald-900">运营管理（{ROLE_LABEL[data.session.role]}）</h3>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                {OPERATOR_LINKS.map((l) => (
                  <Link key={l.to} to={l.to} data-testid={`me-op-link-${l.to.slice(1)}`}
                        className="block rounded-md border border-emerald-200 bg-white p-3 hover:border-emerald-400">
                    <div className="text-sm font-medium text-emerald-800">{l.name} →</div>
                    <div className="mt-0.5 text-[11px] text-gray-500">{l.desc}</div>
                  </Link>
                ))}
              </div>
              <p className="mt-2 text-[11px] text-emerald-700">公告发布、CI 触发等更多运营操作面随「用户控制台」P1 排期；权限以服务端角色闸为准。</p>
            </section>
          )}

          {/* AI 意图导航（零模型外呼；接在册 /api/v1/intent） */}
          <AssistantBox />

          {/* 我的智能体 */}
          <section data-testid="me-agents" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">我的智能体（{data.my_agents.length}）</h3>
            {data.my_agents.length === 0 && <p className="text-sm text-gray-400">名下暂无智能体——去 <Link to="/studio" className="text-emerald-700 underline">Agent Studio</Link> 创建一只</p>}
            <table className="w-full text-sm">
              <tbody>
                {data.my_agents.map((a) => (
                  <tr key={a.agent_id} data-agent={a.agent_id} className="border-b border-gray-100">
                    <td className="py-1.5">
                      <Link to={`/agents/${a.agent_id}`} className="font-medium text-emerald-700 hover:underline">{a.name}</Link>
                      <span className="ml-2 font-mono text-[10px] text-gray-400">{a.agent_id}</span>
                    </td>
                    <td className="py-1.5 text-xs text-gray-500">{a.attestation_state === 'valid' ? '🟢 签章有效' : a.attestation_state === 'expiring' ? '🟡 将过期' : '🔴 失效'}</td>
                    <td className="py-1.5 text-xs text-gray-500">审计 {a.audit_count} 次</td>
                    <td className="py-1.5">{a.data_provenance !== 'real' && <SimulatedBadge nature={a.data_provenance as 'simulated'} />}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {/* 待我签批明细 */}
          {data.my_pending_sign.length > 0 && (
            <section data-testid="me-pending-list" className="rounded-lg border border-red-100 p-4">
              <h3 className="mb-2 text-sm font-semibold text-red-800">签批待办明细</h3>
              {data.my_pending_sign.map((r) => (
                <div key={r.request_id} className="border-b border-red-50 py-1.5 text-xs text-gray-600">
                  <span className="font-mono">{r.request_id}</span> · {r.agent_id} · {r.urgency === 'urgent' ? '🔴 紧急' : r.urgency ?? '普通'} · {r.reason}
                </div>
              ))}
            </section>
          )}

          {/* 资产 / 积分 / 配置权持有（2026-10-04 创始人明示补齐） */}
          <section className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            <div data-testid="me-assets" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">资产（五阶形态目录）</h3>
              {(data.my_assets ?? []).length === 0 && <p className="text-xs text-gray-400">暂无目录</p>}
              {(data.my_assets ?? []).map((a) => (
                <div key={a.order_no} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                  第{a.order_no}阶 · {a.name}
                  <span className="ml-1 text-gray-400">{a.description ?? ''}（{a.asset_count} 件）</span>
                  {a.data_provenance !== 'real' && <SimulatedBadge nature={a.data_provenance as 'simulated'} />}
                </div>
              ))}
              <p className="mt-1 text-[11px] text-gray-400">目录为全站共用形态索引；个人持有见「配置权持有」。</p>
            </div>
            <div data-testid="me-points" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">我的积分（站内）</h3>
              <div className="text-2xl font-bold text-gray-800">{data.my_points?.balance ?? 0}</div>
              <p className="mt-1 text-[11px] text-gray-400">
                {data.my_points?.note ?? '最小链结算记账'}
                {(data.my_points?.data_provenance ?? 'simulated') !== 'real' && (
                  <SimulatedBadge nature={(data.my_points?.data_provenance ?? 'simulated') as 'simulated'} />
                )}
              </p>
              <p className="mt-1 text-[11px] text-gray-400">口径：本人为出让方的最小链要约报价合计。</p>
            </div>
            <div data-testid="me-grants" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">我的场景配置权持有</h3>
              {(data.my_grants ?? []).length === 0 && (
                <p className="text-xs text-gray-400">暂无持有——配置类调用须先凭授权件过 P2 准入闸门</p>
              )}
              {(data.my_grants ?? []).map((g) => (
                <div key={g.grant_id} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                  <span className="font-mono">{g.grant_id}</span> · {g.subject_agent} · {g.status}
                  <span className="block text-[11px] text-gray-400">场景：{g.scene_constraint} ｜ {g.nca_ref ?? ''}</span>
                </div>
              ))}
            </div>
          </section>

          {/* 我的权属登记（P8a · 后端已按本人过滤，此处只渲染本人栏） */}
          <section data-testid="me-ownership" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">我的权属登记（{data.my_ownership?.length ?? 0}）</h3>
            {(data.my_ownership ?? []).length === 0 && (
              <p className="text-xs text-gray-400">暂无登记——去 <Link to="/ownership-registry" className="text-emerald-700 underline">权属登记管理</Link> 登记第一件</p>
            )}
            {(data.my_ownership ?? []).length > 0 && (
              <table className="w-full text-sm">
                <tbody>
                  {(data.my_ownership ?? []).map((o) => (
                    <tr key={o.record_id} data-record={o.record_id} className="border-b border-gray-100">
                      <td className="py-1.5 font-mono text-[11px] text-gray-500">{o.record_id}</td>
                      <td className="py-1.5 text-xs text-gray-700">{o.work_title}</td>
                      <td className="py-1.5 text-xs text-gray-500">{o.jurisdiction_branch}</td>
                      <td className="py-1.5 text-xs text-gray-500">{OWNERSHIP_STATUS[o.status] ?? o.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <Link to="/ownership-registry" className="mt-1 inline-block text-[11px] text-emerald-700 underline">登记 / 变更 / 注销 →</Link>
          </section>

          {/* 判定历史（集群准入闸门：只列 CLUSTER_ADMIT* 判定，摘要与 /me/nca 明细同链） */}
          <section data-testid="me-admits" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">我的准入判定（{admitItems.length}）</h3>
            {admitItems.length === 0 && <p className="text-xs text-gray-400">暂无判定记录</p>}
            {admitItems.map((n) => (
              <div key={n.nca_id} data-action={n.action} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                {admitLabel(n.action)} · <span className="font-mono text-[11px] text-gray-400">{n.nca_id}</span>
                <span className="block text-[11px] text-gray-400">{n.ts.slice(0, 19).replace('T', ' ')}</span>
              </div>
            ))}
          </section>

          {/* 配置记录 + 我的 NCA 存证 */}
          <section className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <div data-testid="me-config-records" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">我的配置记录（最小链）</h3>
              {(data.my_config_records ?? []).length === 0 && (
                <p className="text-xs text-gray-400">暂无记录——去 <Link to="/market-sim" className="text-emerald-700 underline">规范索引与沙盒最小链</Link> 跑一条最小链</p>
              )}
              {(data.my_config_records ?? []).map((r) => (
                <div key={r.run_id} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                  <span className="font-mono">{r.run_id}</span> · {r.result === 'settled' ? '✅ 已结算' : '❌ 未通过'} · {r.price_points ?? 0} 积分
                  <span className="block text-[11px] text-gray-400">{r.asset_summary} ｜ {r.scene} ｜ {r.ts.slice(0, 19).replace('T', ' ')}</span>
                </div>
              ))}
              <SimulatedBadge nature="simulated" />
            </div>
            <div data-testid="me-nca" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">
                我的活动产物 / NCA 存证（已显 {ncaItems.length}{ncaTotal !== null ? ` ／ 共 ${ncaTotal} 条` : ''}）
              </h3>
              {ncaItems.length === 0 && <p className="text-xs text-gray-400">暂无以个人身份落链的存证</p>}
              {ncaItems.map((n) => (
                <div key={n.nca_id} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                  <span className="font-mono text-[11px]">{n.nca_id}</span> · {n.action}
                  <span className="block truncate text-[11px] text-gray-400">{n.artifact_path} ｜ sha256_8={n.sha256_8} ｜ {n.ts.slice(0, 19).replace('T', ' ')}</span>
                </div>
              ))}
              <div className="mt-2 flex items-center gap-3">
                {(ncaTotal === null || ncaItems.length < ncaTotal) && (
                  <button
                    onClick={() => void loadMoreNca()}
                    disabled={ncaLoading}
                    data-testid="me-nca-more"
                    className="rounded-md border border-gray-300 bg-white px-3 py-1 text-xs text-gray-600 hover:border-emerald-400 disabled:opacity-50"
                  >
                    {ncaLoading ? '加载中…' : '加载更多'}
                  </button>
                )}
                <Link to="/audit" className="text-[11px] text-emerald-700 underline">审计透明页查全链 →</Link>
              </div>
            </div>
          </section>

          {/* 我批过的 + 沙盒 + 治理（三栏） */}
          <section className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            <div data-testid="me-decided" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">我批过的</h3>
              {data.my_decided.length === 0 && <p className="text-xs text-gray-400">暂无记录</p>}
              {data.my_decided.map((r) => (
                <div key={r.request_id} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                  <span className="font-mono">{r.request_id}</span> · {r.status === 'approved' ? '✅ 批准' : r.status === 'rejected' ? '❌ 拒绝' : r.status}
                </div>
              ))}
            </div>
            <div data-testid="me-sandbox" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">我的沙盒申请</h3>
              {data.my_sandbox.length === 0 && <p className="text-xs text-gray-400">暂无申请</p>}
              {data.my_sandbox.map((a) => (
                <div key={a.apply_id} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                  <span className="font-mono">{a.apply_id}</span> · {RESULT_LABEL[a.result ?? 'pending'] ?? a.result}
                </div>
              ))}
            </div>
            <div data-testid="me-governance" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">我的治理操作</h3>
              {data.my_governance.length === 0 && <p className="text-xs text-gray-400">暂无操作</p>}
              {data.my_governance.map((g, i) => (
                <div key={i} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                  {g.op === 'huf_sign' ? '✍️ HUF 签批' : '🛑 紧急熔断'} {g.fuse_state ? `· ${g.fuse_state}` : ''}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </PageShell>
  )
}
