// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: G-1 术语表（注册表 V1.1 基线 + 漂移检测词库）
// 约束矩阵: TDCA-TERMINOLOGY-REGISTRY V1.1（G-1 基线，无「V2.1」声称）+ ID93（不引用无权威编号）
// 预期分配: REGISTERED_TERMS + FORBIDDEN_PHRASES + scanTermDrift（供 TermGuard 使用）
// =============================================================================

export interface TermEntry {
  canonical: string
  ref: string
  aliases?: string[]
}

/** 注册表 V1.1 关键术语（G-1 基线）——前端渲染权威术语清单 */
export const REGISTERED_TERMS: TermEntry[] = [
  { canonical: '配置权', ref: 'TERMS-001' },
  { canonical: '所有权', ref: 'TERMS-001' },
  { canonical: '效用计量', ref: 'TERMS-001' },
  { canonical: 'MOU 锚定', ref: 'TERMS-001' },
  { canonical: '正和满意解', ref: 'TERMS-001' },
  { canonical: '负空间', ref: 'TERMS-001' },
  { canonical: '沙盒', ref: 'TERMS-001' },
  { canonical: '通知机', ref: 'TERMS-001' },
  { canonical: '化合', ref: 'TERMS-001' },
  { canonical: '确权', ref: 'TERMS-001' },
  { canonical: '四层架构', ref: 'TERMS-001' },
  { canonical: '配置权市场', ref: 'TERMS-001' },
  { canonical: '税收预缴', ref: 'TERMS-001' },
  { canonical: '激活系数', ref: 'TERMS-001' },
  { canonical: '出盒终裁', ref: 'TERMS-001' },
]

export interface ForbiddenPhrase {
  phrase: string
  reason: string
}

/** 无据声称/漂移词（G-1 强制拦截） */
export const FORBIDDEN_PHRASES: ForbiddenPhrase[] = [
  { phrase: 'V2.1', reason: '「术语防火墙 V2.1」为无据声称——注册表 V1.1（G-1 基线）' },
  { phrase: '配置权重', reason: '非注册术语，应为「配置权」' },
  { phrase: '使用权重', reason: '非注册术语，应为「配置权」' },
]

export interface DriftHit {
  phrase: string
  reason: string
}

/** 扫描文本中的漂移词（TermGuard 调用；ID93/G-1 强制） */
export function scanTermDrift(text: string): DriftHit[] {
  const hits: DriftHit[] = []
  for (const f of FORBIDDEN_PHRASES) {
    if (text.includes(f.phrase)) hits.push({ phrase: f.phrase, reason: f.reason })
  }
  return hits
}
