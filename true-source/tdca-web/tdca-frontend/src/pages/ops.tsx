// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: P7 /ops 站点运维端（上站）
// 约束矩阵: 组三 P7（红线八项写死；触碰升 DCD；上线 NCA 存证＋对账可回滚）
// 复用: PageShell / SimulatedBadge / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '@/api/client'
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface RedLine {
  key: string
  name: string
  index: string
}

interface Ticket {
  ticket_id: string
  title: string
  status: string
  redline_hit: string | null
}

export function OpsPage() {
  const [redlines, setRedlines] = useState<RedLine[]>([])
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [msg, setMsg] = useState('')
  const [title, setTitle] = useState('')
  const [desc, setDesc] = useState('')
  const [ticketId, setTicketId] = useState('')
  const [logToday, setLogToday] = useState<{ filled: boolean; missing_streak: number } | null>(null)

  // ACCESS-FIX-001-AMEND-1 交付三（块四移植）：管理面内容须管理员身份（角色取既有 /me 会话，⛔ 不造新标识）
  const me = useApiGet<{ session: { role: string } }>('/api/v1/me/dashboard')
  const isAdmin =
    me.status === 'ok' &&
    (me.data?.session.role === 'operator' || me.data?.session.role === 'founder')

  useEffect(() => {
    if (!isAdmin) return
    void api.get<{ filled: boolean; missing_streak: number }>('/api/v1/ops/logs/today')
      .then((r) => { if (r.ok) setLogToday(r.data) })
  }, [isAdmin])

  const load = async () => {
    const r = await api.get<{ red_lines: RedLine[] }>('/api/v1/ops/redlines')
    if (r.ok) setRedlines(r.data.red_lines)
    const t = await api.get<{ tickets: Ticket[] }>('/api/v1/ops/tickets')
    if (t.ok) setTickets(t.data.tickets)
  }
  useEffect(() => { if (isAdmin) void load() }, [isAdmin])

  const onFeedback = async () => {
    setMsg('')
    const r = await api.post<{ ticket_id: string }>(
      '/api/v1/ops/feedback', { title, description: desc })
    if (!r.ok) { setMsg(`反馈失败：${r.reason}`); return }
    setMsg(`已入池：${r.data.ticket_id}（INTAKE）`)
    setTitle(''); setDesc('')
    void load()
  }

  const act = async (path: string) => {
    setMsg('')
    const r = await api.post<{ status: string; redline_hit?: string[] }>(
      path, { ticket_id: ticketId })
    if (!r.ok) { setMsg(`操作失败：${r.reason}`); return }
    setMsg(`${path.split('/').pop()} → ${r.data.status}` +
      (r.data.redline_hit ? `（命中：${r.data.redline_hit.join('、')}）` : ''))
    void load()
  }

  return (
    <PageShell
      title="站点运维端（P7）"
      dataSource="A-18 /api/v1/ops/*（红线八项分类器；NCA 存证＋reconcile 对账）"
      permission="登录 DID（操作须 operator；管理面内容须管理员身份登录后可见）"
      description="应用测试期运维工作台：反馈→红线分类→提案→沙盒→上线；触碰根本制度即升 DCD，运维端无权处置。">
      <p className="text-xs">
        <Link to="/ops/me" data-testid="ops-me-entry" className="text-blue-600 underline hover:text-blue-800">
          运维我的（站与服务的）→
        </Link>
        <span className="ml-2 text-gray-400">运维管理员个人面：六栏只读占位，与用户「我的」两套独立。</span>
      </p>
      {isAdmin && logToday && (
        <p className="text-xs" data-testid="ops-logs-entry">
          <Link to="/ops/logs" className="text-blue-600 underline hover:text-blue-800">
            运维日志（每日填写）{!logToday.filled && <span data-testid="ops-logs-red-dot" title="今日未填">🔴</span>}
          </Link>
          <Link to="/ops/logs/list" className="ml-3 text-blue-600 underline hover:text-blue-800">列表与导出 →</Link>
          {logToday.missing_streak >= 2 && (
            <span data-testid="ops-logs-escalation" className="ml-2 text-red-600">
              ⚠ 连续 {logToday.missing_streak} 日未填——已入 P7 工单池上报运维负责人
            </span>
          )}
        </p>
      )}
      {!isAdmin ? (
        <section data-testid="ops-admin-only" className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          须管理员身份登录后可见。一般用户请从「我的」进入个人面；本入口对所有人保持可见。
        </section>
      ) : (
        <>
      <section data-testid="ops-redlines">
        <h2>根本制度红线（八项·写死）</h2>
        <SimulatedBadge nature="simulated" />
        <ul>
          {redlines.map((l) => (
            <li key={l.key}>
              <strong>{l.name}</strong>
              <details><summary>索引入口</summary><p>{l.index}</p></details>
            </li>
          ))}
        </ul>
      </section>
      <section data-testid="ops-tickets">
        <h2>工单</h2>
        <div>
          <input placeholder="标题" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input placeholder="描述" value={desc} onChange={(e) => setDesc(e.target.value)} />
          <button onClick={onFeedback}>提交反馈</button>
        </div>
        <div>
          <input placeholder="工单号" value={ticketId}
            onChange={(e) => setTicketId(e.target.value)} aria-label="工单号" />
          <button onClick={() => act('/api/v1/ops/classify')}>红线分类</button>
          <button onClick={() => act('/api/v1/ops/sandbox')}>沙盒验证</button>
          <button onClick={() => act('/api/v1/ops/release')}>上线登记</button>
        </div>
        {msg && <p role="status">{msg}</p>}
        <ul>
          {tickets.map((t) => (
            <li key={t.ticket_id}>
              [{t.status}] {t.title}（{t.ticket_id}）
              {t.redline_hit ? ` · 红线：${t.redline_hit}` : ''}
            </li>
          ))}
        </ul>
      </section>
        </>
      )}
    </PageShell>
  )
}
