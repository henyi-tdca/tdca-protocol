// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 页面接线测试（税收仪表盘，拆自 pages-f1）
// 约束矩阵: FRAMEWORK-001 §四 + ID79
// 拆搬说明：旧 pages-f1.test.tsx 按页拆为 8 件，本件为税收仪表盘 1 用例，字句未改。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { TaxPage } from '@/pages/TaxPage'

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-08-12T00:00:00Z', data_nature: 'simulated' }
}

function mockApi(pathPart: string, payload: unknown, fail = false) {
  const fn = vi.fn(async (url: string, _init?: RequestInit) => {
    if (fail) throw new Error('network down')
    if (!url.includes(pathPart)) throw new Error(`unexpected url ${url}`)
    return { ok: true, status: 200, json: async () => envelope(payload) } as Response
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

describe('F1 橱窗层页面接线 · 税收仪表盘', () => {
  it('税收仪表盘：MOU 只读 + 硬下限校验（ID79）', async () => {
    mockApi('/api/v1/tax/mou/AGENT-A', {
      agent_id: 'AGENT-A',
      mou_inbound: '1025',
      mou_outbound: '0',
      mou_total: '1025',
      mou_irreducible: true,
      note: '模拟态',
    })
    render(<TaxPage />)
    await waitFor(() => expect(screen.getByTestId('tax-mou')).toBeInTheDocument())
    expect(screen.getAllByTestId('mou-readout')).toHaveLength(3)
    expect(screen.getByTestId('tax-irreducible')).toHaveTextContent('MOU 不可降')
  })
})
