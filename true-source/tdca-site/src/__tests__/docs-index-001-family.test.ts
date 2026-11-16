// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-SITE-DOCS-FAMILY-001 | 目标函数: DOCS-INDEX-001 文档列表族清单
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI215-DOCS-INDEX-001 §二步1/步3＋§三 J-2
//   18 件（help 1＋ops-guides 17）已在册（后端 /api/site/docs/{family} 在册清单驱动，
//   前端族清单不得缺族致列表不可见；⛔ 另造列表数据、⛔ 内部编号外露）
// =============================================================================
import { describe, expect, it } from 'vitest'
import { FAMILIES } from '../lib/siteApi'

describe('DOCS-INDEX-001 文档列表族清单', () => {
  it('族清单含 help 与 ops-guides（在册 18 件两族可列）', () => {
    const keys = FAMILIES.map((f) => f.key)
    expect(keys).toContain('help')
    expect(keys).toContain('ops-guides')
  })

  it('ops-guides 标签为「操作指引」，描述非空（对齐 DOCS-FAMILY-001 口径）', () => {
    const fam = FAMILIES.find((f) => f.key === 'ops-guides')
    expect(fam?.label).toBe('操作指引')
    expect(fam?.desc).toBeTruthy()
  })

  it('regulation 族保留在册（不动存量）', () => {
    expect(FAMILIES.map((f) => f.key)).toContain('regulation')
  })
})
