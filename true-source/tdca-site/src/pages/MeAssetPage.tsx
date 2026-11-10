// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI207 MYSPACE-PHASE1-001 §一.2 — 我的资产 /me/asset（新建）
// 约束矩阵: §二-H-1 ⛔动公域四面；H-2 数据同源（复用 /api/v1/me/dashboard 现聚合，零新后端）；
//           §一.5 三新建面匿名不可见（PrivateGate 探针，⛔渲染任何数据）
// 依据（H-3 私域不简化）: 资产五阶形态目录为全站公开口径（dashboard note 原样）；权属变动依
//           《TDCA注册登记制度（中文人读版V1.0（现行））》
// =============================================================================
import { Link } from 'react-router'
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'
import { PrivateGateNotice, usePrivateGate } from '@/components/PrivateGate'
import { useApiGet } from '@/lib/useApi'

interface AssetRow {
  order_no: number
  name: string
  description: string | null
  asset_count: number
  data_provenance: string
}

interface MeDashboardAssets {
  my_assets: AssetRow[]
  note: string
}

export function MeAssetPage() {
  const gate = usePrivateGate()
  // 门禁未过 ⟹ 零请求零渲染（探针状态由 PrivateGateNotice 呈现）
  const { status, data } = useApiGet<MeDashboardAssets>('/api/v1/me/dashboard', undefined)

  if (gate !== 'ok') {
    return (
      <PageShell title="我的资产" dataSource="—" permission="须登录（谁的数据谁可见）"
                 description="区 2 四入口之一：我的资产。">
        <PrivateGateNotice state={gate} />
      </PageShell>
    )
  }

  return (
    <PageShell
      title="我的资产"
      dataSource="M5 GET /api/v1/me/dashboard（my_assets 切片；与 /me 同账同源，零新后端）"
      permission="须登录（谁的数据谁可见）"
      description="区 2 四入口之一。资产五阶形态目录为全站公开口径；权属变动依《TDCA注册登记制度（中文人读版V1.0（现行））》，本站不另立私域规则。"
    >
      {status === 'loading' && <p data-testid="me-asset-loading" className="text-sm text-gray-400">加载中…</p>}
      {status === 'fail' && (
        <p data-testid="me-asset-fail" className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          账本暂不可达（fail-closed）：未渲染任何资产数据，请稍后再试。
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="me-asset-list" className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead>
              <tr className="border-b text-xs text-gray-500">
                <th className="py-2 pr-4">序</th>
                <th className="py-2 pr-4">名称</th>
                <th className="py-2 pr-4">说明</th>
                <th className="py-2 pr-4">件数</th>
                <th className="py-2 pr-4">数据来源</th>
              </tr>
            </thead>
            <tbody>
              {data.my_assets.map((a) => (
                <tr key={a.order_no} data-testid={`me-asset-${a.order_no}`} className="border-b border-gray-100">
                  <td className="py-2 pr-4 font-mono text-xs text-gray-500">{a.order_no}</td>
                  <td className="py-2 pr-4 font-medium text-gray-800">{a.name}</td>
                  <td className="py-2 pr-4 text-gray-600">{a.description ?? '—'}</td>
                  <td className="py-2 pr-4">{a.asset_count}</td>
                  <td className="py-2 pr-4">
                    {a.data_provenance !== 'real' && <SimulatedBadge nature={a.data_provenance as 'simulated'} />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-[11px] text-gray-500">
            操作留痕与存证号查询见 <Link to="/me/nca" className="text-emerald-700 underline">区 5 存证查看</Link>（存证号可回查区 5）。
          </p>
        </div>
      )}
    </PageShell>
  )
}
