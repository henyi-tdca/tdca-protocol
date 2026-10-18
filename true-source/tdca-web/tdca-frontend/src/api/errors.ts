// =============================================================================
// SPDX-License-Identifier: Apache-2.0
// TDCA 统一错误码表 v1（前端镜像 · L1SI153-ERROR-CODE-001 段一）
// 约束矩阵: 施工令 §二.2——前端显示「码＋中文短句」；短句取令 §四；
//           码与短句 ⛔ 分两处维护：本文件为前端唯一常量源（后端镜像 error_codes.py）。
// 命名规则: TDCA-E-<env>-<type>-<seq3>
// =============================================================================

/** 码 → 中文短句（用户所见；簇 1/2 的〈字段名〉为占位，实码细化归段二/后续） */
export const ERROR_CODE_TABLE: Record<string, string> = {
  'TDCA-E-INPUT-INPUT-001': '缺少必填项：〈字段名〉',
  'TDCA-E-INPUT-INPUT-002': '〈字段名〉格式不符要求',
  'TDCA-E-IDENT-PERM-001': '请先登录',
  'TDCA-E-IDENT-STATE-001': '凭证无效或已过期，请重新取得',
  'TDCA-E-AUTHZ-PERM-001': '当前账户无权执行此操作',
  'TDCA-E-ASSET-STATE-001': '该资源不存在或尚未登记',
  'TDCA-E-STATE-STATE-002': '当前状态不允许此操作',
  'TDCA-E-STATE-STATE-003': '已提交，请勿重复操作',
  'TDCA-E-RES-RES-001': '操作过于频繁，请稍后再试',
  'TDCA-E-SETL-RES-001': '额度不足',
  'TDCA-E-EXT-EXT-001': '外部服务暂不可用，请稍后重试',
  'TDCA-E-SYS-SYS-001': '系统繁忙，请稍后再试',
  'TDCA-E-GOV-PERM-002': '本次操作被制度性拒绝（合规前置未过）',
}

export const FALLBACK_ERROR_CODE = 'TDCA-E-SYS-SYS-001'

/** 后端拒绝体之 code 是否为本表在册码 */
export function isKnownCode(code: unknown): code is string {
  return typeof code === 'string' && code in ERROR_CODE_TABLE
}

/** 「码＋中文短句」显示串；未知/缺失码 → 兜底系统繁忙码 */
export function errorDisplay(code: unknown): string {
  const c = isKnownCode(code) ? code : FALLBACK_ERROR_CODE
  return `${ERROR_CODE_TABLE[c]}（${c}）`
}
