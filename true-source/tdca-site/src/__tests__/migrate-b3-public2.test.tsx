// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI206-MIGRATE-B3 严选池专栏＋披露登记簿自测
// 约束矩阵: L1SI197-PUBLIC2-001 两块自测 ＋ MIGRATE-B3-001 §三/§四-2——
//   严选池：条目全渲染／页面条目数 ≡ curation.json 条目数／六字段齐／汇总现算／留白如实标「待补」；
//   披露簿：contract nd/1.0／空簿如实／三式查具在／rule_type 下拉枚举三值；两页零内部编号形态
// 并轨注记: MIGRATE 批3 自旧树 __tests__/public2.test.tsx 迁移适配——
//   ① 严选池载体改 public/curation.json（运行时 fetch），测试 vi.stubGlobal('fetch') 供数，
//      对账断言＝页面渲染行数 ≡ 导入 json 条目数（真对账，非两硬编码互抄）；
//   ② 状态枚举改令面新值（已挂载/已签批→采纳 14、观察中→待观察 6，映射注记见页面件头）；
//   ③ 行 testid 由 name 改 id（name 含 '/' 不适合作 testid；id=name 置换 '/'→'-'）；
//   ④ 披露簿断言一字未动。
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { CurationPoolPage, validatePoolShape } from '@/pages/Curation'
import { NodeDisclosurePage, validateShape } from '@/pages/NodeDisclosure'
import pool from '../../public/curation.json'
import ledger from '@/data/node-rule-ledger.json'

const POOL = pool as { contract: string; items: { id: string; title: string; summary: string; tags: string[]; status: string; source: string | null; license?: string | null; first_public?: string }[] }

const BANNED = [/L1SI[-:\s]?\d+/, /GSEQ[-:\s]?\d+/, /NCA[-:\s]?\d+/, /FC[-:\s]?\d+/, /A-ECON/]

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => POOL,
  })))
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('严选池专栏（载体 curation.json，页面条目数 ≡ json 条目数）', () => {
  it('清单 20 项全渲染，页面行数与 json 条目数一致（真对账）', async () => {
    render(<MemoryRouter><CurationPoolPage /></MemoryRouter>)
    expect(POOL.items).toHaveLength(20)
    // 等 fetch 回合回填
    await screen.findByTestId('curation-summary')
    const rows = screen.getAllByTestId(/^curation-item-/)
    expect(rows).toHaveLength(POOL.items.length)
    for (const it of POOL.items) {
      expect(screen.getByTestId(`curation-item-${it.id}`)).toBeTruthy()
    }
  })

  it('汇总现算：总数 20＝采纳 14＋待观察 6（令面新枚举，映射注记见页面件头）', async () => {
    render(<MemoryRouter><CurationPoolPage /></MemoryRouter>)
    const summary = await screen.findByTestId('curation-summary')
    expect(summary.textContent).toContain('在册项目总数')
    expect(summary.textContent).toContain('采纳')
    expect(summary.textContent).toContain('待观察')
    const count = (s: string) => POOL.items.filter((i) => i.status === s).length
    expect(count('采纳')).toBe(14)
    expect(count('待观察')).toBe(6)
    expect(count('采纳') + count('待观察')).toBe(POOL.items.length)
  })

  it('六字段表头齐；留白（null 许可／地址）如实标「待补」', async () => {
    render(<MemoryRouter><CurationPoolPage /></MemoryRouter>)
    const list = await screen.findByTestId('curation-list')
    for (const h of ['项目名', '地址', '用途', '状态', '许可', '首次公开日']) {
      expect(list.textContent).toContain(h)
    }
    expect(POOL.items.some((i) => i.license === null)).toBe(true)
    expect(POOL.items.some((i) => i.source === null)).toBe(true)
    expect(list.textContent).toContain('待补')
  })

  it('形状闸 fail-closed：status 枚举不合／contract 不合 ⟹ 拒渲染清单', () => {
    expect(validatePoolShape(POOL)).toBeNull()
    expect(validatePoolShape({ contract: 'curation/2.0', items: [] })).toContain('contract')
    const bad = {
      contract: 'curation/1.0',
      items: [{ id: 'x', title: 'x', summary: 'x', tags: [], status: '已挂载', source: null }],
    }
    expect(validatePoolShape(bad)).toContain('status 枚举不合')
    const noSummary = {
      contract: 'curation/1.0',
      items: [{ id: 'x', title: 'x', summary: '', tags: [], status: '采纳', source: null }],
    }
    expect(validatePoolShape(noSummary)).toContain('summary')
  })

  it('取数失败 fail-closed：不渲染清单、不兜底假数据', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 500 })))
    render(<MemoryRouter><CurationPoolPage /></MemoryRouter>)
    expect(await screen.findByTestId('curation-load-error')).toBeTruthy()
    expect(screen.queryByTestId('curation-list')).toBeNull()
  })
})

describe('节点规则披露登记簿（块 B）', () => {
  it('簿契约 nd/1.0，records 为空数组（如实空簿）', () => {
    const l = ledger as { contract: string; records: unknown[] }
    expect(l.contract).toBe('nd/1.0')
    expect(l.records).toEqual([])
  })

  it('空簿页如实文案与三式查具在', () => {
    render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    expect(screen.getByTestId('disclosure-list').textContent).toContain('登记簿现无在册记录')
    expect(screen.getByTestId('disclosure-q-node')).toBeTruthy()
    expect(screen.getByTestId('disclosure-q-type')).toBeTruthy()
    expect(screen.getByTestId('disclosure-q-date')).toBeTruthy()
  })

  // rule_type 收敛为下拉枚举（三值），形状闸兜底保留
  it('rule_type 查询为下拉枚举：全部＋三值，⛔ 自由文本输入', () => {
    render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    const sel = screen.getByTestId('disclosure-q-type') as HTMLSelectElement
    expect(sel.tagName).toBe('SELECT')
    const values = [...sel.options].map((o) => o.value)
    expect(values).toEqual(['', 'negative_space', 'sandbox_exit', 'positive_space_internal'])
    // 形状闸兜底仍在：contract 不合即整簿不渲染
    const bad = validateShape({ contract: 'nd/0.9', records: [] })
    expect(bad).toContain('contract')
    // rule_type 枚举校验（双层兜底）
    const badType = validateShape({
      contract: 'nd/1.0',
      records: [{
        record_no: 'R-1', recorded_at: '2026-11-05T00:00:00+08:00', node_id: 'n1',
        rule_type: 'unknown_kind', rule_digest: '0123456789ABCDEF', rule_ref: 'ref',
        effective_at: '2026-11-05T00:00:00+08:00', supersedes: null, status: 'ACTIVE',
      }],
    })
    expect(badType).toContain('rule_type 枚举不合')
  })
})

describe('两块渲染文本内部编号形态零命中', () => {
  it('严选池页五式零命中', async () => {
    const { container } = render(<MemoryRouter><CurationPoolPage /></MemoryRouter>)
    await screen.findByTestId('curation-summary')
    const text = container.textContent ?? ''
    for (const re of BANNED) {
      expect(text.match(re) ?? [], String(re)).toEqual([])
    }
  })

  it('披露登记簿页五式零命中', () => {
    const { container } = render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    const text = container.textContent ?? ''
    for (const re of BANNED) {
      expect(text.match(re) ?? [], String(re)).toEqual([])
    }
  })
})
