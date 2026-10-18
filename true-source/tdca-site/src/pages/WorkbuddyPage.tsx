// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F6 /workbuddy 人机协作工作台（P1 上站）
// 约束矩阵: P5 T-P5-001 契约 + 提案 P1 + 授权件四要件 2.4（智能体不得代签）
// 复用: PageShell / SimulatedBadge / api.post（会话令牌自动注入）
// =============================================================================
import { useState } from 'react'
import { api } from '@/lib/client'
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'

const DSL_EXAMPLE = {
  workflow_id: 'WF-DEMO-001',
  steps: [
    { scene: 'scene_alpha', function: 'f_alpha', role: 'L', config_right: 'S-Right', output: 'm1' },
    { scene: 'scene_beta', function: 'f_beta', role: 'L', config_right: 'S-Right', input: 'm1', output: 'm2' },
  ],
  human_gates: [{ after: 'workflow_complete' }],
}

interface ExecView {
  execution_id: string
  workflow_id: string
  status: string
  current_step: number
  nsfl_status: string
  nca_refs: string[]
  elapsed_ms: number
}

export function WorkbuddyPage() {
  const [dslText, setDslText] = useState(JSON.stringify(DSL_EXAMPLE, null, 2))
  const [created, setCreated] = useState<{ workflow_id: string; nca_ref: string } | null>(null)
  const [signature, setSignature] = useState('')
  const [execView, setExecView] = useState<ExecView | null>(null)
  const [execMsg, setExecMsg] = useState('')
  const [statusId, setStatusId] = useState('')
  const [statusView, setStatusView] = useState<ExecView | null>(null)
  const [sigReqId, setSigReqId] = useState('')
  const [hwSig, setHwSig] = useState('')
  const [logInt, setLogInt] = useState<{ integrity: boolean; worm_log_entries: number; workflow_defs: number; workflow_runs: number; signature_requests: number } | null>(null)

  const post = async <T,>(path: string, body: unknown): Promise<T | { error: string }> => {
    const r = await api.post<T>(path, body)
    if (!r.ok) return { error: r.reason }
    return r.data
  }

  const onCreate = async () => {
    setExecMsg('')
    let tpl: unknown
    try {
      tpl = JSON.parse(dslText)
    } catch {
      setExecMsg('DSL 非合法 JSON')
      return
    }
    const d = await post<{ workflow_id: string; nca_ref: string }>(
      '/api/v1/workbuddy/workflow/create', { workflow_template: tpl })
    if ('error' in d) { setExecMsg(`创建失败：${d.error}`); return }
    setCreated(d)
  }

  const onExecute = async () => {
    if (!created) return
    setExecMsg('')
    const d = await post<ExecView>('/api/v1/workbuddy/workflow/execute', {
      workflow_id: created.workflow_id, human_signature: signature,
    })
    if ('error' in d) { setExecMsg(`执行被拒：${d.error}（人类签名权不可绕过）`); return }
    setExecView(d)
    setStatusId(d.execution_id)
  }

  const onStatus = async () => {
    const r = await api.get<ExecView>(`/api/v1/workbuddy/workflow/status?execution_id=${encodeURIComponent(statusId)}`)
    setStatusView(r.ok ? r.data : null)
    if (!r.ok) setExecMsg(`状态查询失败：${r.reason}`)
  }

  const onSigRequest = async () => {
    const d = await post<{ signature_request_id: string }>('/api/v1/workbuddy/signature/request', {
      workflow_id: created?.workflow_id ?? '', gate_id: 'GATE-workflow-complete',
      description: '工作流人类签名门禁',
    })
    if ('error' in d) { setExecMsg(`签名请求失败：${d.error}`); return }
    setSigReqId(d.signature_request_id)
  }

  const onSigConfirm = async () => {
    const d = await post<{ verified: boolean; tx_hash: string }>('/api/v1/workbuddy/signature/confirm', {
      request_id: sigReqId, hardware_signature: hwSig,
    })
    if ('error' in d) { setExecMsg(`签名确认被拒：${d.error}`); return }
    setExecMsg(`签名已确认 tx=${d.tx_hash}`)
  }

  const onLogIntegrity = async () => {
    const r = await api.get<NonNullable<typeof logInt>>('/api/v1/workbuddy/log-integrity')
    if (r.ok && r.data) setLogInt(r.data)
  }

  const statusColor = (s?: string) =>
    s === 'COMPLETED' ? 'text-green-700' : s === 'BLOCKED' ? 'text-red-700' : 'text-amber-700'

  return (
    <PageShell
      title="WorkBuddy 人机协作工作台"
      dataSource="A-12 /api/v1/workbuddy/*（P5 引擎 + DB 持久化 + NCA 落链）"
      permission="登录 DID（会话鉴权 fail-closed；执行须人类签名）"
      description="跨场景工作流：创建 → 人类签名门禁执行 → 状态/NCA 全链可查。智能体不得代签。"
    >
      <div className="space-y-5">
        <section className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center justify-between text-sm font-semibold text-gray-800">
            ① 创建工作流（DSL）
            <SimulatedBadge nature="simulated" />
          </h3>
          <textarea
            className="h-40 w-full rounded border border-gray-300 p-2 font-mono text-xs"
            value={dslText}
            onChange={(e) => setDslText(e.target.value)}
            data-testid="wb-dsl"
          />
          <button className="mt-2 rounded bg-blue-700 px-4 py-1.5 text-sm text-white" onClick={onCreate}>
            创建（PENDING_HUMAN_GATE）
          </button>
          {created && (
            <p className="mt-2 text-xs text-green-700" data-testid="wb-created">
              已创建 {created.workflow_id} · 存证 {created.nca_ref}
            </p>
          )}
        </section>

        <section className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">② 人类签名执行（签名不可绕过）</h3>
          <div className="flex gap-2">
            <input
              className="w-64 rounded border border-gray-300 px-2 py-1 text-sm"
              placeholder="人类签名（≥8 字符）"
              value={signature}
              onChange={(e) => setSignature(e.target.value)}
              data-testid="wb-signature"
            />
            <button
              className="rounded bg-blue-700 px-4 py-1.5 text-sm text-white disabled:opacity-40"
              disabled={!created || signature.length < 8}
              onClick={onExecute}
            >
              执行工作流
            </button>
          </div>
          {execView && (
            <div className="mt-2 text-xs" data-testid="wb-exec">
              <p>
                {execView.execution_id} ·{' '}
                <span className={statusColor(execView.status)}>{execView.status}</span> · NSFL{' '}
                {execView.nsfl_status} · {execView.elapsed_ms} ms
              </p>
              <p className="mt-1 text-gray-500">NCA 链：{execView.nca_refs.length} 条</p>
            </div>
          )}
          {execMsg && <p className="mt-2 text-xs text-red-600" data-testid="wb-msg">{execMsg}</p>}
        </section>

        <section className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">③ 执行状态查询（DB 实读）</h3>
          <div className="flex gap-2">
            <input
              className="w-64 rounded border border-gray-300 px-2 py-1 text-sm"
              placeholder="execution_id"
              value={statusId}
              onChange={(e) => setStatusId(e.target.value)}
              data-testid="wb-status-id"
            />
            <button className="rounded border border-gray-400 px-4 py-1.5 text-sm" onClick={onStatus}>
              查询
            </button>
          </div>
          {statusView && (
            <p className="mt-2 text-xs" data-testid="wb-status">
              {statusView.execution_id} ·{' '}
              <span className={statusColor(statusView.status)}>{statusView.status}</span> · 步骤{' '}
              {statusView.current_step} · NCA {statusView.nca_refs.length} 条
            </p>
          )}
        </section>

        <section className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">④ 硬件签名通道（request → confirm）</h3>
          <div className="flex flex-wrap gap-2">
            <button className="rounded border border-gray-400 px-4 py-1.5 text-sm" onClick={onSigRequest}>
              发起签名请求
            </button>
            {sigReqId && <span className="self-center text-xs text-gray-600">{sigReqId}</span>}
            <input
              className="w-56 rounded border border-gray-300 px-2 py-1 text-sm"
              placeholder="硬件签名（模拟 ≥8 字符）"
              value={hwSig}
              onChange={(e) => setHwSig(e.target.value)}
              data-testid="wb-hwsig"
            />
            <button
              className="rounded border border-gray-400 px-4 py-1.5 text-sm disabled:opacity-40"
              disabled={!sigReqId || hwSig.length < 8}
              onClick={onSigConfirm}
            >
              确认签名
            </button>
          </div>
        </section>

        <section className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">⑤ WORM 日志完整性</h3>
          <button className="rounded border border-gray-400 px-4 py-1.5 text-sm" onClick={onLogIntegrity}>
            校验哈希链
          </button>
          {logInt && (
            <p className="mt-2 text-xs" data-testid="wb-log">
              integrity={String(logInt.integrity)} · WORM {logInt.worm_log_entries} 条 · 定义{' '}
              {logInt.workflow_defs} / 执行 {logInt.workflow_runs} / 签名 {logInt.signature_requests}
            </p>
          )}
        </section>
      </div>
    </PageShell>
  )
}
