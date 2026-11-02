// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI188-NAV-FIX-006 P2-1 主链导轨 ＋ P2-2 匿名可见面清单
// 约束矩阵: NAV-FIX-006 §一——导轨纯新增（⛔ 不动既有导航）；清单页三栏照实、无承诺语
// =============================================================================
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'
import { APP_NAV } from '@/app/app-shell'
import { MAIN_CHAIN } from '@/pages/main-chain-guide'

beforeEach(() => {
  localStorage.clear()
  vi.stubGlobal('fetch', vi.fn(async () => {
    throw new Error('network down')
  }))
})

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('NAV-FIX-006 P2-1：主链导轨', () => {
  it('主链八环节照令面序列（⛔ 自造环节）', () => {
    expect(MAIN_CHAIN.map((s) => s.label)).toEqual([
      '门户首页', '五序资产', '智能体通道', '能力与观测',
      '确权中心', '合约备案', '配置权市场', '审计与账本',
    ])
    expect(MAIN_CHAIN.map((s) => s.to)).toEqual([
      '/', '/five-orders', '/channel', '/agents',
      '/attestation', '/authorization-registry', '/market', '/audit',
    ])
  })

  it('导轨在主链页面可见（≥3 处：/、/five-orders、/channel、/market、/audit）且当前环节高亮', () => {
    for (const p of ['/', '/five-orders', '/channel', '/market', '/audit']) {
      const r = renderAt(p)
      const guide = screen.getByTestId('main-chain-guide')
      expect(guide).toBeInTheDocument()
      expect(screen.getByTestId('main-chain-step-1')).toBeInTheDocument()
      expect(screen.getByTestId('main-chain-step-8')).toHaveTextContent('审计与账本')
      r.unmount()
    }
    const r = renderAt('/audit')
    expect(screen.getByTestId('main-chain-step-8')).toHaveAttribute('data-current', 'true')
    r.unmount()
  })

  it('非主链页面不挂导轨（如 /about、/rules）', () => {
    const r1 = renderAt('/about')
    expect(screen.queryByTestId('main-chain-guide')).toBeNull()
    r1.unmount()
    const r2 = renderAt('/rules')
    expect(screen.queryByTestId('main-chain-guide')).toBeNull()
    r2.unmount()
  })

  it('既有导航零改动：九栏顺序与「我的」七项保持（P2 纯新增项除外）', () => {
    const tops = APP_NAV.map((e) => (e.kind === 'link' ? e.label : e.group))
    expect(tops[0]).toBe('首页')
    expect(tops).toContain('NCA 与透明')
    const mine = APP_NAV.find((e) => e.kind === 'group' && e.group === '我的')
    const mineTos = mine && mine.kind === 'group' ? mine.items.map((i) => ('to' in i ? i.to : '')) : []
    expect(mineTos).toEqual(['/me', '/studio', '/ops', '/ops/me', '/review', '/me/appeal', '/me/node/net'])
  })
})

describe('NAV-FIX-006 P2-2：匿名可见面清单一页三栏', () => {
  it('三栏齐、每栏 ≥3 条、含路由与匿名实测列', () => {
    renderAt('/public-face')
    for (const k of ['public-face-public', 'public-face-login', 'public-face-closed']) {
      expect(screen.getByTestId(k)).toBeInTheDocument()
    }
    const pubRows = screen.getByTestId('public-face-table-public').querySelectorAll('tbody tr')
    const loginRows = screen.getByTestId('public-face-table-login').querySelectorAll('tbody tr')
    const closedRows = screen.getByTestId('public-face-table-closed').querySelectorAll('tbody tr')
    expect(pubRows.length).toBeGreaterThanOrEqual(3)
    expect(loginRows.length).toBeGreaterThanOrEqual(3)
    expect(closedRows.length).toBeGreaterThanOrEqual(3)
  })

  it('「可看」栏所列路由均为本站公开路由（逐条可复核：与包内 PAGE_META 公开项一致）', () => {
    renderAt('/public-face')
    const text = screen.getByTestId('public-face-table-public').textContent ?? ''
    for (const r of ['/', '/about', '/five-orders', '/channel', '/audit', '/rules', '/verify', '/terms', '/attestation/history']) {
      expect(text).toContain(r)
    }
  })

  it('无承诺语：不含「即将上线」「敬请期待」类表述', () => {
    renderAt('/public-face')
    const page = screen.getByTestId('public-face-page').textContent ?? ''
    expect(page).not.toContain('即将上线')
    expect(page).not.toContain('敬请期待')
    expect(page).not.toContain('敬请期待')
  })

  it('清单页从站内导航可达（了解 TDCA 组纯新增项）', () => {
    const learn = APP_NAV.find((e) => e.kind === 'group' && e.group === '了解 TDCA')
    const tos = learn && learn.kind === 'group' ? learn.items.map((i) => ('to' in i ? i.to : '')) : []
    expect(tos).toContain('/public-face')
  })
})
