// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-F4HUF | 目标函数: HUF 人类最终签批模态（AI 无权替代 + 取消即中止）
// 复用注记: FRONTEND-MERGE 批3 自旧版 src/shared/guards/index.tsx 单摘此一件
//           （界面与文案逐字未改，摘出段 sha256_16 = cb4adc60bd34b2e6）；
//           guards 其余件（ReadOnlyStream/FuseIndicator/MouReadout 等）不属本批，不搬。
// =============================================================================

export interface HufModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
  title?: string
  description?: string
}
export function HufModal({ open, onOpenChange, onConfirm, title = 'HUF 人类最终签批', description }: HufModalProps) {
  if (!open) return null
  return (
    <div
      data-testid="huf-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="w-full max-w-md rounded-lg border border-amber-300 bg-white p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-1 text-base font-bold text-gray-900">{title}</h3>
        <p className="mb-3 text-sm text-gray-600">
          {description ?? '本操作涉及制度级决策（治理/创建/签批/确权）。AI 无权替代人类最终签批权（F-4/HUF）。'}
        </p>
        <div className="flex justify-end gap-2">
          <button
            data-testid="huf-cancel"
            className="rounded border border-blue-600 bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            onClick={() => onOpenChange(false)}
          >
            取消（中止操作）
          </button>
          <button
            data-testid="huf-confirm"
            className="rounded bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700"
            onClick={() => {
              onOpenChange(false)
              onConfirm()
            }}
          >
            确认签批 · NCA 存证
          </button>
        </div>
      </div>
    </div>
  )
}
