// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-SITE-001 | 目标函数: MIGRATE 批1 — /search 全站检索页（两态）
// 约束矩阵: L1SI206 MIGRATE-B1-001 §二.3（检索面接入：页面可达、关键词命中、
//          空结果有提示；两态：有结果／空结果＋三族入口；每条带族／版本／数据性质／
//          摘要一行；命中词高亮）＋ AMEND-1 移动通则（窄屏不折行、min-w-0、无固定宽）
// 并轨注记: 自旧版 src/pages/search.tsx 迁入——PageShell 改接新版组件
//           （title/dataSource/permission/description，⛔ 旧版 dataNature 属）；
//           视觉类名改书新版 tailwind 语义（border/bg-card/text-muted-foreground），
//           交互逻辑／data-testid／排序与高亮语义逐字保留。
// SPDX-License-Identifier: TDCA-Internal
// =============================================================================
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router'
import { PageShell } from '@/components/PageShell'
import {
  loadSearchIndex,
  searchEntries,
  splitForHighlight,
  NATURE_BADGE,
  NATURE_LABEL,
  type SearchIndexDoc,
} from '@/lib/search-index'

const TAG = 'inline-block rounded border bg-muted px-1.5 py-px text-[11px] text-muted-foreground'

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

  // G2-INGEST-001（L1SI213）：族筛选补两族（帮助／操作指引）。仅对 searchEntries 已排序结果
  // 做展示层过滤，⛔ 不触检索算法与排序逻辑（S-3）；选项与统计行同八族口径。
  const FAMILY_OPTIONS = ['帮助', '操作指引', '制度', '白皮书', '论文', '素材', '术语', '栏目'] as const
  const [familyFilter, setFamilyFilter] = useState<string>('全部')
  const filtered = useMemo(
    () => (familyFilter === '全部' ? results : results.filter((r) => r.entry.family === familyFilter)),
    [results, familyFilter],
  )

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    const v = input.trim()
    setParams(v ? { q: v } : {})
  }

  return (
    <PageShell
      title="全站检索"
      dataSource="静态索引 search-index.json（构建时生成）＋浏览器本地检索"
      permission="公开（匿名可用）"
      description="帮助／操作指引／制度／白皮书／论文／素材／术语／栏目页的一框检索；排序 标题＞摘要＞正文，同权重制度族优先；结果带数据性质。"
    >
      <div className="space-y-3">
        {/* 搜索框：一行，窄屏不折行（AMEND-1 移动通则：flex-nowrap／min-w-0 flex-1／按钮 shrink-0） */}
        <form data-testid="search-form" onSubmit={onSubmit} className="flex flex-nowrap items-center gap-2">
          <input
            data-testid="search-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入关键词，如：确权、配置权、术语名…"
            aria-label="全站检索"
            className="h-9 min-w-0 flex-1 rounded-lg border bg-background px-3 text-sm text-foreground outline-none focus:border-primary"
          />
          <button
            data-testid="search-submit"
            type="submit"
            className="h-9 shrink-0 rounded-lg bg-primary px-4 text-sm text-primary-foreground hover:opacity-90"
          >
            搜索
          </button>
        </form>

        {indexStatus === 'loading' && <p className="text-sm text-muted-foreground">索引装载中…</p>}
        {indexStatus === 'fail' && (
          <p data-testid="search-fail-closed" className="rounded bg-red-50 p-3 text-sm text-red-600">
            [fail-closed] 检索索引暂不可用，拒绝臆造结果，请稍后重试。
          </p>
        )}

        {indexStatus === 'ok' && !q && (
          <p data-testid="search-hint" className="text-sm text-muted-foreground">
            索引 {doc?.total} 条：帮助 {doc?.counts['帮助']} · 操作指引 {doc?.counts['操作指引']} · 制度{' '}
            {doc?.counts['制度']} · 白皮书 {doc?.counts['白皮书']} · 论文 {doc?.counts['论文']} · 素材{' '}
            {doc?.counts['素材']} · 术语 {doc?.counts['术语']} · 栏目 {doc?.counts['栏目']}
            （分族和＝
            {Object.values(doc?.counts ?? {}).reduce((a, b) => a + b, 0)}）。输入关键词开始检索。
          </p>
        )}

        {indexStatus === 'ok' && q && results.length > 0 && (
          <section data-testid="search-results" aria-label="检索结果">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-xs text-muted-foreground">族筛选：</span>
              {['全部', ...FAMILY_OPTIONS].map((f) => (
                <button
                  key={f}
                  type="button"
                  data-testid={`search-family-${f}`}
                  onClick={() => setFamilyFilter(f)}
                  className={`rounded border px-2 py-px text-[11px] ${
                    familyFilter === f
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border text-muted-foreground hover:bg-muted'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
            <p className="mb-1 mt-1 text-xs text-muted-foreground">
              「{q}」命中 {filtered.length} 条（排序：标题＞摘要＞正文；同权重制度族优先）
            </p>
            {filtered.map((r) => (
              <div
                key={`${r.entry.family}:${r.entry.url}:${r.entry.title}`}
                data-testid="search-result"
                className="border-b border-dashed py-2.5 last:border-b-0"
              >
                <div className="truncate text-sm font-semibold text-card-foreground">
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
                <p className="mt-1 truncate text-xs text-muted-foreground">
                  摘要：<Highlight text={r.entry.summary} q={q} />
                </p>
              </div>
            ))}
          </section>
        )}

        {indexStatus === 'ok' && q && results.length === 0 && (
          <div data-testid="search-empty" className="py-6 text-center">
            <p className="text-sm text-muted-foreground">没找到「{q}」相关结果——换个说法，或按族浏览。</p>
            <div className="mt-4 flex flex-wrap justify-center gap-3">
              <Link to="/docs/regulation" className="rounded-md border border-primary px-4 py-1.5 text-sm text-primary hover:bg-muted">
                制度
              </Link>
              <Link to="/docs/papers" className="rounded-md border border-primary px-4 py-1.5 text-sm text-primary hover:bg-muted">
                论文
              </Link>
              <Link to="/docs/cop-library" className="rounded-md border border-primary px-4 py-1.5 text-sm text-primary hover:bg-muted">
                素材
              </Link>
            </div>
          </div>
        )}
      </div>
    </PageShell>
  )
}
