import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router'
import { siteGet, sitePost, GateRequired, getWriteToken, setWriteToken } from '../lib/siteApi'
import GatePrompt from '../components/GatePrompt'

type JoinItem = {
  id: number
  channel: string
  applicant_kind: string
  display_name: string
  status: string
  nsfl_result: string
  reviewer_note?: string
  created_at: string
}

const statusLabel: Record<string, string> = {
  pending: '待审核', sandbox: '沙盒验证中', active: '已转正',
  rejected: '已谢绝', nsfl_rejected: '触负待复核',
}

export default function Review() {
  const [reviewer, setReviewer] = useState('')
  const [reviewerSet, setReviewerSet] = useState(false)
  const [writeTokenInput, setWriteTokenInput] = useState(getWriteToken())
  const [items, setItems] = useState<JoinItem[] | null>(null)
  const [needGate, setNeedGate] = useState(false)
  const [error, setError] = useState('')
  const [notes, setNotes] = useState<Record<number, string>>({})
  const [busy, setBusy] = useState<number | null>(null)

  const load = useCallback(async () => {
    try {
      const d = await siteGet<{ items: JoinItem[] }>('/join/list')
      setItems(d.items)
      setError('')
    } catch (e) {
      if (e instanceof GateRequired) setNeedGate(true)
      else setError(String(e instanceof Error ? e.message : e))
    }
  }, [])

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (reviewerSet) load() }, [reviewerSet, load])

  const act = async (id: number, action: 'approve' | 'reject') => {
    setBusy(id); setError('')
    try {
      await sitePost('/join/review',
        { join_request_id: id, action, note: notes[id] || null },
        { 'x-tdca-reviewer': reviewer })
      await load()
    } catch (e) {
      const err = e as Error & { status?: number; data?: { detail?: string } }
      setError(`#${id} ${action === 'approve' ? '放行' : '谢绝'}失败：HTTP ${err.status} ${err.data?.detail ?? err.message}`)
    } finally {
      setBusy(null)
    }
  }

  if (needGate) return <GatePrompt onOk={() => { setNeedGate(false); if (reviewerSet) load() }} />

  if (!reviewerSet) {
    return (
      <div className="mx-auto max-w-sm py-24 text-center">
        <Link to="/" className="text-sm text-muted-foreground">← 返回首页</Link>
        <h2 className="mt-4 text-xl font-bold">审核入口</h2>
        <p className="mt-2 text-sm text-muted-foreground">输入审核人标识（留痕用）与写令牌（放行/谢绝时校验，均只存本次会话）</p>
        <form className="mt-4 space-y-2" onSubmit={(e) => {
          e.preventDefault()
          setWriteToken(writeTokenInput)
          if (reviewer.trim()) setReviewerSet(true)
        }}>
          <input className="w-full rounded border px-3 py-2 text-sm" value={reviewer} onChange={(e) => setReviewer(e.target.value)} placeholder="审核人标识" />
          <input className="w-full rounded border px-3 py-2 text-sm" type="password" value={writeTokenInput} onChange={(e) => setWriteTokenInput(e.target.value)} placeholder="写令牌（向管理员索取）" />
          <button className="w-full rounded bg-primary px-4 py-2 text-sm text-primary-foreground">进入</button>
        </form>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <Link to="/" className="text-sm text-muted-foreground">← 返回首页</Link>
      <div className="mt-2 flex items-center justify-between">
        <h1 className="text-2xl font-bold">缔约审核</h1>
        <button onClick={load} className="rounded border px-3 py-1 text-sm hover:bg-muted">刷新</button>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">审核人：{reviewer} · 每次放行都会复核敏感词清单，触负即 409 拦截并留痕。</p>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}

      {items === null ? (
        <p className="mt-10 text-center text-muted-foreground">加载中…</p>
      ) : items.length === 0 ? (
        <p className="mt-10 text-center text-muted-foreground">暂无申请。</p>
      ) : (
        <ul className="mt-6 space-y-3">
          {items.map((it) => (
            <li key={it.id} className="rounded-lg border p-4">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-medium">#{it.id} {it.display_name}</span>
                <span className="text-xs text-muted-foreground">{it.applicant_kind} · {it.channel} · {it.created_at}</span>
                <span className={`rounded-full border px-2 py-0.5 text-xs ${it.status === 'active' ? 'border-green-600 text-green-700' : it.status === 'rejected' ? 'border-red-400 text-red-600' : 'border-amber-500 text-amber-700'}`}>
                  {statusLabel[it.status] ?? it.status}
                </span>
                {it.nsfl_result !== 'pass' && <span className="text-xs text-amber-700">入站扫描：{it.nsfl_result}</span>}
              </div>
              {(it.status === 'pending' || it.status === 'sandbox') && (
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <input className="flex-1 rounded border px-3 py-1.5 text-sm" placeholder="备注（选填）"
                    value={notes[it.id] ?? ''} onChange={(e) => setNotes((n) => ({ ...n, [it.id]: e.target.value }))} />
                  <button disabled={busy === it.id} onClick={() => act(it.id, 'approve')}
                    className="rounded bg-primary px-3 py-1.5 text-sm text-primary-foreground disabled:opacity-50">
                    {it.status === 'pending' ? '放行→沙盒' : '放行→转正'}
                  </button>
                  <button disabled={busy === it.id} onClick={() => act(it.id, 'reject')}
                    className="rounded border border-red-400 px-3 py-1.5 text-sm text-red-600 disabled:opacity-50">谢绝</button>
                </div>
              )}
              {it.reviewer_note && <p className="mt-2 text-xs text-muted-foreground">备注：{it.reviewer_note}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
