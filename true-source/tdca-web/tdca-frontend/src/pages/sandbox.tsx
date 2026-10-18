// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 /sandbox 沙盒准入（A-5 SEA 五要件）
// 约束矩阵: FRAMEWORK-001 §四 /sandbox（L2 前置）+ A-5 契约 + ID92
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface SeaStatusData {
  sea: { requirement: string; status: 'GREEN' | 'AMBER' | 'RED'; note: string }[]
  all_green: boolean
  note: string
}

const STATUS_DOT: Record<string, string> = {
  GREEN: 'bg-emerald-500',
  AMBER: 'bg-amber-500',
  RED: 'bg-red-600',
}

/** NSFL 三层防线状态机（编译期 → 运行期 → 发布期；VISUAL-002 P2-3） */
const NSFL_LAYERS: { phase: string; layer: string; items: string[]; status: 'GREEN' | 'AMBER' | 'RED' }[] = [
  { phase: '编译期', layer: 'C1-C6', items: ['C1 编译规则检查', 'C4 注入防护', 'C6 负空间声明'], status: 'GREEN' },
  { phase: '运行期', layer: 'L1 / R5-R8', items: ['L1 运行时熔断（BLOCK/FUSE）', 'R5-R8 传感器分级（Safe/Warning/Blocked/Cryogenic）'], status: 'GREEN' },
  { phase: '发布期', layer: 'Layer-8', items: ['Layer-8 校验器（M1 移交）', '供应链签名（待裁决）'], status: 'AMBER' },
]

/** L2 前置沙盒（制度化学反应釜）：SEA 五要件状态，未全绿不可入盒 */
export function SandboxPage() {
  const { status, data, nature } = useApiGet<SeaStatusData>('/api/v1/sandbox/sea-status')
  const [sceneIds, setSceneIds] = useState('SCN-A, SCN-B')
  const [budget, setBudget] = useState('9000')
  const [boundary, setBoundary] = useState('SCOPE-PHY-001')
  const [applyMsg, setApplyMsg] = useState('')
  const [expanded, setExpanded] = useState('')
  const { status: meStatus, data: meData } = useApiGet<{ my_sandbox?: { apply_id: string; result: string | null; sea_snapshot: string; ts: string }[] }>('/api/v1/me/dashboard')

  const onApply = async () => {
    setApplyMsg('')
    const ids = sceneIds.split(/[,，\s]+/).map((x) => x.trim()).filter(Boolean)
    if (ids.length === 0) { setApplyMsg('请至少填一个场景 ID'); return }
    const r = await api.post<{ sandbox_id: string; nca_ref: string; note: string }>(
      '/api/v1/sandbox/apply',
      { scene_ids: ids, pcr_budget: Number(budget) || 0, nsfl_boundary: boundary })
    setApplyMsg(r.ok
      ? `已受理 ${r.data.sandbox_id}（存证 ${r.data.nca_ref}）——出盒须人类签名`
      : `申请失败：${r.reason}（须登录）`)
  }

  return (
    <PageShell
      title="沙盒准入（L2 前置反应釜）"
      dataSource="A-5 GET /api/v1/sandbox/sea-status + /cross-scene/*"
      permission="公开读 / 入盒须 HUF"
      description="沙盒 = 制度化学反应釜（CHEM-001~004）：SEA 五要件 + 激活系数 &gt;1.2 验证。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
      {status === 'fail' && (
        <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="sandbox-fail-closed">
          [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="sandbox-sea" className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <SimulatedBadge nature={nature ?? 'simulated'} />
            <span>{data.note}</span>
          </div>
          <div
            data-testid="sandbox-all-green"
            className={`rounded-lg border p-3 text-sm font-medium ${data.all_green ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'}`}
          >
            {data.all_green ? 'SEA 五要件全绿——可入盒' : 'SEA 五要件未全绿——不可入盒（AMBER 项不阻塞预研）'}
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
                <th className="py-1.5">要件</th>
                <th className="py-1.5">状态</th>
                <th className="py-1.5">说明</th>
              </tr>
            </thead>
            <tbody>
              {data.sea.map((s) => (
                <tr key={s.requirement} data-requirement={s.requirement} className="border-b border-gray-100">
                  <td className="py-2 font-medium text-gray-800">{s.requirement}</td>
                  <td className="py-2">
                    <span className="flex items-center gap-1.5">
                      <span className={`h-2.5 w-2.5 rounded-full ${STATUS_DOT[s.status] ?? 'bg-gray-300'}`} />
                      <span className="text-xs text-gray-600">{s.status}</span>
                    </span>
                  </td>
                  <td className="py-2 text-xs text-gray-500">{s.note}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* VISUAL-002 P2-3：NSFL 三层防线状态机（编译期 → 运行期 → 发布期） */}
          <section data-testid="nsfl-layers" className="mt-4 rounded-lg border border-gray-200 p-4">
            <h3 className="mb-3 text-sm font-semibold text-gray-800">NSFL 三层防线状态机（法律绝对负空间无补正 ⊗）</h3>
            <div className="flex flex-col items-stretch gap-3 md:flex-row md:items-center">
              {NSFL_LAYERS.map((layer, i) => (
                <div key={layer.phase} className="flex flex-1 flex-col gap-3 md:flex-row md:items-center">
                  <div data-phase={layer.phase} className="flex-1 rounded-lg border border-gray-200 bg-gray-50 p-3">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-sm font-semibold text-gray-800">{layer.phase} · {layer.layer}</span>
                      <span className="flex items-center gap-1">
                        <span className={`h-2.5 w-2.5 rounded-full ${STATUS_DOT[layer.status]}`} />
                        <span className="text-[10px] text-gray-500">{layer.status}</span>
                      </span>
                    </div>
                    <ul className="space-y-0.5 text-[11px] text-gray-600">
                      {layer.items.map((item) => (
                        <li key={item}>• {item}</li>
                      ))}
                    </ul>
                  </div>
                  {i < NSFL_LAYERS.length - 1 && (
                    <span data-testid={`nsfl-flow-${i}`} className="text-center text-lg text-gray-400 md:px-1">→</span>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* 入盒申请（A-5；带填写示例）＋我的申请全文 */}
          <section data-testid="sandbox-apply" className="mt-4 rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">入盒申请（A-5 沙盒编译-核验闭环）</h3>
            <div className="flex flex-wrap items-center gap-2">
              <input className="min-w-64 flex-1 rounded border border-gray-300 px-2 py-1 text-sm"
                placeholder="场景 ID 列表（如：SCN-A, SCN-B——逗号分隔）"
                value={sceneIds} onChange={(e) => setSceneIds(e.target.value)} />
              <input className="w-36 rounded border border-gray-300 px-2 py-1 text-sm"
                placeholder="PCR 预算（如：9000）"
                value={budget} onChange={(e) => setBudget(e.target.value)} />
              <input className="w-40 rounded border border-gray-300 px-2 py-1 text-sm"
                placeholder="NSFL 边界（如：SCOPE-PHY-001）"
                value={boundary} onChange={(e) => setBoundary(e.target.value)} />
              <button className="rounded bg-emerald-600 px-3 py-1 text-sm text-white hover:bg-emerald-700"
                onClick={onApply}>申请入盒</button>
            </div>
            {applyMsg && <p role="status" className="mt-2 text-xs text-gray-600">{applyMsg}</p>}
            <SimulatedBadge nature="simulated" />
            <span className="ml-2 text-xs text-gray-500">申请落库 sandbox_applications，SEA 快照全文如下（谁的数据谁可见）</span>

            {meStatus === 'ok' && (meData?.my_sandbox?.length ?? 0) > 0 && (
              <ul className="mt-3 space-y-1" data-testid="sandbox-my-applies">
                {meData?.my_sandbox?.map((a) => (
                  <li key={a.apply_id} className="text-xs text-gray-600">
                    <button
                      className="bg-transparent font-medium text-blue-600 underline hover:text-blue-800"
                      onClick={() => setExpanded(expanded === a.apply_id ? '' : a.apply_id)}>
                      {a.apply_id}
                    </button>
                    {' '}· {a.result ?? 'pending'} · {a.ts.slice(0, 19).replace('T', ' ')}
                    {expanded === a.apply_id && (
                      <pre className="mt-1 whitespace-pre-wrap rounded bg-gray-50 p-2 text-[11px] text-gray-700">
                        {a.sea_snapshot}
                      </pre>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </PageShell>
  )
}
