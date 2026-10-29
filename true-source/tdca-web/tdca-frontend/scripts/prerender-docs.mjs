// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: SITE-SEO-A-001 乙-2 —— 文档库条目构建期预渲染
// 约束矩阵: 只对内容页（/docs/:family/:slug 三族：regulation/whitepapers/papers）生成
//   含正文静态 HTML；正文不经浏览器脚本即可直读；操作页一律不动维持 SPA；
//   内容一字不改（直读仓内只读件，现算 sha256 脚注与在册一致）；⛔ 不加依赖（Node 内置）
// 单源: 白名单＝gateway/public_docs_ops.py 在册公开清单（解析其字面量，非另行维护）；
//   正文＝仓内 docs/<族目录>/<件名>（与容器只读挂载同一份）
// =============================================================================
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const FRONTEND = path.resolve(HERE, '..')
const REPO_WEB = path.resolve(FRONTEND, '..')            // true-source/tdca-web
const GATEWAY_OPS = path.join(REPO_WEB, 'gateway', 'public_docs_ops.py')
const DOCS_ROOT = path.resolve(REPO_WEB, '..', '..', 'docs') // 仓根 docs/（regulations/whitepapers/papers）
const DIST = path.join(FRONTEND, 'dist')

/** 解析在册公开清单：只取三族字面量（⛔ 不执行 python、不另行维护清单） */
function parseWhitelist(pySource) {
  const fams = {}
  // 去注释（整行 # 与行尾 # 注释内的引号不得算件名）
  const noComments = pySource.split('\n').map((l) => {
    const i = l.indexOf('#')
    return i === -1 ? l : l.slice(0, i)
  }).join('\n')
  const re = /"(\w+)":\s*\(([\s\S]*?)\)/g
  let m
  while ((m = re.exec(noComments)) !== null) {
    const fam = m[1]
    if (!['regulation', 'whitepapers', 'papers'].includes(fam)) continue
    const names = [...m[2].matchAll(/"([^"]+)"/g)].map((x) => x[1])
    fams[fam] = names
  }
  return fams
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function main() {
  const fams = parseWhitelist(readFileSync(GATEWAY_OPS, 'utf-8'))
  const cssFile = readdirSync(path.join(DIST, 'assets')).find((f) => f.endsWith('.css'))
  const css = cssFile ? readFileSync(path.join(DIST, 'assets', cssFile), 'utf-8') : ''
  const FAMILY_DIRS = { regulation: 'regulations', whitepapers: 'whitepapers', papers: 'papers' }
  const FAMILY_LABEL = { regulation: '制度', whitepapers: '白皮书', papers: '论文' }

  let total = 0
  const missing = []
  const generated = []
  for (const [fam, names] of Object.entries(fams)) {
    const dir = path.join(DOCS_ROOT, FAMILY_DIRS[fam])
    for (const name of names) {
      const src = path.join(dir, name)
      if (!existsSync(src)) { missing.push(`${fam}/${name}`); continue }
      const raw = readFileSync(src)
      const sha256 = createHash('sha256').update(raw).digest('hex')
      const content = raw.toString('utf-8')
      const title = name.replace(/\.(md|yaml|yml)$/, '')
      // 静态内容页：面包屑＋件名＋正文（pre-wrap 纯文本，与 SPA 面同口径）＋版本/哈希脚注
      const html = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>${escapeHtml(title)} · 文档库 · TDCA</title>
<style>${css}</style>
</head>
<body class="bg-gray-50 font-sans">
<div class="mx-auto max-w-4xl px-4 py-8">
<nav class="text-sm text-gray-500" aria-label="面包屑">
<a href="/docs/${fam}" class="hover:text-gray-800">文档库 › ${FAMILY_LABEL[fam] ?? fam}</a>
</nav>
<section class="mt-3 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
<h1 class="text-lg font-bold text-gray-900">${escapeHtml(title)}</h1>
<article class="mt-4 whitespace-pre-wrap text-sm leading-6 text-gray-700">${escapeHtml(content)}</article>
<footer class="mt-8 border-t border-gray-100 pt-3 text-xs text-gray-400">
V1.0 在册 · sha256_16 ${sha256.slice(0, 16).toUpperCase()} · 族 ${fam} · 本页为构建期静态正文面（SPA 全功能面在 <a class="underline" href="/docs/${fam}">/docs/${fam}</a>）
</footer>
</section>
</div>
</body>
</html>
`
      const slugDir = path.join(DIST, 'docs', fam, title)
      mkdirSync(slugDir, { recursive: true })
      writeFileSync(path.join(slugDir, 'index.html'), html, 'utf-8')
      total += 1
      generated.push(`${fam}/${name}`)
    }
  }
  console.log(`[prerender-docs] 三族静态内容页 ${total} 件（regulation ${fams.regulation?.length ?? 0}／whitepapers ${fams.whitepapers?.length ?? 0}／papers ${fams.papers?.length ?? 0}）`)
  if (missing.length) {
    console.error('[prerender-docs] 源件缺失（未静默跳过计数）：', missing)
    process.exitCode = 1
  }
  writeFileSync(path.join(DIST, 'prerender-manifest.json'), JSON.stringify({
    generated_at: new Date().toISOString(),
    families: Object.fromEntries(Object.entries(fams).map(([k, v]) => [k, v.length])),
    total: total,
    missing: missing,
  }, null, 2), 'utf-8')
}

main()
