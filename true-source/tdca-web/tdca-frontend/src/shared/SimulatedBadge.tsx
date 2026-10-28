// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-5 模拟态标注（ID92 全局角标）
// 约束矩阵: ID92（data_nature=simulated → 全局模拟角标）/ FRAMEWORK-001 §5.1
// 预期分配: SimulatedBadge（nature=simulated 时显示 [SIMULATED] 角标）
// =============================================================================

export interface SimulatedBadgeProps {
  nature: 'real' | 'simulated'
  label?: string
}

/** 模拟态角标（ID92）：data_nature=simulated → 显式标注，真实数据不标注 */
export function SimulatedBadge({ nature, label = '数据性质 · 模拟（期一内部真跑）' }: SimulatedBadgeProps) {
  if (nature === 'real') return null
  return (
    <span
      data-testid="simulated-badge"
      data-nature="simulated"
      className="inline-flex items-center rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-semibold text-purple-700"
    >
      {label}
    </span>
  )
}
