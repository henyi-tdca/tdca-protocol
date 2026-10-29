// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块二 — 文档库（/docs 三路·与文库并存·裁点2终定）
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §一裁点2（并存⛔不并线：/api/site/docs ⟷ /api/v1/library 端点不同、族不同）
//          ＋在册分工（LIB-DOCS-SCOPE-001）：文档库＝怎么做（制度/条例/指引/帮助）；知识库＝是什么（理论/白皮书/术语）
// 来源: tdca-site 正版 Docs.tsx —— siteApi 直读只读面；正文 Markdown 按纯文本呈现（新基座无 react-markdown 依赖，不加依赖）
// =============================================================================
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

export const DOC_FAMILIES: { key: string; label: string; desc: string }[] = [
  { key: 'regulation', label: '制度', desc: '制度／条例／规则／办法／章程／指引' },
  { key: 'help', label: '帮助', desc: '说明／示例／帮助' },
]

/** 公开只读面封套（public_docs_ops · PR197）：列表 documents[]／详情 content */
export interface PublicDocMeta {
  family: string
  slug: string
  filename: string
  version: string
  bytes: number
  sha256: string
  sha256_16: string
}
export interface PublicDocList {
  family: string
  count: number
  documents: PublicDocMeta[]
}
export interface PublicDocDetail extends PublicDocMeta {
  content: string
}
/** 标题＝文件名去扩展名（⛔ 不猜测不伪造：新面无独立 title 字段） */
export function docTitle(filename: string): string {
  return filename.replace(/\.(md|yaml|yml)$/, '')
}
/** 族内无件（404）如实视为空清单，⛔ 不当作故障 */
export const EMPTY_DOC_LIST: PublicDocList = { family: '', count: 0, documents: [] }

/** 文档库只读面（/api/site/docs/*）：fail-closed——不可用即明示，不猜测不伪造 */
function useDoc<T>(path: string, emptyOn404 = false): { data: T | null; error: string } {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let alive = true
    setError('')
    fetch(`/api/site${path}`)
      .then((r) => {
        if (!r.ok) {
          if (emptyOn404 && r.status === 404) return EMPTY_DOC_LIST as T
          throw new Error(`API ${r.status}`)
        }
        return r.json()
      })
      .then((d) => alive && setData(d as T))
      .catch((e) => alive && setError(String(e instanceof Error ? e.message : e)))
    return () => {
      alive = false
    }
  }, [path, emptyOn404])
  return { data, error }
}

function DocLoading({ error }: { error: string }) {
  if (error)
    return (
      <p data-testid="docs-fail-closed" className="rounded bg-red-50 p-3 text-sm text-red-600">
        [fail-closed] 文档库不可用：{error}
      </p>
    )
  return <p className="text-sm text-gray-400">加载中…</p>
}

/** 族列表（/docs/:family） */
export function DocsIndexPage() {
  const { family } = useParams()
  const fam = DOC_FAMILIES.find((f) => f.key === family)
  const { data, error } = useDoc<PublicDocList>(`/docs/${family}`, true)
  // 每页独立标题（SITE-SEO-A-001 乙-1）
  useEffect(() => {
    document.title = `${fam?.label ?? family} · 文档库 · TDCA`
  }, [fam, family])
  const docs = data?.documents ?? []
  return (
    <section data-testid="docs-index" className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-1 flex items-center gap-2">
        <h2 className="text-lg font-bold text-gray-900">{fam?.label ?? family}（{data ? docs.length : '…'} 件）</h2>
        <SimulatedBadge nature="real" />
      </div>
      <Link to="/docs" className="text-sm text-gray-500 hover:text-gray-800">← 全部文档</Link>
      <div className="mt-4">
        {(!data || error) && <DocLoading error={error} />}
        {data && docs.length === 0 && <p className="text-sm text-gray-500">该族暂无入库文档。</p>}
        {data && docs.length > 0 && (
          <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
            {docs.map((d) => (
              <li key={d.slug}>
                <Link to={`/docs/${family}/${d.slug}`} className="block px-4 py-3 hover:bg-gray-50">
                  <div className="font-medium text-gray-800">{docTitle(d.filename)}</div>
                  <div className="text-xs text-gray-400">{d.version} · {d.sha256_16}</div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}

/** 文档库首页（/docs） */
export function DocsHomePage() {
  return (
    <section data-testid="docs-home" className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-1 flex items-center gap-2">
        <h2 className="text-lg font-bold text-gray-900">文档库</h2>
        <SimulatedBadge nature="real" />
      </div>
      <p className="text-sm text-gray-600">
        制度 / 帮助二族内容已入库，点开即读。
      </p>
      <div className="mt-3 rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600">
        <strong>怎么用</strong>
        <p className="mt-1">
          ① 先在下方各族中点开要找的那一类；② 族内按标题浏览，点开即读全文；③ 读完可用浏览器返回，回到族内继续看；④ 需要全站检索，用页顶搜索。
        </p>
      </div>
      <p className="mt-2 rounded-md border border-gray-200 bg-gray-50 px-4 py-2 text-xs text-gray-500">
        分工（在册口径）：文档库＝制度／条例／指引／章程／规则／办法／说明／示例／帮助；理论／白皮书／术语／知识图谱／思维协议／文献请走「知识库」（/library，路由不变）。
      </p>
      <div className="mt-4 rounded-md border border-gray-200 px-4 py-3 text-sm text-gray-600">
        <strong className="text-gray-900">五族说明</strong>
        <ul className="mt-1 space-y-1">
          <li><strong>白皮书</strong>：制度与技术的总体主张与论证。</li>
          <li><strong>论文</strong>：专题论文与研究稿。</li>
          <li><strong>制度规范</strong>：生效中的条例、办法、协议与登记规则。</li>
          <li><strong>素材库</strong>：思维协议与工程素材的公开集。</li>
          <li><strong>周刊</strong>：按周发布的动态与观察。</li>
        </ul>
      </div>
      <p className="mt-3 rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600">
        <strong>想了解「是什么」</strong>（概念、理论与术语），请到「知识库」；<strong>想查「怎么做」</strong>（制度、办法与操作规则），留在本页。
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {DOC_FAMILIES.map((f) => (
          <Link key={f.key} to={`/docs/${f.key}`} className="rounded-lg border border-gray-200 p-5 hover:bg-gray-50">
            <div className="font-bold text-gray-900">{f.label}</div>
            <div className="mt-1 text-sm text-gray-500">{f.desc}</div>
            <div className="mt-3 text-xs text-gray-400">进入 →</div>
          </Link>
        ))}
      </div>
    </section>
  )
}

/** 文档详情（/docs/:family/:slug）——正文按纯文本呈现（Markdown 源不转样式，⛔ 不加依赖） */
export function DocDetailPage() {
  const { family, slug } = useParams()
  const { data, error } = useDoc<PublicDocDetail>(`/docs/${family}/${slug}`)
  // 每页独立标题（SITE-SEO-A-001 乙-1）：件载入后用品名，未载入先以地址件名占位
  useEffect(() => {
    document.title = `${data ? docTitle(data.filename) : docTitle(slug ?? '')} · 文档库 · TDCA`
  }, [data, slug])
  return (
    <section data-testid="doc-detail" className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <nav aria-label="面包屑" className="text-sm text-gray-500">
        {/* BREADCRUMB-002：移动端折叠为单条返回链（回族列表），桌面两级 文档库 › 件名 */}
        <Link to={`/docs/${family}`} className="inline-flex items-center gap-1 hover:text-gray-800 md:hidden">← 返回文档库</Link>
        <span className="hidden md:inline">
          <Link to={`/docs/${family}`} className="hover:text-gray-800">文档库</Link>
          {data && <> › {docTitle(data.filename)}</>}
        </span>
      </nav>
      <div className="mt-3">
        {(!data || error) && <DocLoading error={error} />}
        {data && (
          <>
            <h2 className="text-lg font-bold text-gray-900">{docTitle(data.filename)}</h2>
            <article data-testid="doc-body" className="mt-4 whitespace-pre-wrap text-sm leading-6 text-gray-700">
              {data.content}
            </article>
            <footer className="mt-8 border-t border-gray-100 pt-3 text-xs text-gray-400">
              {data.version} · sha256_16 {data.sha256_16} · 族 {data.family}
            </footer>
          </>
        )}
      </div>
    </section>
  )
}
