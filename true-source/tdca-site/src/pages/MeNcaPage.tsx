// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI207 MYSPACE-PHASE1-001 §一.3 — 区 5 存证查看 /me/nca（新建）
// 约束矩阵: §三.3 每个操作/单据可关联存证号（区 5 可查）；H-2 数据同源（复用现端点
//           GET /api/v1/me/nca——actor=本人强制过滤、action 精确过滤、分页，零新后端）；
//           §一.5 匿名不可见（PrivateGate）
// 口径: 列表＝时点／动作／对象／结果／存证号；筛选＝动作类（服务端）＋存证号/关键字（本页内）；
//       导出＝当前筛选结果 CSV（浏览器本地下载，⛔整包索取、只出本人已载页）
// =============================================================================
import { useMemo, useState } from 'react'
import { PageShell } from '@/components/PageShell'
import { PrivateGateNotice, usePrivateGate } from '@/components/PrivateGate'
import { useApiGet } from '@/lib/useApi'

interface NcaRow {
  nca_id: string
  action: string
  artifact_path: string | null
  sha256_8: string | null
  ts: string
}

interface NcaPage {
  total: number
  page: number
  limit: number
  items: NcaRow[]
}

export function MeNcaPage() {
  const gate = usePrivateGate()
  const [page, setPage] = useState(1)
  const [action, setAction] = useState('')
  const [q, setQ] = useState('')
  const LIMIT = 20
  const qs = `/api/v1/me/nca?page=${page}&limit=${LIMIT}${action ? `&action=${encodeURIComponent(action)}` : ''}`
  // 门禁未过时仍发请求也无妨（接口 401 把守）；数据只在 gate==='ok' 分支渲染
  const { status, data } = useApiGet<NcaPage>(qs, undefined)

  const actions = useMemo(() => {
    const set = new Set<string>()
    for (const it of data?.items ?? []) set.add(it.action)
    return [...set].sort()
  }, [data])

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    if (!needle) return data?.items ?? []
    return (data?.items ?? []).filter((r) =>
      r.nca_id.toLowerCase().includes(needle) ||
      r.action.toLowerCase().includes(needle) ||
      (r.artifact_path ?? '').toLowerCase().includes(needle),
    )
  }, [data, q])

  const exportCsv = () => {
    const head = '存证号,时点,动作,对象,结果\n'
    const body = rows
      .map((r) =>
        [r.nca_id, r.ts, r.action, r.artifact_path ?? '', r.sha256_8 ?? '']
          .map((v) => `"${String(v).replace(/"/g, '""')}"`)
          .join(','),
      )
      .join('\n')
    const blob = new Blob([head + body], { type: 'text/csv;charset=utf-8' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `tdca-me-nca-page${page}.csv`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  if (gate !== 'ok') {
    return (
      <PageShell title="存证查看" dataSource="—" permission="须登录（谁的数据谁可见）"
                 description="区 5：我之动作存证列表。">
        <PrivateGateNotice state={gate} />
      </PageShell>
    )
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / LIMIT)) : 1

  return (
    <PageShell
      title="存证查看"
      dataSource="GET /api/v1/me/nca（本人 actor 强制过滤；与 /me 摘要同口径，零新后端）"
      permission="须登录（谁的数据谁可见）"
      description="区 5：我之动作列表——时点／动作／对象／结果／存证号。可筛选、可导出（导出范围为当前页筛选结果，只出本人数据）。存证口径见《NCA 存证说明》（/nca-guide）。"
    >
      <div data-testid="me-nca-toolbar" className="mb-3 flex flex-wrap items-center gap-2">
        <select data-testid="me-nca-action-filter" value={action} onChange={(e) => { setAction(e.target.value); setPage(1) }}
                className="rounded-md border border-gray-300 px-2 py-1 text-xs">
          <option value="">全部动作</option>
          {actions.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        <input data-testid="me-nca-q" value={q} onChange={(e) => setQ(e.target.value)}
               placeholder="筛存证号／关键字（本页内）" className="w-56 rounded-md border border-gray-300 px-2 py-1 text-xs" />
        <button type="button" data-testid="me-nca-export" onClick={exportCsv}
                className="rounded-md border border-emerald-600 bg-emerald-600 px-2 py-1 text-xs text-white hover:bg-emerald-700">
          导出 CSV（{rows.length} 条）
        </button>
      </div>

      {status === 'loading' && <p data-testid="me-nca-loading" className="text-sm text-gray-400">加载中…</p>}
      {status === 'fail' && (
        <p data-testid="me-nca-fail" className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          存证链暂不可达（fail-closed）：未渲染任何存证数据。
        </p>
      )}
      {status === 'ok' && data && (
        <>
          <div className="overflow-x-auto">
            <table data-testid="me-nca-list" className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b text-xs text-gray-500">
                  <th className="py-2 pr-3">时点</th>
                  <th className="py-2 pr-3">动作</th>
                  <th className="py-2 pr-3">对象</th>
                  <th className="py-2 pr-3">结果</th>
                  <th className="py-2 pr-3">存证号</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.nca_id} data-testid={`me-nca-${r.nca_id}`} className="border-b border-gray-100">
                    <td className="py-2 pr-3 font-mono text-xs text-gray-600">{r.ts?.slice(0, 19).replace('T', ' ')}</td>
                    <td className="py-2 pr-3 font-medium text-gray-800">{r.action}</td>
                    <td className="max-w-[220px] truncate py-2 pr-3 text-xs text-gray-600">{r.artifact_path ?? '—'}</td>
                    <td className="py-2 pr-3 font-mono text-xs text-gray-600">{r.sha256_8 ?? '—'}</td>
                    <td className="py-2 pr-3 font-mono text-xs text-emerald-700">{r.nca_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div data-testid="me-nca-pager" className="mt-3 flex items-center gap-2 text-xs text-gray-600">
            <span>共 {data.total} 条 · 第 {data.page}/{totalPages} 页</span>
            <button type="button" data-testid="me-nca-prev" disabled={page <= 1} onClick={() => setPage(page - 1)}
                    className="rounded border border-gray-300 px-2 py-1 disabled:opacity-40">上一页</button>
            <button type="button" data-testid="me-nca-next" disabled={page >= totalPages} onClick={() => setPage(page + 1)}
                    className="rounded border border-gray-300 px-2 py-1 disabled:opacity-40">下一页</button>
          </div>
        </>
      )}
    </PageShell>
  )
}
