// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块四 — /review 评审队列（缔约审核移植）
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §二块四（评审归运维分区 ⛔ 不入公共导航）
//          ＋ 裁点3（/review 归运维分区，⛔ 不并入治理）
// 口径: tdca-site Review.tsx  plumbing 适配（siteApi → 本会话内 fetch /api/site/*）；
//       写令牌只存 sessionStorage（⛔ 不落文件/产物）；审核人标识留痕用；触负 409 拦截照在册
// =============================================================================
import { useCallback, useEffect, useState } from 'react'
import { PageShell } from './PageShell'

// ---- /api/site 面 plumbing（原 @/lib/siteApi 语义等值移植：写令牌仅存 sessionStorage）----
const WRITE_KEY = 'tdca_site_write'

function getWriteToken(): string {
  return sessionStorage.getItem(WRITE_KEY) ?? ''
}

function setWriteToken(v: string): void {
  if (v) sessionStorage.setItem(WRITE_KEY, v)
  else sessionStorage.removeItem(WRITE_KEY)
}

async function siteFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`/api/site${path}`, {
    ...init,
    headers: {
      ...(getWriteToken() ? { Authorization: `TDCA-CRT-${getWriteToken()}`, 'X-TDCA-Token-Type': 'execution' } : {}),
      ...(init.headers || {}),
    },
  })
}

async function siteGet<T>(path: string): Promise<T> {
  const res = await siteFetch(path)
  if (!res.ok) throw new Error(`API ${res.status}`)
  return (await res.json()) as T
}

async function sitePost<T>(path: string, body: unknown, extraHeaders?: Record<string, string>): Promise<T> {
  const res = await siteFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(extraHeaders || {}) },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw Object.assign(new Error(`API ${res.status}`), { status: res.status, data })
  return data as T
}

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

/** 评审队列（缔约审核）：运维分区件，⛔ 不入公共导航；审核人标识＋写令牌均只存本次会话 */
export function ReviewPage() {
  const [reviewer, setReviewer] = useState('')
  const [reviewerSet, setReviewerSet] = useState(false)
  const [writeTokenInput, setWriteTokenInput] = useState(getWriteToken())
  const [items, setItems] = useState<JoinItem[] | null>(null)
  const [error, setError] = useState('')
  const [notes, setNotes] = useState<Record<number, string>>({})
  const [busy, setBusy] = useState<number | null>(null)

  const load = useCallback(async () => {
    try {
      const d = await siteGet<{ items: JoinItem[] }>('/join/list')
      setItems(d.items)
      setError('')
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e))
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

  if (!reviewerSet) {
    return (
      <PageShell
        title="评审（缔约审核）"
        dataSource="/api/site/join/*（只读队列＋审核写端点）"
        permission="须登录＋审核身份（写令牌校验）"
        description="缔约申请的评审队列：放行／谢绝均留痕（审核人标识），每次放行复核敏感词清单，触负即 409 拦截。写令牌向管理员索取，只存本次会话。"
      >
        <section data-testid="review-gate" className="mx-auto max-w-sm py-8 text-center">
          <form className="mt-2 space-y-2" onSubmit={(e) => {
            e.preventDefault()
            setWriteToken(writeTokenInput)
            if (reviewer.trim()) setReviewerSet(true)
          }}>
            <input className="w-full rounded border border-gray-300 px-3 py-2 text-sm" value={reviewer} onChange={(e) => setReviewer(e.target.value)} placeholder="审核人标识" data-testid="review-reviewer" />
            <input className="w-full rounded border border-gray-300 px-3 py-2 text-sm" type="password" value={writeTokenInput} onChange={(e) => setWriteTokenInput(e.target.value)} placeholder="写令牌（向管理员索取）" data-testid="review-token" />
            <button className="w-full rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700" data-testid="review-enter">进入</button>
          </form>
          <p className="mt-3 text-xs text-gray-500">输入审核人标识（留痕用）与写令牌（放行/谢绝时校验，均只存本次会话）</p>
        </section>
      </PageShell>
    )
  }

  return (
    <PageShell
      title="评审（缔约审核）"
      dataSource="/api/site/join/*（只读队列＋审核写端点）"
      permission="须登录＋审核身份（写令牌校验）"
      description="缔约申请的评审队列：放行／谢绝均留痕（审核人标识），每次放行复核敏感词清单，触负即 409 拦截。"
    >
      <div data-testid="review-board">
        <div className="mt-1 flex items-center justify-between">
          <p className="text-xs text-gray-500">审核人：{reviewer} · 每次放行都会复核敏感词清单，触负即 409 拦截并留痕。</p>
          <button onClick={load} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50" data-testid="review-refresh">刷新</button>
        </div>
        {error && <p className="mt-3 text-sm text-red-600" data-testid="review-error">{error}</p>}

        {items === null ? (
          <p className="mt-10 text-center text-gray-400">加载中…</p>
        ) : items.length === 0 ? (
          <p className="mt-10 text-center text-gray-400" data-testid="review-empty">暂无申请。</p>
        ) : (
          <ul className="mt-6 space-y-3">
            {items.map((it) => (
              <li key={it.id} className="rounded-lg border border-gray-200 p-4" data-testid={`review-item-${it.id}`}>
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-medium">#{it.id} {it.display_name}</span>
                  <span className="text-xs text-gray-500">{it.applicant_kind} · {it.channel} · {it.created_at}</span>
                  <span className={`rounded-full border px-2 py-0.5 text-xs ${it.status === 'active' ? 'border-green-600 text-green-700' : it.status === 'rejected' ? 'border-red-400 text-red-600' : 'border-amber-500 text-amber-700'}`}>
                    {statusLabel[it.status] ?? it.status}
                  </span>
                  {it.nsfl_result !== 'pass' && <span className="text-xs text-amber-700">入站扫描：{it.nsfl_result}</span>}
                </div>
                {(it.status === 'pending' || it.status === 'sandbox') && (
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <input className="flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm" placeholder="备注（选填）"
                      value={notes[it.id] ?? ''} onChange={(e) => setNotes((n) => ({ ...n, [it.id]: e.target.value }))} />
                    <button disabled={busy === it.id} onClick={() => act(it.id, 'approve')}
                      className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
                      {it.status === 'pending' ? '放行→沙盒' : '放行→转正'}
                    </button>
                    <button disabled={busy === it.id} onClick={() => act(it.id, 'reject')}
                      className="rounded border border-red-400 px-3 py-1.5 text-sm text-red-600 disabled:opacity-50">谢绝</button>
                  </div>
                )}
                {it.reviewer_note && <p className="mt-2 text-xs text-gray-500">备注：{it.reviewer_note}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </PageShell>
  )
}
