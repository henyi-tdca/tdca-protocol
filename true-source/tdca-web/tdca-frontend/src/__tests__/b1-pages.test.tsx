// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B1-1/2/3 两页测试（/assets /status）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B1-001 §六——空态/三源齐/零编号/零价格/SIMULATED/跑数
// =============================================================================
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AssetsPage } from '@/pages/assets'
import { StatusPage } from '@/pages/status'

function envelope(payload: unknown) {
  return { ok: true, status: 200, json: async () => ({ nca_watermark: 'sha256:test', data_nature: 'simulated', data: payload }) } as Response
}

const FIVE_ORDERS = {
  assets: [
    { order: 1, name: '效用权', desc: '场景效用函数调用权', count: 0 },
    { order: 2, name: '配置权', desc: 'L2 配置权市场层', count: 0 },
    { order: 3, name: 'NCA 嵌套认知资产', desc: '调用即存证', count: 0 },
    { order: 4, name: 'MOU 税收锚定凭证', desc: '进项+出项', count: 0 },
    { order: 5, name: '跨场景配置画像', desc: '多场景偏态档案', count: 0 },
  ],
  note: '五阶资产池',
}

const OVERVIEW = {
  total_deliveries: 128, total_tax_settled: '205.00', avg_latency_ms: 5.2,
  total_fused: 3, total_fail_closed: 7,
  tax_rates: { dispatch_tax: 0.02, royalty: 0.075, transaction_fee: 0.0075 },
  system: 'ECOCOG S-1~S-16 FROZEN（613 测试绿）',
}

const BADGE = { suite: 'gateway-regression', status: 'none', note: '尚无机验记录' }

const CLUSTER = {
  cluster: [
    { endpoint: 'positive-sum', capability: '正和满意解', id: 'EIOS-01', status: 'ACTIVE' },
    { endpoint: 'shapley', capability: 'Shapley 分配', id: 'EIOS-05', status: 'ACTIVE' },
  ],
}

function mockAll() {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const u = String(url)
    if (u.includes('/assets/five-orders')) return envelope(FIVE_ORDERS)
    if (u.includes('/system/overview')) return envelope(OVERVIEW)
    if (u.includes('/ci/badge')) return envelope(BADGE)
    if (u.includes('/eios/cluster-status')) return envelope(CLUSTER)
    return { ok: false, status: 404, json: async () => ({ detail: 'nf' }) } as Response
  }))
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('L1SI175-B1-1 五序资产总览', () => {
  it('count 全 0 出空态「暂无真实资产（待生态接入）」且 SIMULATED 角标在', async () => {
    mockAll()
    render(<MemoryRouter><AssetsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('assets-empty')).toBeTruthy(), { timeout: 3000 })
    expect(screen.getByText(/暂无真实资产（待生态接入）/)).toBeTruthy()
    expect(screen.getByText('SIMULATED')).toBeTruthy()
  })

  it('非零 count 出列表，五序齐', async () => {
    mockAll()
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (String(url).includes('/assets/five-orders')) {
        return envelope({ ...FIVE_ORDERS, assets: FIVE_ORDERS.assets.map((a, i) => ({ ...a, count: i === 0 ? 7 : 0 })) })
      }
      return { ok: false, status: 404, json: async () => ({ detail: 'nf' }) } as Response
    }))
    render(<MemoryRouter><AssetsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('assets-list')).toBeTruthy(), { timeout: 3000 })
    expect(screen.getByText('效用权')).toBeTruthy()
    expect(screen.getByText(/在册 7 件/)).toBeTruthy()
  })
})

describe('L1SI175-B1-2/3 系统健康（含集群并入）', () => {
  it('三源齐：指标/税率/徽章/集群；system 改写「16 个模块 · 已冻结」', async () => {
    mockAll()
    render(<MemoryRouter><StatusPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('status-metrics')).toBeTruthy(), { timeout: 3000 })
    // system 字段改写：禁出 S-1~S-16 与 613
    expect(screen.getByText(/16 个模块 · 已冻结/)).toBeTruthy()
    expect(screen.queryByText(/S-1~S-16/)).toBeNull()
    expect(screen.queryByText(/613/)).toBeNull()
    // 指标原样
    expect(screen.getByText('128')).toBeTruthy()
    expect(screen.getByText('205.00')).toBeTruthy()
    // 税率：演示态标注，百分比呈现
    expect(screen.getByText(/在册税率（演示态）/)).toBeTruthy()
    expect(screen.getByText('7.50%')).toBeTruthy()
    // 徽章一行
    expect(screen.getByTestId('badge-status')).toBeTruthy()
    // 集群：能力名在、id（EIOS-xx）不上页面
    await waitFor(() => expect(screen.getAllByTestId('cluster-item').length).toBe(2), { timeout: 3000 })
    expect(screen.getByText('正和满意解')).toBeTruthy()
    expect(screen.queryByText(/EIOS-0/)).toBeNull()
    // SIMULATED 角标
    expect(screen.getByText('SIMULATED')).toBeTruthy()
  })

  it('页面全文零价格字样（¥/￥/元/价格/档位/付费 均不出）', async () => {
    mockAll()
    const { container } = render(<MemoryRouter><StatusPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('status-page')).toBeTruthy(), { timeout: 3000 })
    const text = container.textContent ?? ''
    for (const bad of ['¥', '￥', '元', '价格', '档位', '付费']) {
      if (text.includes(bad)) throw new Error(`命中价格字样: ${bad} @ ${text.slice(Math.max(0, text.indexOf(bad) - 15), text.indexOf(bad) + 15)}`)
      expect(text.includes(bad)).toBe(false)
    }
  })

  it('集群空数据出「集群状态暂不可得」', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      const u = String(url)
      if (u.includes('/eios/cluster-status')) return envelope({ cluster: [] })
      if (u.includes('/system/overview')) return envelope(OVERVIEW)
      if (u.includes('/ci/badge')) return envelope(BADGE)
      return { ok: false, status: 404, json: async () => ({ detail: 'nf' }) } as Response
    }))
    render(<MemoryRouter><StatusPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('cluster-empty')).toBeTruthy(), { timeout: 3000 })
    expect(screen.getByText(/集群状态暂不可得/)).toBeTruthy()
  })
})
