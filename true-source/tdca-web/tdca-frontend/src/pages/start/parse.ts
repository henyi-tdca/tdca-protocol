// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI163-START-001 · /start 新手指引机读表解析器
// 约束矩阵: 设计件 TDCA-DESIGN-L1SI163-001 §三（唯一数据源＝随件 _START-MAP-20261021-V1·0CE5C89A957B6B60，⛔ 不另写一套）
//          ＋ §三-4（⛔ 改 display_name／术语名——本解析器纯机械映射，零改写）
// 范围: 仅解析本件 steps／docs／terms 三区块之既定 schema（块式映射／标量序列／单引号标量含折行），
//       ⛔ 不是通用 YAML 解析器；换版重出时以 __tests__/start-map.test.tsx 兜住
// =============================================================================

/** steps 项（字段照表，一字不改） */
export interface StartStep {
  key: string
  label: string
  scene: string
  count: number
  gap: boolean
  gap_mark: string
  gap_note: string
  adjacent_steps: string[]
}

/** docs 项（字段照表，一字不改） */
export interface StartDoc {
  filename: string
  display_name: string
  class: string
  state: string
  version: string
  steps: string[]
  page_visible: boolean
  slug: string
  state_note: string
  step_note: string
  keys: string[]
}

/** terms 项（字段照表，一字不改） */
export interface StartTerm {
  id: string
  name: string
  group: string
  short_def: string
  status: string
  keys: string[]
}

export interface StartMapData {
  steps: StartStep[]
  docs: StartDoc[]
  terms: StartTerm[]
}

const STEP_KEYS: (keyof StartStep)[] = ['key', 'label', 'scene', 'count', 'gap', 'gap_mark', 'gap_note', 'adjacent_steps']
const DOC_KEYS: (keyof StartDoc)[] = [
  'filename',
  'display_name',
  'class',
  'state',
  'version',
  'steps',
  'page_visible',
  'slug',
  'state_note',
  'step_note',
  'keys',
]
const TERM_KEYS: (keyof StartTerm)[] = ['id', 'name', 'group', 'short_def', 'status', 'keys']

/** 标量求值：''→空串；'…'→去引号（''→'）；纯数字→int；true/false→bool；其余原样 */
function scalar(v: string): string | number | boolean {
  if (v === "''") return ''
  if (v.startsWith("'")) {
    return v.slice(1, -1).replace(/''/g, "'")
  }
  if (/^-?\d+$/.test(v)) return Number(v)
  if (v === 'true') return true
  if (v === 'false') return false
  return v
}

/** 三区块共通的子序列键（steps／adjacent_steps／keys：缩进 2 带 - 前缀） */
const SUBLIST_KEYS = new Set(['steps', 'adjacent_steps', 'keys'])

type RawItem = Record<string, string | number | boolean | string[]>

/**
 * 解析一个顶层 list-of-map 区块（键在缩进 2，子序列同缩进带 - 前缀，
 * 长单引号标量折行（缩进 ≥4）按 YAML 折行规则以空格拼接）。
 * 区块结束＝首个非缩进且非 - 前缀的行（下一个顶层键）。
 */
function parseListSection(raw: string, marker: string): RawItem[] {
  const lines = raw.split(/\r?\n/)
  const start = lines.findIndex((l) => l === `${marker}:`)
  if (start < 0) throw new Error(`start-map: section ${marker} not found`)

  const block: string[] = []
  for (let i = start + 1; i < lines.length; i++) {
    const l = lines[i]
    if (l === '') continue
    if (!l.startsWith(' ') && !l.startsWith('-')) break // 下一个顶层键
    block.push(l)
  }

  const items: RawItem[] = []
  let cur: RawItem | null = null
  let collecting: string | null = null

  for (let i = 0; i < block.length; i++) {
    const l = block[i]
    if (l.startsWith('- ')) {
      // 新一项（列 0）
      cur = {}
      items.push(cur)
      collecting = null
      const idx = l.indexOf(': ')
      if (idx < 0) throw new Error(`start-map: unparseable item line: ${l.slice(0, 60)}`)
      const key = l.slice(2, idx)
      let val = l.slice(idx + 2)
      // 折行（缩进 ≥4）：单引号与纯量统一按 YAML 折行规则空格拼接
      while (i + 1 < block.length && /^ {4,}/.test(block[i + 1])) {
        val = val + ' ' + block[i + 1].trim()
        i++
      }
      cur[key] = scalar(val)
      continue
    }
    const m = l.match(/^  ([a-z_0-9]+):(?: (.*))?$/)
    if (m) {
      const key = m[1]
      if (SUBLIST_KEYS.has(key)) {
        cur![key] = []
        collecting = key
        continue
      }
      collecting = null
      let val = m[2] ?? ''
      while (i + 1 < block.length && /^ {4,}/.test(block[i + 1])) {
        val = val + ' ' + block[i + 1].trim()
        i++
      }
      cur![key] = scalar(val)
      continue
    }
    if (collecting && /^  - /.test(l)) {
      ;(cur![collecting] as string[]).push(scalar(l.slice(4)) as string)
      continue
    }
    // 折行兜底（理论上前两个分支已接住；此处防未料形态，报错停在前面）
    throw new Error(`start-map: unparseable line: ${l.slice(0, 60)}`)
  }

  if (items.length === 0) throw new Error(`start-map: section ${marker} empty`)
  return items
}

function fillDefaults(items: RawItem[], keys: string[]): RawItem[] {
  return items.map((it) => {
    for (const k of keys) {
      if (!(k in it)) {
        it[k] = SUBLIST_KEYS.has(k) ? [] : ''
      }
    }
    return it
  })
}

/** 解析 _START-MAP 三表（机械映射，零改写） */
export function parseStartMap(raw: string): StartMapData {
  const steps = fillDefaults(parseListSection(raw, 'steps'), STEP_KEYS) as unknown as StartStep[]
  const docs = fillDefaults(parseListSection(raw, 'docs'), DOC_KEYS) as unknown as StartDoc[]
  const terms = fillDefaults(parseListSection(raw, 'terms'), TERM_KEYS) as unknown as StartTerm[]
  if (steps.length !== 6) throw new Error(`start-map: steps ${steps.length} != 6`)
  return { steps, docs, terms }
}
