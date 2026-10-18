// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 /governance 治理中心（A-8 HUF 强制写操作）
// 约束矩阵: FRAMEWORK-001 §四 /governance + A-8 契约 + F-4/HUF（写操作模态 + B-4 token）+ ID92
// =============================================================================
import { useState } from 'react'
import { api } from '@/lib/client'
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'
import { HufModal } from '@/lib/huf-modal'
import { FuseIndicator } from '@/lib/fuse-indicator'

const ACTIONS = [
  { value: 'ota_upgrade', label: 'OTA 升级（活宪法）' },
  { value: 'fuse_confirm', label: '熔断确认' },
  { value: 'scene_approve', label: '场景批准' },
]

/** 治理中心：HUF 强制鉴权（B-4 token + 全局签批模态），写操作 fail-closed */
export function GovernancePage() {
  const [action, setAction] = useState('ota_upgrade')
  const [target, setTarget] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [fuseState] = useState<'CLOSED' | 'SUSPENDED' | 'BLOCKED'>('CLOSED')

  async function confirmSign() {
    setError(null)
    setResult(null)
    const res = await api.post<{ status: string; huf_irreducible: boolean; note: string }>(
      '/api/v1/governance/huf-sign',
      { action, target, signed_by: 'TDCA-FOUNDER-001' },
      { needHuf: true },
    )
    if (res.ok) {
      setResult(`HUF 签批登记：${res.data.status}（${res.data.note}）`)
    } else {
      setError(`写操作失败（fail-closed）：${res.reason}${res.status ? ` HTTP ${res.status}` : ''}`)
    }
  }

  return (
    <PageShell
      title="治理中心"
      dataSource="A-8 POST /api/v1/governance/huf-sign + emergency-fuse"
      permission="HUF 强制鉴权（B-4）"
      description="四大治理操作：HUF 签批 / 动态确权队列 / 紧急熔断 / OTA。"
    >
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <FuseIndicator state={fuseState} />
          <SimulatedBadge nature="simulated" />
        </div>

        {/* HUF 签批表单（F-4：写操作须模态框 + B-4 token） */}
        <section data-testid="governance-huf-form" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">HUF 人类签批登记（AI 无权代行）</h3>
          <div className="mb-3 flex flex-wrap items-center gap-3">
            <label className="text-xs text-gray-600">操作类型</label>
            <select
              data-testid="governance-action"
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            >
              {ACTIONS.map((a) => (
                <option key={a.value} value={a.value}>
                  {a.label}
                </option>
              ))}
            </select>
            <label className="text-xs text-gray-600">目标</label>
            <input
              data-testid="governance-target"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="如 TDID-AGENT-001"
              className="w-48 rounded border border-gray-300 px-2 py-1 text-sm"
            />
            <button
              data-testid="governance-open-modal"
              className="rounded bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700"
              onClick={() => setModalOpen(true)}
            >
              发起 HUF 签批
            </button>
          </div>
          {result && <p className="text-sm text-emerald-700" data-testid="governance-result">{result}</p>}
          {error && <p className="text-sm text-red-600" data-testid="governance-error">{error}</p>}
        </section>

        <HufModal open={modalOpen} onOpenChange={setModalOpen} onConfirm={confirmSign} title="HUF 人类最终签批（治理操作）" />
      </div>
    </PageShell>
  )
}
