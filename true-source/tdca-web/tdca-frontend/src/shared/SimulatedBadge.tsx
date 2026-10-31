// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-5 模拟态标注（ID92 全局角标）
// 约束矩阵: L1SI183-SITEOBS-001 任务A——组件读单一映射表（shared/dataNature.ts），
//   ⛔ 自带默认文案、⛔ 硬写 data-nature 属性值；real 不渲染，mixed/simulated 按映射表渲染。
// 预期分配: SimulatedBadge（data_nature 非 real 时显示角标）
// =============================================================================

import { DATA_NATURE_LABELS, type DataNature } from './dataNature'

export interface SimulatedBadgeProps {
  nature: DataNature
  /** 显式覆盖文案（仅特殊场景如「演示数据」使用；缺省一律取单一映射表） */
  label?: string
}

/** 模拟态角标（ID92）：文案取 DATA_NATURE_LABELS 单一映射表；data-nature 属性如实反映档位 */
export function SimulatedBadge({ nature, label }: SimulatedBadgeProps) {
  const mapped = DATA_NATURE_LABELS[nature]
  if (mapped === null) return null
  return (
    <span
      data-testid="simulated-badge"
      data-nature={nature}
      className="inline-flex items-center rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-semibold text-purple-700"
    >
      {label ?? mapped}
    </span>
  )
}
