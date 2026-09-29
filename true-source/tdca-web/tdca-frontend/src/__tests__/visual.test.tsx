// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: VISUAL-001 可视化增强测试（recharts 图表 + 五元拓扑 Ω）
// 约束矩阵: TDCA-FRONTEND-VISUAL-001 + ID81（Ω 拓扑）+ ID92
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { TaxPage } from '@/pages/tax'
import { HomePage } from '@/pages/home'
import { StudioPage } from '@/pages/studio'
import { NotifierPage } from '@/pages/notifier'
import { SandboxPage } from '@/pages/sandbox'

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
    if (s.includes('/api/v1/sandbox/sea-status')) {
      return {
        ok: true,
        status: 200,
        json: async () => envelope({
          sea: [
            { requirement: '任务书六要素', status: 'GREEN', note: 'FROZEN' },
            { requirement: '激活系数>1.2 门槛', status: 'AMBER', note: '待真实数据' },
          ],
          all_green: false,
          note: '模拟态',
        }),
      } as Response
    }
    if (s.includes('/api/v1/tax/mou/AGENT-A')) {
      return {
        ok: true,
        status: 200,
        json: async () => envelope({
          agent_id: 'AGENT-A',
          mou_inbound: '3240',
          mou_outbound: '2180',
          mou_total: '5420',
          mou_irreducible: true,
          note: '模拟态',
        }),
      } as Response
    }
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

describe('VISUAL-001 可视化增强', () => {
  it('/tax：MOU 双柱图渲染（recharts BarChart）', async () => {
    const r = render(<TaxPage />)
    await waitFor(() => expect(screen.getByTestId('tax-mou-chart')).toBeInTheDocument())
    expect(r.container.querySelector('.recharts-wrapper')).toBeInTheDocument()
    expect(r.container.querySelectorAll('.recharts-bar-rectangle').length).toBeGreaterThan(0)
  })

  it('/tax：三池分流饼图（DRAFT 参数标注）+ Shapley 分账饼图', async () => {
    const r = render(<TaxPage />)
    await waitFor(() => expect(screen.getByTestId('tax-pool-chart')).toBeInTheDocument())
    expect(screen.getByText(/DRAFT 参数（无制度依据，待裁决）/)).toBeInTheDocument()
    expect(r.container.querySelectorAll('.recharts-pie').length).toBeGreaterThan(0)
    expect(screen.getByTestId('tax-shapley-chart')).toBeInTheDocument()
    expect(screen.getByText(/Shapley 分账/)).toBeInTheDocument()
  })

  it('/home：五元拓扑 Ω 挂载（H/M/L 顶点 + 五关系边，ID81）', async () => {
    const r = render(<HomePage />)
    await waitFor(() => expect(screen.getByTestId('home-omega')).toBeInTheDocument())
    expect(screen.getByText(/五元拓扑 Ω/)).toBeInTheDocument()
    expect(r.container.querySelector('[data-testid="home-omega"]')).toBeInTheDocument()
  })

  it('P2-1 /studio：生命周期时间轴动画容器（lifecycle-anim）', () => {
    const r = render(
      <MemoryRouter initialEntries={['/studio']}>
        <StudioPage />
      </MemoryRouter>,
    )
    expect(r.container.querySelector('.lifecycle-anim')).toBeInTheDocument()
    expect(screen.getByTestId('lifecycle-anim')).toBeInTheDocument()
    expect(screen.getAllByTestId(/^node-/).length).toBeGreaterThan(0)
  })

  it('P2-2 /notifier：坐标变换实时流转（WS 消息驱动）', async () => {
    class MockWS {
      static instances: MockWS[] = []
      url = ''
      onopen: (() => void) | null = null
      onmessage: ((ev: { data: string }) => void) | null = null
      onclose: (() => void) | null = null
      onerror: (() => void) | null = null
      close() {
        this.onclose?.()
      }
      constructor(url: string) {
        this.url = url
        MockWS.instances.push(this)
      }
    }
    vi.stubGlobal('WebSocket', MockWS)
    const r = render(
      <MemoryRouter initialEntries={['/notifier']}>
        <NotifierPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('notifier-transform')).toBeInTheDocument())
    expect(screen.getByTestId('transform-flow-count')).toHaveTextContent('等待 WS 消息')
    const notifierWs = MockWS.instances.find((w) => w.url.includes('channel=notifier'))
    act(() => {
      notifierWs?.onmessage?.({ data: JSON.stringify({ type: 'event' }) })
    })
    await waitFor(() => expect(screen.getByTestId('transform-flow-count')).toHaveTextContent('实时流转 1 次'))
    r.unmount()
  })

  it('P2-3 /sandbox：NSFL 三层防线状态机（编译期 → 运行期 → 发布期）', async () => {
    render(<SandboxPage />)
    await waitFor(() => expect(screen.getByTestId('nsfl-layers')).toBeInTheDocument())
    expect(screen.getByText('编译期 · C1-C6')).toBeInTheDocument()
    expect(screen.getByText('运行期 · L1 / R5-R8')).toBeInTheDocument()
    expect(screen.getByText('发布期 · Layer-8')).toBeInTheDocument()
    expect(screen.getByTestId('nsfl-flow-0')).toHaveTextContent('→')
  })
})
