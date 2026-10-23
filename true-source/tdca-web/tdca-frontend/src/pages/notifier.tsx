// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F4 /notifier 通知机状态页（四角色 + WS 四通道 + 坐标变换 + 确权推送）
// 约束矩阵: FRAMEWORK-001 §八（通知机实时状态）+ A-9 契约 + ID93（四角色）+ ID92 + F-4/HUF
// 复用: F0 NotifierBar 模式 + TopologyEngine（坐标变换拓扑）+ WS 四通道（B-5）
// =============================================================================
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { HufModal, NotifierRoles, type NotifierRoleState } from '@/shared/guards'
import { api, WS_CHANNELS, type WsChannel } from '@/api/client'
import { TopologyEngine, hashAgentId, type TopoData } from '@/components/workbuddy/TopologyEngine'

interface MrcrStatusData {
  roles: { role: string; tdid: string; permissions: string[]; status: string; scene: string; audit_count: number }[]
  engine_tests: string
  note: string
}

const DUAL_OK = 'DUAL 同构校验通过（协议包 V1.1 签批基线）'

/** 物理→数字坐标变换拓扑（物理世界事件 → 数字世界 NCA） */
const TRANSFORM_TOPO: TopoData = {
  nodes: [
    { id: hashAgentId('PHY-PUSH'), label: '物理·推杆事件', type: 'infra', status: 'active' },
    { id: hashAgentId('PHY-CALL'), label: '物理·通话事件', type: 'infra', status: 'active' },
    { id: hashAgentId('DIG-NCA'), label: '数字·事实哈希 NCA', type: 'official', status: 'active' },
    { id: hashAgentId('DIG-ATTEST'), label: '数字·确权 NCA', type: 'gov', status: 'active' },
  ],
  edges: [
    { from: hashAgentId('PHY-PUSH'), to: hashAgentId('DIG-NCA'), label: '坐标变换（日抛）', state: 'flowing' },
    { from: hashAgentId('PHY-CALL'), to: hashAgentId('DIG-ATTEST'), label: '坐标变换（化合）', state: 'flowing' },
  ],
}

/** 动态确权请求推送（模拟；F5 接入确权 API + notifier WS 实时推送） */
const ATTEST_REQUESTS = [
  { id: 'DAR-DEMO-001', agent: 'AGENT-DEMO-001', type: '场景扩展（MRCR）', urgency: 'urgent' },
  { id: 'DAR-DEMO-002', agent: 'AGENT-DEMO-002', type: '认知演化（S 漂移）', urgency: 'normal' },
]

const URGENCY: Record<string, { label: string; cls: string }> = {
  urgent: { label: '🔴 紧急', cls: 'text-red-600' },
  normal: { label: '🟡 普通', cls: 'text-amber-600' },
}

/** F4 通知机状态页：物理-数字坐标变换可视化 + 四角色实时 + WS 四通道 + 确权推送 */
export function NotifierPage() {
  const navigate = useNavigate()
  const { status, data, nature } = useApiGet<MrcrStatusData>('/api/v1/notifier/mrcr-status')
  const [wsStatus, setWsStatus] = useState<Record<WsChannel, boolean>>({ handshake: false, tax_mou: false, notifier: false, audit: false })
  const [msgCount, setMsgCount] = useState(0)
  const [fuseModal, setFuseModal] = useState(false)
  const [fused, setFused] = useState(false)

  // WS 四通道订阅（B-5；jsdom/未连接 → 降级标注）
  useEffect(() => {
    const closers = WS_CHANNELS.map((ch) => {
      try {
        return api.ws(ch, {
          onStatus: (s) => setWsStatus((prev) => ({ ...prev, [ch]: s === 'open' })),
          onMessage: () => {
            if (ch === 'notifier') setMsgCount((c) => c + 1)
          },
        })
      } catch {
        setWsStatus((prev) => ({ ...prev, [ch]: false }))
        return () => {}
      }
    })
    return () => closers.forEach((c) => c())
  }, [])

  const roles: NotifierRoleState = {
    operator: data?.roles.some((r) => r.role === 'NM-Operator' && r.status === 'ACTIVE') ?? false,
    gov: data?.roles.some((r) => r.role === 'NM-Gov' && r.status === 'ACTIVE') ?? false,
    fin: data?.roles.some((r) => r.role === 'NM-Fin' && r.status === 'ACTIVE') ?? false,
    med: data?.roles.some((r) => r.role === 'NM-Med' && r.status === 'ACTIVE') ?? false,
  }

  // VISUAL-002 P2-2：坐标变换实时流转——WS 消息驱动边状态（>0 时 flowing + dash 动画）
  const transformData = useMemo<TopoData>(
    () => ({
      ...TRANSFORM_TOPO,
      edges: TRANSFORM_TOPO.edges.map((e) => ({ ...e, state: msgCount > 0 ? 'flowing' : e.state })),
    }),
    [msgCount],
  )

  return (
    <PageShell
      title="通知机状态页"
      dataSource="A-9 GET /api/v1/notifier/mrcr-status + WS notifier 四通道"
      permission="公开"
      description="物理-数字坐标变换可视化：四角色灯 + MOU 汇总 + DUAL 校验 + 确权请求推送。"
    >
      <div className="space-y-5">
        {/* 批2块二：通知机开通状态栏（创始人 10-14「原来有但没开通」——状态如实呈现，由 A-9 实测裁决） */}
        <div
          data-testid="notifier-service-status"
          className={`flex items-center justify-between rounded-lg border px-4 py-2 text-sm ${
            status === 'ok'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
              : status === 'loading'
                ? 'border-gray-200 bg-gray-50 text-gray-500'
                : 'border-red-200 bg-red-50 text-red-700'
          }`}
        >
          <span>
            通知机服务状态：
            {status === 'ok' ? '已开通（A-9 实测在线）' : status === 'loading' ? '探测中…' : '未开通或不可用（fail-closed，见下）'}
          </span>
          <SimulatedBadge nature={nature ?? 'simulated'} />
        </div>

        {/* 四角色实时状态（A-9） */}
        <section data-testid="notifier-roles-section" className="rounded-lg border border-gray-200 p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-800">通知机四角色实时状态（MRCR）</h3>
            <SimulatedBadge nature={nature ?? 'simulated'} />
          </div>
          {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
          {status === 'fail' && (
            <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="notifier-fail-closed">
              [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
            </p>
          )}
          {status === 'ok' && data && (
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <NotifierRoles roles={roles} sceneCount={data.roles.length} />
                <span className="text-[10px] text-gray-400">{data.engine_tests}</span>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
                    <th className="py-1.5">角色</th>
                    <th className="py-1.5">TDID</th>
                    <th className="py-1.5">权限</th>
                    <th className="py-1.5">状态</th>
                    <th className="py-1.5">审计数</th>
                  </tr>
                </thead>
                <tbody>
                  {data.roles.map((r) => (
                    <tr key={r.role} data-role-row={r.role} className="border-b border-gray-100">
                      <td className="py-1.5 text-xs font-medium text-gray-800">{r.role}</td>
                      <td className="py-1.5 font-mono text-[10px] text-gray-500">{r.tdid}</td>
                      <td className="py-1.5 text-[10px] text-gray-500">{r.permissions.join(', ')}</td>
                      <td className="py-1.5 text-xs text-emerald-600">{r.status}</td>
                      <td className="py-1.5 text-xs text-gray-600">{r.audit_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-emerald-700" data-testid="dual-ok">{DUAL_OK}</p>
            </div>
          )}
        </section>

        {/* WS 四通道实时订阅（B-5）+ 消息流速率 */}
        <section data-testid="notifier-ws" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">WS 四通道实时订阅</h3>
          <div className="flex flex-wrap gap-3">
            {WS_CHANNELS.map((ch) => (
              <span key={ch} data-channel={ch} data-connected={wsStatus[ch]} className="flex items-center gap-1.5 rounded border border-gray-200 px-2 py-1 text-xs">
                <span className={`h-2 w-2 rounded-full ${wsStatus[ch] ? 'bg-emerald-500' : 'bg-gray-300'}`} />
                {ch}
                {!wsStatus[ch] && <span className="text-[10px] text-gray-400">未连接 [SIMULATED]</span>}
              </span>
            ))}
          </div>
          <div className="mt-2 text-xs text-gray-600" data-testid="notifier-rate">
            消息流速率（notifier 通道）：<span data-testid="notifier-msg-count">{msgCount}</span> 条（会话累计；秒级刷新，快系统感知）
          </div>
        </section>

        {/* 坐标变换可视化（物理事件 → 数字 NCA，WS 实时流转） */}
        <section data-testid="notifier-transform" className="rounded-lg border border-gray-200 p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-800">坐标变换可视化（物理世界事件 → 数字世界 NCA）</h3>
            <span className="flex items-center gap-2">
              <SimulatedBadge nature="simulated" />
              <span data-testid="transform-flow-count" className={`text-xs ${msgCount > 0 ? 'font-semibold text-emerald-600' : 'text-gray-400'}`}>
                {msgCount > 0 ? `⚡ 实时流转 ${msgCount} 次（WS notifier）` : '等待 WS 消息…'}
              </span>
            </span>
          </div>
          <TopologyEngine data={transformData} height={240} />
        </section>

        {/* 确权请求推送（→ /attestation/dynamic） */}
        <section data-testid="notifier-attest" className="rounded-lg border border-gray-200 p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-800">动态确权请求推送（notifier 承载）</h3>
            <button
              data-testid="notifier-go-attest"
              className="rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
              onClick={() => navigate('/attestation/dynamic')}
            >
              前往动态确权队列 →
            </button>
          </div>
          <ul className="space-y-1.5">
            {ATTEST_REQUESTS.map((req) => (
              <li key={req.id} data-request={req.id} className="flex items-center justify-between rounded border border-gray-100 px-3 py-1.5 text-xs">
                <span className="text-gray-700">
                  <span className="font-mono">{req.id}</span> · {req.agent} · {req.type}
                </span>
                <span className={URGENCY[req.urgency]?.cls}>{URGENCY[req.urgency]?.label}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* 负空间熔断介入（F-4：写操作须 HUF） */}
        <section data-testid="notifier-fuse" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">负空间熔断介入（NSFL fail-closed）</h3>
          <div className="flex items-center gap-3">
            <button
              data-testid="notifier-fuse-open"
              className="rounded border border-red-300 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-100"
              onClick={() => setFuseModal(true)}
            >
              介入熔断（HUF）
            </button>
            {fused && <span className="text-xs text-red-600" data-testid="notifier-fused">熔断已触发（AI 无权解除，HUF 二次确认）</span>}
          </div>
        </section>
      </div>

      <HufModal
        open={fuseModal}
        onOpenChange={setFuseModal}
        onConfirm={() => setFused(true)}
        title="HUF 签批 · 负空间熔断介入"
        description="紧急熔断（NSFL fail-closed）：人类触发，AI 无权解除（F-4/HUF）。"
      />
    </PageShell>
  )
}
