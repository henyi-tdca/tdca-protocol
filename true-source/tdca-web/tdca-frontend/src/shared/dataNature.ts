// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-5 数据性质标注（ID92 全局角标）
// 约束矩阵: L1SI183-SITEOBS-001 任务A——data_nature 三档 → 展示文案
//   「单一真源」映射表：本文件是唯一存放处；接口客户端（api/client.ts）与
//   展示组件（shared/SimulatedBadge.tsx）同源引用，⛔ 另立第二份映射、⛔ 组件自带默认文案。
//   档位口径（ID92）：全真→real（不显示角标）；混杂→mixed（⛔ 显示为「模拟」）；其余→simulated。
// =============================================================================

/** 数据性质三档（与接口侧 data_nature 取值一一对应） */
export type DataNature = 'real' | 'mixed' | 'simulated'

/**
 * 三档 → 展示文案 单一映射表。
 * `real` 映射为 null＝不渲染角标（真实数据不标注，ID92 原口径）。
 */
export const DATA_NATURE_LABELS: Record<DataNature, string | null> = {
  real: null,
  mixed: '数据性质 · 混合',
  simulated: '数据性质 · 模拟（期一内部真跑）',
}

/** 判定未知值（fail-closed）：非三档合法值一律按 simulated 标注，不猜测数据 */
export function coerceDataNature(v: unknown): DataNature {
  return v === 'real' || v === 'mixed' || v === 'simulated' ? v : 'simulated'
}
