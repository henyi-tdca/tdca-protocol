// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI163-START-001 · /start 新手指引页（六步＋检索批3）
// 约束矩阵: 设计件 TDCA-DESIGN-L1SI163-001 §一（六步结构／只列 page_visible／缺口两处同标）
//          ＋ §二（目录筛四维 AND 叠加＋术语跳转 147 条·RTN 两义并列不合并）
//          ＋ §三（唯一数据源＝同目录 start-map.yaml·0CE5C89A957B6B60 ?raw 原字节进包；
//                  解析失败 try/catch 兜底⛔白屏）＋ §四 M-1~M-4 同批
// 数据源: 唯一＝同目录 start-map.yaml（_START-MAP-20261021-V1·0CE5C89A957B6B60）?raw 原字节进包
// =============================================================================
import { useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router'
import { PageShell } from '../PageShell'
import { parseStartMap, type StartDoc, type StartMapData, type StartStep, type StartTerm } from './parse'
// ⭐ 单一事实源：机读表原字节进包（⛔ 不经手改写；哈希核验见 __tests__/start-map.test.tsx）
import startMapYaml from './start-map.yaml?raw'

/** 五态徽标色阶（与 /rules 同档；本页公开面按设计件 §2.1 把「对外候选」显示为「生效」） */
const STATE_STYLES: Record<string, string> = {
  生效: 'bg-green-100 text-green-800 border-green-300',
  指引性: 'bg-cyan-100 text-cyan-800 border-cyan-300',
  草案: 'bg-gray-200 text-gray-700 border-gray-400',
  非制度件: 'bg-gray-50 text-gray-500 border-gray-200',
  待辨: 'bg-yellow-100 text-yellow-800 border-yellow-300',
}

/** 设计件 §2.1：态维度序列（待辨全表 0 件，不列芯片——回报注明） */
const STATE_ORDER = ['生效', '指引性', '草案', '对外候选', '非制度件'] as const
/** 设计件 §2.1：类维度序列 */
const CLASS_ORDER = ['条例', '标准与流程', '规范与细则', '模板与表单', '基本制度'] as const

/** 公开面态显示（设计件 §2.1：对外候选 ⛔ 显示为「生效」——仅显示层归一，筛选与排序仍按表内 raw 态） */
function displayState(state: string): string {
  return state === '对外候选' ? '生效' : state
}

/** 排序：态（§2.1 序列）→ 类（§2.1 序列）→ 显示名 */
function byCatalogOrder(a: StartDoc, b: StartDoc): number {
  const sa = STATE_ORDER.indexOf(a.state as (typeof STATE_ORDER)[number])
  const sb = STATE_ORDER.indexOf(b.state as (typeof STATE_ORDER)[number])
  if (sa !== sb) return (sa < 0 ? 99 : sa) - (sb < 0 ? 99 : sb)
  const ca = CLASS_ORDER.indexOf(a.class as (typeof CLASS_ORDER)[number])
  const cb = CLASS_ORDER.indexOf(b.class as (typeof CLASS_ORDER)[number])
  if (ca !== cb) return (ca < 0 ? 99 : ca) - (cb < 0 ? 99 : cb)
  return a.display_name < b.display_name ? -1 : a.display_name > b.display_name ? 1 : 0
}

/**
 * 反向查接口位（设计件 §2.2：依 DOC 表 keys 含该术语名或 T 号者计数——本批只留接口位，后续批接通）。
 * 返回 null 表示未接通；接通后改为返回具体件数。
 */
export function countReferencingDocs(_term: StartTerm, _docs: StartDoc[]): number | null {
  return null
}

/** T-### 号与术语全名⟹术语条目锚点（设计件 §2.2 文档内识别；同名并列不合并，命中首个在册条目） */
function buildTermPattern(terms: StartTerm[]): RegExp | null {
  const names = terms
    .map((t) => t.name)
    .filter((n) => n !== '')
    .sort((a, b) => b.length - a.length) // 长名优先，防短名截断长名（RTN vs RTN（协议层轧差））
    .map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  if (names.length === 0) return null
  return new RegExp(`(T-\\d{3}|${names.join('|')})`, 'g')
}

/** 正文内识别 T-### 与术语全名并生成跳转链接（⛔ 不改写文字本身） */
function Linkify({ text, terms }: { text: string; terms: StartTerm[] }) {
  const pattern = useMemo(() => buildTermPattern(terms), [terms])
  if (!pattern) return <>{text}</>
  const nodes: ReactNode[] = []
  let last = 0
  for (const m of text.matchAll(pattern)) {
    const idx = m.index
    if (idx > last) nodes.push(text.slice(last, idx))
    const hit = m[0]
    const term = terms.find((t) => t.id === hit) ?? terms.find((t) => t.name === hit)
    if (term) {
      nodes.push(
        <a key={nodes.length} href={`#term-${term.id}`} className="text-purple-700 underline decoration-dotted underline-offset-2">
          {hit}
        </a>,
      )
    } else {
      nodes.push(hit)
    }
    last = idx + hit.length
  }
  if (last < text.length) nodes.push(text.slice(last))
  return <>{nodes}</>
}

function StateBadge({ state }: { state: string }) {
  const shown = displayState(state)
  const style = STATE_STYLES[shown] ?? 'bg-gray-100 text-gray-600 border-gray-300'
  return (
    <span data-testid={`state-badge-${shown}`} className={`inline-block rounded border px-1.5 py-0.5 text-[11px] font-medium ${style}`}>
      {shown}
    </span>
  )
}

/** 定义首句（术语卡展示用：首个句读截断，无句读则整串） */
function firstSentence(s: string): string {
  const m = s.match(/^.*?[。！？]/)
  return m ? m[0] : s
}

function StartDocRow({ item, terms, archived }: { item: StartDoc; terms: StartTerm[]; archived?: boolean }) {
  return (
    <li data-testid="start-doc-row" className="rounded-lg border border-gray-200 bg-white px-3 py-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium text-gray-900">{item.display_name}</span>
        <StateBadge state={item.state} />
        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-600">{item.version || '—'}</span>
        {item.steps.map((s) => (
          <span key={s} className="rounded bg-purple-50 px-1.5 py-0.5 text-[11px] text-purple-700">
            {s}
          </span>
        ))}
        {archived && (
          <span className="rounded bg-gray-50 px-1.5 py-0.5 text-[11px] text-gray-500">历史草案（见 /rules 折叠区）</span>
        )}
      </div>
      {item.state_note !== '' && (
        <p data-testid="state-note" className="mt-1 text-xs text-gray-600">
          <Linkify text={item.state_note} terms={terms} />
        </p>
      )}
    </li>
  )
}

/** 解析兜底失败时的六步骨架（设计件 §三-4：保留骨架⛔白屏；名称照 §一 设计常量） */
const FALLBACK_STEPS: Pick<StartStep, 'key' | 'label' | 'scene'>[] = [
  { key: 'S1', label: '了解 TDCA', scene: '这是什么组织、在做什么、与本方有什么关系' },
  { key: 'S2', label: '读懂基本制度', scene: '宪法与基本制度：谁能做什么、底线在哪' },
  { key: 'S3', label: '看资产与授权', scene: '版权资产、权属登记、授权怎么拿、不能怎么用' },
  { key: 'S4', label: '参与协作', scene: '智能体互调、协作配置、接入与沙盒' },
  { key: 'S5', label: '结算与计税', scene: '钱怎么结、税怎么计、账怎么记' },
  { key: 'S6', label: '争议与退出', scene: '出了分歧怎么裁、怎么退、资产怎么继受' },
]

const PAGE_SHELL_PROPS = {
  title: '新手指引 · 六步上手 TDCA',
  dataSource: '_START-MAP 三表（单一事实源·仓内单源 ?raw 进包）',
  permission: '公开',
  description:
    'S1~S6 六步了解 TDCA：每步挂接该步制度件，缺口步如实标「待补」；目录四维筛选与 147 条术语检索同读 _START-MAP 三表。',
  dataNature: 'real' as const, // L1SI177-B123 块丁：仓内单源制度件 → real
}

export function StartPage() {
  // M-4：解析 try/catch 兜底——表坏显示提示＋骨架，⛔ 白屏
  const [parsed] = useState<{ data: StartMapData | null }>(() => {
    try {
      return { data: parseStartMap(startMapYaml) }
    } catch {
      return { data: null }
    }
  })
  return <StartPageBody data={parsed.data} />
}

export function StartPageBody({ data }: { data: StartMapData | null }) {
  const [selectedStep, setSelectedStep] = useState<string | null>(null)
  const [clsFilter, setClsFilter] = useState<string | null>(null)
  const [stateFilter, setStateFilter] = useState<string | null>(null)
  const [stepFilter, setStepFilter] = useState<string | null>(null)
  const [kw, setKw] = useState('')
  const [termKw, setTermKw] = useState('')

  const steps = useMemo(() => data?.steps ?? [], [data])
  const docs = useMemo(() => data?.docs ?? [], [data])
  const terms = useMemo(() => data?.terms ?? [], [data])

  const stepByKey = useMemo(() => new Map(steps.map((s) => [s.key, s])), [steps])

  /** §一-2：步内只列 page_visible=true（折叠 2 件仅在 /rules 折叠区可见） */
  const visibleDocs = useMemo(() => docs.filter((d) => d.page_visible), [docs])

  /** §一-5：相邻件＝本步之前两步＋后一步（越界省略，adjacent_steps 表内已算好） */
  const adjacentDocs = useMemo(() => {
    if (!selectedStep) return []
    const adj = stepByKey.get(selectedStep)?.adjacent_steps ?? []
    const set = new Set(adj)
    return visibleDocs.filter((d) => d.steps.some((s) => set.has(s)))
  }, [selectedStep, stepByKey, visibleDocs])

  const stepDocs = useMemo(() => {
    if (!selectedStep) return []
    return visibleDocs.filter((d) => d.steps.includes(selectedStep))
  }, [selectedStep, visibleDocs])

  /** §一-3 注记：步徽数＝STEP 表 count（含历史草案挂接数），与在列件数之差即折叠件，如实标注 */
  const stepFoldDelta = useMemo(() => {
    if (!selectedStep) return 0
    const step = stepByKey.get(selectedStep)
    if (!step) return 0
    return Math.max(0, step.count - stepDocs.length)
  }, [selectedStep, stepByKey, stepDocs])

  /* ---- 目录筛（§2.1：类／态／步／关键词，AND 叠加，实时计数） ---- */
  const classCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const k of CLASS_ORDER) c[k] = 0
    for (const d of docs) c[d.class] = (c[d.class] ?? 0) + 1
    return c
  }, [docs])

  const stateCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const s of STATE_ORDER) c[s] = 0
    for (const d of docs) c[d.state] = (c[d.state] ?? 0) + 1
    return c
  }, [docs])

  const stepCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const s of steps) c[s.key] = 0
    for (const d of docs) for (const s of d.steps) c[s] = (c[s] ?? 0) + 1
    return c
  }, [docs, steps])

  const catalog = useMemo(() => {
    const needle = kw.trim().toLowerCase()
    return docs
      .filter((d) => (clsFilter ? d.class === clsFilter : true))
      .filter((d) => (stateFilter ? d.state === stateFilter : true))
      .filter((d) => (stepFilter ? d.steps.includes(stepFilter) : true))
      .filter((d) => {
        if (needle === '') return true
        // 关键词命中 keys（显示名／件名／类／态／步／slug）＋公开面显示态（对外候选按「生效」可检）
        const hay = [...d.keys, displayState(d.state), ...d.steps].join('\n').toLowerCase()
        return hay.includes(needle)
      })
      .sort(byCatalogOrder)
  }, [docs, clsFilter, stateFilter, stepFilter, kw])

  const catalogLabel = [
    stateFilter ? `态＝${stateFilter}` : null,
    clsFilter ? `类＝${clsFilter}` : null,
    stepFilter ? `步＝${stepFilter}` : null,
    kw.trim() !== '' ? `关键词「${kw.trim()}」` : null,
  ]
    .filter(Boolean)
    .join(' · ')

  /* ---- 术语检索（§2.2：id／name／short_def 子串匹配） ---- */
  const termResults = useMemo(() => {
    const needle = termKw.trim().toLowerCase()
    if (needle === '') return terms
    return terms.filter((t) =>
      [t.id, t.name, t.short_def].join('\n').toLowerCase().includes(needle),
    )
  }, [terms, termKw])

  if (data === null) {
    return (
      <PageShell {...PAGE_SHELL_PROPS}>
        <div data-testid="load-error" className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          本次数据加载失败，请稍后重试
        </div>
        <div data-testid="step-cards" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {FALLBACK_STEPS.map((s) => (
            <div key={s.key} data-testid={`step-card-${s.key}`} className="rounded-lg border border-gray-200 bg-white p-3">
              <div className="text-sm font-semibold text-gray-900">
                {s.key} {s.label}
              </div>
              <p className="mt-1 text-xs text-gray-600">{s.scene}</p>
            </div>
          ))}
        </div>
      </PageShell>
    )
  }

  return (
    <PageShell {...PAGE_SHELL_PROPS}>
      {/* L1SI167-START-ROUTE-001：四路分流（页顶；六步区以下⛔动一字；start-map.yaml 不动） */}
      <section data-testid="start-routes" className="mb-6">
        <h3 className="mb-2 text-sm font-semibold text-gray-800">你来做甚么？</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <div data-testid="route-r1" className="rounded-lg border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900">我想把作品登记成资产</h4>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs text-gray-600">
              <li>先看什么能登记 → <Link className="text-emerald-700 underline" to="/ownership">所有权</Link></li>
              <li>填登记单 → <Link className="text-emerald-700 underline" to="/ownership-registry">权属登记</Link></li>
              <li>查我的登记 → <Link className="text-emerald-700 underline" to="/me">个人后台</Link></li>
            </ol>
            <Link data-testid="route-r1-btn" to="/ownership-registry"
              className="mt-3 inline-block rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700">去登记资产</Link>
          </div>
          <div data-testid="route-r2" className="rounded-lg border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900">我想让自己的智能体进这个网</h4>
            <p className="mt-2 rounded bg-amber-50 px-2 py-1 text-[11px] text-amber-800">
              通道当前为内部开通期，外部自助登记暂未开放；内部账号可经登录后登记。
            </p>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs text-gray-600">
              <li>看清两条路（原生／非原生）→ <Link className="text-emerald-700 underline" to="/agents">智能体集群</Link></li>
              <li>提交登记 → <Link className="text-emerald-700 underline" to="/channel/registry">自助登记</Link></li>
              <li>查我的登记 → <Link className="text-emerald-700 underline" to="/me">个人后台</Link></li>
            </ol>
            <Link data-testid="route-r2-btn" to="/channel/registry"
              className="mt-3 inline-block rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700">去登记智能体</Link>
          </div>
          <div data-testid="route-r3" className="rounded-lg border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900">我想用别人的东西</h4>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs text-gray-600">
              <li>看有什么 → <Link className="text-emerald-700 underline" to="/market">市场</Link></li>
              <li>看授权条件 → <Link className="text-emerald-700 underline" to="/authorization-registry">授权登记</Link></li>
              <li>申请授权 → <Link className="text-emerald-700 underline" to="/authorization-registry">同页办理</Link></li>
            </ol>
            <Link data-testid="route-r3-btn" to="/market"
              className="mt-3 inline-block rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700">去市场看看</Link>
          </div>
          <div data-testid="route-r4" className="rounded-lg border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900">我先随便看看</h4>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs text-gray-600">
              <li>这是干什么的 → <Link className="text-emerald-700 underline" to="/about">关于</Link></li>
              <li>有哪些规矩 → <Link className="text-emerald-700 underline" to="/rules">制度地图</Link></li>
              <li>六步全览 → 本页往下</li>
            </ol>
            <Link data-testid="route-r4-btn" to="/rules"
              className="mt-3 inline-block rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700">看看规章制度</Link>
          </div>
        </div>
      </section>

      {/* 顶部总述（§一-1） */}
      <p data-testid="overview" className="mb-4 text-sm text-gray-700">
        按六步了解 TDCA：从「这是什么组织」到「出了分歧怎么退」，每步列出该步制度件（只列在册现行件）；缺口步如实标「待补」，⛔ 不以草案充数。
      </p>

      {/* §一-1：六步卡片（名称＋一句话＋件数徽标；缺口步按钮角标「待补」——M-2 同标） */}
      <div data-testid="step-cards" className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {steps.map((s) => (
          <button
            key={s.key}
            type="button"
            data-testid={`step-card-${s.key}`}
            onClick={() => setSelectedStep(selectedStep === s.key ? null : s.key)}
            className={`relative rounded-lg border p-3 text-left ${
              selectedStep === s.key ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-200 bg-white'
            }`}
          >
            {s.gap && (
              <span data-testid={`step-gap-${s.key}`} className="absolute right-2 top-2 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-700">
                {s.gap_mark || '待补'}
              </span>
            )}
            <div className={`text-sm font-semibold ${selectedStep === s.key ? 'text-white' : 'text-gray-900'}`}>
              {s.key} {s.label}
            </div>
            <p className={`mt-1 text-xs ${selectedStep === s.key ? 'text-gray-200' : 'text-gray-600'}`}>{s.scene}</p>
            <span className={`mt-2 inline-block rounded px-1.5 py-0.5 text-[11px] ${selectedStep === s.key ? 'bg-gray-700 text-gray-100' : 'bg-gray-100 text-gray-600'}`}>
              {s.count} 件
            </span>
          </button>
        ))}
      </div>

      {/* §一-4：缺口步横幅（两处同标：横幅＋按钮角标）；相邻件口径＝本步前两步＋后一步（M-1） */}
      {selectedStep && stepByKey.get(selectedStep)?.gap && (
        <div data-testid="gap-banner" className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          <strong>{stepByKey.get(selectedStep)!.gap_mark || '待补'}</strong>：本步制度件尚在补足途中（⛔ 不以草案充数）。
          <span className="mt-1 block text-xs">
            相邻件（本步前两步 ＋ 后一步）挂接 {adjacentDocs.length} 件，见下表（含相邻步标签者）。
          </span>
        </div>
      )}

      {/* 步内制度件（§一-2/3：只列 page_visible；显示名／五态徽标／版本／state_note 原样＋术语跳转） */}
      {selectedStep ? (
        <section data-testid="step-docs" className="mb-6">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">
            {selectedStep} {stepByKey.get(selectedStep)?.label}（本步在列 {stepDocs.length} 件）
          </h3>
          {stepFoldDelta > 0 && (
            <p className="mb-2 text-xs text-gray-500">
              本步挂接 {stepByKey.get(selectedStep)!.count} 件，其中历史草案 {stepFoldDelta} 件不入本表（见 /rules 折叠区）。
            </p>
          )}
          {stepDocs.length === 0 && adjacentDocs.length === 0 ? (
            <p className="text-sm text-gray-500">本组合无件，换个条件试试。</p>
          ) : (
            <ul className="space-y-2">
              {stepDocs.map((d) => (
                <StartDocRow key={d.filename} item={d} terms={terms} />
              ))}
            </ul>
          )}
          {stepByKey.get(selectedStep)?.gap && adjacentDocs.length > 0 && (
            <ul className="mt-3 space-y-2" data-testid="adjacent-docs">
              {adjacentDocs.map((d) => (
                <StartDocRow key={`adj-${d.filename}`} item={d} terms={terms} />
              ))}
            </ul>
          )}
        </section>
      ) : (
        <p data-testid="step-hint" className="mb-6 text-sm text-gray-500">
          点选上方任一步，查看该步制度件。
        </p>
      )}

      {/* L1SI175-B2-002 引链（6186 放行令）：六步区以下不动，此处追加一句一链×2 */}
      <section data-testid="start-b2-links" className="mb-6 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 text-xs text-gray-600">
        <p>
          动手前先自问三件事：是不是你原创、用没用 AI、用在什么场景 →{' '}
          <Link data-testid="start-link-threeq" to="/start/three-questions" className="text-emerald-700 underline">先做三问</Link>
        </p>
        <p className="mt-1.5">
          想知道自己能到哪一阶、每阶要什么件 →{' '}
          <Link data-testid="start-link-contribute" to="/contribute" className="text-emerald-700 underline">我要贡献</Link>
        </p>
      </section>

      {/* 目录筛（§2.1 批3：类／态／步／关键词四维 AND 叠加·实时计数） */}
      <section data-testid="catalog" className="mb-6">
        <h3 className="mb-2 text-sm font-semibold text-gray-800">制度件目录筛（{docs.length} 件全表）</h3>
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-gray-500">类：</span>
          {CLASS_ORDER.map((c) => (
            <button
              key={c}
              type="button"
              data-testid={`catalog-chip-class-${c}`}
              onClick={() => setClsFilter(clsFilter === c ? null : c)}
              className={`rounded px-2 py-0.5 ${clsFilter === c ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700'}`}
            >
              {c} {classCounts[c]}
            </button>
          ))}
        </div>
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-gray-500">态：</span>
          {STATE_ORDER.map((s) => (
            <button
              key={s}
              type="button"
              data-testid={`catalog-chip-state-${s}`}
              onClick={() => setStateFilter(stateFilter === s ? null : s)}
              className={`rounded px-2 py-0.5 ${stateFilter === s ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700'}`}
            >
              {s} {stateCounts[s]}
            </button>
          ))}
        </div>
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-gray-500">步：</span>
          {steps.map((s) => (
            <button
              key={s.key}
              type="button"
              data-testid={`catalog-chip-step-${s.key}`}
              onClick={() => setStepFilter(stepFilter === s.key ? null : s.key)}
              className={`rounded px-2 py-0.5 ${stepFilter === s.key ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700'}`}
            >
              {s.key} {stepCounts[s.key]}
            </button>
          ))}
        </div>
        <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-gray-500">关键词：</span>
          <input
            type="text"
            data-testid="catalog-kw"
            value={kw}
            onChange={(e) => setKw(e.target.value)}
            placeholder="命中显示名／件名／类／态／步／slug，大小写不敏感"
            className="w-72 rounded border border-gray-300 px-2 py-1 text-xs"
          />
        </div>
        <p data-testid="catalog-count" className="mb-2 text-xs text-gray-600">
          {catalogLabel === '' ? '全部' : catalogLabel}：{catalog.length} 件
        </p>
        {catalog.length === 0 ? (
          <p data-testid="catalog-empty" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-500">
            本组合无件，换个条件试试。
          </p>
        ) : (
          <ul className="space-y-2">
            {catalog.map((d) => (
              <StartDocRow key={d.filename} item={d} terms={terms} archived={!d.page_visible} />
            ))}
          </ul>
        )}
      </section>

      {/* 术语检索（§2.2 批3：147 条·id／name／short_def；RTN 两义并列不合并；反向查只留接口位） */}
      <section data-testid="terms" className="mb-6">
        <h3 className="mb-2 text-sm font-semibold text-gray-800">术语检索（{terms.length} 条／{new Set(terms.map((t) => t.group)).size} 组）</h3>
        <input
          type="text"
          data-testid="term-kw"
          value={termKw}
          onChange={(e) => setTermKw(e.target.value)}
          placeholder="按 T-###／术语名／定义检索，同词多义并列显示"
          className="mb-3 w-72 rounded border border-gray-300 px-2 py-1 text-xs"
        />
        {termResults.length === 0 ? (
          <p className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-500">本组合无件，换个条件试试。</p>
        ) : (
          <ul className="space-y-2">
            {termResults.map((t) => (
              <li key={t.id} id={`term-${t.id}`} data-testid="term-card" className="rounded-lg border border-gray-200 bg-white px-3 py-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span data-testid="term-id" className="rounded bg-purple-50 px-1.5 py-0.5 text-[11px] font-medium text-purple-700">
                    {t.id}
                  </span>
                  <strong className="text-sm text-gray-900">{t.name}</strong>
                  <span className="text-[11px] text-gray-500">{t.group}</span>
                  {t.status !== '' && <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-600">{t.status}</span>}
                </div>
                <p className="mt-1 text-xs text-gray-600">
                  <Linkify text={firstSentence(t.short_def)} terms={terms} />
                </p>
                <p className="mt-1 text-[11px] text-gray-400">引用本术语的制度件：待接（反向查接口位·后续批接通）</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* §一-6：页尾数据源句 */}
      <p data-testid="source-note" className="text-xs text-gray-500">
        本页数据源：_START-MAP 三表（单一事实源）· 制度件以 /rules 为准 · 术语以术语登记表为准
      </p>
    </PageShell>
  )
}
