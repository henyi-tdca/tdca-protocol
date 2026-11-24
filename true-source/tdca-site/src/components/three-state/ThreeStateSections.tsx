// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: B1-001 三态可读面（负空间清单/沙盒可行域四维/正空间认读）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI228-B1-001 §二（页与接口同源·单一事实源 three_state_data.py）
// 红线: 人读正文零内部编号（H-4）；件号/存证号只入凭证位小字；⛔三态互混（1-12）
// =============================================================================
import { useApiGet } from '@/lib/useApi'

export interface NsClause {
  text: string
  basis_doc: string
  basis_ref: string
  basis_volume: string
  anchor: string
  strength: string
}

export interface NsCell {
  category: string
  operator: string
  status: 'has_clauses' | 'no_clauses'
  clauses?: NsClause[]
  note?: string
  note_basis_doc?: string
  note_basis_ref?: string
  note_basis_volume?: string
}

export interface NegativeSpaceData {
  version: string
  purpose: string
  wording_note: string
  operators: { symbol: string; name: string; desc: string }[]
  cells: NsCell[]
  human_judged: { title: string; items: { situation: string; trigger: string; basis_ref: string }[] }
}

export interface SandboxData {
  version: string
  purpose: string
  feasible_domain: {
    source_one: { name: string; detail: string }
    source_two: { name: string; detail: string }
    gate: { name: string; detail: string }
  }
  dimensions: {
    key: string
    name: string
    reads: string[]
    evidence: { type: string; label: string; sha256_16: string | null; ref: string; volume: string; note: string }[]
    unsolved: string
  }[]
}

export interface PositiveSpaceData {
  version: string
  purpose: string
  recompute_how: string
  items: { name: string; klass: string; read: string; commit: string; sha256_16: string; bytes: number; path: string }[]
  selection_note: string
}

const CELL_STYLE: Record<string, string> = {
  '⊗': 'border-red-200 bg-red-50/50',
  '⊘': 'border-amber-200 bg-amber-50/50',
  '⊙': 'border-sky-200 bg-sky-50/50',
}

const OPT_NAME: Record<string, string> = { '⊗': '禁止', '⊘': '限制', '⊙': '观察' }

/** 负空间清单式呈现（B1-1）：五类 × 三操作符十五格 */
export function NegativeSpaceListing() {
  const { status, data } = useApiGet<NegativeSpaceData>('/api/v1/three-state/negative-space', { tolerateMissingWatermark: true })
  if (status === 'loading') return <p className="text-sm text-gray-400">清单载入中…</p>
  if (status !== 'ok' || !data) return <p className="text-sm text-red-600">清单暂不可读（fail-closed：源异常即拒，请稍后重试）</p>

  const cats = ['法律', '公序良俗', '情绪', '信仰', '技术']
  return (
    <section data-testid="ns-listing" className="space-y-4">
      <div>
        <h3 className="mb-1 text-sm font-semibold text-gray-900">负空间清单（五类 × 三操作符 · 逐格到款）</h3>
        <p className="text-xs leading-relaxed text-gray-500">{data.purpose}</p>
        <p className="mt-1 text-xs leading-relaxed text-amber-800">{data.wording_note}</p>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {data.operators.map((op) => (
          <div key={op.symbol} className={`rounded-lg border p-3 ${CELL_STYLE[op.symbol]}`}>
            <div className="text-sm font-semibold text-gray-900">{op.symbol} {op.name}</div>
            <p className="mt-0.5 text-xs text-gray-600">{op.desc}</p>
          </div>
        ))}
      </div>
      <div className="space-y-3">
        {cats.map((cat) => (
          <div key={cat} className="rounded-lg border border-gray-200">
            <div className="border-b border-gray-100 px-3 py-2 text-sm font-semibold text-gray-900">{cat}</div>
            <div className="grid gap-3 p-3 md:grid-cols-3">
              {(['⊗', '⊘', '⊙'] as const).map((op) => {
                const cell = data.cells.find((c) => c.category === cat && c.operator === op)
                if (!cell) return null
                return (
                  <div key={op} data-testid={`ns-cell-${cat}-${op}`} className={`rounded-lg border p-3 ${CELL_STYLE[op]}`}>
                    <div className="mb-2 text-xs font-semibold text-gray-700">{op} {OPT_NAME[op]}</div>
                    {cell.status === 'has_clauses' ? (
                      <ul className="space-y-2">
                        {cell.clauses!.map((cl, i) => (
                          <li key={i} className="text-xs leading-relaxed text-gray-700">
                            <p>{cl.text}</p>
                            <p className="mt-1 text-[11px] text-gray-500">
                              依据：{cl.basis_doc}（{cl.basis_volume} 册）{cl.anchor ? `· ${cl.anchor}` : ''}
                            </p>
                            <p className="text-[11px] text-gray-400">强度：{cl.strength}</p>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-xs leading-relaxed text-gray-600">
                        <p>{cell.note}</p>
                        <p className="mt-1 text-[11px] text-gray-500">依据：{cell.note_basis_doc}{cell.note_basis_ref ? `（${cell.note_basis_volume} 册）` : ''}</p>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
      <div className="rounded-lg border border-gray-200 p-3">
        <h4 className="mb-2 text-sm font-semibold text-gray-900">{data.human_judged.title}</h4>
        <ul className="space-y-1.5">
          {data.human_judged.items.map((it, i) => (
            <li key={i} className="text-xs leading-relaxed text-gray-700">
              · {it.situation}——机验触发：{it.trigger}。
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[11px] text-gray-400">以上情形机器只触发、不裁决，一律归人判（凭证位依据见机读接口）。</p>
      </div>
    </section>
  )
}

/** 沙盒可行域 ＋ 四维分项（B1-2） */
export function SandboxDomainPanel() {
  const { status, data } = useApiGet<SandboxData>('/api/v1/three-state/sandbox', { tolerateMissingWatermark: true })
  if (status === 'loading') return <p className="text-sm text-gray-400">可行域载入中…</p>
  if (status !== 'ok' || !data) return <p className="text-sm text-red-600">可行域暂不可读（fail-closed）</p>

  return (
    <section data-testid="sandbox-domain" className="space-y-4">
      <div>
        <h3 className="mb-1 text-sm font-semibold text-gray-900">沙盒可行域（两源定界）</h3>
        <p className="text-xs leading-relaxed text-gray-500">{data.purpose}</p>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {[data.feasible_domain.source_one, data.feasible_domain.source_two, data.feasible_domain.gate].map((s, i) => (
          <div key={i} className="rounded-lg border border-gray-200 bg-gray-50/60 p-3">
            <div className="text-sm font-medium text-gray-900">{s.name}</div>
            <p className="mt-1 text-xs leading-relaxed text-gray-600">{s.detail}</p>
          </div>
        ))}
      </div>
      <div>
        <h4 className="mb-2 text-sm font-semibold text-gray-900">四维分项读数（⛔只给总分）</h4>
        <div className="space-y-3">
          {data.dimensions.map((d) => (
            <div key={d.key} data-testid={`sb-dim-${d.key}`} className="rounded-lg border border-gray-200 p-3">
              <div className="text-sm font-semibold text-gray-900">{d.name}</div>
              <ul className="mt-1.5 space-y-1">
                {d.reads.map((r, i) => (
                  <li key={i} className="text-xs leading-relaxed text-gray-700">· {r}</li>
                ))}
              </ul>
              <div className="mt-2 border-t border-dashed border-gray-100 pt-2">
                <div className="text-[11px] font-medium text-gray-500">证据件</div>
                <ul className="mt-1 space-y-1">
                  {d.evidence.map((e, i) => (
                    <li key={i} className="text-[11px] text-gray-500">
                      {e.type}｜{e.label}{e.sha256_16 ? `｜哈希 ${e.sha256_16}` : ''}{e.note ? `｜${e.note}` : ''}
                    </li>
                  ))}
                </ul>
                {d.unsolved && <p className="mt-1.5 text-[11px] leading-relaxed text-amber-800">{d.unsolved}</p>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/** 正空间认读文件（B1-3）：生效制度件选编，对存证可复算 */
export function PositiveSpaceReading() {
  const { status, data } = useApiGet<PositiveSpaceData>('/api/v1/three-state/positive-space', { tolerateMissingWatermark: true })
  if (status === 'loading') return <p className="text-sm text-gray-400">认读文件载入中…</p>
  if (status !== 'ok' || !data) return <p className="text-sm text-red-600">认读文件暂不可读（fail-closed）</p>

  return (
    <section data-testid="positive-reading" className="space-y-4">
      <div>
        <h3 className="mb-1 text-sm font-semibold text-gray-900">正空间认读（照什么条例做 · 对存证可复算）</h3>
        <p className="text-xs leading-relaxed text-gray-500">{data.purpose}</p>
        <p className="mt-1 text-xs leading-relaxed text-gray-600">复算路径：{data.recompute_how}</p>
      </div>
      <div className="space-y-2.5">
        {data.items.map((it, i) => (
          <div key={i} data-testid={`ps-item-${i}`} className="rounded-lg border border-gray-200 p-3">
            <div className="text-sm font-medium text-gray-900">{it.name}<span className="ml-2 text-[11px] font-normal text-gray-500">{it.klass}</span></div>
            <p className="mt-1 text-xs leading-relaxed text-gray-700">{it.read}</p>
            <p className="mt-1.5 font-mono text-[11px] text-gray-500">
              件哈希 {it.sha256_16} ｜ {it.bytes} 字节 ｜ 仓端提交 {it.commit}
            </p>
          </div>
        ))}
      </div>
      <p className="text-[11px] leading-relaxed text-gray-400">{data.selection_note}</p>
      <p className="text-[11px] leading-relaxed text-amber-800">本段是认读文件，不替代存证本身——核验以复算路径实跑为准（认读文件⛔代存证）。</p>
    </section>
  )
}
