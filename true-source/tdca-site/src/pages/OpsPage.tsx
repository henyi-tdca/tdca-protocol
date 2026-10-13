// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: P7 /ops 站点运维端（上站）
// 约束矩阵: 组三 P7（红线八项写死；触碰升 DCD；上线 NCA 存证＋对账可回滚）
// 复用: PageShell / SimulatedBadge / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/lib/client'
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'

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

  const load = async () => {
    const r = await api.get<{ red_lines: RedLine[] }>('/api/v1/ops/redlines')
    if (r.ok) setRedlines(r.data.red_lines)
    const t = await api.get<{ tickets: Ticket[] }>('/api/v1/ops/tickets')
    if (t.ok) setTickets(t.data.tickets)
  }
  useEffect(() => { void load() }, [])

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
      permission="登录 DID（操作须 operator）"
      description="应用测试期运维工作台：反馈→红线分类→提案→沙盒→上线；触碰根本制度即升 DCD，运维端无权处置。">
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
    </PageShell>
  )
}
