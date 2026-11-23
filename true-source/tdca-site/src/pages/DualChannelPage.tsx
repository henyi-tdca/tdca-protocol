// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: DUALCH-021 双通道等价对照页（/dual-channel）
// 约束矩阵: 令 TDCA-HANDOFF-EXEC-L1SI227-DUALCH-021——
//   页与接口同源：数据唯一来源 GET /api/v1/dual-channel（匿名只读·JSON 数组），⛔页内另编一套；
//   一表可读：功能域／人怎么走／机怎么走／共用后端／等价型／缺侧理由；
//   丙型显式标「仅人」/「仅机」＋理由；页首通俗说明；⛔渲染内部编号（件号只入机读字段）；
//   本页只作等价陈述（H-1），⛔以等价打通签名/授权/付费/私域/身份绑定五类禁混面。
// 复用: PageShell / api（tolerateMissingWatermark——接口按 J-1 返回裸 JSON 数组）
// =============================================================================
import { api } from '@/lib/client'
import { PageShell } from '@/components/PageShell'
import { useEffect, useState } from 'react'

export interface DualChannelEntry {
  domain: string
  human_path: string
  machine_path: string
  shared_backend: boolean
  equivalence_type: '甲' | '乙' | '丙'
  single_side_reason: string
  updated_at: string
  institution_ref?: string // 机读字段——⛔渲染（H-4）
}

const TYPE_LABEL: Record<DualChannelEntry['equivalence_type'], string> = {
  甲: '甲·全共享同源',
  乙: '乙·双通道各有',
  丙: '丙·单通道',
}

/** 缺侧标注：丙型必填「仅人」/「仅机」徽标（令 §三 2） */
function sideBadge(e: DualChannelEntry): string | null {
  if (e.equivalence_type !== '丙') return null
  return e.single_side_reason.includes('仅机') ? '仅机' : '仅人'
}

export function DualChannelPage() {
  const [items, setItems] = useState<DualChannelEntry[] | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    api
      .get<DualChannelEntry[]>('/api/v1/dual-channel', { tolerateMissingWatermark: true })
      .then((res) => {
        if (res.ok && Array.isArray(res.data)) setItems(res.data)
        else setFailed(true)
      })
      .catch(() => setFailed(true))
  }, [])

  return (
    <PageShell
      title="双通道等价对照"
      dataSource="GET /api/v1/dual-channel（同源清单·匿名只读）"
      permission="公开"
      description="同一件事的两个通道：人怎么走、机怎么走，是否同一套后端、同一份结果。"
    >
      <div data-testid="dc-page" className="space-y-6">
        <p data-testid="dc-lede" className="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-800">
          本表说明同一件事人与智能体各自怎么做，是否同一套制度、同一份结果。
        </p>

        {failed && (
          <p data-testid="dc-fail" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            对照清单暂不可用（数据源未应答）。本页不猜测、不默认，请稍后重试。
          </p>
        )}

        {items === null && !failed && (
          <p className="text-sm text-gray-500">载入中……</p>
        )}

        {items !== null && (
          <>
            <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
              <table data-testid="dc-table" className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
                    <th className="py-2 px-3 font-medium">功能域</th>
                    <th className="py-2 px-3 font-medium">人怎么走</th>
                    <th className="py-2 px-3 font-medium">机怎么走</th>
                    <th className="py-2 px-3 font-medium">共用后端</th>
                    <th className="py-2 px-3 font-medium">等价型</th>
                    <th className="py-2 px-3 font-medium">缺侧理由</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((e) => {
                    const badge = sideBadge(e)
                    return (
                      <tr key={e.domain} data-testid="dc-row" className="border-b border-gray-100 align-top">
                        <td className="py-2 px-3 font-medium text-gray-900">{e.domain}</td>
                        <td className="py-2 px-3 text-gray-700">
                          <code className="text-xs">{e.human_path}</code>
                        </td>
                        <td className="py-2 px-3 text-gray-700">
                          <code className="text-xs">{e.machine_path}</code>
                        </td>
                        <td className="py-2 px-3 text-gray-700">{e.shared_backend ? '是' : '否'}</td>
                        <td className="py-2 px-3 text-gray-700">
                          <span data-testid="dc-type">{TYPE_LABEL[e.equivalence_type]}</span>
                          {badge && (
                            <span
                              data-testid="dc-side-badge"
                              className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-800"
                            >
                              {badge}
                            </span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-gray-700">
                          {e.single_side_reason === 'n/a' ? (
                            <span className="text-gray-400">—</span>
                          ) : (
                            e.single_side_reason
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <p data-testid="dc-updated" className="text-xs text-gray-500">
              清单版本时间：{items[0]?.updated_at ?? '—'}（页与接口同源，同取一处）
            </p>
          </>
        )}
      </div>
    </PageShell>
  )
}
