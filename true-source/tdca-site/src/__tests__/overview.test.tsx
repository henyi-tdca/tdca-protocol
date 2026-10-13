// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: /overview 制度总览面测试（A-1 KPI + fail-closed + 五元拓扑 Ω）
// 约束矩阵: FRAMEWORK-001 §四 + A-1 契约 + ID91/ID85/ID92 + ID81（Ω 拓扑）
// 并轨注记: 自旧版 pages-f1.test.tsx（首页两用例）＋ visual.test.tsx（Ω 用例）随面迁入
//           （FRONTEND-MERGE 批1）；⚠️ 新版树暂未配 vitest 运行器（infra 未随迁），
//           本件随搬备跑，待测试栈入批后启用——如实标注「暂不可跑」
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { OverviewPage } from '@/pages/Overview'

vi.mock('cytoscape', () => {
  const fakeNode = () => ({ position: () => ({ x: 10, y: 10 }), id: () => 'n' })
  const fakeCore = {
    nodes: () => [fakeNode()],
    elements: () => ({ boundingBox: () => ({ x1: 0, y1: 0, x2: 100, y2: 100 }), nodes: () => [fakeNode()] }),
    ready: (cb: () => void) => cb(),
    destroy: () => {},
  }
  return { default: () => fakeCore }
})

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

describe('/overview 制度总览面（旧版首页迁入）', () => {
  it('A-1 KPI 渲染（税率 + 统计）', async () => {
    mockApi('/api/v1/system/overview', {
      total_deliveries: 42,
      total_tax_settled: '1025',
      avg_latency_ms: 2.5,
      total_fused: 1,
      total_fail_closed: 0,
      tax_rates: { dispatch_tax: 0.02, royalty: 0.075, transaction_fee: 0.0075 },
      theta: 0.7,
      phi: 0.3,
      system: 'ECOCOG FROZEN',
    })
    render(<MemoryRouter><OverviewPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('home-kpi')).toBeTruthy())
    expect(screen.getByText('42')).toBeTruthy()
    expect(screen.getByText(/调度税 2%/)).toBeTruthy()
  })

  it('后端不可用 → fail-closed 提示（ID85）', async () => {
    mockApi('/api/v1/system/overview', {}, true)
    render(<MemoryRouter><OverviewPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('home-fail-closed')).toBeTruthy())
  })

  it('五元拓扑 Ω 挂载（H/M/L 顶点 + 五关系边，ID81）', async () => {
    mockApi('/api/v1/system/overview', {
      total_deliveries: 42,
      total_tax_settled: '1025',
      avg_latency_ms: 2.5,
      total_fused: 1,
      total_fail_closed: 0,
      tax_rates: { dispatch_tax: 0.02, royalty: 0.075, transaction_fee: 0.0075 },
      theta: 0.7,
      phi: 0.3,
      system: 'ECOCOG FROZEN',
    })
    const r = render(<MemoryRouter><OverviewPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('home-omega')).toBeTruthy())
    expect(screen.getByText(/五元拓扑 Ω/)).toBeTruthy()
    expect(r.container.querySelector('[data-testid="home-omega"]')).toBeTruthy()
  })
})
