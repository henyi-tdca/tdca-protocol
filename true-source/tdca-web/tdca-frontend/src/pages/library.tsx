// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 内容区文库（/library 白皮书·论文·产物库）
// 约束矩阵: 站点入站令·甲/乙——只读面；以在册仓库为唯一权威源；A-22 /api/v1/library/*
// 复用: PageShell / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { api } from '@/api/client'
import { PageShell } from './PageShell'

interface FamilyView { family: string; name: string; count: number }
interface ItemView { slug: string; title: string; synced_at: string; has_content?: boolean }
interface DetailView {
  family: string; slug: string; title: string; body_md: string
  source_path: string; synced_at: string; note?: string
}

const FAMILY_TABS: { key: string; label: string }[] = [
  { key: 'whitepaper', label: '白皮书' },
  { key: 'paper', label: '论文与实证' },
  { key: 'cop-library', label: '产物库' },
  { key: 'regulation', label: '制度规范' },
]

// 产物库族内子库分组（slug 前缀 <子库>--；批一在册件无此前缀，归入说明件与代表件）
const COP_SUB_NAMES: Record<string, string> = {
  chengyu: '成语库',
  compositions: '化合库',
  emissary: '特使库',
  'engineering-three': '工程三协议',
  games: '博弈库',
  hundred_schools: '诸子百家',
  marxism: '马克思主义库',
  microeconomics: '微观经济学库',
  simulations: '模拟推演',
  stratagems: '三十六计',
}
const COP_SUB_ORDER = Object.keys(COP_SUB_NAMES)

interface CopGroup { key: string; name: string; items: ItemView[] }

function groupCopItems(items: ItemView[]): CopGroup[] {
  const byKey = new Map<string, ItemView[]>()
  for (const it of items) {
    const i = it.slug.indexOf('--')
    const key = i > 0 ? it.slug.slice(0, i) : '_legacy'
    const arr = byKey.get(key) ?? []
    arr.push(it)
    byKey.set(key, arr)
  }
  const groups: CopGroup[] = []
  // 批一在册件：无 <子库>-- 前缀者，加上批一自起 ad-hoc 前缀者（如 COMPOSITION-REPORT--*），
  // 一律归入「说明件与代表件」组，不做伪子库分组。
  const legacyItems = [
    ...(byKey.get('_legacy') ?? []),
    ...[...byKey.keys()]
      .filter((k) => k !== '_legacy' && !(k in COP_SUB_NAMES))
      .flatMap((k) => byKey.get(k)!),
  ]
  if (legacyItems.length > 0) {
    groups.push({ key: '_legacy', name: '说明件与代表件（批一在册）', items: legacyItems })
  }
  for (const k of COP_SUB_ORDER) {
    if (byKey.has(k)) {
      groups.push({ key: k, name: `${COP_SUB_NAMES[k]}（${k}）`, items: byKey.get(k)! })
    }
  }
  return groups
}

function CopItem({ it, detail, onPick }: {
  it: ItemView; detail: DetailView | null; onPick: (slug: string) => void
}) {
  const openable = it.has_content !== false
  const active = detail?.slug === it.slug
  const btn = (
    <button
      data-testid={`lib-item-${it.slug}`}
      data-openable={openable}
      disabled={!openable}
      title={openable ? '点击读正文' : '该件暂无可直接阅读的正文'}
      className={`w-full rounded-md border px-2 py-1.5 text-left text-sm ${
        !openable
          ? 'cursor-not-allowed border-gray-100 bg-gray-50 text-gray-400'
          : active
            ? 'border-blue-600 bg-blue-50 text-blue-800'
            : 'border-gray-200 bg-white text-blue-600 hover:bg-blue-50'}`}
      onClick={() => openable && onPick(it.slug)}>
      <span className="block truncate font-medium">
        {it.title || it.slug}
        {!openable && (
          <span className="ml-1 rounded bg-amber-100 px-1 py-px text-[9px] font-medium text-amber-700">在建中</span>
        )}
      </span>
      <span className={`block truncate text-xs ${openable ? 'text-gray-400' : 'text-gray-300'}`}>{it.slug}</span>
    </button>
  )
  return <li>{btn}</li>
}

export function LibraryPage() {
  const [params] = useSearchParams()
  const [families, setFamilies] = useState<FamilyView[]>([])
  const [family, setFamily] = useState(
    ['whitepaper', 'paper', 'cop-library', 'regulation'].includes(params.get('family') ?? '')
      ? (params.get('family') as string)
      : 'whitepaper')
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
      title="内容区文库（白皮书 · 论文 · 产物库 · 制度规范）"
      dataSource="A-22 GET /api/v1/library/*（docs 表只读面）"
      permission="登录 DID"
      description="站点入站令·甲/乙内容区＋规范全文面：只读索引＋正文阅读；产物库按子库分组呈现；以在册仓库为唯一权威源，本站不复制不改写。">
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
          <ul className="max-h-[70vh] space-y-1 overflow-auto md:col-span-1" data-testid="lib-list">
            {family === 'cop-library'
              ? groupCopItems(items).map((g) => (
                  <li key={g.key} className="pt-2 first:pt-0">
                    <p className="px-1 pb-1 text-xs font-semibold text-gray-500">
                      {g.name}
                      <span className="ml-1 font-normal text-gray-400">{g.items.length} 件</span>
                    </p>
                    <ul className="space-y-1">
                      {g.items.map((it) => (
                        <CopItem key={it.slug} it={it} detail={detail} onPick={onPick} />
                      ))}
                    </ul>
                  </li>
                ))
              : items.map((it) => <CopItem key={it.slug} it={it} detail={detail} onPick={onPick} />)}
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
                ← 点左侧件名读正文（蓝字＝可直接阅读；灰显＝暂无可读正文。只读面；权威源以在册仓库为准）
              </p>
            )}
          </div>
        </div>
      </div>
    </PageShell>
  )
}
