// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 /tax 税收仪表盘（A-2 MOU 只读 + MouReadout ID79）+ VISUAL-001 图表增强
// 约束矩阵: FRAMEWORK-001 §四 /tax（L3）+ A-2 契约 + ID79（MOU 不可降）+ ID92 + recharts
// 预期分配: TaxPage（MOU 数值 + 双柱图 + 三池分流 DRAFT 饼图 + Shapley 饼图）
// =============================================================================
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { MouReadout } from '@/shared/guards'
import { Bar, BarChart, Cell, Pie, PieChart, Tooltip, XAxis, YAxis } from 'recharts'

interface TaxMouData {
  agent_id: string
  mou_inbound: string
  mou_outbound: string
  mou_total: string
  mou_irreducible: boolean
  note: string
}

/** 三池分流（TDCA-MICROTAX-VALIDATE-001 P1-1：无制度依据——DRAFT 演示参数，待裁决） */
const POOL_SPLIT = [
  { name: '国库', value: 60, color: '#3b82f6' },
  { name: '社保', value: 25, color: '#22c55e' },
  { name: '生态基金', value: 15, color: '#f59e0b' },
]

/** Shapley 分账（ID43，模拟态——真实分账在结算链路） */
const SHAPLEY_SPLIT = [
  { name: 'AGENT-A', value: 4362.85, color: '#6366f1' },
  { name: 'AGENT-B', value: 2717.43, color: '#0ea5e9' },
  { name: 'AGENT-C', value: 1894.72, color: '#f59e0b' },
]

/** L3 效用计量层：税收仪表盘（只读，ID79 MOU 不可降 + 硬下限校验 + 图表可视化） */
export function TaxPage() {
  const { status, data, nature } = useApiGet<TaxMouData>('/api/v1/tax/mou/AGENT-A')

  const mouInbound = Number(data?.mou_inbound) || 0
  const mouOutbound = Number(data?.mou_outbound) || 0
  const mouBars = [
    { name: '进项（买/调用方）', 金额: mouInbound },
    { name: '出项（卖/被调用方）', 金额: mouOutbound },
    { name: '总额（ID79）', 金额: Number(data?.mou_total) || 0 },
  ]

  return (
    <PageShell
      title="税收仪表盘（L3 效用计量）"
      dataSource="A-2 GET /api/v1/tax/mou/{agent_id} + WS tax_mou"
      permission="公开（只读）"
      description="每次调用产生 MOU 税收锚定（ID79）：计税/预缴/MOU 归零只读看板。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
      {status === 'fail' && (
        <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="tax-fail-closed">
          [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染（ID91/ID85）
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="tax-mou" className="space-y-4">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            智能体：{data.agent_id} <SimulatedBadge nature={nature ?? 'simulated'} />
            <span>{data.note}</span>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <MouReadout label="MOU 进项（买/调用方）" amount={mouInbound} />
            <MouReadout label="MOU 出项（卖/被调用方）" amount={mouOutbound} />
            <MouReadout label="MOU 总额（ID79 硬下限 ≥0）" amount={Number(data.mou_total) || 0} minThreshold={0} />
          </div>
          <div
            data-testid="tax-irreducible"
            className={`rounded-lg border p-3 text-sm ${data.mou_irreducible ? 'border-amber-200 bg-amber-50 text-amber-800' : 'border-red-200 bg-red-50 text-red-700'}`}
          >
            {data.mou_irreducible
              ? 'MOU 不可降（ID79）：税款不得绕过预缴，正和性判定不受损害'
              : '⚠ MOU 可降——违反 ID79（结算应拒绝）'}
          </div>

          {/* VISUAL-001：MOU 双柱图（recharts） */}
          <section data-testid="tax-mou-chart" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">MOU 进项/出项/总额（双柱）</h3>
            <BarChart width={520} height={220} data={mouBars}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="金额" fill="#d97706" radius={[4, 4, 0, 0]} />
            </BarChart>
          </section>

          {/* VISUAL-001：三池分流（DRAFT 演示参数，TDCA-MICROTAX-VALIDATE-001 P1-1 待裁决） */}
          <section data-testid="tax-pool-chart" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-1 text-sm font-semibold text-gray-800">
              三池分流 <span className="ml-1 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-700">DRAFT 参数（无制度依据，待裁决）</span>
            </h3>
            <div className="flex items-center gap-4">
              <PieChart width={200} height={200}>
                <Pie data={POOL_SPLIT} dataKey="value" nameKey="name" cx={100} cy={100} outerRadius={80} label>
                  {POOL_SPLIT.map((p) => (
                    <Cell key={p.name} fill={p.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
              <ul className="space-y-1 text-xs text-gray-600">
                {POOL_SPLIT.map((p) => (
                  <li key={p.name}>
                    <span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: p.color }} />
                    {p.name} {p.value}%
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* VISUAL-001：Shapley 分账饼图（ID43，模拟态） */}
          <section data-testid="tax-shapley-chart" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-1 flex items-center gap-2 text-sm font-semibold text-gray-800">
              Shapley 分账（多主体税后分配，ID43） <SimulatedBadge nature="simulated" />
            </h3>
            <div className="flex items-center gap-4">
              <PieChart width={200} height={200}>
                <Pie data={SHAPLEY_SPLIT} dataKey="value" nameKey="name" cx={100} cy={100} outerRadius={80} label>
                  {SHAPLEY_SPLIT.map((s) => (
                    <Cell key={s.name} fill={s.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
              <ul className="space-y-1 text-xs text-gray-600">
                {SHAPLEY_SPLIT.map((s) => (
                  <li key={s.name}>
                    <span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: s.color }} />
                    {s.name} ¥{s.value.toFixed(2)}（Σ = 税后净额，A-3 一致）
                  </li>
                ))}
              </ul>
            </div>
          </section>
        </div>
      )}
    </PageShell>
  )
}

