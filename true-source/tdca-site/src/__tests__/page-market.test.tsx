// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 页面接线测试（配置权市场，拆自 pages-f1）
// 约束矩阵: FRAMEWORK-001 §四 + A-4 契约
// 拆搬说明：旧 pages-f1.test.tsx 按页拆为 8 件，本件为配置权市场 1 用例，字句未改。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MarketPage } from '@/pages/MarketPage'

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

describe('F1 橱窗层页面接线 · 配置权市场', () => {
  it('配置权市场：A-4 五阶资产池渲染', async () => {
    mockApi('/api/v1/assets/five-orders', {
      assets: [
        { order: 1, name: '效用权', desc: '场景效用函数调用权', count: 0 },
        { order: 2, name: '配置权', desc: 'L2 配置权市场层', count: 0 },
      ],
      note: '演示框架',
    })
    render(<MarketPage />)
    await waitFor(() => expect(screen.getByTestId('market-assets')).toBeInTheDocument())
    expect(screen.getByText(/#1 效用权/)).toBeInTheDocument()
    expect(screen.getByText(/#2 配置权/)).toBeInTheDocument()
  })
})
