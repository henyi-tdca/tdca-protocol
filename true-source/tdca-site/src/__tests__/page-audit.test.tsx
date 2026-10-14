// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 页面接线测试（审计透明，拆自 pages-f1）
// 约束矩阵: FRAMEWORK-001 §四 + A-7 契约
// 拆搬说明：旧 pages-f1.test.tsx 按页拆为 8 件，本件为审计透明 1 用例，字句未改。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuditPage } from '@/pages/AuditPage'

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

describe('F1 橱窗层页面接线 · 审计透明', () => {
  it('审计透明：A-7 公共账本事件渲染（只读）', async () => {
    mockApi('/api/v1/audit/ledger-public', {
      events: [
        { event_id: 'EV-001', type: 'TAX_SETTLE', ts: '2026-08-12T00:00:00Z', amount: '1025' },
      ],
      total: 1,
      note: '公共账本',
    })
    render(<AuditPage />)
    await waitFor(() => expect(screen.getByTestId('audit-ledger')).toBeInTheDocument())
    expect(screen.getByText('EV-001')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
