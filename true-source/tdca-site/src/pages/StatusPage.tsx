// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B1-2/3 · 系统健康 /status（匿名可见，集群并入）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B1-001 §三 B1-2/B1-3——
//   三源合一（overview＋ci/badge＋cluster-status）；system 字段改写「16 个模块 · 已冻结」
//   （⛔ S-1~S-16 与测试数上页面）；税率标「在册税率（演示态）」⛔ 价格字样；
//   集群只显能力名+endpoint+status，⛔ 显 id（EIOS-xx）；⛔ 新建 /api/health
// L1SI214（SITE-HEALTH-001 ＋ AMEND-1）：第四区块「运维异常」——
//   真实巡检产物（data_nature=real），独立第四路 /api/v1/system/ops-alert；
//   ⛔ 不动既有三块与三路数据源；块头显式声明与模拟态不同源不同性质。
// 口径: 只前端呈现层；⛔ 改后端；页面零内部编号（七类＋EIOS-＋S-/A-）
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/lib/client'
import { PageShell } from '@/components/PageShell'

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

/** L1SI214 第四区块：运维异常报告（real；无件=「当日运维无异常」） */
interface OpsAlertData {
  has_alert: boolean
  report_date: string
  generated_at: string | null
  source_file: string | null
  message: string
  raw_md: string | null
}

/** 系统健康：指标（overview 原样数值）＋徽章（ci/badge 一行）＋集群（⛔ id）＋运维异常（real） */
export function StatusPage() {
  const [ov, setOv] = useState<OverviewData | null>(null)
  const [badge, setBadge] = useState<BadgeData | null>(null)
  const [cluster, setCluster] = useState<ClusterItem[] | null>(null)
  const [fail, setFail] = useState('')
  const [ops, setOps] = useState<OpsAlertData | null>(null)
  const [opsFail, setOpsFail] = useState(false)
  const [opsShownAt, setOpsShownAt] = useState('')

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

  // L1SI214：第四路独立取数，⛔ 不与上方三路共用 fail 逻辑（互不牵连）
  useEffect(() => {
    let alive = true
    ;(async () => {
      const r4 = await api.get<OpsAlertData>('/api/v1/system/ops-alert')
      if (!alive) return
      if (r4.ok) {
        setOps(r4.data)
        setOpsShownAt(new Date().toLocaleString('zh-CN', {
          timeZone: 'Asia/Shanghai', hour12: false,
        }))
      } else {
        setOpsFail(true)
      }
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
      dataSource="GET /api/v1/system/overview ＋ /api/v1/ci/badge ＋ /api/v1/eios/cluster-status ＋ /api/v1/system/ops-alert（运维异常·真实巡检产物）"
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

        {/* B1-2 机验徽章（一行）；badge 为空＝尚未运行（触发须 operator 角色会话，见 L1SI206 回报） */}
        <section data-testid="status-badge">
          <h3 className="mb-2 text-sm font-bold text-gray-700">机验徽章</h3>
          {badge ? (
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
          ) : (
            <p data-testid="badge-none" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 px-4 py-2 text-sm text-gray-500">
              尚未运行：CI 自检须 operator 角色登录后从站内触发（同步执行 lake build / core-go / pytest 三套件）。
            </p>
          )}
        </section>

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
        {/* L1SI214 第四区块「运维异常」：真实巡检产物（data_nature=real），独立第四路取数；
            块头显式声明与上方模拟态三块不同源、不同性质（AMEND-1 硬约束第 6 条） */}
        <section data-testid="status-ops-alert">
          <h3 className="mb-2 text-sm font-bold text-gray-700">运维异常（真实巡检产物）</h3>
          <p className="mb-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-700">
            本块为真实巡检产物（data_nature=real），与上方模拟态区块不同源、不同性质。
          </p>
          {opsFail ? (
            <p data-testid="ops-alert-fail" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 px-4 py-2 text-sm text-gray-500">
              运维异常报告暂不可得（fail-closed）
            </p>
          ) : !ops ? (
            <p className="rounded-lg border border-dashed border-gray-300 bg-gray-50 px-4 py-2 text-sm text-gray-500">加载中…</p>
          ) : ops.has_alert && ops.raw_md ? (
            <div data-testid="ops-alert-body" className="rounded-lg border border-gray-200">
              <p className="border-b border-gray-100 px-4 py-2 text-xs text-gray-500">
                报告生成时点：{ops.generated_at} ｜ 报告日：{ops.report_date} ｜ 源件：{ops.source_file} ｜ 本页展示时点：{opsShownAt}（非实时）
              </p>
              <pre className="whitespace-pre-wrap px-4 py-3 text-sm leading-6 text-gray-800">{ops.raw_md}</pre>
            </div>
          ) : (
            <p data-testid="ops-alert-none" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 px-4 py-2 text-sm text-gray-500">
              {ops.message}（本页展示时点 {opsShownAt}）
            </p>
          )}
        </section>
      </div>
    </PageShell>
  )
}
