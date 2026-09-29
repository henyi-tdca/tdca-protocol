// =============================================================================
// TDCA 制度水印
// FC-ID: KIMI-WEB-DB-TASK-001-M5 | 目标函数: /agents/:id 智能体后台（五区块聚合）
// 约束矩阵: M5-PLAN §三.2 + 裁定③（公开读 + 归属人脱敏）+ BV-3 制度即公开 + ID79
// 预期分配: AgentDashboardPage（画像 + MOU 计量 + 税单 + 签章记录 + NCA 存证）
// =============================================================================
import { Link, useParams } from 'react-router'
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface AgentDashboard {
  profile: {
    agent_id: string; name: string; endpoint: string | null; capability: string | null
    status: string; tdid: string | null; five_role: string | null; scene: string | null
    attestation_state: string; audit_count: number; owner_display: string | null
    created_at: string; data_provenance: string
  }
  mou: { period: string; mou_inbound: number; mou_outbound: number; mou_total: number; note: string | null; ts: string }[]
  tax_events: { event_id: string; type: string; amount: number; tax_rate_bp: number; call_id: string | null; nca_ref: string | null; ts: string }[]
  attestations: { request_id: string; request_type: string; urgency: string | null; status: string; decided_by: string | null; reason: string | null; nca_ref: string | null; ts: string }[]
  nca_chain: { nca_id: string; action: string; actor: string; prev_nca: string | null; ts: string }[]
  note: string
}

const ATTEST_LABEL: Record<string, string> = { valid: '🟢 签章有效', expiring: '🟡 将过期', invalid: '🔴 失效待审' }
const STATUS_LABEL: Record<string, string> = { pending: '⏳ 待审', approved: '✅ 批准', rejected: '❌ 拒绝' }
const yuan = (fen: number) => `¥${(fen / 100).toFixed(2)}`

/** M5 智能体后台：每一只智能体都有自己的一页（公开可查，BV-3） */
export function AgentDashboardPage() {
  const { id = '' } = useParams()
  const { status, data } = useApiGet<AgentDashboard>(`/api/v1/agents/${id}/dashboard`)

  return (
    <PageShell
      title="智能体后台"
      dataSource="M5 GET /api/v1/agents/{id}/dashboard（五区块聚合）"
      permission="公开读（制度即公开；归属人脱敏）"
      description={`当前查看：${id}——这只智能体的画像、效用计量、税单流水、签章记录与存证链，一页看全。`}
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中…</p>}
      {status === 'fail' && (
        <div data-testid="agent-dash-404" className="max-w-md rounded border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
          没有找到这只智能体（{id}）。
          <Link to="/agents" className="ml-2 font-medium text-emerald-700 underline">回智能体集群 →</Link>
        </div>
      )}
      {status === 'ok' && data && (
        <div className="space-y-5">
          {/* 注册画像 */}
          <section data-testid="agent-dash-profile" className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex flex-wrap items-center gap-3">
              <div className="text-lg font-semibold text-gray-800">{data.profile.name}</div>
              <span className="text-xs">{ATTEST_LABEL[data.profile.attestation_state] ?? data.profile.attestation_state}</span>
              <SimulatedBadge nature={data.profile.data_provenance as 'simulated'} />
            </div>
            <div className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-gray-600 md:grid-cols-4">
              <div>标识：<span className="font-mono">{data.profile.agent_id}</span></div>
              <div>五角色：{data.profile.five_role ?? '—'}</div>
              <div>场景：{data.profile.scene ?? '—'}</div>
              <div>审计：{data.profile.audit_count} 次</div>
              <div>能力：{data.profile.capability ?? '—'}</div>
              <div>归属：{data.profile.owner_display ?? '未认领'}</div>
              <div>状态：{data.profile.status}</div>
              <div>出生：{data.profile.created_at.slice(0, 10)}</div>
            </div>
          </section>

          {/* MOU 效用计量 */}
          <section data-testid="agent-dash-mou" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">MOU 效用计量（只增不降；单位：元）</h3>
            {data.mou.length === 0 && <p className="text-xs text-gray-400">暂无计量记录</p>}
            {data.mou.map((m) => (
              <div key={m.period} className="flex items-center gap-4 border-b border-gray-100 py-1.5 text-xs text-gray-600">
                <span className="font-mono">{m.period}</span>
                <span>进项 {yuan(m.mou_inbound)}</span>
                <span>出项 {yuan(m.mou_outbound)}</span>
                <span data-testid="agent-dash-mou-total" className="font-semibold text-emerald-700">MOU {yuan(m.mou_total)}</span>
              </div>
            ))}
          </section>

          {/* 税单流水 */}
          <section data-testid="agent-dash-tax" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">税单流水（最近 {data.tax_events.length} 条）</h3>
            {data.tax_events.length === 0 && <p className="text-xs text-gray-400">暂无税单</p>}
            {data.tax_events.map((t) => (
              <div key={t.event_id} className="flex items-center gap-4 border-b border-gray-100 py-1 text-xs text-gray-600">
                <span className="font-mono">{t.event_id}</span>
                <span>{t.type}</span>
                <span>{yuan(t.amount)}</span>
                <span className="text-gray-400">税率 {(t.tax_rate_bp / 100).toFixed(2)}%</span>
                <span className="text-gray-400">{t.ts.slice(0, 10)}</span>
              </div>
            ))}
          </section>

          {/* 签章记录 */}
          <section data-testid="agent-dash-attest" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">签章记录（{data.attestations.length}）</h3>
            {data.attestations.length === 0 && <p className="text-xs text-gray-400">暂无签章申请</p>}
            {data.attestations.map((r) => (
              <div key={r.request_id} className="border-b border-gray-100 py-1.5 text-xs text-gray-600">
                <span className="font-mono">{r.request_id}</span> · {r.request_type} · {STATUS_LABEL[r.status] ?? r.status}
                {r.urgency === 'urgent' && ' · 🔴 紧急'}
                {r.reason && <span className="text-gray-400"> · {r.reason}</span>}
              </div>
            ))}
          </section>

          {/* 关联存证 */}
          <section data-testid="agent-dash-nca" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">关联存证（NCA 链，{data.nca_chain.length}）</h3>
            {data.nca_chain.length === 0 && <p className="text-xs text-gray-400">暂无关联存证</p>}
            {data.nca_chain.map((n) => (
              <div key={n.nca_id} className="border-b border-gray-100 py-1 font-mono text-[11px] text-gray-500">
                {n.nca_id} ← {n.prev_nca ?? 'GENESIS'} · {n.action} · {n.actor}
              </div>
            ))}
          </section>
        </div>
      )}
    </PageShell>
  )
}
