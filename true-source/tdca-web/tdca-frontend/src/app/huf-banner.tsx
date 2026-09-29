// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-1 HUF 常驻 Banner（全局签批模态框入口）
// 约束矩阵: F-4/HUF（升级权人类，AI 无权代行）/ ID33（OTA 需 HUF）/ ID92（模拟态标注）
// 预期分配: HufBanner（常驻横幅 + 全局 HufModal；确认 → 记录签批存证状态）
// =============================================================================
import { useState } from 'react'
import { HufModal } from '@/shared/guards'

export interface HufBannerProps {
  /** 自定义签批动作描述（默认：通用制度级操作） */
  actionLabel?: string
}

/** HUF 常驻 Banner：全局人类最终签批入口（F-4/HUF） */
export function HufBanner({ actionLabel = '制度级操作（治理/创建/签批/确权）' }: HufBannerProps) {
  const [open, setOpen] = useState(false)
  const [signed, setSigned] = useState(false)

  return (
    <div data-testid="huf-banner" className="flex items-center justify-between gap-3 rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5">
      <span className="text-xs font-medium text-amber-800">
        HUF 人类最终签批权（F-4）：AI 无权替代 · {actionLabel}
      </span>
      <button
        data-testid="huf-banner-open"
        className="rounded border border-amber-500 bg-white px-2.5 py-1 text-xs font-medium text-amber-700 hover:bg-amber-100"
        onClick={() => setOpen(true)}
      >
        {signed ? '已签批存证 · 再次发起' : '发起签批'}
      </button>
      <HufModal
        open={open}
        onOpenChange={setOpen}
        onConfirm={() => setSigned(true)}
        title="HUF 人类最终签批"
        description={`确认签批「${actionLabel}」？AI 无权替代人类最终签批权（F-4/HUF）；签批将生成 NCA 存证。`}
      />
    </div>
  )
}
