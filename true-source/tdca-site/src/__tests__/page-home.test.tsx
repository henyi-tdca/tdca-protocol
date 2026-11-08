// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 页面接线测试（首页，拆自 pages-f1）
// 约束矩阵: FRAMEWORK-001 §四 + A-1 契约 + ID85
// 拆搬说明：旧 pages-f1.test.tsx 按页拆为 8 件，本件为首页 2 用例，字句未改；
//   仅 import 适配新树（Home 为 default export）。新壳首页引用 react-router <Link>，
//   须包 MemoryRouter 方可挂载（同旧件对 studio/notifier 之脚手架做法，不动断言）。
//   新壳首页若无对应 testid，属面本身差异，如实报，不删用例凑绿。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
// 对齐令 SITE-TESTFIX-001（甲组）：F1 橱窗层 KPI/fail-closed 面已随迁 /overview（FRONTEND-MERGE
// 新壳首页改为静态落地页，无 A-1 接线）——本件改渲染对象为 OverviewPage，断言（home-kpi /
// home-fail-closed testid）随面随迁、一字未动。
import { OverviewPage } from '@/pages/Overview'

// /overview 面内嵌五元拓扑 Ω（TopologyEngine/Cytoscape）——jsdom 无 canvas 环境，
// 照 visual-home / routing 同款做法 stub 布局计算（仅脚手架，不动断言）
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

describe('F1 橱窗层页面接线 · 首页', () => {
  it('首页：A-1 KPI 渲染（税率 + 统计）', async () => {
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
    render(
      <MemoryRouter>
        <OverviewPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('home-kpi')).toBeInTheDocument())
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText(/调度税 2%/)).toBeInTheDocument()
  })

  it('首页：后端不可用 → fail-closed 提示（ID85）', async () => {
    mockApi('/api/v1/system/overview', {}, true)
    render(
      <MemoryRouter>
        <OverviewPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('home-fail-closed')).toBeInTheDocument())
  })
})
