// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 公告栏（对外公告区＋运营发布栏）
// 约束矩阵: 创始人 2026-10-04 明示「对外公告，要有公告栏」+ 2026-10-09 开工令（发布面施工）
// 口径: 公告内容须创始人逐次明示后才可发布——
//       ⛔ 不自行拟稿、⛔ 不先行发布、⛔ 不预置示例公告冒充正式公告；
//       发布栏仅 operator/founder 可见（角色取 /me/dashboard 会话口径）；
//       对外纪律：零内部编号、零凭据值、零人名、零自然人敏感信息。
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface AnnouncementView {
  announcement_id: string
  title: string
  body: string
  published_at: string
}

interface BoardData {
  count: number
  announcements: AnnouncementView[]
  note: string
}

/** 公告栏：对外公告区（公开可读；初始空栏为常态）＋运营发布栏（operator/founder） */
export function AnnouncementsPage() {
  const [rows, setRows] = useState<AnnouncementView[]>([])
  const [count, setCount] = useState(0)
  const [note, setNote] = useState('')
  const [nature, setNature] = useState<'real' | 'simulated' | null>(null)
  const [status, setStatus] = useState<'loading' | 'ok' | 'fail'>('loading')
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  // 角色口径：与「我的」页同源（/me/dashboard 会话）；未登录/非 operator 不渲染发布栏
  const me = useApiGet<{ session: { role: string } }>('/api/v1/me/dashboard')
  const canPublish = me.status === 'ok' && (me.data?.session.role === 'operator' || me.data?.session.role === 'founder')

  const load = async () => {
    const r = await api.get<BoardData>('/api/v1/announcements/list')
    if (r.ok) {
      setRows(r.data.announcements)
      setCount(r.data.count)
      setNote(r.data.note)
      setNature(r.nature)
      setStatus('ok')
    } else {
      setStatus('fail')
    }
  }
  useEffect(() => { void load() }, [])

  const onPublish = async () => {
    setMsg('')
    if (!title.trim() || !body.trim()) { setMsg('标题与正文均不得为空'); return }
    setBusy(true)
    try {
      const r = await api.post<{ announcement_id: string; title: string; nca_ref: string }>(
        '/api/v1/announcements/publish',
        { title: title.trim(), body: body.trim() })
      if (!r.ok) { setMsg(`发布失败：${r.reason}${r.status ? `（${r.status}）` : ''}`); return }
      setMsg(`已发布并入存证链：${r.data.announcement_id}（存证 ${r.data.nca_ref}）`)
      setTitle('')
      setBody('')
      void load()
    } finally {
      setBusy(false)
    }
  }

  return (
    <PageShell dataNature="real"
      title="公告栏"
      dataSource="A-23 GET /api/v1/announcements/list（公开读）＋ POST /api/v1/announcements/publish（operator/founder，NCA 存证）"
      permission="公开读 / 发布须 operator"
      description="站点对外公告区：公告内容经创始人明示后由运营发布；空栏为常态，不预置内容。"
    >
      <div className="space-y-4">
        {/* 运营发布栏：仅 operator/founder 可见；拟稿仍须创始人逐次明示 */}
        {canPublish && (
          <section data-testid="ann-publish" className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
            <h3 className="mb-2 text-sm font-semibold text-emerald-900">公告发布（operator）</h3>
            <input
              data-testid="ann-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="公告标题"
              className="mb-2 w-full rounded-md border border-emerald-200 bg-white px-3 py-1.5 text-sm"
            />
            <textarea
              data-testid="ann-body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="公告正文（对外可见；零内部编号、零凭据值、零人名、零自然人敏感信息）"
              rows={4}
              className="mb-2 w-full rounded-md border border-emerald-200 bg-white px-3 py-1.5 text-sm"
            />
            <button
              data-testid="ann-publish-btn"
              onClick={() => void onPublish()}
              disabled={busy}
              className="rounded-md bg-emerald-700 px-3 py-1.5 text-sm text-white disabled:opacity-50"
            >
              {busy ? '发布中…' : '发布'}
            </button>
            {msg && <p data-testid="ann-msg" role="status" className="mt-2 text-xs text-emerald-800">{msg}</p>}
            <p className="mt-1 text-[11px] text-emerald-700">内容未经创始人逐次明示不得发布；发布落 NCA 存证链（real），对外纪律四零 fail-closed。</p>
          </section>
        )}

        {status === 'loading' && <p className="text-sm text-gray-400">加载中…</p>}
        {status === 'fail' && (
          <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="ann-fail-closed">
            [fail-closed] 公告栏后端不可用，拒绝渲染
          </p>
        )}
        {status === 'ok' && (
          <section data-testid="ann-list" className="space-y-3">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <SimulatedBadge nature={nature ?? 'simulated'} />
              <span>{note}</span>
            </div>
            {count === 0 ? (
              <p className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-500"
                 data-testid="ann-empty">
                暂无公告。
              </p>
            ) : (
              rows.map((a) => (
                <article key={a.announcement_id}
                         className="rounded-lg border border-gray-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-gray-900">{a.title}</h3>
                  <p className="mt-0.5 text-xs text-gray-400">{a.published_at}</p>
                  <p className="mt-2 whitespace-pre-wrap text-sm text-gray-700">{a.body}</p>
                </article>
              ))
            )}
          </section>
        )}
      </div>
    </PageShell>
  )
}
