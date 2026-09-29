// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F2 /agents 观测层（A-10 集群 + 五面板确权灯 + 拓扑）
// 约束矩阵: FRAMEWORK-001 §四 /agents + A-10 契约 + REV-002 §8B.5（确权状态灯）+ ID92
// 复用: TopologyEngine（tdca-frontend 既有，Cytoscape→SVG，B2 脱敏）
// =============================================================================
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { TopologyEngine, hashAgentId, type TopoData } from '@/components/workbuddy/TopologyEngine'

interface ClusterData {
  cluster: { endpoint: string; capability: string; id: string; status: string }[]
  note: string
}

type AttestState = 'valid' | 'expiring' | 'invalid'

const FIVE_PANELS: { key: string; name: string; desc: string; attestation: AttestState }[] = [
  { key: 'Trainer', name: '培训导师', desc: '学术交流 / 考核测评 / 学习路径（tdca-trainer）', attestation: 'valid' },
  { key: 'Executor', name: '执行官', desc: '任务执行 / 交付闭环（tdca-executor）', attestation: 'valid' },
  { key: 'Auditor', name: '审查官', desc: '代码审查 / 合规审计（tdca-code-reviewer）', attestation: 'valid' },
  { key: 'Service', name: '服务官', desc: '行业顾问 / 落地匹配（tdca-industry-advisor）', attestation: 'expiring' },
  { key: 'Genie', name: '效用精灵', desc: '正和满意解 / 效用计量（tdca-utility-genie）', attestation: 'valid' },
]

const ATTEST_DOT: Record<AttestState, string> = {
  valid: 'bg-emerald-500',
  expiring: 'bg-amber-500',
  invalid: 'bg-red-600',
}
const ATTEST_LABEL: Record<AttestState, string> = { valid: '有效', expiring: '将过期', invalid: '失效待审' }

/** F2 协作拓扑（模拟 TDCA 智能体网络；主体标识哈希化脱敏 B2） */
const TOPO_DATA: TopoData = {
  nodes: [
    { id: hashAgentId('TDID-TRAINER'), label: 'Trainer', type: 'official', status: 'active' },
    { id: hashAgentId('TDID-EXECUTOR'), label: 'Executor', type: 'official', status: 'active' },
    { id: hashAgentId('TDID-AUDITOR'), label: 'Auditor', type: 'gov', status: 'active' },
    { id: hashAgentId('TDID-GENIE'), label: 'Genie', type: 'gov', status: 'active' },
    { id: hashAgentId('TDID-NOTIFIER'), label: 'Notifier', type: 'infra', status: 'idle' },
  ],
  edges: [
    { from: hashAgentId('TDID-TRAINER'), to: hashAgentId('TDID-EXECUTOR'), label: '协作', state: 'flowing', tps: '150' },
    { from: hashAgentId('TDID-EXECUTOR'), to: hashAgentId('TDID-AUDITOR'), label: '审查', state: 'flowing', tps: '120' },
    { from: hashAgentId('TDID-GENIE'), to: hashAgentId('TDID-EXECUTOR'), label: '正和', state: 'idle' },
    { from: hashAgentId('TDID-NOTIFIER'), to: hashAgentId('TDID-AUDITOR'), label: '通知', state: 'idle' },
  ],
}

/** F2 观测层：智能体集群（A-10 能力状态 + 五面板确权灯 + 协作拓扑） */
export function AgentsPage() {
  const { status, data, nature } = useApiGet<ClusterData>('/api/v1/eios/cluster-status')

  return (
    <PageShell
      title="智能体集群观测"
      dataSource="A-10 GET /api/v1/eios/cluster-status + WS handshake + TopologyEngine"
      permission="登录 DID"
      description="五大智能体面板（Trainer/Executor/Auditor/Service/Genie）+ 确权状态灯 + 协作拓扑。"
    >
      <div className="space-y-5">
        {/* 集群能力状态（A-10） */}
        <section data-testid="agents-cluster" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">集群能力状态（GenieAPI 十端点）</h3>
          {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
          {status === 'fail' && (
            <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="agents-fail-closed">
              [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染（ID91/ID85）
            </p>
          )}
          {status === 'ok' && data && (
            <>
              <div className="mb-2 flex items-center gap-2 text-xs text-gray-500">
                <SimulatedBadge nature={nature ?? 'simulated'} />
                <span>{data.note}</span>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
                    <th className="py-1.5">端点</th>
                    <th className="py-1.5">能力</th>
                    <th className="py-1.5">ID</th>
                    <th className="py-1.5">状态</th>
                  </tr>
                </thead>
                <tbody>
                  {data.cluster.map((c) => (
                    <tr key={c.endpoint} data-endpoint={c.endpoint} className="border-b border-gray-100">
                      <td className="py-1.5 font-mono text-xs text-gray-700">{c.endpoint}</td>
                      <td className="py-1.5 text-xs text-gray-600">{c.capability}</td>
                      <td className="py-1.5 font-mono text-[10px] text-gray-400">{c.id}</td>
                      <td className="py-1.5">
                        <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${c.status === 'READY' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                          {c.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </section>

        {/* 五大智能体面板 + 确权状态灯（REV-002 §8B.5） */}
        <section data-testid="agents-panels" className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-5">
          {FIVE_PANELS.map((p) => (
            <div key={p.key} data-panel={p.key} className="rounded-lg border border-gray-200 bg-white p-3">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-800">{p.name}</span>
                <span className="flex items-center gap-1">
                  <span data-attestation={p.attestation} className={`h-2.5 w-2.5 rounded-full ${ATTEST_DOT[p.attestation]}`} />
                  <span className="text-[10px] text-gray-500">{ATTEST_LABEL[p.attestation]}</span>
                </span>
              </div>
              <div className="text-[11px] text-gray-500">{p.desc}</div>
            </div>
          ))}
        </section>

        {/* 协作拓扑（TopologyEngine 复用，B2 脱敏） */}
        <section data-testid="agents-topology" className="rounded-lg border border-gray-200 p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-800">协作拓扑（Cytoscape → SVG，主体哈希化脱敏）</h3>
            <SimulatedBadge nature="simulated" />
          </div>
          <TopologyEngine data={TOPO_DATA} height={320} />
        </section>
      </div>
    </PageShell>
  )
}
