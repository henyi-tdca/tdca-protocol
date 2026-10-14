// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: VISUAL-001 可视化增强测试（/tax 图表，拆自 visual）
// 约束矩阵: TDCA-FRONTEND-VISUAL-001 + ID92
// 拆搬说明：旧 visual.test.tsx 按场景拆为 5 件，本件为 /tax 双用例，用例字句未改；
//   共享脚手架（envelope/fetch 桩）逐字随件。页 import 适配新树 named export。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { TaxPage } from '@/pages/TaxPage'

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

describe('VISUAL-001 可视化增强 · /tax', () => {
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
})
