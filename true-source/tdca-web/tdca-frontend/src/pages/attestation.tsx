// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F5 确权中心四页（总览/meta/dynamic/history）+ A-11 闭环
// 约束矩阵: FRAMEWORK-001 §八·B（确权中心）+ REV-002（出盒终裁）+ A-11 契约 + F-4/HUF + ID92
// =============================================================================
import { useState } from 'react'
import { Link } from 'react-router'
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { HufModal } from '@/shared/guards'
import { api } from '@/api/client'

// ---- A-11 契约类型 ----
interface QueueItem {
  request_id: string
  agent_id: string
  request_type: string
  urgency: string
  reason: string
}
interface QueueData {
  queue: QueueItem[]
  total: number
  note: string
}
interface HistoryItem {
  index: number
  nca_ref: string
  agent: string
  type: string
  status: string
  ts: string
}
interface HistoryData {
  chain: HistoryItem[]
  total: number
  note: string
}

const URGENCY: Record<string, { label: string; cls: string }> = {
  urgent: { label: '🔴 紧急', cls: 'text-red-600' },
  normal: { label: '🟡 普通', cls: 'text-amber-600' },
  low: { label: '🟢 低危', cls: 'text-emerald-600' },
}

const SIX_ELEMENTS = [
  'objective_function（目标函数）',
  'constraint_matrix（约束矩阵）',
  'prior_distribution（先验分布）',
  'config_boundary（配置权边界）',
  'expected_allocation（预期分配）',
  'audit_trail（审计轨迹）',
]

// =============================================================================
// /attestation 总览（队列摘要 + 统计 + 三入口）
// =============================================================================
export function AttestationOverviewPage() {
  const { status, data, nature } = useApiGet<QueueData>('/api/v1/attestation/queue')
  const urgent = data?.queue.filter((q) => q.urgency === 'urgent').length ?? 0

  return (
    <PageShell
      title="确权中心总览"
      dataSource="A-11 GET /api/v1/attestation/queue"
      permission="登录 DID + HUF"
      description="待审队列 + 最近事件 + 确权统计（元函数/动态/历史入口）。"
    >
      <div className="space-y-4">
        {/* L1SI182-RIGHT-CENTER-001 处2（照抄落定稿，⛔ 改写）：确权四类口径 */}
        <p data-testid="attestation-scope-note" className="rounded-lg border border-gray-200 bg-gray-50/60 p-3 text-sm text-gray-700">
          确权中心确认的是权利归属，共四类：① 所有权初始登记确权 ② 权属变更确权 ③ 使用权授权确权 ④ 使用权权利变更确权。合约的履行与备案不在本中心。
        </p>
        <div className="flex gap-3">
          <Link to="/attestation/meta" data-testid="link-meta" className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800 hover:bg-amber-100">
            元函数初始确权（出盒终裁）→
          </Link>
          <Link to="/attestation/dynamic" data-testid="link-dynamic" className="rounded-lg border border-blue-300 bg-blue-50 px-4 py-3 text-sm font-medium text-blue-800 hover:bg-blue-100">
            动态确权队列 → {urgent > 0 ? `${urgent} 紧急` : ''}
          </Link>
          <Link to="/attestation/history" data-testid="link-history" className="rounded-lg border border-gray-300 bg-gray-50 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-100">
            确权历史（NCA 链）→
          </Link>
        </div>
        {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
        {status === 'fail' && (
          <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="attest-overview-fail">
            [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
          </p>
        )}
        {status === 'ok' && data && (
          <section data-testid="attest-overview" className="rounded-lg border border-gray-200 p-4">
            <div className="mb-2 flex items-center gap-2 text-xs text-gray-500">
              <SimulatedBadge nature={nature ?? 'simulated'} />
              <span>待审队列：{data.total} 条（{urgent} 紧急）· {data.note}</span>
            </div>
            <ul className="space-y-1.5">
              {data.queue.map((q) => (
                <li key={q.request_id} data-queue-item={q.request_id} className="flex items-center justify-between rounded border border-gray-100 px-3 py-1.5 text-xs">
                  <span className="text-gray-700">{q.request_id} · {q.agent_id} · {q.reason}</span>
                  <span className={URGENCY[q.urgency]?.cls}>{URGENCY[q.urgency]?.label}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </PageShell>
  )
}

// =============================================================================
// /attestation/meta 元函数初始确权（沙盒出盒终裁，REV-002）
// =============================================================================
export function AttestationMetaPage() {
  const [activation, setActivation] = useState('1.35')
  const [checked, setChecked] = useState<string[]>([])
  const [modal, setModal] = useState(false)
  const [result, setResult] = useState<{ status: string; attestation_id: string; verified: boolean } | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function confirm() {
    setError(null)
    const res = await api.post<{ status: string; attestation_id: string; verified: boolean }>(
      '/api/v1/attestation/meta',
      { agent_id: 'AGENT-DEMO-001', activation: Number(activation) || 0, six_elements: Object.fromEntries(checked.map((c) => [c, 'ok'])) },
      { needHuf: true },
    )
    if (res.ok) setResult(res.data)
    else setError(`提交失败（fail-closed）：${res.reason}`)
  }

  const allChecked = SIX_ELEMENTS.length > 0 && checked.length === SIX_ELEMENTS.length

  return (
    <PageShell
      title="元函数初始确权（出盒终裁）"
      dataSource="A-11 POST /api/v1/attestation/meta"
      permission="HUF 强制"
      description="沙盒验证后、进入配置权市场前的人类确权（先验证后背书，REV-002 修正）。"
    >
      <div className="space-y-4">
        {/* 步骤 1：沙盒验证报告审阅 */}
        <section data-testid="meta-step1" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-1 text-sm font-semibold text-gray-800">步骤 1 · 沙盒验证报告审阅（只读）</h3>
          <ul className="space-y-0.5 text-xs text-gray-600">
            <li>✓ NCA 审计轨迹：compile_for_scene → NCA-SBX-DEMO（哈希完整）</li>
            <li>✓ 税收锚定：MOU ¥1,200（进项+出项）</li>
            <li>✓ 正和性验证：u_positive_sum PASS（θ=0.70）</li>
            <li>✓ L2-R8 核验 + 素材映射 10 冲突消解</li>
          </ul>
        </section>

        {/* 步骤 2：激活系数确认 */}
        <section data-testid="meta-step2" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-1 text-sm font-semibold text-gray-800">步骤 2 · 激活系数确认（&gt;1.2 财政自给性）</h3>
          <input
            data-testid="meta-activation"
            value={activation}
            onChange={(e) => setActivation(e.target.value)}
            className="w-32 rounded border border-gray-300 px-2 py-1 text-sm"
          />
          <span className="ml-2 text-xs text-gray-500">
            {Number(activation) > 1.2 ? '✅ 达标（&gt;1.2）' : '⚠ 未达标（≤1.2 → 继续孵化或 HUF 特批）'}
          </span>
        </section>

        {/* 步骤 3：六要素终审 + HUF */}
        <section data-testid="meta-step3" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-1 text-sm font-semibold text-gray-800">步骤 3 · 六要素终审 + HUF 签署</h3>
          <ul className="mb-3 space-y-1">
            {SIX_ELEMENTS.map((el) => (
              <li key={el} className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  data-element={el}
                  checked={checked.includes(el)}
                  onChange={() => setChecked((c) => (c.includes(el) ? c.filter((x) => x !== el) : [...c, el]))}
                />
                <span className="text-gray-700">{el}</span>
              </li>
            ))}
          </ul>
          <button
            data-testid="meta-huf"
            disabled={!allChecked}
            className="rounded bg-amber-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-700 disabled:opacity-40"
            onClick={() => setModal(true)}
          >
            HUF 签署 · 生成 Meta-Attestation-NCA
          </button>
          {result && (
            <p data-testid="meta-result" className={`mt-2 text-sm ${result.status === 'SIGNED' ? 'text-emerald-700' : 'text-red-600'}`}>
              {result.status === 'SIGNED' ? `✅ 出盒终裁通过：${result.attestation_id}（激活系数 ${activation}）` : `❌ 拒绝：${result.attestation_id}`}
            </p>
          )}
          {error && <p className="mt-2 text-sm text-red-600" data-testid="meta-error">{error}</p>}
        </section>
      </div>
      <HufModal
        open={modal}
        onOpenChange={setModal}
        onConfirm={confirm}
        title="HUF 签批 · 元函数初始确权"
        description="出盒终裁：人类对智能体「存在合法性」的最终签署（慢系统）。AI 无权代行。"
      />
    </PageShell>
  )
}

// =============================================================================
// /attestation/dynamic 动态确权请求队列（紧急度排序 + 四操作）
// =============================================================================
export function AttestationDynamicPage() {
  const { status, data, nature, } = useApiGet<QueueData>('/api/v1/attestation/queue')
  const [deciding, setDeciding] = useState<{ id: string; decision: string } | null>(null)
  const [decisions, setDecisions] = useState<Record<string, string>>({})

  const DECISION_OPTIONS = [
    { value: 'approve', label: '批准' },
    { value: 'approve_modified', label: '修改后批准' },
    { value: 'reject', label: '拒绝' },
    { value: 'defer', label: '延后' },
  ]

  return (
    <PageShell
      title="动态确权请求队列"
      dataSource="A-11 GET /api/v1/attestation/queue + POST /api/v1/attestation/dynamic"
      permission="登录 DID + HUF"
      description="五类动态确权请求（场景扩展/认知演化/化合授权/负空间逼近/目标修正）紧急度排序。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
      {status === 'fail' && (
        <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="dynamic-fail">
          [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="dynamic-queue" className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <SimulatedBadge nature={nature ?? 'simulated'} />
            <span>共 {data.total} 条 · {data.note}</span>
          </div>
          {data.queue.map((q) => {
            const decided = decisions[q.request_id]
            return (
              <div key={q.request_id} data-request={q.request_id} className="rounded-lg border border-gray-200 p-3">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-800">{q.request_id} · {q.agent_id}</span>
                  <span className={URGENCY[q.urgency]?.cls}>{URGENCY[q.urgency]?.label}</span>
                </div>
                <div className="mb-2 text-xs text-gray-600">
                  {q.request_type}：{q.reason}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {DECISION_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      data-decision={opt.value}
                      data-request-id={q.request_id}
                      className="rounded border border-blue-600 bg-blue-600 px-2 py-0.5 text-[11px] text-white hover:bg-blue-700"
                      onClick={() => setDeciding({ id: q.request_id, decision: opt.value })}
                    >
                      {opt.label}
                    </button>
                  ))}
                  {decided && (
                    <span data-testid={`decision-${q.request_id}`} className={`text-[11px] font-medium ${decided === 'reject' ? 'text-red-600' : 'text-emerald-600'}`}>
                      → {decided}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
      <HufModal
        open={deciding !== null}
        onOpenChange={(o) => setDeciding(o ? deciding : null)}
        onConfirm={async () => {
          if (!deciding) return
          const res = await api.post<{ status: string; nca_ref: string }>(
            '/api/v1/attestation/dynamic',
            { request_id: deciding.id, decision: deciding.decision },
            { needHuf: true },
          )
          if (res.ok) {
            setDecisions((d) => ({ ...d, [deciding.id]: res.data.status }))
          }
          setDeciding(null)
        }}
        title="HUF 签批 · 动态确权审批"
        description={`审批请求 ${deciding?.id ?? ''}（决策：${deciding?.decision ?? ''}）。人类 HUF 决策，AI 无权代行。`}
      />
    </PageShell>
  )
}

// =============================================================================
// /attestation/history 确权历史（NCA 链跨代 + 拒绝高亮）
// =============================================================================
export function AttestationHistoryPage() {
  const { status, data, nature } = useApiGet<HistoryData>('/api/v1/attestation/history')

  return (
    <PageShell dataNature="real"
      title="确权历史（NCA 链跨代）"
      dataSource="A-11 GET /api/v1/attestation/history"
      permission="公开（制度即公开）"
      description="Meta-Attestation-NCA 跨代追溯 + 拒绝事件高亮 + 延迟分析。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
      {status === 'fail' && (
        <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="history-fail">
          [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="history-chain" className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <SimulatedBadge nature={nature ?? 'simulated'} />
            <span>NCA 链跨代：{data.total} 条 · {data.note}</span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
                <th className="py-1.5">#</th>
                <th className="py-1.5">NCA 引用</th>
                <th className="py-1.5">智能体</th>
                <th className="py-1.5">类型</th>
                <th className="py-1.5">状态</th>
                <th className="py-1.5">时间</th>
              </tr>
            </thead>
            <tbody>
              {data.chain.map((c) => (
                <tr key={c.index} data-nca={c.nca_ref} data-status={c.status} className={`border-b border-gray-100 ${c.status === 'REJECTED' ? 'bg-red-50' : ''}`}>
                  <td className="py-1.5 text-xs text-gray-400">{c.index}</td>
                  <td className="py-1.5 font-mono text-xs text-blue-700">{c.nca_ref}</td>
                  <td className="py-1.5 text-xs text-gray-600">{c.agent}</td>
                  <td className="py-1.5 text-xs text-gray-600">{c.type}</td>
                  <td className={`py-1.5 text-xs font-medium ${c.status === 'REJECTED' ? 'text-red-600' : 'text-emerald-600'}`}>
                    {c.status}
                  </td>
                  <td className="py-1.5 font-mono text-[10px] text-gray-400">{c.ts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PageShell>
  )
}
