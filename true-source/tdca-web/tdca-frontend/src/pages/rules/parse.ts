// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI162-RULES-MAP-001 · /rules 制度地图机读表解析器
// 约束矩阵: 交办令 §一（唯一数据源＝随件机读表 V6.1·0C0FE95560264A8E，⛔ 不另写一套）
//          ＋ §三-2（⛔ 改 display_name／版本字样——本解析器纯机械映射，零改写）
// 范围: 仅解析本表 items 区块之既定 schema（块式映射／标量序列／单引号标量含折行），
//       ⛔ 不是通用 YAML 解析器；换版重出时以 __tests__/rules-map.test.tsx 兜住
// =============================================================================

/** 机读表 items 项（字段照表，一字不改） */
export interface DocMapItem {
  filename: string
  class: string
  steps: string[]
  state: string
  version: string
  bytes: number
  sha256_16: string
  in_public: boolean
  in_repo: boolean
  slug: string
  state_basis: string
  display_name: string
  state_note: string
  step_note: string
  page_visible: boolean
  integrity_basis: string
}

const ITEM_KEYS: (keyof DocMapItem)[] = [
  'filename',
  'class',
  'steps',
  'state',
  'version',
  'bytes',
  'sha256_16',
  'in_public',
  'in_repo',
  'slug',
  'state_basis',
  'display_name',
  'state_note',
  'step_note',
  'page_visible',
  'integrity_basis',
]

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

const STEPS_KEY = 'steps'

/** 解析 items 区块（块式 list-of-map；键在缩进 2，steps 子序列同缩进带 - 前缀，
 *  长单引号标量折行（缩进 ≥4）按 YAML 折行规则以空格拼接） */
export function parseDocMapItems(raw: string): DocMapItem[] {
  const lines = raw.split(/\r?\n/)
  const start = lines.findIndex((l) => l === 'items:')
  if (start < 0) throw new Error('doc-map: items block not found')

  const block: string[] = []
  for (let i = start + 1; i < lines.length; i++) {
    const l = lines[i]
    if (l === '') continue
    if (!l.startsWith(' ') && !l.startsWith('-')) break // 下一个顶层键
    block.push(l)
  }

  const items: Record<string, string | number | boolean | string[]>[] = []
  let cur: Record<string, string | number | boolean | string[]> | null = null
  let lastKey: string | null = null
  let collectingSteps = false

  for (let i = 0; i < block.length; i++) {
    const l = block[i]
    if (l.startsWith('- ')) {
      // 新一项（列 0）
      cur = {}
      items.push(cur)
      collectingSteps = false
      const idx = l.indexOf(': ')
      const key = l.slice(2, idx)
      let val = l.slice(idx + 2)
      // 折行（缩进 ≥4）：单引号与纯量统一按 YAML 折行规则空格拼接
      while (i + 1 < block.length && /^ {4,}/.test(block[i + 1])) {
        val = val + ' ' + block[i + 1].trim()
        i++
      }
      cur[key] = scalar(val)
      lastKey = key
      continue
    }
    const m = l.match(/^  ([a-z_0-9]+):(?: (.*))?$/)
    if (m) {
      const key = m[1]
      if (key === STEPS_KEY) {
        cur![STEPS_KEY] = []
        collectingSteps = true
        lastKey = key
        continue
      }
      collectingSteps = false
      let val = m[2] ?? ''
      while (i + 1 < block.length && /^ {4,}/.test(block[i + 1])) {
        val = val + ' ' + block[i + 1].trim()
        i++
      }
      cur![key] = scalar(val)
      lastKey = key
      continue
    }
    if (collectingSteps && /^  - /.test(l)) {
      ;(cur![STEPS_KEY] as string[]).push(scalar(l.slice(4)) as string)
      continue
    }
    // 折行兜底（理论上前两个分支已接住；此处防未料形态，报错停在前面）
    throw new Error(`doc-map: unparseable line: ${l.slice(0, 60)}`)
  }

  return items.map((raw2) => {
    const it = raw2 as unknown as DocMapItem
    for (const k of ITEM_KEYS) {
      if (!(k in raw2)) {
        // 稀疏字段（step_note 等）缺省补空串／空序列
        ;(it as unknown as Record<string, unknown>)[k] = k === STEPS_KEY ? [] : ''
      }
    }
    return it
  })
}

export const DOC_MAP_STATE_ORDER = ['生效', '指引性', '草案', '对外候选', '非制度件', '待辨'] as const
export const DOC_MAP_CLASS_ORDER = ['基本制度', '条例', '规范与细则', '标准与流程', '模板与表单'] as const
export const DOC_MAP_STEP_LABELS: Record<string, string> = {
  S1: '了解 TDCA',
  S2: '读懂基本制度',
  S3: '看资产与授权',
  S4: '参与协作',
  S5: '结算与计税',
  S6: '争议与退出',
}
