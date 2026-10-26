// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B1-1 · 五序资产总览 /assets（匿名可见）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B1-001 §三 B1-1——五序名称+一句说明+count；
//   count 全 0 显「暂无真实资产（待生态接入）」；SIMULATED 角标；⛔ 购买/定价/挂牌入口
// 口径: 只读 GET /api/v1/assets/five-orders；匿名开放面（接口匿名 200）；⛔ 改后端
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import { PageShell } from './PageShell'

interface AssetItem {
  order: number
  name: string
  desc: string
  count: number
}

interface AssetsData {
  assets: AssetItem[]
  note: string
}

/** 五序资产总览：名称＋说明＋数量；count 全 0 出空态；⛔ 任何收费入口 */
export function AssetsPage() {
  const [rows, setRows] = useState<AssetItem[]>([])
  const [status, setStatus] = useState<'loading' | 'ok' | 'fail'>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    ;(async () => {
      const r = await api.get<AssetsData>('/api/v1/assets/five-orders')
      if (!alive) return
      if (r.ok) {
        setRows(r.data.assets)
        setStatus('ok')
      } else {
        setStatus('fail')
        setError(r.ok ? '' : `API ${(r as { status?: number }).status ?? 'fail'}`)
      }
    })()
    return () => { alive = false }
  }, [])

  const allZero = rows.length > 0 && rows.every((a) => a.count === 0)

  return (
    <PageShell
      title="五序资产总览"
      dataSource="GET /api/v1/assets/five-orders（DB 实读）"
      permission="公开"
      description="五序资产池总览：效用权／配置权／NCA 资产／MOU 凭证／跨场景画像；真实资产待生态接入，本页只读展示，不含任何交易入口。"
    >
      <div data-testid="assets-page" className="space-y-4">
        {status === 'loading' && <p className="text-sm text-gray-400">加载中…</p>}
        {status === 'fail' && (
          <p data-testid="assets-fail-closed" className="rounded bg-red-50 p-3 text-sm text-red-600">
            [fail-closed] 资产总览暂不可用：{error}
          </p>
        )}
        {status === 'ok' && allZero && (
          <p data-testid="assets-empty" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
            暂无真实资产（待生态接入）
          </p>
        )}
        {status === 'ok' && !allZero && (
          <ul data-testid="assets-list" className="divide-y divide-gray-100 rounded-lg border border-gray-200">
            {rows.map((a) => (
              <li key={a.order} className="flex items-center gap-3 px-4 py-3">
                <span className="inline-flex h-6 w-6 items-center justify-center rounded bg-blue-100 text-xs font-bold text-blue-700">
                  {a.order}
                </span>
                <div>
                  <div className="text-sm font-semibold text-gray-800">{a.name}</div>
                  <div className="text-xs text-gray-500">{a.desc}</div>
                </div>
                <span className="ml-auto text-xs text-gray-400">在册 {a.count} 件</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </PageShell>
  )
}
