// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-A1-2 · 术语页 /terms（登录可见）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-A1-001——列表（词/释义）＋关键词检索（走服务端 ?q=）
//   ＋空态「暂无匹配」；页内 ⛔ 出 id 列（T-xxx 编号不上页面）
// 口径: 登录可见（本令 ⛔ 匿名开放）；匿名返回已后端脱敏，登录面全量
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import { PageShell } from './PageShell'

interface TermItem {
  term: string
  def: string
}

interface TermsData {
  terms: TermItem[]
  total: number
  note: string
}

/** 术语页：词表＋服务端检索（?q=）；⛔ 不渲染 id 列 */
export function TermsPage() {
  const [rows, setRows] = useState<TermItem[]>([])
  const [total, setTotal] = useState(0)
  const [note, setNote] = useState('')
  const [q, setQ] = useState('')
  const [status, setStatus] = useState<'loading' | 'ok' | 'fail'>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    const t = setTimeout(async () => {
      const path = q.trim() ? `/api/v1/knowledge/terms?q=${encodeURIComponent(q.trim())}` : '/api/v1/knowledge/terms'
      const r = await api.get<TermsData>(path)
      if (!alive) return
      if (r.ok) {
        setRows(r.data.terms)
        setTotal(r.data.total)
        setNote(r.data.note)
        setStatus('ok')
      } else {
        setStatus('fail')
        setError(`API ${r.status}`)
      }
    }, 250) // 输入防抖 250ms
    return () => {
      alive = false
      clearTimeout(t)
    }
  }, [q])

  return (
    <PageShell
      title="术语检索"
      dataSource="A-6 GET /api/v1/knowledge/terms?q=（服务端过滤）"
      permission="登录 DID"
      description="站内术语注册表检索：输入关键词即走服务端过滤，词与释义两列；登录可见全量，匿名面后端已脱敏内部编号。"
    >
      <div data-testid="terms-page" className="space-y-4">
        {/* 检索框（走服务端 ?q=） */}
        <div data-testid="terms-search">
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="输入关键词检索术语（服务端过滤）…"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        {status === 'loading' && <p className="text-sm text-gray-400">加载中…</p>}
        {status === 'fail' && (
          <p data-testid="terms-fail-closed" className="rounded bg-red-50 p-3 text-sm text-red-600">
            [fail-closed] 术语库暂不可用：{error}
          </p>
        )}
        {status === 'ok' && rows.length === 0 && (
          <p data-testid="terms-empty" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
            暂无匹配
          </p>
        )}
        {status === 'ok' && rows.length > 0 && (
          <section data-testid="terms-list">
            <p className="mb-2 text-xs text-gray-500">共 {total} 条{q.trim() ? `（关键词「${q.trim()}」）` : ''}</p>
            <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
              {rows.map((t) => (
                <li key={t.term} className="px-4 py-3">
                  <div className="text-sm font-semibold text-gray-800">{t.term}</div>
                  <div className="mt-0.5 text-xs leading-relaxed text-gray-600">{t.def}</div>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-[11px] text-gray-400">{note}</p>
          </section>
        )}
      </div>
    </PageShell>
  )
}
