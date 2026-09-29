// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 /audit 审计透明（A-7 公共账本只读 BV-3）
// 约束矩阵: FRAMEWORK-001 §四 /audit + A-7 契约 + BV-3（只读）+ ID92
// =============================================================================
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface LedgerData {
  events: { event_id: string; type: string; ts: string; amount: string }[]
  total: number
  note: string
}

/** 审计透明：公共账本（制度即公开，O(n) 可审计，只读 BV-3） */
export function AuditPage() {
  const { status, data, nature } = useApiGet<LedgerData>('/api/v1/audit/ledger-public')

  return (
    <PageShell
      title="审计透明"
      dataSource="A-7 GET /api/v1/audit/ledger-public + /nca/chain"
      permission="公开（制度即公开）"
      description="NCA 存证链 + 熔断历史 + 哈希审计（宪法第十六条 可观测）。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
      {status === 'fail' && (
        <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="audit-fail-closed">
          [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染（ID91/ID85）
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="audit-ledger" className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            公共账本（只读，BV-3）：共 {data.total} 条 <SimulatedBadge nature={nature ?? 'simulated'} />
          </div>
          {data.events.length === 0 && <p className="text-sm text-gray-400">暂无账本事件（模拟态）</p>}
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
                <th className="py-1.5">event_id</th>
                <th className="py-1.5">类型</th>
                <th className="py-1.5">金额</th>
                <th className="py-1.5">时间戳</th>
              </tr>
            </thead>
            <tbody>
              {data.events.map((e) => (
                <tr key={e.event_id} data-event={e.event_id} className="border-b border-gray-100">
                  <td className="py-1.5 font-mono text-xs text-gray-700">{e.event_id}</td>
                  <td className="py-1.5 text-xs text-gray-600">{e.type}</td>
                  <td className="py-1.5 text-xs text-gray-600">{e.amount}</td>
                  <td className="py-1.5 font-mono text-[10px] text-gray-400">{e.ts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PageShell>
  )
}
