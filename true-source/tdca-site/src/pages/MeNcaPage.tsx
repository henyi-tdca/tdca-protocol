// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI207 MYSPACE-PHASE1-001 §一.3 — 区 5 存证查看 /me/nca（新建）
// 约束矩阵: §三.3 每个操作/单据可关联存证号（区 5 可查）；H-2 数据同源（复用现端点
//           GET /api/v1/me/nca——actor=本人强制过滤、action 精确过滤、分页，零新后端）；
//           §一.5 匿名不可见（PrivateGate）
//           SEG2-B2-REFIRE-001 B2 增补（AMEND-3 §三/§四）：权限边界举证六项×三时点块——
//           数据从本端点行映射（action/artifact_path/sha256_8/ts），端点未载字段明标「本期无」，
//           ⛔ 留空 ⛔ 臆造；原文 ⛔ 入证（只存哈希与摘要）
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

          {/* 权限边界举证（AMEND-3 §三/§四）：存证＝未越服务权限之证明；六项×三时点 */}
          <section data-testid="nca-boundary-proof" className="mt-4 rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="mb-1 text-sm font-semibold text-gray-800">权限边界举证（AMEND-3：每次服务存证必含六项·三时点）</h3>
            <p className="mb-2 text-[11px] text-gray-400">
              读数映射自本页 GET /api/v1/me/nca 行；端点未载之字段如实标「本期无」（⛔ 留空 ⛔ 臆造）；原文 ⛔ 入证（只存哈希与摘要）。
            </p>
            <div className="overflow-x-auto">
              <table data-testid="nca-proof-six" className="w-full min-w-[720px] text-left text-xs">
                <thead>
                  <tr className="border-b text-gray-500">
                    <th className="py-1.5 pr-3">存证号</th>
                    <th className="py-1.5 pr-3">①主体（工具／智能体 TDID）</th>
                    <th className="py-1.5 pr-3">②授权依据（件号＋档位＋期限）</th>
                    <th className="py-1.5 pr-3">③触发事由</th>
                    <th className="py-1.5 pr-3">④访问范围（类·对象·时间窗）</th>
                    <th className="py-1.5 pr-3">⑤比对结论（实际⊆授权？）</th>
                    <th className="py-1.5 pr-3">⑥对象指纹</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.nca_id} data-testid={`nca-proof-${r.nca_id}`} className="border-b border-gray-100 align-top">
                      <td className="py-1.5 pr-3 font-mono text-emerald-700">{r.nca_id}</td>
                      <td className="py-1.5 pr-3 text-gray-400">本期无（端点未载主体字段）</td>
                      <td className="py-1.5 pr-3 text-gray-400">本期无（端点未载授权件号／档位／期限）</td>
                      <td className="py-1.5 pr-3 text-gray-700">{r.action || '—'}</td>
                      <td className="py-1.5 pr-3 text-gray-700">
                        对象：{r.artifact_path ?? '—'} · 时间窗：{r.ts?.slice(0, 19).replace('T', ' ') ?? '—'}（类数本期无）
                      </td>
                      <td className="py-1.5 pr-3 text-gray-400">本期无（端点未载比对结论）</td>
                      <td className="py-1.5 pr-3 font-mono text-gray-700">{r.sha256_8 ?? '—'}</td>
                    </tr>
                  ))}
                  {rows.length === 0 && (
                    <tr><td colSpan={7} className="py-2 text-gray-400">本页无行（筛选结果为空）——举证读数与列表同口径。</td></tr>
                  )}
                </tbody>
              </table>
            </div>
            {/* 三时点（§四） */}
            <div data-testid="nca-proof-moments" className="mt-3 grid gap-2 sm:grid-cols-3">
              <div className="rounded-md border border-gray-100 bg-gray-50 p-2">
                <div className="font-medium text-gray-700">授权时 · 授权存证</div>
                <div className="mt-0.5 text-[11px] text-gray-400">谁授·授什么·到何时·怎么撤＋档位：本期无（端点未载授权面字段，接账候后续令）。</div>
              </div>
              <div className="rounded-md border border-emerald-200 bg-emerald-50/50 p-2">
                <div className="font-medium text-gray-700">执行时 · 逐次访问存证（六项齐）</div>
                <div className="mt-0.5 text-[11px] text-gray-500">在册 {rows.length} 行（本页筛选结果），事由／对象／时间窗／指纹见上表。</div>
              </div>
              <div className="rounded-md border border-gray-100 bg-gray-50 p-2">
                <div className="font-medium text-gray-700">结束时 · 汇总与回落存证</div>
                <div className="mt-0.5 text-[11px] text-gray-400">共读几次·是否按约回落档位：本期无（端点未载回落字段，接账候后续令）。</div>
              </div>
            </div>
            <p className="mt-2 text-[11px] text-gray-400">
              越界处理四步（§五，越权必留痕）：①即时中止该访问（⛔ 继续执行）；②记录越界事实（第⑤项判「否」之具体项与差额）；③告知用户（哪一项越界·已中止·可选处理）；④报运维并登记（D-3 紧急激活档）。
            </p>
          </section>
        </>
      )}
    </PageShell>
  )
}
