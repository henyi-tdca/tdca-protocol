// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B1-2/3 · 系统健康 /status（匿名可见，集群并入）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B1-001 §三 B1-2/B1-3——
//   三源合一（overview＋ci/badge＋cluster-status）；system 字段改写「16 个模块 · 已冻结」
//   （⛔ S-1~S-16 与测试数上页面）；税率标「在册税率（演示态）」⛔ 价格字样；
//   集群只显能力名+endpoint+status，⛔ 显 id（EIOS-xx）；⛔ 新建 /api/health
// 口径: 只前端呈现层；⛔ 改后端；页面零内部编号（七类＋EIOS-＋S-/A-）
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import { PageShell } from './PageShell'

interface OverviewData {
  total_deliveries: number
  total_tax_settled: string
  avg_latency_ms: number
  total_fused: number
  total_fail_closed: number
  tax_rates: { dispatch_tax: number; royalty: number; transaction_fee: number }
  system: string
}

interface BadgeData {
  suite: string
  status: string
  note: string
}

interface ClusterItem {
  endpoint: string
  capability: string
  status: string
}

interface ClusterData {
  cluster: ClusterItem[]
}

/** 系统健康：指标（overview 原样数值）＋徽章（ci/badge 一行）＋集群（⛔ id） */
export function StatusPage() {
  const [ov, setOv] = useState<OverviewData | null>(null)
  const [badge, setBadge] = useState<BadgeData | null>(null)
  const [cluster, setCluster] = useState<ClusterItem[] | null>(null)
  const [fail, setFail] = useState('')

  useEffect(() => {
    let alive = true
    ;(async () => {
      const [r1, r2, r3] = await Promise.all([
        api.get<OverviewData>('/api/v1/system/overview'),
        api.get<BadgeData>('/api/v1/ci/badge'),
        api.get<ClusterData>('/api/v1/eios/cluster-status'),
      ])
      if (!alive) return
      const errs = [r1, r2, r3].filter((r) => !r.ok)
      if (errs.length > 0) {
        setFail(errs.map((r) => (r as { status?: number }).status ?? 'fail').join('/'))
        return
      }
      if (r1.ok) setOv(r1.data)
      if (r2.ok) setBadge(r2.data)
      if (r3.ok) setCluster(r3.data.cluster)
    })()
    return () => { alive = false }
  }, [])

  const metrics: { label: string; value: string }[] = ov
    ? [
        { label: '交付数', value: String(ov.total_deliveries) },
        { label: '税结算', value: ov.total_tax_settled },
        { label: '熔断数', value: String(ov.total_fused) },
        { label: 'fail-closed 数', value: String(ov.total_fail_closed) },
        { label: '平均时延（ms）', value: String(ov.avg_latency_ms) },
      ]
    : []

  return (
    <PageShell
      title="系统健康"
      dataSource="GET /api/v1/system/overview ＋ /api/v1/ci/badge ＋ /api/v1/eios/cluster-status"
      permission="公开"
      description="运行指标、机验徽章与集群状态三合一健康面；模块状态以「已冻结」呈现，税率仅为在册演示值，不含任何收费信息。"
    >
      <div data-testid="status-page" className="space-y-6">
        {fail && !ov && (
          <p data-testid="status-fail-closed" className="rounded bg-red-50 p-3 text-sm text-red-600">
            [fail-closed] 健康数据暂不可用：{fail}
          </p>
        )}

        {/* B1-2 模块状态：system 字段前端改写（⛔ S-1~S-16 与测试数上页面） */}
        <section data-testid="status-modules">
          <h3 className="mb-2 text-sm font-bold text-gray-700">模块状态</h3>
          <p className="rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700">
            16 个模块 · 已冻结
          </p>
        </section>

        {/* B1-2 运行指标（原样数值） */}
        <section data-testid="status-metrics">
          <h3 className="mb-2 text-sm font-bold text-gray-700">运行指标</h3>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
            {metrics.map((m) => (
              <div key={m.label} className="rounded-lg border border-gray-200 p-3 text-center">
                <div className="text-lg font-bold text-gray-800">{m.value}</div>
                <div className="text-[11px] text-gray-500">{m.label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* B1-2 在册税率（演示态）：⛔ 价格/费用金额字样 */}
        {ov && (
          <section data-testid="status-rates">
            <h3 className="mb-2 text-sm font-bold text-gray-700">在册税率（演示态）</h3>
            <div className="grid grid-cols-3 gap-2">
              {([
                ['调度税', ov.tax_rates.dispatch_tax],
                ['权益金', ov.tax_rates.royalty],
                ['交易费', ov.tax_rates.transaction_fee],
              ] as [string, number][]).map(([label, v]) => (
                <div key={label} className="rounded-lg border border-gray-200 p-3 text-center">
                  <div className="text-lg font-bold text-gray-800">{(v * 100).toFixed(2)}%</div>
                  <div className="text-[11px] text-gray-500">{label}</div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* B1-2 机验徽章（一行） */}
        {badge && (
          <section data-testid="status-badge">
            <h3 className="mb-2 text-sm font-bold text-gray-700">机验徽章</h3>
            <p className="rounded-lg border border-gray-200 px-4 py-2 text-sm">
              <span
                data-testid="badge-status"
                className={
                  badge.status === 'green'
                    ? 'font-semibold text-green-600'
                    : badge.status === 'red'
                      ? 'font-semibold text-red-600'
                      : 'text-gray-500'
                }
              >
                {badge.status === 'green' ? '● 绿' : badge.status === 'red' ? '● 红' : `○ ${badge.status}`}
              </span>
              <span className="ml-2 text-gray-500">{badge.note}</span>
            </p>
          </section>
        )}

        {/* B1-3 集群状态：⛔ id（EIOS-xx），只显能力名＋endpoint＋status */}
        <section data-testid="status-cluster">
          <h3 className="mb-2 text-sm font-bold text-gray-700">集群状态</h3>
          {!cluster || cluster.length === 0 ? (
            <p data-testid="cluster-empty" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
              集群状态暂不可得
            </p>
          ) : (
            <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
              {cluster.map((c) => (
                <li key={c.endpoint} data-testid="cluster-item" className="flex items-center gap-3 px-4 py-2.5">
                  <span className="text-sm font-semibold text-gray-800">{c.capability}</span>
                  <span className="text-xs text-gray-400">{c.endpoint}</span>
                  <span
                    className={
                      c.status === 'ACTIVE'
                        ? 'ml-auto rounded bg-green-100 px-1.5 py-0.5 text-[10px] font-semibold text-green-700'
                        : 'ml-auto rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-semibold text-gray-500'
                    }
                  >
                    {c.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </PageShell>
  )
}
