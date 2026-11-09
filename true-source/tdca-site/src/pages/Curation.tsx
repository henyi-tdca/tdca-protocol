// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI206-MIGRATE-B3 /curation 严选池专栏
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-MIGRATE-B3-001 §三——载体 public/curation.json
//   机读单一真源（页面 ⛔ 硬编码条目）；每条至少 id/title/summary/tags/status/source；
//   页面条目数 ≡ json 条目数（沙盒验证第 2 项）
// 并轨注记: MIGRATE 批3 自旧树 pages/curation.tsx 同栈直拷适配——
//   ① 引路三换（PageShell→@/components、数据 import→运行时 fetch('/curation.json')、
//      新 schema 状态枚举 采纳·待观察·不采——旧值映射 已挂载/已签批→采纳、观察中→待观察，
//      值域照令面，映射在本注记公示；license/first_public 作令面「至少」之外保留字段照带）；
//   ② 形状闸 fail-closed（contract/必填字段/status 枚举，不合 ⟹ 不渲染清单，只报形状不合）；
//   ③ 取数失败/形状不合 ⛔ 兜底假数据（降级文案如实标注）。
//   版面结构/testid 一字未动（curation-page/header/summary/list/footer）。
// =============================================================================
import { useEffect, useMemo, useState } from 'react'
import { PageShell } from '@/components/PageShell'

interface PoolItem {
  id: string
  title: string
  summary: string
  tags: string[]
  status: string
  source: string | null
  license?: string | null
  first_public?: string
}

interface PoolFile {
  contract: string
  items: PoolItem[]
}

/** 状态枚举（照令面三值，禁自增删） */
const STATUS_ORDER = ['采纳', '待观察', '不采']

/** 形状闸（fail-closed）：任一条不合 ⟹ 整单不渲染，只报形状不合 */
export function validatePoolShape(file: unknown): string | null {
  const f = file as PoolFile
  if (!f || typeof f !== 'object') return '清单非对象'
  if (f.contract !== 'curation/1.0') return 'contract 字段不合（须为 curation/1.0）'
  if (!Array.isArray(f.items)) return 'items 非数组'
  for (const it of f.items) {
    if (!it.id || typeof it.id !== 'string') return 'id 缺失或非串'
    if (!it.title || typeof it.title !== 'string') return 'title 缺失或非串'
    if (!it.summary || typeof it.summary !== 'string') return `summary 缺失或非串（id=${it.id}）`
    if (!Array.isArray(it.tags)) return `tags 非数组（id=${it.id}）`
    if (!STATUS_ORDER.includes(it.status)) return `status 枚举不合（id=${it.id}）`
    if (it.source !== null && typeof it.source !== 'string') return `source 非串非空（id=${it.id}）`
  }
  return null
}

export function CurationPoolPage() {
  const [pool, setPool] = useState<PoolFile | null>(null)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    let alive = true
    fetch('/curation.json')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<PoolFile>
      })
      .then((data) => {
        if (!alive) return
        const err = validatePoolShape(data)
        if (err) setLoadError(`形状不合：${err}`)
        else setPool(data)
      })
      .catch((e: unknown) => {
        if (alive) setLoadError(`取数失败：${e instanceof Error ? e.message : String(e)}`)
      })
    return () => { alive = false }
  }, [])

  const { total, byStatus } = useMemo(() => {
    const items = pool?.items ?? []
    const m = new Map<string, number>()
    for (const it of items) m.set(it.status, (m.get(it.status) ?? 0) + 1)
    return { total: items.length, byStatus: m }
  }, [pool])

  return (
    <PageShell
      title="严选池 · 精选项目一栏"
      dataSource="严选池清单 public/curation.json（机读单一真源，运行时只读取数）"
      permission="公开（匿名可读）"
      description="严选池：经在册严选流程留池的项目清单。本栏只出汇总数、项目名与用途一句，逐项照单如实呈现，留白如实标注。"
    >
      <div data-testid="curation-page" className="space-y-5">
        {/* 页头 */}
        <div data-testid="curation-header" className="rounded-lg bg-teal-700 px-5 py-4 text-white">
          <div className="text-lg font-bold">严选池 · 精选项目一栏</div>
          <span className="mt-1.5 inline-block rounded-full bg-teal-100 px-3 py-0.5 text-xs text-teal-800">
            匿名可读 · 清单唯一源 · 未增删一项
          </span>
        </div>

        {/* 取数失败／形状不合：fail-closed，不渲染清单、不兜底假数据 */}
        {loadError && (
          <div data-testid="curation-load-error" className="rounded-lg border border-red-300 bg-red-50 p-4 text-[13px] text-red-700">
            严选池清单暂不可用（fail-closed，不予渲染）：{loadError}
          </div>
        )}

        {!loadError && !pool && (
          <p data-testid="curation-loading" className="text-sm text-gray-400">清单载入中…</p>
        )}

        {pool && (
          <>
            {/* 汇总数（总数＋三态计数，由清单数据现算） */}
            <div data-testid="curation-summary" className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded-lg border border-gray-200 bg-white p-4">
                <div className="text-2xl font-bold text-gray-900">{total}</div>
                <div className="mt-0.5 text-xs text-gray-500">在册项目总数</div>
              </div>
              {STATUS_ORDER.map((s) => (
                <div key={s} className="rounded-lg border border-gray-200 bg-white p-4">
                  <div className="text-2xl font-bold text-gray-900">{byStatus.get(s) ?? 0}</div>
                  <div className="mt-0.5 text-xs text-gray-500">{s}</div>
                </div>
              ))}
            </div>

            {/* 逐项照单渲染（六列：项目名／地址／用途／状态／许可／首次公开日） */}
            <div data-testid="curation-list" className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
              <table className="w-full min-w-[720px] text-[13px]">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs text-gray-500">
                    <th className="px-3 py-2.5 font-medium">项目名</th>
                    <th className="px-3 py-2.5 font-medium">地址</th>
                    <th className="px-3 py-2.5 font-medium">用途</th>
                    <th className="px-3 py-2.5 font-medium">状态</th>
                    <th className="px-3 py-2.5 font-medium">许可</th>
                    <th className="px-3 py-2.5 font-medium">首次公开日</th>
                  </tr>
                </thead>
                <tbody>
                  {pool.items.map((it) => (
                    <tr key={it.id} data-testid={`curation-item-${it.id}`} className="border-b border-gray-100 last:border-0">
                      <td className="px-3 py-2.5 font-medium text-gray-900">{it.title}</td>
                      <td className="px-3 py-2.5">
                        {it.source ? (
                          <a href={it.source} target="_blank" rel="noreferrer" className="text-teal-700 underline decoration-dotted underline-offset-2">
                            {it.source}
                          </a>
                        ) : (
                          <span className="text-gray-400">待补</span>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-gray-700">{it.summary}</td>
                      <td className="px-3 py-2.5">
                        <span className="rounded bg-sky-100 px-2 py-0.5 text-xs text-sky-800">{it.status}</span>
                      </td>
                      <td className="px-3 py-2.5">{it.license ?? <span className="text-gray-400">待补</span>}</td>
                      <td className="px-3 py-2.5 text-gray-700">{it.first_public ?? '待补'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <footer data-testid="curation-footer" className="pb-6 text-xs leading-relaxed text-gray-400">
              本栏由智库侧严选清单供给，执行侧照单渲染：未增删一项、未改一个字段值；清单留白处（许可／地址未载者）如实标注「待补」，⛔ 猜测。
              <br />
              本栏只列汇总数与六字段；评选标准与流程细节不在公开面。
            </footer>
          </>
        )}
      </div>
    </PageShell>
  )
}
