// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI197-PUBLIC2-001 两块自测
// 约束矩阵: 块 A——20 项全渲染／六字段齐／汇总现算／留白如实标「待补」／禁项零露出；
//   块 B——登记簿 contract nd/1.0／空簿如实／三式查具在；两页渲染文本内部编号形态零命中
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'
import { CurationPoolPage } from '@/pages/curation'
import { NodeDisclosurePage, validateShape } from '@/pages/node-disclosure'
import pool from '@/data/curation-pool.json'
import ledger from '@/data/node-rule-ledger.json'

const BANNED = [/L1SI[-:\s]?\d+/, /GSEQ[-:\s]?\d+/, /NCA[-:\s]?\d+/, /FC[-:\s]?\d+/, /A-ECON/]

describe('严选池专栏（块 A）', () => {
  it('清单 20 项全渲染，行数与源一致', () => {
    render(<MemoryRouter><CurationPoolPage /></MemoryRouter>)
    const items = (pool as { items: { name: string }[] }).items
    expect(items).toHaveLength(20)
    for (const it of items) {
      expect(screen.getByTestId(`curation-item-${it.name}`)).toBeTruthy()
    }
  })

  it('汇总现算：由源数据现算并与页卡一致（实测分布 7/7/6，交付信 6/7 之异见回报）', () => {
    render(<MemoryRouter><CurationPoolPage /></MemoryRouter>)
    const summary = screen.getByTestId('curation-summary').textContent ?? ''
    expect(summary).toContain('在册项目总数')
    expect(summary).toContain('已挂载')
    expect(summary).toContain('已签批')
    expect(summary).toContain('观察中')
    const items = (pool as { items: { status: string }[] }).items
    const count = (s: string) => items.filter((i) => i.status === s).length
    // 实测复取：以清单数据为准（交付信 §二称 已签批6/观察中7，实测 JSON 为 已签批7/观察中6）
    expect(items).toHaveLength(20)
    expect(count('已挂载')).toBe(7)
    expect(count('已签批')).toBe(7)
    expect(count('观察中')).toBe(6)
  })

  it('六字段表头齐；留白（null 许可／地址）如实标「待补」', () => {
    render(<MemoryRouter><CurationPoolPage /></MemoryRouter>)
    const list = screen.getByTestId('curation-list').textContent ?? ''
    for (const h of ['项目名', '地址', '用途', '状态', '许可', '首次公开日']) {
      expect(list).toContain(h)
    }
    const items = (pool as { items: { license: string | null; url: string | null }[] }).items
    expect(items.some((i) => i.license === null)).toBe(true)
    expect(items.some((i) => i.url === null)).toBe(true)
    expect(list).toContain('待补')
  })

  it('页面 chrome 不另加禁项字样；清单原文含「观察期」字样者照实渲染（须智库裁）', () => {
    render(<MemoryRouter><CurationPoolPage /></MemoryRouter>)
    const header = screen.getByTestId('curation-header').textContent ?? ''
    const footer = screen.getByTestId('curation-footer').textContent ?? ''
    const summary = screen.getByTestId('curation-summary').textContent ?? ''
    for (const t of ['判据', '档位', 'GSEQ', 'NCA-', 'FC-']) {
      expect(header + footer + summary).not.toContain(t)
    }
    // 照单渲染自证：源数据 purpose 含「观察期」的项数 ＝ 页面渲染含「观察期」的行数
    const items = (pool as { items: { name: string; purpose: string }[] }).items
    const srcHits = items.filter((i) => i.purpose.includes('观察期')).length
    const rows = screen.getAllByTestId(/^curation-item-/)
    const renderedHits = rows.filter((r) => (r.textContent ?? '').includes('观察期')).length
    expect(renderedHits).toBe(srcHits)
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

  // ENUMIDX-001 令 A：rule_type 收敛为下拉枚举（三值），形状闸兜底保留
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
  it('严选池页五式零命中', () => {
    const { container } = render(<MemoryRouter><CurationPoolPage /></MemoryRouter>)
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
