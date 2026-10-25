// L1SI175-A1-2：术语页测试（登录可见·服务端检索·⛔ 页面不出 id 列）
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { TermsPage } from '@/pages/terms'

const SEED = [
  { term: '配置权', def: '不拥有参数，只拥有场景化调用权' },
  { term: 'NCA', def: '嵌套认知资产——调用即存证' },
]

function mockTerms(rows: typeof SEED) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.includes('/api/v1/knowledge/terms')) {
      const q = new URL(url, 'http://localhost').searchParams.get('q') ?? ''
      const hit = q ? rows.filter((r) => r.term.includes(q) || r.def.includes(q)) : rows
      return { ok: true, status: 200, json: async () => ({ nca_watermark: 'sha256:test', data_nature: 'real', data: { terms: hit, total: hit.length, note: 't' } }) } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'nf' }) } as Response
  }))
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('L1SI175-A1-2 术语页', () => {
  it('列表渲染：词/释义两列，⛔ 不出 id', async () => {
    mockTerms(SEED)
    render(<MemoryRouter><TermsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('terms-list')).toBeTruthy(), { timeout: 3000 })
    expect(screen.getByText('配置权')).toBeTruthy()
    expect(screen.getByText('嵌套认知资产——调用即存证')).toBeTruthy()
    expect(screen.queryByText('T-NCA')).toBeNull()   // id 不上页面
    expect(screen.queryByText(/T-\d{3}/)).toBeNull()
  })

  it('检索走服务端 ?q=：无匹配出「暂无匹配」空态', async () => {
    mockTerms(SEED)
    render(<MemoryRouter><TermsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('terms-list')).toBeTruthy(), { timeout: 3000 })
    const input = screen.getByPlaceholderText(/输入关键词检索术语/)
    fireEvent.change(input, { target: { value: '绝不存在词xyz' } })
    await waitFor(() => expect(screen.getByTestId('terms-empty')).toBeTruthy(), { timeout: 3000 })
    const calls = (vi.mocked(fetch) as unknown as { mock: { calls: unknown[][] } }).mock.calls.map((c) => String(c[0]))
    expect(calls.some((u) => u.includes('q=') && u.includes(encodeURIComponent('绝不存在词xyz')))).toBe(true)
  })

  it('检索命中：返回匹配条数', async () => {
    mockTerms(SEED)
    render(<MemoryRouter><TermsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('terms-list')).toBeTruthy(), { timeout: 3000 })
    const input = screen.getByPlaceholderText(/输入关键词检索术语/)
    fireEvent.change(input, { target: { value: '配置权' } })
    await waitFor(() => expect(screen.getByText(/共 1 条/)).toBeTruthy(), { timeout: 3000 })
  })
})
