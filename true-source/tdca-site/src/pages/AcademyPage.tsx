// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 /academy 知识学院（A-6 术语 G-1）
// 约束矩阵: FRAMEWORK-001 §四 /academy + A-6 契约 + G-1（术语基线）
// =============================================================================
import { useMemo, useState } from 'react'
import { useApiGet } from '@/lib/useApi'
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'
import { TermGuard } from '@/lib/term-guard'

interface TermsData {
  terms: { term: string; id: string; def: string }[]
  total: number
  note: string
}

/** 知识学院：G-1 术语检索（注册表 V1.1 子集） */
export function AcademyPage() {
  const { status, data, nature } = useApiGet<TermsData>('/api/v1/knowledge/terms')
  const [q, setQ] = useState('')

  const filtered = useMemo(() => {
    if (!data) return []
    if (!q) return data.terms
    return data.terms.filter((t) => t.term.includes(q) || t.def.includes(q))
  }, [data, q])

  return (
    <PageShell
      title="知识学院"
      dataSource="A-6 GET /api/v1/knowledge/terms + /api/edu/*（bridge）"
      permission="公开"
      description="商学院教材 + 教学模拟器 + 考核测评（E-EDU 生态）。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
      {status === 'fail' && (
        <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="academy-fail-closed">
          [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="academy-terms" className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            术语基线：注册表 V1.1（G-1）· {data.total} 条（演示子集）
            <SimulatedBadge nature={nature ?? 'simulated'} />
          </div>
          <TermGuard text={q} />
          <input
            data-testid="academy-search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="检索术语（G-1 基线）"
            className="w-full max-w-sm rounded border border-gray-300 px-3 py-1.5 text-sm"
          />
          <ul className="space-y-2">
            {filtered.map((t) => (
              <li key={t.term} data-term={t.term} className="rounded-lg border border-gray-200 p-3">
                <div className="text-sm font-semibold text-gray-800">
                  {t.term} <span className="ml-1 text-xs font-normal text-gray-400">{t.id}</span>
                </div>
                <div className="text-xs text-gray-600">{t.def}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </PageShell>
  )
}
