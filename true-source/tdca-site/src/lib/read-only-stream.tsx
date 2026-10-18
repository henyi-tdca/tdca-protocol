// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-BV3 | 目标函数: BV-3 只读流（数据只读渲染，无编辑路径，无本地缓存修改）
// 复用注记: FRONTEND-MERGE 批4 自旧版 src/shared/guards/index.tsx 单摘此一件
//           （界面与文案逐字未改，摘出段 sha256_16 = 1e49713eb5729db0）；
//           guards 其余件不属本批，不搬。
// =============================================================================

export interface ReadOnlyStreamProps {
  title: string
  data: unknown
  nature?: 'real' | 'simulated'
}
export function ReadOnlyStream({ title, data, nature = 'simulated' }: ReadOnlyStreamProps) {
  return (
    <div data-testid="readonly-stream" className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">{title}</span>
        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">
          BV-3 只读 · {nature === 'simulated' ? 'SIMULATED' : 'REAL'}
        </span>
      </div>
      <pre className="max-h-40 overflow-auto rounded bg-gray-50 p-2 text-xs text-gray-700">
        {JSON.stringify(data, null, 2)}
      </pre>
      <p className="mt-1 text-[10px] text-gray-400">只读流：无编辑路径 · 无本地缓存修改</p>
    </div>
  )
}
