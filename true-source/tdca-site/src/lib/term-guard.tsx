// 单摘自旧版 shared/guards/index.tsx（G-1 术语防漂移：ID93/G-1 强制）
// 以内容定界；界面与文案逐字未改；import 由旧件顶部随摘（@/shared/terms → @/lib/terms）

import { scanTermDrift } from '@/lib/terms'

// ---------------------------------------------------------------------------
// G-1 术语守卫：扫描渲染文本中的漂移词（ID93/G-1）
// ---------------------------------------------------------------------------
export interface TermGuardProps {
  text: string
}
export function TermGuard({ text }: TermGuardProps) {
  const hits = scanTermDrift(text)
  if (hits.length === 0) return null
  return (
    <div data-testid="term-guard" className="rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700">
      G-1 术语漂移：{hits.map((h) => `「${h.phrase}」${h.reason}`).join('；')}
    </div>
  )
}
