// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 批3 A块 — /search 全站检索页（两态）
// 约束矩阵: L1SI177 SITE-FIND-CODE-001 §一.A（本地检索·两态：有结果／空结果＋三族入口；
//          每条带族／版本／数据性质／摘要一行；命中词高亮；编号形态与价格零命中）
// SPDX-License-Identifier: TDCA-Internal
// =============================================================================
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router'
import { PageShell } from './PageShell'
import {
  loadSearchIndex,
  searchEntries,
  splitForHighlight,
  NATURE_BADGE,
  NATURE_LABEL,
  type SearchIndexDoc,
} from '@/shared/search-index'

const TAG = 'inline-block rounded border border-gray-200 px-1.5 py-px text-[11px] text-gray-500'

function Highlight({ text, q }: { text: string; q: string }) {
  const parts = splitForHighlight(text, q)
  return (
    <>
      {parts.map((p, i) =>
        p.hit ? (
          <mark key={i} className="rounded-sm bg-yellow-200 px-0 text-inherit">
            {p.text}
          </mark>
        ) : (
          <span key={i}>{p.text}</span>
        ),
      )}
    </>
  )
}

/** 全站检索：静态索引（构建时生成）＋浏览器本地排序，无后端、无数据库 */
export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const q = (params.get('q') ?? '').trim()
  const [input, setInput] = useState(q)
  const [doc, setDoc] = useState<SearchIndexDoc | null>(null)
  const [indexStatus, setIndexStatus] = useState<'loading' | 'ok' | 'fail'>('loading')

  useEffect(() => {
    setInput(q)
  }, [q])

  useEffect(() => {
    let cancelled = false
    loadSearchIndex().then((d) => {
      if (cancelled) return
      setDoc(d)
      setIndexStatus(d ? 'ok' : 'fail')
    })
    return () => {
      cancelled = true
    }
  }, [])

  const results = useMemo(() => (doc && q ? searchEntries(doc.entries, q) : []), [doc, q])

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    const v = input.trim()
    setParams(v ? { q: v } : {})
  }

  return (
    <PageShell
      dataNature="real"
      title="全站检索"
      dataSource="静态索引 search-index.json（构建时生成）＋浏览器本地检索"
      permission="公开（匿名可用）"
      description="四族公开件＋术语＋栏目页的一框检索；排序 标题＞摘要＞正文，同权重制度族优先；结果带数据性质。"
    >
      <div className="space-y-3">
        {/* 搜索框：一行，窄屏不折行（点样形态） */}
        <form data-testid="search-form" onSubmit={onSubmit} className="flex items-center gap-2">
          <input
            data-testid="search-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入关键词，如：确权、配置权、术语名…"
            aria-label="全站检索"
            className="h-9 min-w-0 flex-1 rounded-lg border border-gray-200 px-3 text-sm outline-none focus:border-blue-400"
          />
          <button
            data-testid="search-submit"
            type="submit"
            className="h-9 shrink-0 rounded-lg bg-blue-700 px-4 text-sm text-white hover:bg-blue-800"
          >
            搜索
          </button>
        </form>

        {indexStatus === 'loading' && <p className="text-sm text-gray-400">索引装载中…</p>}
        {indexStatus === 'fail' && (
          <p data-testid="search-fail-closed" className="rounded bg-red-50 p-3 text-sm text-red-600">
            [fail-closed] 检索索引暂不可用，拒绝臆造结果，请稍后重试。
          </p>
        )}

        {indexStatus === 'ok' && !q && (
          <p data-testid="search-hint" className="text-sm text-gray-500">
            索引 {doc?.total} 条：制度 {doc?.counts['制度']} · 白皮书 {doc?.counts['白皮书']} · 论文{' '}
            {doc?.counts['论文']} · 素材 {doc?.counts['素材']} · 术语 {doc?.counts['术语']} · 栏目{' '}
            {doc?.counts['栏目']}。输入关键词开始检索。
          </p>
        )}

        {indexStatus === 'ok' && q && results.length > 0 && (
          <section data-testid="search-results" aria-label="检索结果">
            <p className="mb-1 text-xs text-gray-400">
              「{q}」命中 {results.length} 条（排序：标题＞摘要＞正文；同权重制度族优先）
            </p>
            {results.map((r) => (
              <div
                key={`${r.entry.family}:${r.entry.url}:${r.entry.title}`}
                data-testid="search-result"
                className="border-b border-dashed border-gray-200 py-2.5 last:border-b-0"
              >
                <div className="truncate text-sm font-semibold text-gray-900">
                  <Link to={r.entry.url} className="hover:underline">
                    <Highlight text={r.entry.title} q={q} />
                  </Link>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-1.5">
                  <span className={TAG}>{r.entry.family}</span>
                  <span className={TAG}>{r.entry.version || '在册'}</span>
                  <span className={`inline-block rounded px-1.5 py-px text-[11px] ${NATURE_BADGE[r.entry.nature] ?? 'bg-gray-400 text-white'}`}>
                    {NATURE_LABEL[r.entry.nature] ?? r.entry.nature}
                  </span>
                </div>
                <p className="mt-1 truncate text-xs text-gray-500">
                  摘要：<Highlight text={r.entry.summary} q={q} />
                </p>
              </div>
            ))}
          </section>
        )}

        {indexStatus === 'ok' && q && results.length === 0 && (
          <div data-testid="search-empty" className="py-6 text-center">
            <p className="text-sm text-gray-600">没找到「{q}」相关结果——换个说法，或按族浏览。</p>
            <div className="mt-4 flex flex-wrap justify-center gap-3">
              <Link to="/docs/regulation" className="rounded-md border border-blue-700 px-4 py-1.5 text-sm text-blue-700 hover:bg-blue-50">
                制度
              </Link>
              <Link to="/docs/papers" className="rounded-md border border-blue-700 px-4 py-1.5 text-sm text-blue-700 hover:bg-blue-50">
                论文
              </Link>
              <Link to="/docs/cop-library" className="rounded-md border border-blue-700 px-4 py-1.5 text-sm text-blue-700 hover:bg-blue-50">
                素材
              </Link>
            </div>
          </div>
        )}
      </div>
    </PageShell>
  )
}
