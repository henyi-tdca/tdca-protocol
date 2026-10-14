// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: VISUAL-001 可视化增强测试（/home 五元拓扑 Ω，拆自 visual）
// 约束矩阵: TDCA-FRONTEND-VISUAL-001 + ID81（Ω 拓扑）
// 拆搬说明：旧 visual.test.tsx 按场景拆为 5 件，本件为 /home 五元拓扑用例，字句未改；
//   页 import 适配新树（Home 为 default export）。cytoscape 桩随件保留（该用例对象为
//   Ω 拓扑）。新壳首页引用 react-router <Link>，须包 MemoryRouter 方可挂载
//   （同旧件对 studio/notifier 之脚手架做法，不动断言）。
//   若新壳首页无 home-omega 等 testid，属面本身差异，如实报，不删用例凑绿。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import Home from '@/pages/Home'

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
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-08-13T00:00:00Z', data_nature: 'simulated' }
}

beforeEach(() => {
  localStorage.clear()
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const s = String(url)
    if (s.includes('/api/v1/system/overview')) {
      return {
        ok: true,
        status: 200,
        json: async () => envelope({
          total_deliveries: 42,
          total_tax_settled: '5420',
          avg_latency_ms: 2.5,
          total_fused: 1,
          total_fail_closed: 0,
          tax_rates: { dispatch_tax: 0.02, royalty: 0.075, transaction_fee: 0.0075 },
          theta: 0.7,
          phi: 0.3,
          system: 'ECOCOG FROZEN',
        }),
      } as Response
    }
    throw new Error('unexpected url')
  }))
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('VISUAL-001 可视化增强 · /home', () => {
  it('/home：五元拓扑 Ω 挂载（H/M/L 顶点 + 五关系边，ID81）', async () => {
    const r = render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('home-omega')).toBeInTheDocument())
    expect(screen.getByText(/五元拓扑 Ω/)).toBeInTheDocument()
    expect(r.container.querySelector('[data-testid="home-omega"]')).toBeInTheDocument()
  })
})
