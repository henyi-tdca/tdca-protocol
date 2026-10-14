// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 页面接线测试（沙盒准入，拆自 pages-f1）
// 约束矩阵: FRAMEWORK-001 §四 + ID91
// 拆搬说明：旧 pages-f1.test.tsx 按页拆为 8 件，本件为沙盒准入 1 用例，字句未改。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { SandboxPage } from '@/pages/SandboxPage'

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

describe('F1 橱窗层页面接线 · 沙盒准入', () => {
  it('沙盒准入：SEA 五要件 + 未全绿不可入盒', async () => {
    mockApi('/api/v1/sandbox/sea-status', {
      sea: [
        { requirement: '任务书六要素', status: 'GREEN', note: 'FROZEN' },
        { requirement: '激活系数>1.2 门槛', status: 'AMBER', note: '待真实数据' },
      ],
      all_green: false,
      note: '模拟态',
    })
    render(<SandboxPage />)
    await waitFor(() => expect(screen.getByTestId('sandbox-sea')).toBeInTheDocument())
    expect(screen.getByTestId('sandbox-all-green')).toHaveTextContent('不可入盒')
    expect(screen.getByText('任务书六要素')).toBeInTheDocument()
  })
})
