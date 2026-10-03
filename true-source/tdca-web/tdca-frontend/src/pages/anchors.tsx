// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: P6 /anchors 模拟外部锚与版权事件（上站）
// 约束矩阵: 组三 P6（三锚 SIMULATED 硬标注；权属登记事件＝登记/变更/注销）
// 复用: PageShell / SimulatedBadge / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface AnchorStatus {
  simulated: boolean
  anchors: Record<string, string>
  components: Record<string, string>
}

interface CEvent {
  event_id: string
  event_type: string
  work_title: string
  owner_ref: string
  template_ref: string
  nca_ref: string
}

const EVENT_LABEL: Record<string, string> = {
  register: '登记',
  amend: '变更',
  cancel: '注销',
}

export function AnchorsPage() {
  const [status, setStatus] = useState<AnchorStatus | null>(null)
  const [events, setEvents] = useState<CEvent[]>([])
  const [msg, setMsg] = useState('')
  const [eventType, setEventType] = useState('register')
  const [title, setTitle] = useState('')
  const [owner, setOwner] = useState('')
  const [lineage, setLineage] = useState('')
  const [note, setNote] = useState('')

  const load = async () => {
    const r = await api.get<AnchorStatus>('/api/v1/anchor/status')
    if (r.ok) setStatus(r.data)
    const e = await api.get<{ events: CEvent[] }>('/api/v1/anchor/copyright-events')
    if (e.ok) setEvents(e.data.events)
  }
  useEffect(() => { void load() }, [])

  const onSubmit = async () => {
    setMsg('')
    const r = await api.post<{ event_id: string; template_ref: string }>(
      '/api/v1/anchor/copyright-event',
      { event_type: eventType, work_title: title, owner_ref: owner,
        source_lineage: lineage, note })
    if (!r.ok) { setMsg(`事件登记失败：${r.reason}`); return }
    setMsg(`已落 NCA 链：${r.data.event_id}（${r.data.template_ref}；三锚全 SIMULATED）`)
    setTitle(''); setLineage(''); setNote('')
    void load()
  }

  return (
    <PageShell
      title="模拟外部锚与版权事件（P6）"
      dataSource="A-17 /api/v1/anchor/*（三锚 SIMULATED；权属登记事件落 NCA 链）"
      permission="登录 DID"
      description="版权链（NCA 链）／结算（站内积分）／税务（金税四期功能）三锚全站内模拟；版权事件＝登记／变更／注销。">
      <section data-testid="anchor-status">
        <h2>三锚状态</h2>
        <SimulatedBadge nature="simulated" />
        {status && (
          <div>
            <ul>
              {Object.entries(status.anchors).map(([k, v]) => (
                <li key={k}><strong>{k}</strong>：{v}</li>
              ))}
            </ul>
            <h3>组件在位核查</h3>
            <ul>
              {Object.entries(status.components).map(([k, v]) => (
                <li key={k}>{k} → {v}</li>
              ))}
            </ul>
          </div>
        )}
      </section>
      <section data-testid="anchor-events">
        <h2>权属登记事件（登记／变更／注销）</h2>
        <p>转让／许可属权利处分，⛔ 本期不做（归 8b）。</p>
        <div>
          <select value={eventType} onChange={(e) => setEventType(e.target.value)} aria-label="事件类型">
            <option value="register">登记</option>
            <option value="amend">变更</option>
            <option value="cancel">注销</option>
          </select>
          <input placeholder="作品／元函数名称" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input placeholder="权属主体引用" value={owner} onChange={(e) => setOwner(e.target.value)} />
          <input placeholder="生成来源谱系（登记必填）" value={lineage} onChange={(e) => setLineage(e.target.value)} />
          <input placeholder="事由备注" value={note} onChange={(e) => setNote(e.target.value)} />
          <button onClick={onSubmit}>落链登记</button>
        </div>
        {msg && <p role="status">{msg}</p>}
        <ul>
          {events.map((e) => (
            <li key={e.event_id}>
              [{EVENT_LABEL[e.event_type] ?? e.event_type}] {e.work_title} · {e.owner_ref}
              （{e.template_ref} · {e.nca_ref}）
            </li>
          ))}
        </ul>
      </section>
    </PageShell>
  )
}
