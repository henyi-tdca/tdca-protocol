// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-1 四层架构层级指示器（L0/L1/L2/L3 常驻）
// 约束矩阵: FRAMEWORK-001 §八·C.3（层级颜色编码）+ ID43（四层架构完整性）
// 预期分配: LayerIndicator（当前层高亮 + 颜色编码：L1 蓝 / L2 绿 / L3 金 / 沙盒紫 / studio 渐变）
// =============================================================================

export type LayerKey = 'L0' | 'L1' | 'L2' | 'L3' | 'SANDBOX' | 'STUDIO'

export interface LayerInfo {
  key: LayerKey
  label: string
  short: string
  /** tailwind 类：当前层高亮样式 */
  activeClass: string
  dot: string
}

export const LAYERS: LayerInfo[] = [
  { key: 'L0', label: 'L0 法律底层', short: 'L0', activeClass: 'bg-slate-800 text-white', dot: 'bg-slate-400' },
  { key: 'L1', label: 'L1 所有权市场', short: 'L1', activeClass: 'bg-blue-600 text-white', dot: 'bg-blue-500' },
  { key: 'L2', label: 'L2 配置权市场', short: 'L2', activeClass: 'bg-emerald-600 text-white', dot: 'bg-emerald-500' },
  { key: 'L3', label: 'L3 效用计量', short: 'L3', activeClass: 'bg-amber-500 text-white', dot: 'bg-amber-400' },
  { key: 'SANDBOX', label: '沙盒（L2 前置）', short: '沙盒', activeClass: 'bg-purple-600 text-white', dot: 'bg-purple-500' },
  { key: 'STUDIO', label: 'Studio（L1→L2 桥梁）', short: 'Studio', activeClass: 'bg-gradient-to-r from-blue-600 to-emerald-600 text-white', dot: 'bg-gradient-to-r from-blue-500 to-emerald-500' },
]

export function layerInfo(key: LayerKey): LayerInfo {
  return LAYERS.find((l) => l.key === key) ?? LAYERS[0]
}

export interface LayerIndicatorProps {
  current: LayerKey
}

/** 四层架构层级指示器：L0/L1/L2/L3 常驻 + 沙盒/Studio 特态（FRAMEWORK-001 §八·C.3）
 *  创始人 2026-10-17 指示：上下竖排（非左右横排）、不逾中屏宽 */
export function LayerIndicator({ current }: LayerIndicatorProps) {
  const shown: LayerKey[] = ['L0', 'L1', 'L2', 'L3']
  return (
    <div
      data-testid="layer-indicator"
      data-current={current}
      className="flex w-min flex-col gap-0.5 rounded-lg border border-gray-200 bg-white px-1.5 py-1.5 text-xs"
    >
      {shown.map((key) => {
        const info = layerInfo(key)
        const active = key === current || (current === 'SANDBOX' && key === 'L2') || (current === 'STUDIO' && (key === 'L1' || key === 'L2'))
        return (
          <span
            key={key}
            data-layer={key}
            data-active={active}
            className={`whitespace-nowrap rounded px-2 py-0.5 text-left font-medium ${active ? info.activeClass : 'bg-gray-100 text-gray-500'}`}
          >
            {info.label}
          </span>
        )
      })}
      {(current === 'SANDBOX' || current === 'STUDIO') && (
        <span
          data-layer={current}
          data-active
          className={`whitespace-nowrap rounded px-2 py-0.5 text-left font-medium text-white ${layerInfo(current).activeClass}`}
        >
          {layerInfo(current).label}
        </span>
      )}
    </div>
  )
}
