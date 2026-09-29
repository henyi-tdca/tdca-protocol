// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 /market 配置权市场（A-4 五阶资产池只读优先）
// 约束矩阵: FRAMEWORK-001 §四 /market（L2）+ A-4 契约 + ID92
// =============================================================================
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface FiveOrdersData {
  assets: { order: number; name: string; desc: string; count: number }[]
  note: string
}

/** L2 配置权市场：A-4 五阶资产池（只读优先；A-3 调用写操作待 HUF 通道） */
export function MarketPage() {
  const { status, data, nature } = useApiGet<FiveOrdersData>('/api/v1/assets/five-orders')

  return (
    <PageShell
      title="配置权市场（L2）"
      dataSource="A-4 GET /api/v1/assets/five-orders + A-3 POST /api/v1/config-right/call"
      permission="公开读 / 调用须 DID"
      description="配置权协议化流转市场——使用权/配置权可流转，所有权不流转（防混淆）。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
      {status === 'fail' && (
        <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="market-fail-closed">
          [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="market-assets" className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <SimulatedBadge nature={nature ?? 'simulated'} />
            <span>{data.note}</span>
          </div>
          {data.assets.map((a) => (
            <div key={a.order} className="flex items-center justify-between rounded-lg border border-gray-200 p-3">
              <div>
                <div className="text-sm font-semibold text-gray-800">
                  #{a.order} {a.name}
                </div>
                <div className="text-xs text-gray-500">{a.desc}</div>
              </div>
              <span className="rounded bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                {a.count} 在册（模拟）
              </span>
            </div>
          ))}
        </div>
      )}
    </PageShell>
  )
}
