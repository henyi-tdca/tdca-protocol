// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-002 | 目标函数: F0-3 构建期预渲染（SITE-SEC-001 §三 ②案）
// 令件: TDCA-HANDOFF-EXEC-L1SI211-SITE-SEC-001 §三 —— 方案②「构建期脚本为路由
//       生成独立 title/description/og」；智库核证单（-297）记「预渲染取 2 案」。
// 硬要求照守: 影响面=纯构建期，零路由重构（S-3 不触）；对账断言 sitemap 条数 ==
//       生成分数 == 覆盖表全数（fail-closed，不齐即构建失败）；回滚法=整包 dist 回滚。
// 机制: 从 dist/index.html 出发，为每条 sitemap 路由写 dist<route>/index.html，
//       仅替换 <title> 与 meta description/og —— 路由兼容零改动，nginx try_files
//       $uri $uri/ 天然优先命中本件（@spa 壳降为后备）。
// =============================================================================
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const siteRoot = join(dirname(fileURLToPath(import.meta.url)), '..')
const dist = join(siteRoot, 'dist')
const shellPath = join(dist, 'index.html')

// ── 一、sitemap 57 条（2026-11-12 线上实测 41 条核证口径照录＋PRERENDER-001 首扩 16 项）──
const SITEMAP_ROUTES = [
  '/', '/about', '/academy', '/academy/outline', '/announcements',
  '/attestation/history', '/audit', '/authorization-registry', '/authorization/panel',
  '/channel', '/contribute', '/curation', '/demo', '/disclosure', '/docs',
  '/docs/papers', '/docs/regulation', '/docs/whitepapers', '/five-orders', '/help',
  '/lab', '/library', '/market', '/nca-guide', '/negativespace', '/nodes',
  '/notifier', '/official-assets', '/ownership', '/private', '/process',
  '/public-face', '/registrations', '/rules', '/sandbox', '/search', '/start',
  '/start/three-questions', '/status', '/tax', '/verify',
  // PRERENDER-001（L1SI213，依 TDCA-RULING-L1SI213-SITE2-SELFHANDLE-001 §三甲档 16 项）：
  // 已有实质内容未预渲染之公域栏目纳入；S-3 已逐面核非空壳，零撤出
  '/channel/portal', '/channel/agents', '/channel/registry', '/channel/market',
  '/channel/tools', '/agents', '/agent-shelf', '/toolshelf', '/terms',
  '/attestation', '/attestation/meta', '/attestation/dynamic', '/anchors',
  '/ownership-registry', '/overview', '/cluster',
]

// ── 二、PAGE_META 真源直读（src/pages/PagesIndex.tsx，单一事实源，⛔手抄）──
const pmSrc = readFileSync(join(siteRoot, 'src/pages/PagesIndex.tsx'), 'utf-8')
const meta = new Map()
for (const m of pmSrc.matchAll(/\{ path: '([^']+)', title: '([^']+)'[\s\S]*?description: '([^']*)' \}/g)) {
  meta.set(m[1], { title: m[2], description: m[3] })
}

// ── 三、补充表：sitemap 有而 PAGE_META 未登记的 16 面（公开面，标题照各页 PageShell 实读）──
const SUPPLEMENT = {
  '/academy': { title: '知识学院', description: 'TDCA 知识学院：教材目录（纲要）与学习方法公开面。' },
  '/attestation/history': { title: '确权历史 · NCA 链跨代留痕', description: '确权历史公开留痕：时间／事件类型／公开状态，拒绝高亮照实标。' },
  '/audit': { title: '审计透明', description: '审计透明面：账本可公开核证，记录哈希可核对不可复算。' },
  '/authorization-registry': { title: '授权登记管理（P8b）', description: '授权登记管理面：授权关系登记与查询，谁的数据谁可见。' },
  '/authorization/panel': { title: '授权配置面板（C-1）', description: '授权配置面板：档位与边界由本人设定，默认最低档。' },
  '/docs/papers': { title: '论文族文档', description: '论文族站内索引：中英双版论文与实证材料入口。' },
  '/docs/regulation': { title: '条例族文档', description: '条例族站内索引：在册规则与判据件入口。' },
  '/docs/whitepapers': { title: '白皮书族文档', description: '白皮书族站内索引：公开白皮书入口。' },
  '/library': { title: '知识库（白皮书 · 论文 · 术语 · 知识图谱 · 素材库）', description: '知识库总入口：四族文档、术语检索、知识图谱与素材库。' },
  '/market': { title: '配置权市场（L2）', description: '配置权市场公开面：只读展示，不含任何交易入口。' },
  '/notifier': { title: '通知机状态页', description: '通知机状态公开面：只读状态展示。' },
  '/ownership': { title: '法定交易中心 · 提交入口', description: '所有权登记提交面：登记号公开可查，证据包可核。' },
  '/process': { title: '流程总览', description: '站点流程总览：六步硬序与各面关系一页看懂。' },
  '/registrations': { title: '登记查询 · 公开留痕', description: '登记查询公开面：列表／详情／证据包三件匿名只读。' },
  '/sandbox': { title: '沙盒准入（L2 前置反应釜）', description: '沙盒准入说明面：出盒前的一切验证都在沙盒完成。' },
  '/tax': { title: '税收仪表盘（L3 效用计量）', description: '税收仪表盘公开面：L3 效用计量只读展示。' },
  // PRERENDER-001 首扩 14 面（/terms／/overview 已见于 PAGE_META 真源，不重复登）；
  // 以下题述一律照各页 PageShell／组件实读（⛔ 手编臆造）
  '/channel/portal': { title: '门户', description: '了解 TDCA：公告、知识库与学院——信息公开与交互的入口。' },
  '/channel/agents': { title: '智能体', description: '智能体相遇、协作与作业：集群、工作室与工具面。' },
  '/channel/registry': { title: '登记与存证', description: '权属、授权与存证：登记合一与可核验台账。' },
  '/channel/market': { title: '市场与经济', description: '配置权市场与结算：谈判、计量与分配的规则面。' },
  '/channel/tools': { title: '工具与运维', description: '工具、通知与沙盒：试错与验证的公共操作面。' },
  '/agents': { title: '智能体集群观测', description: '五大智能体面板（Trainer/Executor/Auditor/Service/Genie）+ 确权状态灯 + 协作拓扑。' },
  '/agent-shelf': { title: '智能体区（组二 10 件呈现）', description: '组二 10 件以智能体形态呈现：每条只列名称／一句用途／形态。' },
  '/toolshelf': { title: '工具货架（P4）', description: '站内工具与模板目录：编译器、适配器等；配置类工具须凭授权件过准入闸门。' },
  '/attestation': { title: '确权中心总览', description: '待审队列 + 最近事件 + 确权统计（元函数/动态/历史入口）。' },
  '/attestation/meta': { title: '元函数初始确权（出盒终裁）', description: '沙盒验证后、进入配置权市场前的人类确权（先验证后背书，REV-002 修正）。' },
  '/attestation/dynamic': { title: '动态确权请求队列', description: '五类动态确权请求（场景扩展/认知演化/化合授权/负空间逼近/目标修正）紧急度排序。' },
  '/anchors': { title: '模拟外部锚与版权事件（P6）', description: '版权链（NCA 链）／结算（站内积分）／税务（金税四期功能）三锚全站内模拟；版权事件＝登记／变更／注销。' },
  '/ownership-registry': { title: '权属登记管理（P8a）', description: '登记二分之权属侧：凡具表达形式者皆可登记；须载生成来源谱系；场景非必须；法域四支仅索引不代法律判定。' },
  '/cluster': { title: '集群编排与准入闸门（P2）', description: '授权件登记与多层转授链；配置类调用须凭有效授权件过闸门——可信联通 ≠ 可信协作，仅握手不成立。' },
}
for (const [p, v] of Object.entries(SUPPLEMENT)) meta.set(p, v)

// ── 四、对账断言（fail-closed：不齐即构建失败，C-45 合并式落盘口径）──
const errors = []
for (const r of SITEMAP_ROUTES) if (!meta.has(r)) errors.push(`缺 meta：${r}`)
for (const p of meta.keys()) if (!SITEMAP_ROUTES.includes(p)) { /* PAGE_META 私域面（/me/* 等）不入 sitemap、不预渲染，登记即可 */ }
if (!existsSync(shellPath)) errors.push('dist/index.html 不存在（须在 vite build 之后运行）')
if (SITEMAP_ROUTES.length !== 57) errors.push(`sitemap 清单实数 ${SITEMAP_ROUTES.length} ≠ 57（核证口径变动须人工复核）`)
if (errors.length) { console.error('预渲染对账失败：\n' + errors.join('\n')); process.exit(1) }

// ── 五、生成：每条路由独立 title/description/og ──
const shell = readFileSync(shellPath, 'utf-8')
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const manifest = []
for (const route of SITEMAP_ROUTES) {
  const { title, description } = meta.get(route)
  const canonical = `https://tdca.com.cn${route}`
  let html = shell
  html = html.replace(/<title>[^<]*<\/title>/, `<title>${esc(title)}</title>`)
  const inject = [
    `<meta name="description" content="${esc(description)}" />`,
    `<link rel="canonical" href="${canonical}" />`,
    `<meta property="og:title" content="${esc(title)}" />`,
    `<meta property="og:description" content="${esc(description)}" />`,
    `<meta property="og:url" content="${canonical}" />`,
  ].join('\n    ')
  if (/<meta name="description"[^>]*>/.test(html)) {
    html = html.replace(/<meta name="description"[^>]*>/, inject)
  } else {
    html = html.replace(/<\/head>/, `    ${inject}\n  </head>`)
  }
  const out = route === '/' ? shellPath : join(dist, route, 'index.html')
  if (route !== '/') { mkdirSync(dirname(out), { recursive: true }); writeFileSync(out, html) }
  else writeFileSync(out, html) // 首页壳同替换，title 与首条一致
  manifest.push({ route, title, bytes: html.length })
}

writeFileSync(join(dist, 'prerender-routes-manifest.json'), JSON.stringify({ generated_at: new Date().toISOString(), count: manifest.length, routes: manifest }, null, 2))
const uniq = new Set(manifest.map((m) => m.title))
console.log(`预渲染完成：${manifest.length}/57 份；title 唯一 ${uniq.size}/57；manifest → dist/prerender-routes-manifest.json`)
if (uniq.size !== manifest.length) { console.error('title 出现重复，判对账失败'); process.exit(1) }
