// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 首页（A-1 system/overview KPI）+ VISUAL-001 五元拓扑 Ω
// 约束矩阵: FRAMEWORK-001 §四 /（全层总览）+ A-1 契约 + ID81（五元拓扑 Ω）+ ID92
// 并轨注记: 自旧版 home.tsx 迁入（FRONTEND-MERGE 批1），改名 Overview（路由 /overview）；
//           制度语义与判据原样保留，仅适配导入路径（@/api 链 → @/lib）
// =============================================================================
import { Link } from 'react-router'
import { useApiGet } from '@/lib/useApi'
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'
import { TopologyEngine, hashAgentId, type TopoData } from '@/lib/TopologyEngine'

interface OverviewData {
  total_deliveries: number
  total_tax_settled: string
  avg_latency_ms: number
  total_fused: number
  total_fail_closed: number
  tax_rates: { dispatch_tax: number; royalty: number; transaction_fee: number }
  theta: number
  phi: number
  system: string
}

/** 五元拓扑 Ω（ID81）：H/M/L 顶点 + 五关系边（官网 = Ω 前端坐标卡） */
const OMEGA_TOPO: TopoData = {
  nodes: [
    { id: hashAgentId('NODE-H'), label: 'H 人类', type: 'gov', status: 'active' },
    { id: hashAgentId('NODE-M'), label: 'M 智能体', type: 'official', status: 'active' },
    { id: hashAgentId('NODE-L'), label: 'L 学习体', type: 'user', status: 'active' },
  ],
  edges: [
    { from: hashAgentId('NODE-H'), to: hashAgentId('NODE-M'), label: '确权（HUF）', state: 'flowing' },
    { from: hashAgentId('NODE-M'), to: hashAgentId('NODE-L'), label: '教育（E-EDU）', state: 'flowing' },
    { from: hashAgentId('NODE-L'), to: hashAgentId('NODE-H'), label: '学习回馈', state: 'flowing' },
    { from: hashAgentId('NODE-M'), to: hashAgentId('NODE-H'), label: '税收锚定', state: 'flowing' },
    { from: hashAgentId('NODE-H'), to: hashAgentId('NODE-L'), label: '化合授权', state: 'flowing' },
  ],
}

export function OverviewPage() {
  const { status, data, nature } = useApiGet<OverviewData>('/api/v1/system/overview')

  return (
    <PageShell
      title="首页 · 四层架构总览"
      dataSource="A-1 GET /api/v1/system/overview + /health"
      permission="公开"
      description="TDCA 四层架构（L0 法律底层 → L1 所有权 → L2 配置权 → L3 效用计量）制度橱窗总览。"
    >
      <p className="mb-3 text-sm">
        <Link to="/" className="text-muted-foreground underline underline-offset-4 hover:text-card-foreground">
          ← 返回三体可视化中心首页
        </Link>
      </p>
      {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
      {status === 'fail' && (
        <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="home-fail-closed">
          [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="home-kpi" className="space-y-4">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            体系状态：{data.system} <SimulatedBadge nature={nature ?? 'simulated'} />
          </div>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
            {[
              { label: '累计微交付', value: data.total_deliveries },
              { label: '税收结算（模拟）', value: data.total_tax_settled },
              { label: '平均计税时延', value: `${data.avg_latency_ms} ms` },
              { label: '熔断次数', value: data.total_fused },
              { label: 'fail-closed 次数', value: data.total_fail_closed },
              { label: '正和阈值 θ/ϕ', value: `${data.theta} / ${data.phi}` },
            ].map((kpi) => (
              <div key={kpi.label} className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                <div className="text-xs text-gray-500">{kpi.label}</div>
                <div className="mt-1 text-xl font-bold text-gray-900">{kpi.value}</div>
              </div>
            ))}
          </div>
          <div className="rounded-lg border border-gray-200 p-3 text-xs text-gray-600">
            税率（CALL-001 模拟态）：调度税 {data.tax_rates.dispatch_tax * 100}% / 版税{' '}
            {data.tax_rates.royalty * 100}% / 交易费 {data.tax_rates.transaction_fee * 100}%
          </div>

          {/* VISUAL-001：五元拓扑 Ω（ID81，官网 = Ω 前端坐标卡） */}
          <section data-testid="home-omega" className="rounded-lg border border-gray-200 p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-800">五元拓扑 Ω（H/M/L 顶点 + 五关系边）</h3>
              <SimulatedBadge nature="simulated" />
            </div>
            <TopologyEngine data={OMEGA_TOPO} height={260} />
          </section>
        </div>
      )}
    </PageShell>
  )
}

