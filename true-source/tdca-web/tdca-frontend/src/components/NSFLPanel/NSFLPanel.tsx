// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-5CC-W7-001 | 目标函数: W7 前端面板（NSFLPanel）
// 约束矩阵: TDCA-TASK-W7-FRONTEND-001 §2.1（边界三色/并集视图/⊗阻断/操作日志）
// 配置权边界: L2 展示层（只读消费冻结 API，不触发任何后端变更）
// 负空间版本: NSFL-V0.2 | 审计轨迹: TDCA-NCA-W7-20260811
// =============================================================================
import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, Ban, CheckCircle2, GitMerge, ShieldAlert } from 'lucide-react'

// ---- 颜色令牌（对齐 TDCA 设计系统，任务书 §2.1）----
export const NSFL_COLORS = {
  allow: '#22c55e',
  forbid: '#ef4444',
  limit: '#eab308',
} as const

export interface BoundaryItem {
  id: string
  label: string
  state: 'allow' | 'forbid' | 'limit'
}

export interface UnionConflict {
  ns_type: string
  description: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface UnionViewData {
  scene_a: string
  scene_b: string
  conflicts: UnionConflict[]
  alt_paths?: string[]
  risk_premium: number
}

export interface LogEntry {
  time: string
  message: string
  status?: 'ok' | 'warn' | 'block' | 'info'
}

// ---- 左侧：负空间边界清单（三色分类，H-W7-001 <100ms）----
export function NSFLBoundaryList({ items }: { items: BoundaryItem[] }) {
  const groups = {
    allow: items.filter((i) => i.state === 'allow'),
    forbid: items.filter((i) => i.state === 'forbid'),
    limit: items.filter((i) => i.state === 'limit'),
  }
  return (
    <div data-testid="nsfl-boundary-list" className="space-y-3 text-sm">
      <div>
        <div className="flex items-center gap-1 font-medium" style={{ color: NSFL_COLORS.allow }}>
          <CheckCircle2 size={14} /> 允许操作
        </div>
        {groups.allow.map((i) => (
          <div key={i.id} data-testid={`boundary-allow-${i.id}`} className="pl-4">
            · {i.label}
          </div>
        ))}
      </div>
      <div>
        <div className="flex items-center gap-1 font-medium" style={{ color: NSFL_COLORS.forbid }}>
          <Ban size={14} /> 禁止操作（⊗）
        </div>
        {groups.forbid.map((i) => (
          <div key={i.id} data-testid={`boundary-forbid-${i.id}`} className="pl-4">
            · {i.label} ⊗
          </div>
        ))}
      </div>
      <div>
        <div className="flex items-center gap-1 font-medium" style={{ color: NSFL_COLORS.limit }}>
          <AlertTriangle size={14} /> 限制操作
        </div>
        {groups.limit.map((i) => (
          <div key={i.id} data-testid={`boundary-limit-${i.id}`} className="pl-4">
            · {i.label}
          </div>
        ))}
      </div>
    </div>
  )
}

// ---- 右侧：跨场景并集视图（冲突高亮闪烁 1Hz，H-W7-002）----
export function CrossSceneUnionView({ data }: { data: UnionViewData }) {
  const [flash, setFlash] = useState(true)
  useEffect(() => {
    const t = setInterval(() => setFlash((f) => !f), 500) // 1Hz 闪烁
    return () => clearInterval(t)
  }, [])
  return (
    <div data-testid="union-view" className="space-y-2 text-sm">
      <div className="flex items-center gap-2">
        <span className="rounded bg-gray-100 px-2 py-1">{data.scene_a}</span>
        <GitMerge size={16} />
        <span className="rounded bg-gray-100 px-2 py-1">{data.scene_b}</span>
        <span data-testid="conflict-count">冲突 {data.conflicts.length} 项</span>
      </div>
      {data.conflicts.map((c) => (
        <div
          key={c.ns_type}
          data-testid={`conflict-${c.ns_type}`}
          className="rounded border px-2 py-1"
          style={{
            borderColor: NSFL_COLORS.forbid,
            opacity: flash ? 1 : 0.35, // 1Hz 闪烁
            transition: 'opacity 0.5s',
          }}
        >
          🔴 {c.ns_type}: {c.description}（{c.severity}）
        </div>
      ))}
      {data.alt_paths && data.alt_paths.length > 0 && (
        <div data-testid="alt-path" className="text-blue-600">
          💡 Alt-Path 推荐：绕行场景 {data.alt_paths.join(' / ')}
        </div>
      )}
      <div className="text-xs text-gray-500">risk_premium: {data.risk_premium}</div>
    </div>
  )
}

// ---- ⊗ 阻断弹窗（不可 ESC/外部关闭，必须选择，H-W7-003）----
export function BlockingModal({
  title,
  conflicts,
  altPaths,
  onChoose,
}: {
  title: string
  conflicts: UnionConflict[]
  altPaths?: string[]
  onChoose: (choice: 'alt' | 'cancel') => void
}) {
  const ref = useRef<HTMLDivElement>(null)
  return (
    <div
      data-testid="blocking-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
      onClick={(e) => e.stopPropagation()} // 点击外部不可关闭
    >
      <div ref={ref} className="w-[480px] rounded-lg bg-white p-6 shadow-xl" role="alertdialog">
        <div className="flex items-center gap-2 text-lg font-bold text-red-600">
          <ShieldAlert size={20} /> {title}
        </div>
        <p className="mt-2 text-sm">检测到负空间 ⊗ 阻断，必须选择处置路径：</p>
        <ul className="mt-2 space-y-1 text-sm">
          {conflicts.map((c) => (
            <li key={c.ns_type} className="text-red-500">
              ⊗ {c.ns_type}: {c.description}
            </li>
          ))}
        </ul>
        {altPaths && altPaths.length > 0 && (
          <p className="mt-2 text-sm text-blue-600">💡 可用替代路径：{altPaths.join(' / ')}</p>
        )}
        <div className="mt-4 flex gap-2">
          <button
            data-testid="choose-alt"
            className="rounded bg-blue-600 px-3 py-1.5 text-white"
            onClick={() => onChoose('alt')}
          >
            选择 Alt-Path
          </button>
          <button
            data-testid="choose-cancel"
            className="rounded bg-gray-200 px-3 py-1.5"
            onClick={() => onChoose('cancel')}
          >
            取消
          </button>
        </div>
      </div>
    </div>
  )
}

// ---- 底部：实时操作日志（H-W7-005 WebSocket <500ms）----
export function OperationLog({ entries }: { entries: LogEntry[] }) {
  return (
    <div data-testid="operation-log" className="h-32 overflow-y-auto bg-gray-900 p-2 font-mono text-xs text-gray-200">
      {entries.map((e, i) => (
        <div key={i} data-testid={`log-${i}`}>
          <span className="text-gray-500">[{e.time}]</span>{' '}
          <span className={e.status === 'block' ? 'text-red-400' : e.status === 'ok' ? 'text-green-400' : ''}>
            {e.message}
          </span>
        </div>
      ))}
    </div>
  )
}
