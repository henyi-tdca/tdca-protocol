// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期 C-1 授权配置面板页（L1SI193-B1-001）
// 约束矩阵: 施工令 §二——五操作（各成一表单流程、共用八字段）＋四要件缺一即拒（提示缺哪项）
//   ＋本人签署（⛔ 智能体代签代填）＋五态机（draft→pending_sign→active→suspended/revoked）
//   ＋撤回路径页面上写明并可用；可靠性九项（GK-03）后端同守
// 复用: PageShell / api（会话令牌自动注入）；后端 /api/v1/authorization/draft|sign|revoke
//   ＋ GET /{auth_id} 公开读（范围/期限/状态；⛔ 凭据值）
// ⛔ 部署、⛔ 对外可见（S-4）；本页受护（未登录重定向 /auth）
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/lib/client'
import { PageShell } from '@/components/PageShell'

const OPERATIONS: { key: string; label: string; hint: string }[] = [
  { key: 'pre_accept', label: '预收权', hint: '授权件已预收、待生效确认' },
  { key: 'activate', label: '实时授权', hint: '授权即时生效' },
  { key: 'append', label: '追加授权', hint: '范围／构成追加' },
  { key: 'amend_terms', label: '许可变更', hint: '许可条款变更' },
  { key: 'sub_grant', label: '多层级授权', hint: '再授权层级操作' },
]

const CONDITION_ITEMS: { key: string; label: string }[] = [
  { key: 'may_sub_grant', label: '可否再授权' },
  { key: 'may_commercialize', label: '可否商用' },
  { key: 'attribution_required', label: '须否标注来源' },
]

interface DraftResult {
  auth_id: string
  status: string
  operation: string
  operation_label: string
  nca_seq: string
  note: string
}

interface PublicView {
  auth_id: string
  operation: string
  operation_label: string
  status: string
  subject: string
  scope: string
  term: string
  conditions: Record<string, string>
  nca_seq: string
  note: string
}

const LS_KEY = 'tdca_auth_panel_my_ids'

function myIds(): string[] {
  try {
    const v = JSON.parse(localStorage.getItem(LS_KEY) ?? '[]')
    return Array.isArray(v) ? v.filter((x) => typeof x === 'string') : []
  } catch {
    return []
  }
}
function rememberId(id: string) {
  const v = myIds().filter((x) => x !== id)
  v.unshift(id)
  localStorage.setItem(LS_KEY, JSON.stringify(v.slice(0, 20)))
}

export function AuthorizationPanelPage() {
  const [op, setOp] = useState('activate')
  const [grantor, setGrantor] = useState('')
  const [grantee, setGrantee] = useState('')
  const [subject, setSubject] = useState('')
  const [scope, setScope] = useState('')
  const [term, setTerm] = useState('')
  const [cond, setCond] = useState<Record<string, string>>({
    may_sub_grant: '', may_commercialize: '', attribution_required: '' })
  const [credRef, setCredRef] = useState('')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')
  const [result, setResult] = useState<DraftResult | null>(null)
  const [mine, setMine] = useState<PublicView[]>([])

  const loadMine = async () => {
    const out: PublicView[] = []
    for (const id of myIds()) {
      const r = await api.get<PublicView>(`/api/v1/authorization/${id}`)
      if (r.ok) out.push(r.data)
    }
    setMine(out)
  }
  useEffect(() => { void loadMine() }, [])

  const onDraft = async (submit: boolean) => {
    if (busy) return
    setBusy(true)
    setMsg('')
    setResult(null)
    const r = await api.post<DraftResult>('/api/v1/authorization/draft', {
      operation: op,
      grantor, grantee, subject, scope, term,
      conditions: cond,
      credential_ref: credRef,
      submit,
    })
    setBusy(false)
    if (!r.ok) {
      // 四要件缺一即拒：后端提示缺哪一项（照原文显示）
      setMsg(`未受理：${r.detail ?? r.reason}`)
      return
    }
    setResult(r.data)
    rememberId(r.data.auth_id)
    setMsg(r.data.note)
    void loadMine()
  }

  const onSign = async (authId: string) => {
    setMsg('')
    const r = await api.post<DraftResult>('/api/v1/authorization/sign', { auth_id: authId })
    setMsg(r.ok ? `已签署：${authId}（生效 active）` : `签署未受理：${r.detail ?? r.reason}`)
    void loadMine()
  }

  const onRevoke = async (authId: string) => {
    setMsg('')
    const r = await api.post<DraftResult>('/api/v1/authorization/revoke',
      { auth_id: authId, note: '本人于面板撤回' })
    setMsg(r.ok ? `已撤回：${authId}（既往记录保留不抹）` : `撤回未受理：${r.detail ?? r.reason}`)
    void loadMine()
  }

  return (
    <PageShell
      title="授权配置面板（C-1）"
      dataSource="POST /api/v1/authorization/draft|sign|revoke ＋ GET /api/v1/authorization/{auth_id}（公开读）"
      permission="登录 DID（起草／签署／撤回须本人；公开查免会话）"
      description="五操作授权件：八字段逐项填、四要件缺一即拒；签署须本人（⛔ 智能体代签代填）；五态可查；每次推进落 NCA 存证。">
      <div data-testid="authorization-panel" className="max-w-2xl space-y-6">

        <section className="space-y-3 rounded border p-4">
          <h2 className="text-base font-semibold">第一步·选操作（五操作，各成一流程）</h2>
          <div className="flex flex-wrap gap-2">
            {OPERATIONS.map((o) => (
              <button key={o.key} type="button"
                onClick={() => setOp(o.key)}
                className={`rounded px-3 py-1 text-sm border ${op === o.key ? 'bg-gray-900 text-white' : 'bg-white'}`}>
                {o.label}
              </button>
            ))}
          </div>
          <p className="text-sm text-gray-600">{OPERATIONS.find((o) => o.key === op)?.hint}</p>
        </section>

        <section className="space-y-3 rounded border p-4">
          <h2 className="text-base font-semibold">第二步·填八字段（逐项写，⛔「等」字兜底）</h2>
          <label className="block text-sm">① 授权方（主体名称，⛔ 昵称/账号名）
            <input value={grantor} onChange={(e) => setGrantor(e.target.value)}
              className="mt-1 w-full rounded border px-2 py-1" /></label>
          <label className="block text-sm">② 被授权方（主体名称）
            <input value={grantee} onChange={(e) => setGrantee(e.target.value)}
              className="mt-1 w-full rounded border px-2 py-1" /></label>
          <label className="block text-sm">③ 标的（配置权／内容／工具／数据）
            <input value={subject} onChange={(e) => setSubject(e.target.value)}
              className="mt-1 w-full rounded border px-2 py-1" /></label>
          <label className="block text-sm">④ 范围（场景、期限、次数或用量、地域——逐项写）
            <textarea value={scope} onChange={(e) => setScope(e.target.value)}
              className="mt-1 w-full rounded border px-2 py-1" rows={2} /></label>
          <label className="block text-sm">⑤ 期限（起止，或「至撤回为止」）
            <input value={term} onChange={(e) => setTerm(e.target.value)}
              className="mt-1 w-full rounded border px-2 py-1" /></label>
          <div className="text-sm">⑥ 条件（三问，各填 是／否）
            <div className="mt-1 flex gap-4">
              {CONDITION_ITEMS.map((c) => (
                <label key={c.key}>{c.label}
                  <select value={cond[c.key]} className="ml-1 rounded border px-1 py-1"
                    onChange={(e) => setCond({ ...cond, [c.key]: e.target.value })}>
                    <option value="">未选</option>
                    <option value="是">是</option>
                    <option value="否">否</option>
                  </select>
                </label>
              ))}
            </div>
          </div>
          <label className="block text-sm">⑦ 签署（须本人；本页签署步即本人确认）
            <span className="ml-2 text-gray-600">——签署在第三步完成</span></label>
          <label className="block text-sm">⑧ 凭据号（选填；只回指针，⛔ 值不入件）
            <input value={credRef} onChange={(e) => setCredRef(e.target.value)}
              className="mt-1 w-full rounded border px-2 py-1" /></label>
        </section>

        <section className="space-y-3 rounded border p-4">
          <h2 className="text-base font-semibold">第三步·起草与签署（本人）</h2>
          <div className="flex gap-2">
            <button type="button" disabled={busy} onClick={() => void onDraft(false)}
              className="rounded border px-3 py-1 text-sm disabled:opacity-50">存草稿（draft）</button>
            <button type="button" disabled={busy} onClick={() => void onDraft(true)}
              className="rounded bg-gray-900 px-3 py-1 text-sm text-white disabled:opacity-50">
              提交待签（pending_sign）</button>
          </div>
          {result && (
            <p className="text-sm">编号 <code>{result.auth_id}</code>（{result.operation_label}）·
              状态 <b>{result.status}</b> · 存证 <code>{result.nca_seq}</code></p>
          )}
          <p className="text-sm text-gray-600">
            签署（须本人，⛔ 智能体代签代填）：在下方「我的授权件」对 pending_sign / draft 件点「本人签署」。
            撤回路径：对 active / pending_sign 件点「撤回」——撤回后已发生使用另记一笔，既往记录保留不抹。
          </p>
          {msg && <p className="text-sm text-amber-700" data-testid="panel-msg">{msg}</p>}
        </section>

        <section className="space-y-2 rounded border p-4">
          <h2 className="text-base font-semibold">我的授权件（本机记录编号，公开面回读）</h2>
          {mine.length === 0 && <p className="text-sm text-gray-500">还没有——起草一件后会记在这里。</p>}
          {mine.map((m) => (
            <div key={m.auth_id} className="flex flex-wrap items-center gap-2 text-sm border-b py-2">
              <code>{m.auth_id}</code>
              <span>{m.operation_label}</span>
              <span>状态 <b>{m.status}</b></span>
              <span className="text-gray-600">期限 {m.term}</span>
              {(m.status === 'pending_sign' || m.status === 'draft') && (
                <button type="button" onClick={() => void onSign(m.auth_id)}
                  className="rounded bg-gray-900 px-2 py-0.5 text-white">本人签署</button>
              )}
              {(m.status === 'pending_sign' || m.status === 'draft' || m.status === 'active') && (
                <button type="button" onClick={() => void onRevoke(m.auth_id)}
                  className="rounded border px-2 py-0.5">撤回</button>
              )}
              {m.status === 'suspended' && (
                <span className="text-amber-700">已熔断停链——须 operator 复核解冻</span>
              )}
            </div>
          ))}
        </section>

        <p className="text-xs text-gray-500">
          口径：本面板与「合约备案（P8b）」分立并存——<a className="underline" href="/authorization-registry">前往合约备案页</a>。
          全程模拟态标注；本页 ⛔ 对外可见前须过试验门＋灰度门。
        </p>
      </div>
    </PageShell>
  )
}
