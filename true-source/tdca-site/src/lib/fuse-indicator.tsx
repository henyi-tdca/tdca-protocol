// 单摘自旧版 shared/guards/index.tsx（F-4 熔断三色灯 · 连带 FuseState/FUSE_META）
// 界面与文案逐字未改

export type FuseState = 'CLOSED' | 'SUSPENDED' | 'BLOCKED'

const FUSE_META: Record<FuseState, { label: string; dot: string; desc: string }> = {
  CLOSED: { label: 'CLOSED 运行', dot: 'bg-emerald-500', desc: '熔断器闭合，规则流正常运行' },
  SUSPENDED: { label: 'SUSPENDED 挂起', dot: 'bg-amber-500', desc: '疑似负空间逼近，规则流挂起待审' },
  BLOCKED: { label: 'BLOCKED 阻断', dot: 'bg-red-600', desc: '触碰法律/伦理红线（LEGAL 绝对熔断，无替代路径）' },
}

// ---------------------------------------------------------------------------
// F-4 熔断三色灯：绿=CLOSED / 金=SUSPENDED / 红=BLOCKED
// ---------------------------------------------------------------------------
export interface FuseIndicatorProps {
  state: FuseState
  label?: string
}
export function FuseIndicator({ state, label }: FuseIndicatorProps) {
  const meta = FUSE_META[state]
  return (
    <div data-testid="fuse-indicator" data-state={state} className="flex items-center gap-2">
      <span data-testid="fuse-dot" className={`h-3 w-3 rounded-full ${meta.dot}`} />
      <span className="text-sm font-medium text-gray-800">{label ?? meta.label}</span>
      <span className="text-xs text-gray-500">{meta.desc}</span>
    </div>
  )
}
