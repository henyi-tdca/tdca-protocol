// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 追平批B2（L1SI206-PARITY-B2）六面验证
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-PARITY-FILL-001 §四验收——
//   ① 逐面可点（公开面匿名态）② 题名净名照旧版 ③ 索引三产物机算自洽
//   ④ /five-orders 空池如实标＋⛔ 交易入口
//   ⑤ /official-assets 工具在上产物在下＋调用未开放如实标（⛔ 支付集成）
//   ⑥ /status 三源合一＋fail-soft 人话兜底（⛔ 白屏）＋⛔ 内部编号上页
//   ⑦ /terms 服务端检索＋空态；登录全量/匿名脱敏（后端口径，⛔ 匿名开放）
//   ⑧ /ops/logs 六组填写（V-1~V-8 服务端为准）＋ /ops/logs/list 区间＋CSV
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { FiveOrdersPage } from '@/pages/FiveOrdersPage'
import { OfficialAssetsPage } from '@/pages/OfficialAssetsPage'
import { StatusPage } from '@/pages/StatusPage'
import { TermsPage } from '@/pages/TermsPage'
import { OpsLogsPage } from '@/pages/OpsLogsPage'
import { OpsLogsListPage } from '@/pages/OpsLogsListPage'
import { PAGE_META, ROUTE_PATHS } from '@/pages/PagesIndex'

// 六面同走 @/lib/client：整模块打桩（api.get/post 按路径分发）
const getMock = vi.fn()
const postMock = vi.fn()
vi.mock('@/lib/client', () => ({
  api: { get: (...a: unknown[]) => getMock(...a), post: (...a: unknown[]) => postMock(...a) },
  sessionToken: () => '',
}))

beforeEach(() => {
  localStorage.clear(); sessionStorage.clear()
  getMock.mockReset(); postMock.mockReset()
})
afterEach(() => { vi.unstubAllGlobals(); getMock.mockReset(); postMock.mockReset() })

describe('追平批B2：/five-orders 五序资产总览（空池如实标·⛔ 交易入口）', () => {
  it('count 全 0 出空态文案', async () => {
    getMock.mockResolvedValue({ ok: true, status: 200, data: { assets: [
      { order: 1, name: '效用权', desc: 'd', count: 0 },
      { order: 2, name: '配置权', desc: 'd', count: 0 },
    ], note: 'n' } })
    render(<MemoryRouter><FiveOrdersPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('assets-empty')).toBeTruthy())
    expect(screen.getByTestId('assets-empty').textContent).toContain('暂无真实资产（待生态接入）')
    expect(getMock).toHaveBeenCalledWith('/api/v1/assets/five-orders')
  })

  it('接口失败 fail-closed 人话兜底', async () => {
    getMock.mockResolvedValue({ ok: false, status: 503, data: null })
    render(<MemoryRouter><FiveOrdersPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('assets-fail-closed')).toBeTruthy())
    expect(screen.getByTestId('assets-fail-closed').textContent).toContain('fail-closed')
  })
})

describe('追平批B2：/official-assets 官方资产区（工具在上产物在下·未开放如实标）', () => {
  it('三区在架＋调用按钮未开放置灰', () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 404, text: async () => '' }) as Response))
    render(<MemoryRouter><OfficialAssetsPage /></MemoryRouter>)
    expect(screen.getByTestId('official-assets-page')).toBeTruthy()
    // 工具在上、产物在下（DOM 序）
    const tools = screen.getByTestId('official-tools')
    const products = screen.getByTestId('official-products')
    expect(tools.compareDocumentPosition(products) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    // 调用未开放：按钮置灰存在（⛔ 支付集成）
    expect((screen.getByTestId('product-call-disabled') as HTMLButtonElement).disabled).toBe(true)
  })
})

describe('追平批B2：/status 系统健康（三源合一·fail-soft）', () => {
  it('三源齐：指标＋徽章＋集群渲染', async () => {
    getMock.mockImplementation(async (path: string) => {
      if (path === '/api/v1/system/overview') return { ok: true, status: 200, data: {
        total_deliveries: 3, total_tax_settled: '0', avg_latency_ms: 12,
        total_fused: 1, total_fail_closed: 2,
        tax_rates: { dispatch_tax: 0.01, royalty: 0.02, transaction_fee: 0.003 }, system: 'x' } }
      if (path === '/api/v1/ci/badge') return { ok: true, status: 200, data: { suite: 'gateway-regression', status: 'green', note: '最近一回通过' } }
      if (path === '/api/v1/eios/cluster-status') return { ok: true, status: 200, data: { cluster: [{ endpoint: 'https://eios.example', capability: '集群能力', status: 'ACTIVE' }] } }
      return { ok: false, status: 404, data: null }
    })
    render(<MemoryRouter><StatusPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('status-metrics').textContent).toContain('交付数'))
    expect(screen.getByTestId('badge-status').textContent).toContain('绿')
    expect(screen.getAllByTestId('cluster-item').length).toBe(1)
    // 模块状态改写口径（⛔ S 编号上页）
    expect(screen.getByTestId('status-modules').textContent).toContain('16 个模块 · 已冻结')
    expect(screen.getByTestId('status-page').textContent).not.toContain('EIOS-')
  })

  it('任一源失败即 fail-closed 兜底（⛔ 白屏）', async () => {
    getMock.mockResolvedValue({ ok: false, status: 500, data: null })
    render(<MemoryRouter><StatusPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('status-fail-closed')).toBeTruthy())
    expect(screen.getByTestId('status-fail-closed').textContent).toContain('健康数据暂不可用')
  })
})

describe('追平批B2：/terms 术语检索（服务端 ?q=·空态）', () => {
  it('检索框在架＋列表渲染＋空态', async () => {
    getMock.mockResolvedValue({ ok: true, status: 200, data: { terms: [
      { term: '配置权', def: 'L2 层权利' },
    ], total: 1, note: 'n' } })
    render(<MemoryRouter><TermsPage /></MemoryRouter>)
    expect(screen.getByTestId('terms-search')).toBeTruthy()
    await waitFor(() => expect(screen.getByTestId('terms-list')).toBeTruthy())
    expect(screen.getByTestId('terms-list').textContent).toContain('配置权')
    // 空态（第二次检索返回空）
    getMock.mockResolvedValue({ ok: true, status: 200, data: { terms: [], total: 0, note: 'n' } })
    fireEvent.change(screen.getByTestId('terms-search').querySelector('input') as HTMLInputElement, { target: { value: 'zzz' } })
    await waitFor(() => expect(screen.getByTestId('terms-empty')).toBeTruthy(), { timeout: 2000 })
  })
})

describe('追平批B2：/ops/logs 运维日志填写（六组·V-1~V-8 服务端为准）', () => {
  it('六组表单渲染＋今日未填红点＋提交走 POST', async () => {
    getMock.mockResolvedValue({ ok: true, status: 200, data: { filled: false } })
    postMock.mockResolvedValue({ ok: true, status: 201, data: {} })
    render(<MemoryRouter><OpsLogsPage /></MemoryRouter>)
    expect(screen.getByTestId('ops-logs-form')).toBeTruthy()
    for (const k of ['f-root_http_status', 'f-acme_selftest', 'f-trail_seven_cols', 'f-exceptions']) {
      expect(screen.getByTestId(k)).toBeTruthy()
    }
    await waitFor(() => expect(screen.getByTestId('ops-logs-unfilled')).toBeTruthy())
    fireEvent.click(screen.getByTestId('ops-logs-submit'))
    await waitFor(() => expect(postMock).toHaveBeenCalledWith('/api/v1/ops/logs', expect.anything()))
  })
})

describe('追平批B2：/ops/logs/list 区间筛选＋CSV 导出', () => {
  it('查询渲染表格＋导出按钮在架', async () => {
    getMock.mockResolvedValue({ ok: true, status: 200, data: { total: 1, logs: [{
      log_date: '2026-11-09', duty_role: '值日', duty_no: 'U-1', handover: 'x',
      exceptions_count: 0, unclosed_count: 0, backfill: false, backfill_reason: null,
      filled_by: 'op', filled_at: '2026-11-09T22:00', sections: {},
    }] } })
    render(<MemoryRouter><OpsLogsListPage /></MemoryRouter>)
    expect(screen.getByTestId('ops-logs-filter')).toBeTruthy()
    expect(screen.getByTestId('ops-logs-export')).toBeTruthy()
    fireEvent.click(screen.getByTestId('ops-logs-search'))
    await waitFor(() => expect(screen.getByTestId('ops-logs-table').textContent).toContain('2026-11-09'))
  })
})

describe('追平批B2：站点地图入册（30→34）', () => {
  it('四面入册 ROUTE_PATHS（题名净名照旧版）', () => {
    expect(PAGE_META).toHaveLength(36) /* 追平批B4：+1（/verify） */
    const titles: Record<string, string> = {
      '/five-orders': '五序资产总览',
      '/official-assets': '官方资产区',
      '/status': '系统健康',
      '/terms': '术语检索',
    }
    for (const [path, title] of Object.entries(titles)) {
      expect(PAGE_META.find((m) => m.path === path)?.title).toBe(title)
      expect(ROUTE_PATHS).toContain(path)
    }
    // 运维私域面 ⛔ 入册
    expect(ROUTE_PATHS).not.toContain('/ops/logs')
    expect(ROUTE_PATHS).not.toContain('/ops/logs/list')
  })
})
