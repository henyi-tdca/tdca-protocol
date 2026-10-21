// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI162-RULES-MAP-001 · /rules 制度地图页
// 约束矩阵: 交办令 §二 A~F（五类分组／五态徽标／六步导航／折叠区／注记原样）
//          ＋ §三（⛔ 标错态／⛔ 改 display_name／⛔ 改件／⛔ 直推 main）
//          ＋ §四（三族 9 件甲案标法·V1.0-FROZEN ＋ 必载注明）
//          ＋ §五（S5/S6 内容缺口：挂相邻件＋明标「待补」）
// 数据源: 唯一＝同目录 doc-map-rules.yaml（V6.1·0C0FE95560264A8E）?raw 原字节进包
// =============================================================================
import { useMemo, useState } from 'react'
import { PageShell } from '../PageShell'
import {
  parseDocMapItems,
  DOC_MAP_STATE_ORDER,
  DOC_MAP_CLASS_ORDER,
  DOC_MAP_STEP_LABELS,
  type DocMapItem,
} from './parse'
// ⭐ 单一事实源：机读表原字节进包（⛔ 不经手改写；哈希核验见 __tests__/rules-map.test.tsx）
import docMapYaml from './doc-map-rules.yaml?raw'

/** 五态徽标色阶（交办令 §二-C 建议档：文字与表内 state 逐字一致） */
const STATE_STYLES: Record<string, string> = {
  生效: 'bg-green-100 text-green-800 border-green-300',
  对外候选: 'bg-blue-100 text-blue-800 border-blue-300',
  草案: 'bg-gray-200 text-gray-700 border-gray-400',
  指引性: 'bg-cyan-100 text-cyan-800 border-cyan-300',
  非制度件: 'bg-gray-50 text-gray-500 border-gray-200',
  待辨: 'bg-yellow-100 text-yellow-800 border-yellow-300',
}

/** §四 三族甲案必载注明（创始人 2026-10-21 取甲·逐字） */
const FROZEN_NOTE = '文件开头仍载 V0.1-DRAFT；生效凭证 ＝ 2026-10-03 签批落地件（范围：期一内部运行）'

/** §四 注明适用件：三族（配置权市场／注册登记／授权件模板）且件头仍载 DRAFT 面貌者（恰 9 件） */
const FROZEN_NOTE_FAMILIES = [
  'TDCA-SPEC-CONFIGMARKET-001-',
  'TDCA-SPEC-REGISTER-OF-RIGHTS-001-',
  'TDCA-TEMPLATE-AUTH-001-',
]
function carriesFrozenNote(item: DocMapItem): boolean {
  return item.version === 'V1.0-FROZEN' && FROZEN_NOTE_FAMILIES.some((p) => item.filename.startsWith(p))
}

/** 「待补」步（§五）：S5 结算与计税／S6 争议与退出 */
const GAP_STEPS = ['S5', 'S6']
const STEP_SEQ = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']

function byFilename(a: DocMapItem, b: DocMapItem): number {
  return a.filename < b.filename ? -1 : a.filename > b.filename ? 1 : 0
}

function StateBadge({ state }: { state: string }) {
  const style = STATE_STYLES[state] ?? 'bg-gray-100 text-gray-600 border-gray-300'
  return (
    <span data-testid={`state-badge-${state}`} className={`inline-block rounded border px-1.5 py-0.5 text-[11px] font-medium ${style}`}>
      {state}
    </span>
  )
}

function DocRow({ item }: { item: DocMapItem }) {
  const showFrozenNote = carriesFrozenNote(item)
  return (
    <li data-testid="doc-row" className="rounded-lg border border-gray-200 bg-white px-3 py-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium text-gray-900">{item.display_name}</span>
        <StateBadge state={item.state} />
        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-600">{item.version || '—'}</span>
        {item.steps.map((s) => (
          <span key={s} className="rounded bg-purple-50 px-1.5 py-0.5 text-[11px] text-purple-700">
            {s}
          </span>
        ))}
        <span className={`rounded px-1.5 py-0.5 text-[11px] ${item.in_public ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>
          {item.in_public ? '公开可读' : '须登录'}
        </span>
      </div>
      {showFrozenNote && (
        <p data-testid="frozen-note" className="mt-1 text-xs text-blue-800">
          ⭐ {FROZEN_NOTE}
        </p>
      )}
      {item.state_note !== '' && (
        <p data-testid="state-note" className="mt-1 text-xs text-gray-600">
          {item.state_note}
        </p>
      )}
      {item.step_note !== '' && (
        <p data-testid="step-note" className="mt-1 text-xs text-gray-600">
          {item.step_note}
        </p>
      )}
    </li>
  )
}

export function RulesMapPage() {
  // M-4：解析 try/catch 兜底——表坏显示提示＋骨架，⛔ 白屏
  const [parsed] = useState<{ items: DocMapItem[]; error: boolean }>(() => {
    try {
      return { items: parseDocMapItems(docMapYaml), error: false }
    } catch {
      return { items: [], error: true }
    }
  })
  const items = parsed.items
  const [stepFilter, setStepFilter] = useState<string | null>(null)

  const visible = useMemo(() => items.filter((i) => i.page_visible), [items])
  const archived = useMemo(() => items.filter((i) => !i.page_visible), [items])

  const filtered = useMemo(
    () => (stepFilter ? visible.filter((i) => i.steps.includes(stepFilter)) : visible),
    [visible, stepFilter],
  )

  /** §五：待补步的相邻件（序列上前一／后一步；S6 无前可挂，挂 S5/S4 侧） */
  const adjacent = useMemo(() => {
    if (!stepFilter || !GAP_STEPS.includes(stepFilter)) return []
    const idx = STEP_SEQ.indexOf(stepFilter)
    const neighbors = new Set([STEP_SEQ[idx - 1], STEP_SEQ[idx - 2], STEP_SEQ[idx + 1]].filter(Boolean))
    return visible.filter((i) => i.steps.some((s) => neighbors.has(s)))
  }, [stepFilter, visible])

  const stateCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const s of DOC_MAP_STATE_ORDER) c[s] = 0
    for (const i of items) c[i.state] = (c[i.state] ?? 0) + 1
    return c
  }, [items])

  const classCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const k of DOC_MAP_CLASS_ORDER) c[k] = 0
    for (const i of items) c[i.class] = (c[i.class] ?? 0) + 1
    return c
  }, [items])

  const grouped = useMemo(() => {
    const g = new Map<string, DocMapItem[]>()
    for (const cls of DOC_MAP_CLASS_ORDER) g.set(cls, [])
    for (const i of filtered) {
      if (!g.has(i.class)) g.set(i.class, [])
      g.get(i.class)!.push(i)
    }
    for (const arr of g.values()) arr.sort(byFilename)
    return g
  }, [filtered])

  return (
    <PageShell
      title="制度地图"
      dataSource="机读表 _DOC-MAP-RULES-20261021-V6.1-FINAL（页面与检索同一源·仓内单源 ?raw 进包）"
      permission="公开"
      description="56 件制度件按五类分组、五态如实标、S1~S6 六步导航；五态与版本以在册机读表为唯一口径。"
    >
      {/* S1~S6 六步导航（§二-D：点步筛同一份表） */}
      <div data-testid="step-nav" className="mb-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setStepFilter(null)}
          className={`rounded px-2 py-1 text-xs ${stepFilter === null ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700'}`}
        >
          全部
        </button>
        {STEP_SEQ.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setStepFilter(stepFilter === s ? null : s)}
            className={`rounded px-2 py-1 text-xs ${stepFilter === s ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700'}`}
          >
            {s} {DOC_MAP_STEP_LABELS[s]}
            {GAP_STEPS.includes(s) && (
              <span data-testid={`step-gap-${s}`} className="ml-1 rounded bg-amber-100 px-1 py-px text-[9px] font-medium text-amber-700">
                待补
              </span>
            )}
          </button>
        ))}
      </div>

      {/* M-4：解析失败兜底提示（骨架保留：六步导航与空表仍在） */}
      {parsed.error && (
        <div data-testid="load-error" className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          本次数据加载失败，请稍后重试
        </div>
      )}

      {/* §五：S5/S6 待补横幅＋相邻件 */}
      {stepFilter && GAP_STEPS.includes(stepFilter) && (
        <div data-testid="gap-banner" className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          <strong>待补</strong>：{stepFilter} {DOC_MAP_STEP_LABELS[stepFilter]} 为内容缺口，本步制度件尚在补足途中（⛔ 不以草案充数）。
          {adjacent.length > 0 && (
            <span className="mt-1 block text-xs">
              相邻件（本步前两步 ＋ 后一步）挂接 {adjacent.length} 件，见下表（含相邻步标签者）。
            </span>
          )}
        </div>
      )}

      {/* 计数带（程序统计） */}
      <div data-testid="count-band" className="mb-4 flex flex-wrap gap-2 text-[11px] text-gray-600">
        <span className="rounded bg-gray-100 px-2 py-0.5">主表 {visible.length} 件 ＋ 历史草案 {archived.length} 件</span>
        {DOC_MAP_STATE_ORDER.map((s) => (
          <span key={s} className="rounded bg-gray-100 px-2 py-0.5">
            {s} {stateCounts[s]}
          </span>
        ))}
        {DOC_MAP_CLASS_ORDER.map((c) => (
          <span key={c} className="rounded bg-gray-100 px-2 py-0.5">
            {c} {classCounts[c]}
          </span>
        ))}
      </div>

      {/* 主表：五类分组（§二-A 顺序），组内 filename 升序 */}
      <div data-testid="rules-main" className="space-y-4">
        {DOC_MAP_CLASS_ORDER.map((cls) => {
          const arr = grouped.get(cls) ?? []
          if (arr.length === 0) return null
          return (
            <section key={cls} data-testid={`class-section-${cls}`}>
              <h3 className="mb-2 text-sm font-semibold text-gray-800">
                {cls}（{classCounts[cls]}）
              </h3>
              <ul className="space-y-2">
                {arr.map((i) => (
                  <DocRow key={i.filename} item={i} />
                ))}
              </ul>
            </section>
          )
        })}
      </div>

      {/* 历史草案折叠区（§二-E：page_visible=false 者不列主表） */}
      <details data-testid="rules-archived" className="mt-6 rounded-lg border border-gray-200 bg-gray-50 p-3">
        <summary className="cursor-pointer text-sm font-medium text-gray-700">
          历史草案（{archived.length}）——同制度已有 V1.0 生效版，以生效版为准
        </summary>
        <ul className="mt-2 space-y-2">
          {archived.sort(byFilename).map((i) => (
            <DocRow key={i.filename} item={i} />
          ))}
        </ul>
      </details>
    </PageShell>
  )
}
