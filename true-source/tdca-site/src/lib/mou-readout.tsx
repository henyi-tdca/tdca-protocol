// 单摘自旧版 shared/guards/index.tsx（ID79 MOU 不可降：金色高亮 + 税额硬下限校验）
// 以内容定界（ID79 注释起 → MouReadout 函数末）；界面与文案逐字未改

// ---------------------------------------------------------------------------
// MOU 不可降（ID79）：金色高亮 + 税额硬下限校验
// ---------------------------------------------------------------------------
export interface MouReadoutProps {
  label: string
  amount: number
  minThreshold?: number
}
export function MouReadout({ label, amount, minThreshold = 0 }: MouReadoutProps) {
  const violated = amount < minThreshold
  return (
    <div data-testid="mou-readout" data-violated={violated} className="flex items-center gap-2">
      <span className="text-sm text-gray-600">{label}</span>
      <span className={`rounded px-2 py-0.5 text-sm font-semibold ${violated ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
        ¥{amount.toFixed(2)}
      </span>
      {violated && (
        <span className="text-xs font-medium text-red-600" data-testid="mou-violation">
          MOU 硬下限违反（&lt; {minThreshold}）——结算拒绝
        </span>
      )}
    </div>
  )
}
