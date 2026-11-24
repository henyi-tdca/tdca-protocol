// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: B1-001 三态可读面渲染接线（负空间十五格/沙盒四维/正空间认读）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI228-B1-001 卡1（1-2 逐格有交代 / 1-7 四维分项 / 1-9 人可读认读）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { NegativeSpaceListing, SandboxDomainPanel, PositiveSpaceReading } from '@/components/three-state/ThreeStateSections'

const NS_PAYLOAD = {
  version: 'B1-1-V1.0-20261124',
  purpose: '负空间清单式呈现（测试样例）',
  wording_note: '词面不公开（测试样例）',
  operators: [
    { symbol: '⊗', name: '禁止', desc: '命中即拒' },
    { symbol: '⊘', name: '限制', desc: '附条件放行' },
    { symbol: '⊙', name: '观察', desc: '计量留痕' },
  ],
  cells: [
    { category: '法律', operator: '⊗', status: 'has_clauses', clauses: [
      { text: '数据不得外泄（测试样例）', basis_doc: '法源映射规范件', basis_ref: 'X-1', basis_volume: 'checks', anchor: '001', strength: '已核' },
    ] },
    ...['⊗', '⊘', '⊙'].flatMap((op) =>
      ['公序良俗', '情绪', '信仰', '技术'].map((cat) => ({
        category: cat, operator: op,
        status: 'no_clauses' as const,
        clauses: [],
        note: `本格暂无可适用条款（测试样例：${cat}${op} 的理由与依据，长度须足以过判据）`,
        note_basis_doc: '在册检索实况', note_basis_ref: '', note_basis_volume: 'records',
      }))),
  ],
  human_judged: { title: '不可机判须归人（测试样例）', items: [
    { situation: '是否构成洗钱（测试样例）', trigger: '多跳过桥', basis_ref: 'X-9' },
  ] },
}

const SB_PAYLOAD = {
  version: 'B1-2-V1.0-20261124',
  purpose: '沙盒可行域（测试样例）',
  feasible_domain: {
    source_one: { name: '负空间清单引用', detail: '上界＝负空间清单十五格（测试样例）' },
    source_two: { name: '场景允许域', detail: 'SEA 五要件与场景线（测试样例）' },
    gate: { name: '出盒门槛', detail: '激活系数大于 1.2（占位待实例）' },
  },
  dimensions: [
    { key: 'functional', name: '功能', reads: ['入盒申请（测试样例）'], evidence: [{ type: '件哈希', label: '嵌套场景沙盒记录', sha256_16: 'D2E737109CB19DDF', ref: 'SBX-1', volume: 'sandbox', note: '' }], unsolved: '' },
    { key: 'security', name: '安全', reads: ['分卷限流（测试样例）'], evidence: [{ type: '件哈希', label: '三空间接入令', sha256_16: '625753737FC5EE37', ref: 'SBX-2', volume: 'handoffs', note: '' }], unsolved: '' },
    { key: 'performance', name: '性能', reads: ['限流参数可配（测试样例）'], evidence: [{ type: '实测', label: 'sea-status 200', sha256_16: null, ref: '', volume: '', note: '实测' }], unsolved: '吞吐量基准：本批无解——在册无性能基准件（测试样例）' },
    { key: 'compliance', name: '合规', reads: ['四判出证（测试样例）'], evidence: [{ type: '件哈希', label: '三空间接入令', sha256_16: '625753737FC5EE37', ref: 'SBX-2', volume: 'handoffs', note: '' }], unsolved: '' },
  ],
}

const PS_PAYLOAD = {
  version: 'B1-3-V1.0-20261124',
  purpose: '正空间认读（测试样例）',
  recompute_how: '取站上件→sha256→对位仓端提交号（测试样例）',
  items: [
    { name: '身份可信等级认定条例（测试样例）', klass: '条例', read: '四档认定次序（测试样例）', commit: 'ab1468eb', sha256_16: '910B19E1C3D05329', bytes: 6861, path: 'docs/regulations/x.md' },
  ],
  selection_note: '选编口径（测试样例）',
}

function stubThreeState() {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const s = String(url)
    const hit = s.includes('negative-space') ? NS_PAYLOAD
      : s.includes('/sandbox') ? SB_PAYLOAD
      : s.includes('positive-space') ? PS_PAYLOAD : null
    if (!hit) throw new Error(`unexpected url ${url}`)
    return { ok: true, status: 200, json: async () => hit } as Response
  }))
}

beforeEach(() => {
  localStorage.clear()
  stubThreeState()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('B1-001 三态可读面渲染接线', () => {
  it('负空间：十五格逐格渲染（含空格理由）＋归人清单', async () => {
    render(<NegativeSpaceListing />)
    await waitFor(() => expect(screen.getByTestId('ns-listing')).toBeInTheDocument())
    expect(screen.getByTestId('ns-cell-法律-⊗')).toHaveTextContent('数据不得外泄')
    expect(screen.getByTestId('ns-cell-信仰-⊙')).toHaveTextContent('暂无可适用条款')
    expect(screen.getByText(/不可机判须归人/)).toBeInTheDocument()
  })

  it('沙盒：可行域两源＋四维分项各自单列', async () => {
    render(<SandboxDomainPanel />)
    await waitFor(() => expect(screen.getByTestId('sandbox-domain')).toBeInTheDocument())
    expect(screen.getByTestId('sb-dim-functional')).toHaveTextContent('功能')
    expect(screen.getByTestId('sb-dim-compliance')).toHaveTextContent('合规')
    expect(screen.getByText(/本批无解/)).toBeInTheDocument()
  })

  it('正空间：认读件人可读＋哈希与提交号凭证位', async () => {
    render(<PositiveSpaceReading />)
    await waitFor(() => expect(screen.getByTestId('positive-reading')).toBeInTheDocument())
    expect(screen.getByTestId('ps-item-0')).toHaveTextContent('910B19E1C3D05329')
    expect(screen.getByTestId('ps-item-0')).toHaveTextContent('ab1468eb')
  })
})
