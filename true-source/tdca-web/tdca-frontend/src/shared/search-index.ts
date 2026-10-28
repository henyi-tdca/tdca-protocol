// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 批3 A块 — 全站检索静态索引装载与本地排序
// 约束矩阵: L1SI177 SITE-FIND-CODE-001 §一.A（构建时静态索引；前端本地检索，无后端无库；
//          排序 标题＞摘要＞正文；同权重制度族优先；命中词高亮）
// SPDX-License-Identifier: TDCA-Internal
// =============================================================================

export interface SearchIndexEntry {
  title: string
  /** 制度·白皮书·论文·素材·术语·栏目（施工令 §一.A.1） */
  family: string
  /** 一行摘要 */
  summary: string
  keywords: string[]
  /** 站内路由（文档件 /docs/{family}/{slug}；术语 /terms；栏目页本站路径） */
  url: string
  /** 有则填（无则空串） */
  version: string
  /** real·simulated·synthetic */
  nature: string
  /** 正文纯文本摘录（截断，仅供命中排序，不在界面展开） */
  body: string
}

export interface SearchIndexDoc {
  spec: string
  generated_at: string
  generated_by: string
  sources: Record<string, string>
  counts: Record<string, number>
  total: number
  entries: SearchIndexEntry[]
}

export const NATURE_LABEL: Record<string, string> = { real: '真实', simulated: '模拟', synthetic: '合成' }
export const NATURE_BADGE: Record<string, string> = {
  real: 'bg-emerald-600 text-white',
  simulated: 'bg-amber-600 text-white',
  synthetic: 'bg-slate-500 text-white',
}

/** 族排序权重：同权重制度族优先 */
const FAMILY_PRIORITY: Record<string, number> = { 制度: 0, 白皮书: 1, 论文: 2, 素材: 3, 术语: 4, 栏目: 5 }

const TIER_TITLE = 3
const TIER_SUMMARY = 2
const TIER_BODY = 1

let cache: Promise<SearchIndexDoc | null> | null = null

/** 旁挂索引（public/search-index.json）一次性装载；失败即 null（fail-closed，不臆造） */
export function loadSearchIndex(): Promise<SearchIndexDoc | null> {
  if (!cache) {
    const base = (import.meta as { env?: { BASE_URL?: string } }).env?.BASE_URL ?? '/'
    cache =
      typeof fetch === 'function'
        ? fetch(`${base}search-index.json`)
            .then((r) => (r.ok ? (r.json() as Promise<SearchIndexDoc>) : null))
            .catch(() => null)
        : Promise.resolve(null)
  }
  return cache
}

/** 测试用：清缓存 */
export function __resetSearchIndexCacheForTest(): void {
  cache = null
}

export interface RankedEntry {
  entry: SearchIndexEntry
  tier: number
}

/**
 * 本地检索：空白分词为术语组，AND 语义；档位取各术语命中最高档（标题＞摘要＞正文）；
 * keywords 视同摘要档；排序 档位降序 → 族优先（制度在前） → 标题升序。
 */
export function searchEntries(entries: SearchIndexEntry[], query: string, limit = 50): RankedEntry[] {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean)
  if (terms.length === 0) return []
  const out: RankedEntry[] = []
  for (const e of entries) {
    const title = e.title.toLowerCase()
    const summary = e.summary.toLowerCase()
    const body = e.body.toLowerCase()
    const kw = e.keywords.join(' ').toLowerCase()
    let tier = 0
    let matched = true
    for (const t of terms) {
      const inTitle = title.includes(t)
      const inSummary = summary.includes(t) || kw.includes(t)
      const inBody = body.includes(t)
      if (!inTitle && !inSummary && !inBody) {
        matched = false
        break
      }
      tier = Math.max(tier, inTitle ? TIER_TITLE : inSummary ? TIER_SUMMARY : TIER_BODY)
    }
    if (matched) out.push({ entry: e, tier })
  }
  out.sort((a, b) => {
    if (b.tier !== a.tier) return b.tier - a.tier
    const fa = FAMILY_PRIORITY[a.entry.family] ?? 9
    const fb = FAMILY_PRIORITY[b.entry.family] ?? 9
    if (fa !== fb) return fa - fb
    return a.entry.title.localeCompare(b.entry.title, 'zh')
  })
  return out.slice(0, limit)
}

/** 高亮切分：按查询术语（长词优先）切出命中段，供 <mark> 渲染 */
export function splitForHighlight(text: string, query: string): { text: string; hit: boolean }[] {
  const terms = query
    .split(/\s+/)
    .filter(Boolean)
    .sort((x, y) => y.length - x.length)
  if (terms.length === 0) return [{ text, hit: false }]
  const esc = terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const re = new RegExp(`(${esc.join('|')})`, 'gi')
  const parts: { text: string; hit: boolean }[] = []
  let last = 0
  for (const m of text.matchAll(re)) {
    const i = m.index ?? 0
    if (i > last) parts.push({ text: text.slice(last, i), hit: false })
    parts.push({ text: m[0], hit: true })
    last = i + m[0].length
  }
  if (last < text.length) parts.push({ text: text.slice(last), hit: false })
  return parts.length > 0 ? parts : [{ text, hit: false }]
}
