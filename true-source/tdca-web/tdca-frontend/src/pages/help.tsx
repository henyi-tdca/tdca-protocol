// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块二 — 「帮助与联系」（复用文档库「帮助」族＋联系块）
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §二块二（帮助与联系＝复用文档库「帮助」族＋联系块）
// 口径: ⛔ 不新造内容——帮助条目动态读 /api/site/docs/help；联系块未入站则如实空栏（空栏为常态，不预置）
// =============================================================================
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { PageShell } from './PageShell'

interface HelpItem {
  slug: string
  title: string
  synced_at: string
}

export function HelpPage() {
  const [items, setItems] = useState<HelpItem[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    fetch('/api/site/docs/help')
      .then((r) => {
        if (!r.ok) throw new Error(`API ${r.status}`)
        return r.json()
      })
      .then((d) => alive && setItems((d as { items: HelpItem[] }).items))
      .catch((e) => alive && setError(String(e instanceof Error ? e.message : e)))
    return () => {
      alive = false
    }
  }, [])

  const contactItems = (items ?? []).filter((it) => it.title.includes('联系'))

  return (
    <PageShell
      title="帮助与联系"
      dataSource="GET /api/site/docs/help（只读面）"
      permission="公开"
      description="站点帮助与官方联系入口。帮助内容复用文档库「帮助」族；论坛暂不建、先定位。"
    >
      <div className="space-y-6">
        {/* 帮助族条目（动态，⛔ 不预置） */}
        <section data-testid="help-list">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">帮助</h3>
          {error && (
            <p data-testid="help-fail-closed" className="rounded bg-red-50 p-3 text-sm text-red-600">
              [fail-closed] 帮助族暂不可用：{error}
            </p>
          )}
          {!error && items === null && <p className="text-sm text-gray-400">加载中…</p>}
          {!error && items !== null && items.length === 0 && (
            <p className="text-sm text-gray-500">帮助族暂无入库文档（空栏为常态）。</p>
          )}
          {!error && items !== null && items.length > 0 && (
            <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
              {items.map((it) => (
                <li key={it.slug}>
                  <Link to={`/docs/help/${it.slug}`} className="block px-4 py-3 hover:bg-gray-50">
                    <div className="font-medium text-gray-800">{it.title}</div>
                    <div className="text-xs text-gray-400">入库：{it.synced_at}</div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* 联系块（⛔ 不预置联系渠道：帮助族含「联系」条目则列，无则如实空栏） */}
        <section data-testid="help-contact" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">联系</h3>
          {contactItems.length > 0 ? (
            <ul className="space-y-1 text-sm">
              {contactItems.map((it) => (
                <li key={it.slug}>
                  <Link to={`/docs/help/${it.slug}`} className="text-blue-700 underline hover:text-blue-900">
                    {it.title}
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">
              官方联系渠道未入站（空栏为常态，不预置）；入站后自动在此列出。如需人工协助，可先试用右栏「AI 助手」。
            </p>
          )}
        </section>
      </div>
    </PageShell>
  )
}
