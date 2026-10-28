// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 批3 A块 — 构建时生成全站检索静态索引 JSON
// 约束矩阵: L1SI177 SITE-FIND-CODE-001 批3动码施工令 §一.A
//   索引范围＝四族公开件（以 gateway/public_docs_ops.py 在册公开清单为唯一权威源）
//   ＋术语 151 条（docs/terms 机读快照）＋站点栏目页（pages.tsx PAGE_META 公开项）；
//   ⛔ 不索引内部件（签批记录／条例本体／草稿件／台账）——白名单外一律不入；
//   只读仓内公开件，⛔ 不写回、⛔ 不改原文；产物落 public/search-index.json（旁挂不进入包）。
// 追加约束: L1SI177 TAIL-CLEAN-001 块A —— body 摘录过同一禁则表；件名编号形态剥入 slug 化名，
//   url 留真名（S-1 防断链），前端跳转以真 url 映射回真名。
// SPDX-License-Identifier: TDCA-Internal
// =============================================================================
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..')
const GATEWAY = join(ROOT, 'true-source', 'tdca-web', 'gateway', 'public_docs_ops.py')
const DOCS = join(ROOT, 'docs')
const TERMS_YAML = join(ROOT, 'docs', 'terms', 'TDCA-TERMINOLOGY-REGISTRY-V1.0-EXPORT-20261027-151条机读快照.yaml')
const PAGES_TSX = join(ROOT, 'true-source', 'tdca-web', 'tdca-frontend', 'src', 'pages', 'pages.tsx')
const OUT = join(ROOT, 'true-source', 'tdca-web', 'tdca-frontend', 'public', 'search-index.json')

const FAMILY_DIRS = { regulation: 'regulations', whitepapers: 'whitepapers', papers: 'papers', 'cop-library': 'cop-library' }
const FAMILY_LABEL = { regulation: '制度', whitepapers: '白皮书', papers: '论文', 'cop-library': '素材' }
const FAMILY_ORDER = ['制度', '白皮书', '论文', '素材', '术语', '栏目']

// 编号形态禁则（施工令 §三.2；TAIL-CLEAN-001 块A：title/summary/body 共用本表，⛔ 不另写一套）
// /g：同字段多次命中全部剥除（验收＝逐条扫描零命中，⛔ 只剥首个漏残余）
const FORBIDDEN = [/\bCOP-\d+\b/gi, /\bGSEQ-\d+\b/g, /(^|[^A-Z0-9])A-\d+(?![0-9])/g, /\bT-\d{3}\b/g, /base_protocol/gi]
const stripForbidden = (s) => {
  let out = s
  for (const re of FORBIDDEN) out = out.replace(re, '')
  return out.replace(/-{2,}/g, '-').replace(/\s{2,}/g, ' ').trim()
}
// slug 化名（TAIL-CLEAN-001 块A#1）：件名编号形态剥除，与剥头共用同一规则表；
// url 保留真名不改（改则断链，停手 S-1），前端跳转用真 url 即映射回真名。
const slugFromEntry = (entry) =>
  stripForbidden(entry.split('/').pop().replace(/\.(md|yaml)$/, '')).replace(/^-+|-+$/g, '')
const isForbiddenToken = (t) => FORBIDDEN.some((re) => {
  re.lastIndex = 0 // /g 正则 test 带状态，逐次归位（⛔ 防交替漏判）
  return re.test(t)
})

const latinTokens = (s) => {
  const toks = s.match(/[A-Za-z][A-Za-z0-9-]{1,15}/g) ?? []
  const seen = new Set()
  return toks.filter((t) => {
    const k = t.toLowerCase()
    if (seen.has(k) || isForbiddenToken(t)) return false
    seen.add(k)
    return true
  }).slice(0, 8)
}

const decodeEntities = (s) => s.replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&quot;/g, '"').replace(/&amp;/g, '&')

// ---------------------------------------------------------------- 白名单读取
function readWhitelist() {
  const src = readFileSync(GATEWAY, 'utf8')
  const start = src.indexOf('_PUBLIC_DOCS = {')
  if (start < 0) throw new Error('public_docs_ops.py: _PUBLIC_DOCS 未找到')
  const out = {}
  let i = start
  for (const fam of Object.keys(FAMILY_DIRS)) {
    const key = `"${fam}": (`
    const k = src.indexOf(key, i)
    if (k < 0) throw new Error(`public_docs_ops.py: 族 ${fam} 未找到`)
    let depth = 1
    let j = k + key.length
    while (depth > 0 && j < src.length) {
      const c = src[j]
      if (c === '(') depth++
      else if (c === ')') depth--
      j++
    }
    const block = src
      .slice(k + key.length, j - 1)
      .split('\n')
      .filter((l) => !l.trimStart().startsWith('#'))
      .join('\n')
    const items = [...block.matchAll(/"([^"\n]+)"/g)].map((m) => m[1])
    if (items.length === 0) throw new Error(`public_docs_ops.py: 族 ${fam} 清单为空`)
    out[fam] = items
    i = j
  }
  return out
}

// ---------------------------------------------------------------- 件头解析（md）
function mdTitle(head) {
  for (const line of head.split('\n')) {
    const t = line.trim()
    if (t.startsWith('# ')) {
      return decodeEntities(
        t.slice(2)
          .replace(/\*\*/g, '').replace(/`/g, '')
          .replace(/（[^（）]*(?:V\d[^（）]*)）/g, (m) => (m.includes('V') ? '' : m))
          .trim(),
      )
    }
  }
  return ''
}

function mdVersion(name, head) {
  const inName = name.match(/V\d+\.\d+(?:\.\d+)?(?:-[A-Za-z-]+)?/)
  if (inName) return inName[0]
  const inHead = head.slice(0, 800).match(/V\d+\.\d+(?:\.\d+)?(?:-[A-Za-z-]+)?/)
  return inHead ? inHead[0] : ''
}

function mdSummary(text) {
  const lines = text.split('\n')
  let seenTitle = false
  for (const raw of lines) {
    const t = raw.trim()
    if (!seenTitle) {
      if (t.startsWith('# ')) seenTitle = true
      continue
    }
    if (t === '' || t === '---' || t.startsWith('#') || t.startsWith('>') || t.startsWith('![') || t.startsWith('|')) continue
    const plain = decodeEntities(
      t.replace(/!\[[^\]]*\]\([^)]*\)/g, '')
        .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
        .replace(/^\s*[-*]\s+/, '')
        .replace(/[*`>]/g, '')
        .trim(),
    )
    if (plain.length === 0) continue
    return plain.length > 90 ? `${plain.slice(0, 90)}…` : plain
  }
  return ''
}

function mdNature(head, famKey) {
  const m = head.slice(0, 1500).match(/data_nature\s*[:：]\s*([a-z]+)/i)
  if (m) return m[1].toLowerCase()
  // 在册制度/白皮书/论文默认真实；素材族 markdown（README/OPENING 等）标合成
  return famKey === 'cop-library' ? 'synthetic' : 'real'
}

function plainBody(text, limit) {
  const p = text
    .replace(/^---$/gm, ' ')
    .replace(/[#>*`|-]{1,}/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return p.length > limit ? p.slice(0, limit) : p
}

// ---------------------------------------------------------------- 件头解析（yaml·轻量）
function yamlScalar(block, key) {
  const m = block.match(new RegExp(`^\\s*${key}:\\s*(.+)$`, 'm'))
  return m ? m[1].trim().replace(/^'(.*)'$/, '$1').replace(/^"(.*)"$/, '$1') : ''
}

function yamlEntry(text, entry) {
  const base = entry.split('/').pop().replace(/-PUB\.yaml$/, '').replace(/\.yaml$/, '').replace(/\.md$/, '')
  const nature = (yamlScalar(text, 'data_nature') || (entry.endsWith('.md') ? '' : 'synthetic')).toLowerCase()
  let title = yamlScalar(text, 'display_name') || yamlScalar(text.slice(text.indexOf('soul:')), 'identity')
  if (!title || /[{}]/.test(title)) title = base
  let summary = yamlScalar(text.slice(text.indexOf('soul:')), 'core') || yamlScalar(text, 'source')
  if (!summary) summary = yamlScalar(text, 'branch') || base
  let version = (entry.match(/V\d+\.\d+(?:\.\d+)?(?:-[A-Za-z-]+)?/) ?? [''])[0]
  return { title: title.trim(), summary: summary.trim(), nature, version }
}

// ---------------------------------------------------------------- 术语快照解析（151 条）
function readTerms() {
  const src = readFileSync(TERMS_YAML, 'utf8')
  const exported = (src.match(/^exported_at:\s*(.+)$/m) ?? ['', ''])[1].trim()
  const entries = []
  let cur = null
  let inDef = false
  for (const raw of src.split('\n')) {
    if (raw.startsWith('- term: ')) {
      if (cur) entries.push(cur)
      cur = { term: raw.slice(8).trim(), def: '' }
      inDef = false
      continue
    }
    if (!cur) continue
    if (/^\s{2}def:\s*/.test(raw)) {
      cur.def = raw.replace(/^\s{2}def:\s*/, '').replace(/^'(.*)'$/, '$1').trim()
      inDef = true
      continue
    }
    if (inDef && /^\s{4,}\S/.test(raw)) {
      cur.def = `${cur.def} ${raw.trim()}`.replace(/\s+/g, ' ').trim()
      continue
    }
    inDef = false
  }
  if (cur) entries.push(cur)
  return { exported, entries }
}

// ---------------------------------------------------------------- 栏目页（PAGE_META 公开项）
function readColumns() {
  const src = readFileSync(PAGES_TSX, 'utf8')
  const out = []
  const re = /\{ path: '([^']+)', title: '((?:[^'\\]|\\.)*)', layer: '[^']*', dataSource: '[^']*', permission: '([^']*)', description: '((?:[^'\\]|\\.)*)' \},?/g
  for (const m of src.matchAll(re)) {
    const [, path, title, permission, description] = m
    if (path.includes(':')) continue
    if (!permission.includes('公开')) continue
    if (path === '/auth' || path === '/register') continue // 动作页非栏目
    out.push({ path, title: decodeEntities(title.replace(/\\'/g, "'")), description: decodeEntities(description.replace(/\\'/g, "'")) })
  }
  return out
}

// ---------------------------------------------------------------- 主流程
const whitelist = readWhitelist()
const { exported: termsExportedAt, entries: terms } = readTerms()
const columns = readColumns()

const entries = []
const missing = []
let forbiddenStripped = 0
const stripLog = []

for (const [famKey, items] of Object.entries(whitelist)) {
  const dir = FAMILY_DIRS[famKey]
  const label = FAMILY_LABEL[famKey]
  for (const entry of items) {
    const file = join(DOCS, dir, entry)
    if (!existsSync(file)) {
      missing.push(`${famKey}/${entry}`)
      continue
    }
    const text = readFileSync(file, 'utf8')
    let meta
    if (entry.endsWith('.yaml')) {
      meta = yamlEntry(text, entry)
    } else {
      meta = {
        title: mdTitle(text.slice(0, 4000)) || entry.split('/').pop().replace(/\.md$/, ''),
        summary: mdSummary(text),
        nature: mdNature(text, famKey),
        version: mdVersion(entry, text.slice(0, 4000)),
      }
    }
    const bodyRaw = plainBody(text, 1500)
    const before = `${meta.title}|${meta.summary}|${bodyRaw}`
    meta.title = stripForbidden(meta.title)
    meta.summary = stripForbidden(meta.summary)
    const bodyClean = stripForbidden(bodyRaw)
    if (before !== `${meta.title}|${meta.summary}|${bodyClean}`) {
      forbiddenStripped++
      stripLog.push(`${famKey}/${entry} :: ${before.slice(0, 90)}`)
    }
    entries.push({
      title: meta.title,
      family: label,
      summary: meta.summary,
      keywords: latinTokens(`${meta.title} ${entry.split('/').pop()}`),
      url: `/docs/${famKey}/${entry}`,
      slug: slugFromEntry(entry),
      version: meta.version,
      nature: meta.nature,
      body: bodyClean,
    })
  }
}

for (const t of terms) {
  const def = stripForbidden(t.def.replace(/〔内部编号〕/g, '（内部编号已脱敏）'))
  entries.push({
    title: stripForbidden(t.term),
    family: '术语',
    summary: def.length > 90 ? `${def.slice(0, 90)}…` : def,
    keywords: latinTokens(t.term),
    url: '/terms',
    version: '',
    nature: 'real',
    body: def.length > 300 ? def.slice(0, 300) : def,
  })
}

for (const c of columns) {
  const summary = c.description.length > 90 ? `${c.description.slice(0, 90)}…` : c.description
  entries.push({
    title: stripForbidden(c.title),
    family: '栏目',
    summary: stripForbidden(summary),
    keywords: latinTokens(c.title),
    url: c.path,
    version: '',
    nature: 'real',
    body: '',
  })
}

if (missing.length > 0) {
  console.error(`✗ 白名单件在磁盘缺失 ${missing.length} 件：\n  ${missing.join('\n  ')}`)
  process.exit(1)
}
if (terms.length !== 151) {
  console.error(`✗ 术语快照解析得 ${terms.length} 条，应为 151`)
  process.exit(1)
}

const counts = {}
for (const f of FAMILY_ORDER) counts[f] = entries.filter((e) => e.family === f).length

const doc = {
  spec: 'TDCA-SEARCH-INDEX-V1',
  generated_at: new Date().toISOString(),
  generated_by: 'scripts/build-search-index.mjs（构建时静态生成）',
  sources: {
    public_docs: 'gateway/public_docs_ops.py 在册公开清单（唯一权威源）',
    terms: `docs/terms 术语快照（151 条，exported_at ${termsExportedAt}）`,
    columns: 'src/pages/pages.tsx PAGE_META 公开栏目页',
  },
  counts,
  total: entries.length,
  entries,
}

writeFileSync(OUT, `${JSON.stringify(doc)}\n`, 'utf8')
console.log(`✓ public/search-index.json 生成：共 ${entries.total ?? entries.length} 条`)
for (const f of FAMILY_ORDER) console.log(`  ${f}: ${counts[f]}`)
console.log(`  栏目页来源: ${columns.length} 项公开 PAGE_META`)
if (forbiddenStripped > 0) console.log(`  ⚠ 编号形态剥除: ${forbiddenStripped} 处（title/summary 命中禁则已剥除）`)
for (const s of stripLog) console.log(`    ${s}`)
