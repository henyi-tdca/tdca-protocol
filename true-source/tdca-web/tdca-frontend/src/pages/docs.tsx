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

/** 文档库只读面（/api/site/docs/*）：fail-closed——不可用即明示，不猜测不伪造 */
function useDoc<T>(path: string): { data: T | null; error: string } {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let alive = true
    setError('')
    fetch(`/api/site${path}`)
      .then((r) => {
        if (!r.ok) throw new Error(`API ${r.status}`)
        return r.json()
      })
      .then((d) => alive && setData(d as T))
      .catch((e) => alive && setError(String(e instanceof Error ? e.message : e)))
    return () => {
      alive = false
    }
  }, [path])
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
  const { data, error } = useDoc<{ items: { slug: string; title: string; synced_at: string }[] }>(`/docs/${family}`)
  return (
    <section data-testid="docs-index" className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-1 flex items-center gap-2">
        <h2 className="text-lg font-bold text-gray-900">{fam?.label ?? family}（{data?.items.length ?? '…'} 件）</h2>
        <SimulatedBadge nature="simulated" />
      </div>
      <Link to="/docs" className="text-sm text-gray-500 hover:text-gray-800">← 全部文档</Link>
      <div className="mt-4">
        {(!data || error) && <DocLoading error={error} />}
        {data && data.items.length === 0 && <p className="text-sm text-gray-500">该族暂无入库文档。</p>}
        {data && data.items.length > 0 && (
          <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
            {data.items.map((d) => (
              <li key={d.slug}>
                <Link to={`/docs/${family}/${d.slug}`} className="block px-4 py-3 hover:bg-gray-50">
                  <div className="font-medium text-gray-800">{d.title}</div>
                  <div className="text-xs text-gray-400">{d.slug} · {d.synced_at}</div>
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
        <SimulatedBadge nature="simulated" />
      </div>
      <p className="text-sm text-gray-600">
        制度 / 帮助二族内容已入库，点开即读。
      </p>
      <p className="mt-2 rounded-md border border-gray-200 bg-gray-50 px-4 py-2 text-xs text-gray-500">
        分工（LIB-DOCS-SCOPE-001）：文档库＝制度／条例／指引／章程／规则／办法／说明／示例／帮助；理论／白皮书／术语／知识图谱／思维协议／文献请走「知识库」（/library，路由不变）。
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
  const { data, error } = useDoc<{ title: string; body_md: string; source_path: string; synced_at: string }>(
    `/docs/${family}/${slug}`,
  )
  return (
    <section data-testid="doc-detail" className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <Link to={`/docs/${family}`} className="text-sm text-gray-500 hover:text-gray-800">← 返回列表</Link>
      <div className="mt-3">
        {(!data || error) && <DocLoading error={error} />}
        {data && (
          <>
            <h2 className="text-lg font-bold text-gray-900">{data.title}</h2>
            <article data-testid="doc-body" className="mt-4 whitespace-pre-wrap text-sm leading-6 text-gray-700">
              {data.body_md}
            </article>
            <footer className="mt-8 border-t border-gray-100 pt-3 text-xs text-gray-400">
              源路径：{data.source_path} · 入库：{data.synced_at}
            </footer>
          </>
        )}
      </div>
    </section>
  )
}
