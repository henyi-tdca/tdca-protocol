// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 内容区文库（/library 白皮书·论文·产物库）
// 约束矩阵: 站点入站令·甲/乙——只读面；以在册仓库为唯一权威源；A-22 /api/v1/library/*
// 复用: PageShell / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import { PageShell } from './PageShell'

interface FamilyView { family: string; name: string; count: number }
interface ItemView { slug: string; title: string; synced_at: string }
interface DetailView {
  family: string; slug: string; title: string; body_md: string
  source_path: string; synced_at: string; note?: string
}

const FAMILY_TABS: { key: string; label: string }[] = [
  { key: 'whitepaper', label: '白皮书' },
  { key: 'paper', label: '论文与实证' },
  { key: 'cop-library', label: '产物库' },
]

export function LibraryPage() {
  const [families, setFamilies] = useState<FamilyView[]>([])
  const [family, setFamily] = useState('whitepaper')
  const [items, setItems] = useState<ItemView[]>([])
  const [detail, setDetail] = useState<DetailView | null>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    void api.get<{ families: FamilyView[] }>('/api/v1/library/families').then((r) => {
      if (r.ok) setFamilies(r.data.families)
    })
  }, [])

  useEffect(() => {
    setDetail(null); setErr('')
    void api.get<{ items: ItemView[] }>(`/api/v1/library/${family}`).then((r) => {
      if (r.ok) setItems(r.data.items)
      else setErr(`文库加载失败：${r.reason}`)
    })
  }, [family])

  const onPick = (slug: string) => {
    void api.get<DetailView>(`/api/v1/library/${family}/${encodeURIComponent(slug)}`).then((r) => {
      if (r.ok) setDetail(r.data)
      else setErr(`正文加载失败：${r.reason}`)
    })
  }

  const famName = families.find((f) => f.family === family)?.name ?? family

  return (
    <PageShell
      title="内容区文库（白皮书 · 论文 · 产物库）"
      dataSource="A-22 GET /api/v1/library/*（docs 表只读面）"
      permission="登录 DID"
      description="站点入站令·甲/乙内容区：只读索引＋正文阅读；以在册仓库为唯一权威源，本站不复制不改写。">
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {FAMILY_TABS.map((t) => (
            <button
              key={t.key}
              data-testid={`lib-tab-${t.key}`}
              data-active={family === t.key}
              className={`rounded-md border px-3 py-1 text-sm ${
                family === t.key
                  ? 'border-blue-600 bg-blue-600 text-white'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'}`}
              onClick={() => setFamily(t.key)}>
              {t.label}
              <span className="ml-1 text-xs opacity-75">
                {families.find((f) => f.family === t.key)?.count ?? 0}
              </span>
            </button>
          ))}
          <span className="ml-2">{famName}</span>
        </div>

        {err && <p className="rounded bg-red-50 p-3 text-sm text-red-600" role="alert">{err}</p>}

        <div className="grid gap-3 md:grid-cols-3">
          <ul className="space-y-1 md:col-span-1" data-testid="lib-list">
            {items.map((it) => (
              <li key={it.slug}>
                <button
                  data-testid={`lib-item-${it.slug}`}
                  className={`w-full rounded-md border px-2 py-1.5 text-left text-sm ${
                    detail?.slug === it.slug
                      ? 'border-blue-600 bg-blue-50 text-blue-800'
                      : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'}`}
                  onClick={() => onPick(it.slug)}>
                  <span className="block truncate font-medium">{it.title || it.slug}</span>
                  <span className="block truncate text-xs text-gray-400">{it.slug}</span>
                </button>
              </li>
            ))}
            {items.length === 0 && !err && (
              <li className="text-sm text-gray-400">本族暂无已入站件</li>
            )}
          </ul>

          <div className="md:col-span-2">
            {detail ? (
              <article data-testid="lib-detail" className="rounded-lg border border-gray-200">
                <header className="border-b border-gray-100 px-4 py-2">
                  <h2 className="text-base font-semibold text-gray-800">{detail.title}</h2>
                  <p className="text-xs text-gray-500">
                    {detail.slug} ｜ 源：{detail.source_path} ｜ 入站：{detail.synced_at}
                  </p>
                </header>
                <pre className="max-h-[70vh] overflow-auto whitespace-pre-wrap px-4 py-3 text-sm leading-6 text-gray-800">
                  {detail.body_md}
                </pre>
              </article>
            ) : (
              <p className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-sm text-gray-400">
                ← 点左侧件名读正文（只读面；权威源以在册仓库为准）
              </p>
            )}
          </div>
        </div>
      </div>
    </PageShell>
  )
}
