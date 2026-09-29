// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 页面接线测试（gateway 水印响应渲染）
// 约束矩阵: FRAMEWORK-001 §四 + A-1~A-8 契约 + ID91/ID85/ID92
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { HomePage } from '@/pages/home'
import { OwnershipPage } from '@/pages/ownership'
import { MarketPage } from '@/pages/market'
import { SandboxPage } from '@/pages/sandbox'
import { TaxPage } from '@/pages/tax'
import { AcademyPage } from '@/pages/academy'
import { AuditPage } from '@/pages/audit'
import { GovernancePage } from '@/pages/governance'

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

describe('F1 橱窗层页面接线', () => {
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
    render(<HomePage />)
    await waitFor(() => expect(screen.getByTestId('home-kpi')).toBeInTheDocument())
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText(/调度税 2%/)).toBeInTheDocument()
  })

  it('首页：后端不可用 → fail-closed 提示（ID85）', async () => {
    mockApi('/api/v1/system/overview', {}, true)
    render(<HomePage />)
    await waitFor(() => expect(screen.getByTestId('home-fail-closed')).toBeInTheDocument())
  })

  it('所有权市场：确权路径向导五步 + 登记簿只读（无编辑路径）', () => {
    render(<OwnershipPage />)
    expect(screen.getByTestId('ownership-attest-path')).toBeInTheDocument()
    expect(screen.getByText('提交至法定交易中心')).toBeInTheDocument()
    expect(screen.getByText('进入 L2 配置权市场')).toBeInTheDocument()
    const registry = screen.getByText('所有权登记簿（公开查询）')
    expect(registry).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

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

  it('税收仪表盘：MOU 只读 + 硬下限校验（ID79）', async () => {
    mockApi('/api/v1/tax/mou/AGENT-A', {
      agent_id: 'AGENT-A',
      mou_inbound: '1025',
      mou_outbound: '0',
      mou_total: '1025',
      mou_irreducible: true,
      note: '模拟态',
    })
    render(<TaxPage />)
    await waitFor(() => expect(screen.getByTestId('tax-mou')).toBeInTheDocument())
    expect(screen.getAllByTestId('mou-readout')).toHaveLength(3)
    expect(screen.getByTestId('tax-irreducible')).toHaveTextContent('MOU 不可降（ID79）')
  })

  it('知识学院：A-6 术语渲染 + 检索过滤（G-1）', async () => {
    mockApi('/api/v1/knowledge/terms', {
      terms: [
        { term: '配置权', id: 'ID76', def: '不拥有参数，只拥有场景化调用权' },
        { term: 'MOU', id: 'ID79', def: '最低可见效用' },
      ],
      total: 2,
      note: 'G-1 子集',
    })
    render(<AcademyPage />)
    await waitFor(() => expect(screen.getByTestId('academy-terms')).toBeInTheDocument())
    expect(screen.getByText('配置权')).toBeInTheDocument()
    fireEvent.change(screen.getByTestId('academy-search'), { target: { value: 'MOU' } })
    expect(screen.queryByText('配置权')).not.toBeInTheDocument()
    expect(screen.getByText('MOU')).toBeInTheDocument()
  })

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

// HomePage 新增五元拓扑 Ω（TopologyEngine/Cytoscape）——jsdom stub 布局计算
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