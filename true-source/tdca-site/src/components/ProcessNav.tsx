// 批 2 骨架：左侧协作流程竖列（14 环通俗名，可折叠，信息向）
// 环名取对外通俗口径；「争议裁决」如实呈现（裁决权属司法，平台不代裁）
import { useState } from 'react'

const RINGS: { name: string; note?: string }[] = [
  { name: '发现' },
  { name: '相遇' },
  { name: '握手' },
  { name: '谈判' },
  { name: '试错' },
  { name: '验证' },
  { name: '签约' },
  { name: '履约准备' },
  { name: '履约' },
  { name: '交付' },
  { name: '验收' },
  { name: '结算分配' },
  { name: '争议裁决', note: '权属司法' },
  { name: '信用及遗产管理' },
]

export function ProcessNav() {
  const [open, setOpen] = useState(true)
  return (
    <aside data-testid="process-nav" className="w-44 shrink-0 border-r bg-background p-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="mb-1 w-full rounded px-2 py-1 text-left text-xs font-semibold text-muted-foreground hover:bg-muted/60"
      >
        协作流程 {open ? '▾' : '▸'}
      </button>
      {open && (
        <ol className="space-y-0.5">
          {RINGS.map((r, i) => (
            <li key={r.name} className="rounded px-2 py-1 text-xs text-muted-foreground">
              {i + 1}. {r.name}
              {r.note ? <span className="ml-1 text-[10px] opacity-70">（{r.note}）</span> : null}
            </li>
          ))}
        </ol>
      )}
    </aside>
  )
}
