// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 导航 PC 端横排（L1SI178-NAV-PC-HORZ-001）形态守护
// 约束矩阵: 创始人 2026-10-28「回滚到以前的横排版」指示（NAV-A 横排同构，乙案折叠面板不采用）；
//          移动端（<768px）☰ 竖版 toggle 为 10-27 已验收形态，⛔ 本令不动
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect, vi } from 'vitest'
import { APP_NAV } from '@/app/app-shell'
import App from '@/App'

// /agents 渲染 TopologyEngine（Cytoscape）——jsdom 无布局环境，stub 布局计算
vi.mock('cytoscape', () => {
  const fakeNode = () => ({ position: () => ({ x: 10, y: 10 }), id: () => 'n' })
  const fakeCore = {
    nodes: () => [fakeNode()],
    elements: () => ({
      boundingBox: () => ({ x1: 0, y1: 0, x2: 100, y2: 100 }),
      nodes: () => [fakeNode()],
    }),
    ready: (cb: () => void) => cb(),
    destroy: () => {},
  }
  return { default: () => fakeCore }
})

const GROUPS = APP_NAV.filter((e) => e.kind === 'group').map((e) => (e.kind === 'group' ? e.group : ''))

describe('导航 PC 横排（L1SI178-NAV-PC-HORZ-001）', () => {
  it('九栏行内横排：桌面容器 flex-wrap，八栏 testid 齐全，栏名灰色小标签', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const nav = screen.getByTestId('app-nav')
    const desktop = nav.querySelector('.md\\:flex')
    expect(desktop).not.toBeNull()
    expect(desktop!.className).toContain('flex-wrap')
    // ⛔ 不回到纵排折叠：桌面段不得再出现 flex-col 容器
    expect(desktop!.className).not.toContain('flex-col')
    for (const g of GROUPS) {
      const col = screen.getByTestId(`nav-col-${g}`)
      expect(col.className).toContain('flex-wrap')
      expect(col.firstElementChild!.className).toContain('text-gray-400')
    }
  })

  it('全部直链常显（无折叠）：桌面段无 aria-expanded 按钮，各栏子项 textContent 完整可见', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const nav = screen.getByTestId('app-nav')
    const desktop = nav.querySelector('.md\\:flex')!
    // 折叠态退役：桌面段不得再出现 aria-expanded（移动端 ☰ toggle 的 aria-expanded 不在桌面段）
    expect(desktop.querySelector('[aria-expanded]')).toBeNull()
    // 逐项常显（旧折叠版收起时不可见的项，横排版必须直接在 textContent 中）
    expect(nav).toHaveTextContent('存证说明')
    expect(nav).toHaveTextContent('确权中心')
    expect(nav).toHaveTextContent('工具货架')
    expect(nav).toHaveTextContent('商学院')
    expect(nav).toHaveTextContent('身份与账户')
    expect(nav).toHaveTextContent('机器可读规格')
  })

  it('子组「·」前缀横排：data-subgroup 横排容器（flex flex-wrap）且前缀可见', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const nav = screen.getByTestId('app-nav')
    const desktop = nav.querySelector('.md\\:flex')!
    const subgroups = desktop.querySelectorAll('[data-subgroup]')
    expect(subgroups.length).toBeGreaterThanOrEqual(6) // 资产×2 ＋ 主体×2 ＋ 服务×2
    for (const s of Array.from(subgroups)) {
      expect(s.className).toContain('flex-wrap')
      expect(s.firstElementChild!.textContent).toMatch(/^· /)
    }
  })

  it('authOnly 口径不变：匿名态隐藏「术语检索」', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const nav = screen.getByTestId('app-nav')
    expect(nav).not.toHaveTextContent('术语检索')
  })

  it('移动端 ☰ 竖版未动：toggle 在，默认收起（aria-expanded=false）', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const toggle = screen.getByTestId('nav-mobile-toggle')
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(toggle).toHaveTextContent('☰ 站点导航')
  })
})
