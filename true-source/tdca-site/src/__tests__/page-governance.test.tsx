// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 页面接线测试（治理中心，拆自 pages-f1）
// 约束矩阵: FRAMEWORK-001 §四 + A-8 契约
// 拆搬说明：旧 pages-f1.test.tsx 按页拆为 8 件，本件为治理中心 2 用例，字句未改。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { GovernancePage } from '@/pages/GovernancePage'

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

describe('F1 橱窗层页面接线 · 治理中心', () => {
  it('治理中心：HUF 签批全流程（模态 → needHuf POST → 结果）', async () => {
    const fn = mockApi('/api/v1/governance/huf-sign', {
      status: 'SIGNED',
      huf_irreducible: true,
      note: '人类最终签名权（HUF）',
    })
    render(<GovernancePage />)
    fireEvent.click(screen.getByTestId('governance-open-modal'))
    expect(screen.getByTestId('huf-modal')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('huf-confirm'))
    await waitFor(() => expect(screen.getByTestId('governance-result')).toHaveTextContent('SIGNED'))
    const [, init] = fn.mock.calls[0]
    const headers = (init as RequestInit).headers as Record<string, string>
    expect(headers.Authorization).toBeDefined()
  })

  it('治理中心：写操作失败 → fail-closed 错误提示', async () => {
    mockApi('/api/v1/governance/huf-sign', {}, true)
    render(<GovernancePage />)
    fireEvent.click(screen.getByTestId('governance-open-modal'))
    fireEvent.click(screen.getByTestId('huf-confirm'))
    await waitFor(() => expect(screen.getByTestId('governance-error')).toHaveTextContent('fail-closed'))
  })
})
