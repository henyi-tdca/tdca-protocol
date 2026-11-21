// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: KB-TABS-001 知识库页族 tab 与接口同源对账
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI224-KB-TABS-001 §二步3：tab 集合（除 kg）== 接口返回族集合；
//           ?family= 深链白名单同源（接口族集合 ∪ {kg}），非法回落 whitepaper
// 先验分布: /library 旧 FAMILY_TABS 硬编码 5 族致制度 60 条不可见（-514 回报 S-2 根因）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { LibraryPage } from '@/pages/LibraryPage'

// 与后端 _OPEN_FAMILIES 九族同名（label 取自接口 name 字段，此处为测试桩值）
const NINE_FAMILIES = [
  { family: 'cop-library', name: '素材库', count: 894 },
  { family: 'terms', name: '术语', count: 1 },
  { family: 'laws', name: '法律', count: 3 },
  { family: 'law-notes', name: '法律适用说明', count: 5 },
  { family: 'whitepaper', name: '白皮书', count: 2 },
  { family: 'paper', name: '论文', count: 35 },
  { family: 'help', name: '帮助', count: 4 },
  { family: 'ops-guides', name: '运维指引', count: 17 },
  { family: 'regulation', name: '制度', count: 60 },
]

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-08-12T00:00:00Z', data_nature: 'simulated' }
}

function mockLibraryApi() {
  const fn = vi.fn(async (url: string, _init?: RequestInit) => {
    if (url.includes('/api/v1/library/families')) {
      return { ok: true, status: 200, json: async () => envelope({ items: NINE_FAMILIES, total: 9 }) } as Response
    }
    const m = url.match(/\/api\/v1\/library\/([a-z-]+)$/)
    if (m) {
      return { ok: true, status: 200, json: async () => envelope({ items: [], family: m[1] }) } as Response
    }
    throw new Error(`unexpected url ${url}`)
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

beforeEach(() => {
  localStorage.clear()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('KB-TABS-001 族 tab 同源对账', () => {
  it('tab 集合（除 kg）== 接口返回族集合；kg 为文档族外单独追加位', async () => {
    mockLibraryApi()
    render(<MemoryRouter initialEntries={['/library']}><LibraryPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('lib-tab-regulation')).toBeInTheDocument())
    const tabKeys = screen.getAllByTestId(/^lib-tab-/).map((el) =>
      (el.getAttribute('data-testid') ?? '').replace('lib-tab-', ''))
    const apiFamilies = new Set(NINE_FAMILIES.map((f) => f.family))
    expect(tabKeys).toContain('kg')                       // 追加位在架
    expect(new Set(tabKeys.filter((k) => k !== 'kg'))).toEqual(apiFamilies)  // 对账断言
    expect(tabKeys).toHaveLength(10)                      // 9 族＋kg
  })

  it('?family=regulation 深链可进（白名单同源派生）', async () => {
    const fn = mockLibraryApi()
    render(<MemoryRouter initialEntries={['/library?family=regulation']}><LibraryPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('lib-tab-regulation')).toBeInTheDocument())
    await waitFor(() =>
      expect(fn.mock.calls.some((c) => String(c[0]).includes('/api/v1/library/regulation'))).toBe(true))
    await waitFor(() =>
      expect(screen.getByTestId('lib-tab-regulation')).toHaveAttribute('data-active', 'true'))
  })

  it('非法 family 参数回落 whitepaper（不白屏不越界取件）', async () => {
    const fn = mockLibraryApi()
    render(<MemoryRouter initialEntries={['/library?family=evil-zone']}><LibraryPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('lib-tab-whitepaper')).toBeInTheDocument())
    await waitFor(() =>
      expect(screen.getByTestId('lib-tab-whitepaper')).toHaveAttribute('data-active', 'true'))
    expect(fn.mock.calls.some((c) => String(c[0]).includes('/api/v1/library/evil-zone'))).toBe(false)
  })
})
