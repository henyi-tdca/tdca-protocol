// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-5CC-W7-002 | 目标函数: W7 全周期仪表盘（LifecycleDashboard）
// 约束矩阵: TDCA-TASK-W7-FRONTEND-001 §2.2（时间轴/详情/异常/NCA 链/导出）
// 配置权边界: L2 展示层（只读消费冻结 API）
// 负空间版本: NSFL-V0.2 | 审计轨迹: TDCA-NCA-W7-20260811
// =============================================================================
import { useState } from 'react'
import { Download, ExternalLink } from 'lucide-react'

export interface LifecycleNode {
  step: string
  label: string
  status: 'ok' | 'block' | 'pending'
  detail?: Record<string, string | number | boolean>
  nca_ref?: string
}

export interface DashboardData {
  request_id: string
  nodes: LifecycleNode[]
  nca_chain: string[]
}

// ---- 生命周期时间轴（H-W7-006 节点点击展开 <200ms）----
export function LifecycleTimeline({
  nodes,
  onSelect,
}: {
  nodes: LifecycleNode[]
  onSelect: (n: LifecycleNode) => void
}) {
  return (
    <div data-testid="lifecycle-timeline" className="flex items-center gap-1 overflow-x-auto p-2">
      {nodes.map((n, i) => (
        <div key={n.step} className="flex items-center">
          <button
            data-testid={`node-${n.step}`}
            className="rounded border px-2 py-1 text-xs"
            style={{
              borderColor: n.status === 'block' ? '#ef4444' : n.status === 'ok' ? '#22c55e' : '#eab308',
              animation: n.status === 'block' ? 'pulse 1s infinite' : undefined,
            }}
            onClick={() => onSelect(n)}
          >
            {n.label}
          </button>
          {i < nodes.length - 1 && <span className="mx-0.5 text-gray-400">→</span>}
        </div>
      ))}
    </div>
  )
}

// ---- 详情面板（数据与后端 100% 一致，CP-4）----
export function DetailPanel({ node }: { node: LifecycleNode | null }) {
  if (!node) return <div data-testid="detail-panel" className="p-3 text-sm text-gray-400">选中节点查看详情</div>
  return (
    <div data-testid="detail-panel" className="p-3 text-sm">
      <div className="font-medium">{node.label}</div>
      <ul className="mt-1 space-y-0.5">
        {Object.entries(node.detail ?? {}).map(([k, v]) => (
          <li key={k}>
            <span className="text-gray-500">{k}:</span> {String(v)}
          </li>
        ))}
        {node.nca_ref && (
          <li>
            <span className="text-gray-500">NCA:</span>{' '}
            <a data-testid={`nca-link-${node.nca_ref}`} href={`nca://${node.nca_ref}`} className="text-blue-600">
              {node.nca_ref} <ExternalLink size={12} className="inline" />
            </a>
          </li>
        )}
      </ul>
    </div>
  )
}

// ---- NCA 链追踪（H-W7-008 链接可点击，无断裂 CP-5）----
export function NCAChain({ chain }: { chain: string[] }) {
  return (
    <div data-testid="nca-chain" className="p-3 text-xs">
      <div className="font-medium text-gray-500">NCA 链（{chain.length} 条）</div>
      <div className="mt-1 space-y-0.5">
        {chain.map((ref, i) => (
          <div key={i} className="flex items-center gap-1">
            <span className="text-gray-400">{i + 1}.</span>
            <a data-testid={`chain-link-${i}`} href={`nca://${ref}`} className="text-blue-600 hover:underline">
              {ref}
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---- 导出报告（H-W7-010 JSON 审计报告）----
export function exportReport(data: DashboardData): string {
  return JSON.stringify(
    {
      request_id: data.request_id,
      exported_at: new Date().toISOString(),
      nodes: data.nodes.map((n) => ({
        step: n.step,
        label: n.label,
        status: n.status,
        detail: n.detail ?? {},
        nca_ref: n.nca_ref ?? null,
      })),
      nca_chain: data.nca_chain,
    },
    null,
    2,
  )
}

export function ExportButton({ data }: { data: DashboardData }) {
  const download = () => {
    const blob = new Blob([exportReport(data)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-${data.request_id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }
  return (
    <button data-testid="export-button" className="flex items-center gap-1 rounded bg-gray-800 px-2 py-1 text-xs text-white" onClick={download}>
      <Download size={12} /> 导出报告
    </button>
  )
}
