// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: P3 /formal 形式化与实验线结论入站（上站）
// 约束矩阵: 期一段二追加四要件（结论面/性质标注/入站≠入主仓≠对外）
// 复用: PageShell / SimulatedBadge / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface ConclusionView {
  conclusion_id: string
  claim_text: string
  data_nature: string
  scope_note: string | null
}

const NATURE_LABEL: Record<string, string> = {
  'formal-proved': '形式化已证',
  simulated: '有限模型模拟',
  assessed: '评估判断',
}

export function FormalPage() {
  const [claim, setClaim] = useState('')
  const [nature, setNature] = useState('formal-proved')
  const [scope, setScope] = useState('')
  const [msg, setMsg] = useState('')
  const [rows, setRows] = useState<ConclusionView[]>([])

  const load = async () => {
    const r = await api.get<{ data: { conclusions: ConclusionView[] } }>(
      '/api/v1/formal/conclusion/list')
    if (r.ok) setRows(r.data.data.conclusions)
  }
  useEffect(() => { void load() }, [])

  const onSubmit = async () => {
    setMsg('')
    const r = await api.post<{ data: { conclusion_id: string } }>(
      '/api/v1/formal/conclusion',
      { claim_text: claim, data_nature: nature, scope_note: scope })
    if (!r.ok) { setMsg(`入站失败：${r.reason}`); return }
    setMsg(`已入站：${r.data.data.conclusion_id}（入站 ≠ 入主仓 ≠ 对外）`)
    setClaim(''); setScope('')
    void load()
  }

  return (
    <PageShell
      title="形式化与实验线结论入站（P3）"
      dataSource="A-14 /api/v1/formal/*（只做结论面；三禁机验）"
      permission="登录 DID"
      description="只收结论面：不转公式、不引数值、不带内部编号；数据性质随文显式标注。">
      <section data-testid="formal-ingest">
        <h2>结论入站</h2>
        <SimulatedBadge nature="simulated" />
        <div>
          <textarea
            aria-label="结论面文字"
            placeholder="纯文字结论（禁公式符号、数值引用、内部编号）"
            value={claim} onChange={(e) => setClaim(e.target.value)} />
          <select value={nature} onChange={(e) => setNature(e.target.value)} aria-label="数据性质">
            <option value="formal-proved">形式化已证</option>
            <option value="simulated">有限模型模拟</option>
            <option value="assessed">评估判断</option>
          </select>
          <input placeholder="适用边界（条件形态必填）" value={scope}
            onChange={(e) => setScope(e.target.value)} />
          <button onClick={onSubmit}>提交入站</button>
        </div>
        {msg && <p role="status">{msg}</p>}
      </section>
      <section data-testid="formal-list">
        <h2>入站清单</h2>
        <ul>
          {rows.map((c) => (
            <li key={c.conclusion_id}>
              [{NATURE_LABEL[c.data_nature] ?? c.data_nature}] {c.claim_text}
              {c.scope_note ? `（边界：${c.scope_note}）` : ''}
            </li>
          ))}
        </ul>
      </section>
    </PageShell>
  )
}
