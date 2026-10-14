// 【术语基线对齐 · TDCA-HANDOFF-EXEC-L1SI142-TERMCONST-ALIGN-001】本件术语基线已由
// 注册表 V1.1 对齐至在册权威源 TDCA-TERMINOLOGY-REGISTRY V3.2（T-001~T-147）：
// ① 15 条注册术语逐条分判（7 条在册者保留现名＋标对应条目号／3 条通行名保留原名不动／
//    5 条已承载者保留原名＋标承载条目号）；② 引用号 TERMS-001（正源未得）改指现行注册表；
// ③ 禁用语由子串匹配改分类匹配（词级／短语级），V2.1 不再拦单串、只拦完整说法
//   「术语防火墙 V2.1」；④ 头注基线改 V3.2。⛔ 未改调用方（term-guard.tsx／academy 页）一字。
// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: G-1 术语表（注册表 V3.2 基线 + 漂移检测词库）
// 约束矩阵: TDCA-TERMINOLOGY-REGISTRY V3.2（G-1 基线）+ ID93（不引用无权威编号）
// 预期分配: REGISTERED_TERMS + FORBIDDEN_PHRASES + scanTermDrift（供 TermGuard 使用）
// =============================================================================

export interface TermEntry {
  canonical: string
  ref: string
  aliases?: string[]
}

/** 注册表 V3.2 关键术语（G-1 基线）——前端渲染权威术语清单
 *  分判口径（TERMCONST-ALIGN-001 §一.1）：
 *  ・在册 7 条：保留现名＋标对应条目号（注册表无同名条目，其对应者系下位具体条目，⛔不可径改条目名）
 *  ・通行名 3 条（所有权／效用计量／通知机）：保留原名，未作条目、不标号
 *  ・已承载 5 条：保留原名＋标承载条目号 */
export const REGISTERED_TERMS: TermEntry[] = [
  { canonical: '配置权', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-006 配置权调度税／T-008 协作签约' },
  { canonical: '所有权', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · 通行名（未作条目）' },
  { canonical: '效用计量', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · 通行名（未作条目）' },
  { canonical: 'MOU 锚定', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-039 MOU 本体（＋分层锚定原理）' },
  { canonical: '正和满意解', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-007 正和阈值／T-068 SWU_s 满意解阈值' },
  { canonical: '负空间', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-016 主体负空间／T-069~T-079 场景负空间族' },
  { canonical: '沙盒', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-080~T-088 场景化合与沙盒族' },
  { canonical: '通知机', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · 产品名（未作条目）' },
  { canonical: '化合', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-080~T-088 场景化合与沙盒族' },
  { canonical: '确权', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · 辖 ID56 数据确权（无 T 号条目）' },
  { canonical: '四层架构', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-023 行为安全四层' },
  { canonical: '配置权市场', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-014 CCP 配置权调用协议（L2 配置权市场层）／T-130 族' },
  { canonical: '税收预缴', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-032 供应链结算调度税 等' },
  { canonical: '激活系数', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-085 激活系数统一形式 AC_inst' },
  { canonical: '出盒终裁', ref: 'TDCA-TERMINOLOGY-REGISTRY V3.2 · T-082 SandboxSM／T-083 Gate_exit' },
]

export interface ForbiddenPhrase {
  phrase: string
  reason: string
  /** 匹配级：word＝完整误用词（词级）；phrase＝无据声称之完整说法（短语级） */
  match: 'word' | 'phrase'
}

/** 无据声称/漂移词（G-1 强制拦截；分类匹配——词级拦完整误用词，短语级拦完整说法） */
export const FORBIDDEN_PHRASES: ForbiddenPhrase[] = [
  { phrase: '术语防火墙 V2.1', reason: '「术语防火墙 V2.1」为无据声称——在册注册表 V3.2 无此版本声称', match: 'phrase' },
  { phrase: '配置权重', reason: '非注册术语，应为「配置权」', match: 'word' },
  { phrase: '使用权重', reason: '非注册术语，应为「配置权」', match: 'word' },
]

export interface DriftHit {
  phrase: string
  reason: string
}

/** 扫描文本中的漂移词（TermGuard 调用；ID93/G-1 强制；分类匹配：词级／短语级）
 *  两类皆采完整说法之子串匹配，差别在登记之「说法」本身：
 *  ・词级（word）——登记的是完整误用词（配置权重／使用权重），其任何出现皆系误用
 *    （CJK 无语义词界，不做前后界判定，以免漏拦）；
 *  ・短语级（phrase）——登记的是无据声称之完整说法（术语防火墙 V2.1），
 *    ⛔ 不登记单串（如裸「V2.1」），免误伤正常版本号。 */
export function scanTermDrift(text: string): DriftHit[] {
  const hits: DriftHit[] = []
  for (const f of FORBIDDEN_PHRASES) {
    if (text.includes(f.phrase)) hits.push({ phrase: f.phrase, reason: f.reason })
  }
  return hits
}
