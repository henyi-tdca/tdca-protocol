// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI197 严选池专栏（公开面一级栏目单页）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI197-PUBLIC2-001 块 A——只出三项（汇总数／项目名／用途一句）
//   ＋逐项六字段（项目名／地址／用途／状态／许可／首次公开日）；⛔ 判据细节／档位／观察期理由／
//   内部编号形态／告知函全文；清单为唯一源，执行侧 ⛔ 增删项 ⛔ 改字段值；⛔ 建详情页 ⛔ 入 sitemap 多层
// =============================================================================
import { PageShell } from './PageShell'
import pool from '@/data/curation-pool.json'

interface PoolItem {
  name: string
  url: string | null
  purpose: string
  status: string
  license: string | null
  first_public: string
}

const ITEMS = (pool as { items: PoolItem[] }).items

/** 汇总只出「总数＋三态计数」，由清单数据现算（渲染，非改值） */
function summarize(items: PoolItem[]) {
  const byStatus = new Map<string, number>()
  for (const it of items) byStatus.set(it.status, (byStatus.get(it.status) ?? 0) + 1)
  return { total: items.length, byStatus }
}

export function CurationPoolPage() {
  const { total, byStatus } = summarize(ITEMS)
  const statusOrder = ['已挂载', '已签批', '观察中']
  return (
    <PageShell
      title="严选池 · 精选项目一栏"
      dataSource="严选池清单（本侧供给，逐项照单渲染）"
      permission="公开（匿名可读）"
      description="严选池：经在册严选流程留池的项目清单。本栏只出汇总数、项目名与用途一句，逐项六字段照单如实呈现，留白如实标注。"
      dataNature="real"
    >
      <div data-testid="curation-page" className="space-y-5">
        {/* 页头 */}
        <div data-testid="curation-header" className="rounded-lg bg-teal-700 px-5 py-4 text-white">
          <div className="text-lg font-bold">严选池 · 精选项目一栏</div>
          <span className="mt-1.5 inline-block rounded-full bg-teal-100 px-3 py-0.5 text-xs text-teal-800">
            匿名可读 · 清单唯一源 · 未增删一项
          </span>
        </div>

        {/* 汇总数（只出三项之一：汇总数） */}
        <div data-testid="curation-summary" className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="text-2xl font-bold text-gray-900">{total}</div>
            <div className="mt-0.5 text-xs text-gray-500">在册项目总数</div>
          </div>
          {statusOrder.map((s) => (
            <div key={s} className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="text-2xl font-bold text-gray-900">{byStatus.get(s) ?? 0}</div>
              <div className="mt-0.5 text-xs text-gray-500">{s}</div>
            </div>
          ))}
        </div>

        {/* 逐项六字段（项目名／地址／用途／状态／许可／首次公开日） */}
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
              {ITEMS.map((it) => (
                <tr key={it.name} data-testid={`curation-item-${it.name}`} className="border-b border-gray-100 last:border-0">
                  <td className="px-3 py-2.5 font-medium text-gray-900">{it.name}</td>
                  <td className="px-3 py-2.5">
                    {it.url ? (
                      <a href={it.url} target="_blank" rel="noreferrer" className="text-teal-700 underline decoration-dotted underline-offset-2">
                        {it.url}
                      </a>
                    ) : (
                      <span className="text-gray-400">待补</span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-gray-700">{it.purpose}</td>
                  <td className="px-3 py-2.5">
                    <span className="rounded bg-sky-100 px-2 py-0.5 text-xs text-sky-800">{it.status}</span>
                  </td>
                  <td className="px-3 py-2.5">{it.license ?? <span className="text-gray-400">待补</span>}</td>
                  <td className="px-3 py-2.5 text-gray-700">{it.first_public}</td>
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
      </div>
    </PageShell>
  )
}
