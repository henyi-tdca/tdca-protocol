// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 导航-甲补正令（L1SI176-NAV-B1-001）视觉编码与折叠验收
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI176-NAV-B1-001 §一六条硬约束 + §四 V-1~V-5
// =============================================================================
import { render, screen, fireEvent } from '@testing-library/react'
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

describe('导航-甲补正令 §1.5 折叠式（V-4）', () => {
  it('八个栏按钮 aria-expanded 齐全；首屏只展开第一栏「了解 TDCA」', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const buttons = GROUPS.map((g) => screen.getByTestId(`nav-col-btn-${g}`))
    expect(buttons).toHaveLength(8)
    for (const b of buttons) {
      expect(b).toHaveAttribute('aria-expanded')
    }
    expect(screen.getByTestId('nav-col-btn-了解 TDCA')).toHaveAttribute('aria-expanded', 'true')
    for (const g of GROUPS.filter((g) => g !== '了解 TDCA')) {
      expect(screen.getByTestId(`nav-col-btn-${g}`)).toHaveAttribute('aria-expanded', 'false')
    }
    // 首屏展开数 = 1（aria-expanded=true 恰一枚）
    const expanded = buttons.filter((b) => b.getAttribute('aria-expanded') === 'true')
    expect(expanded).toHaveLength(1)
  })

  it('点击栏名可切换展开/收起', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const btn = screen.getByTestId('nav-col-btn-NCA 与透明')
    expect(btn).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(btn)
    expect(btn).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(btn)
    expect(btn).toHaveAttribute('aria-expanded', 'false')
  })

  it('收起栏的项留 DOM（hidden），导航 textContent 完整（旧断言不回归）', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const nav = screen.getByTestId('app-nav')
    // 收起栏「NCA 与透明」的项仍在 DOM（textContent 可核），但不可见
    expect(nav).toHaveTextContent('存证说明')
    const col = screen.getByTestId('nav-col-NCA 与透明')
    expect(col.querySelector('.hidden')).not.toBeNull()
  })
})

describe('导航-甲补正令 §1.1/1.2/1.3/1.4 视觉编码（V-1/V-2/V-3）', () => {
  it('栏与栏分行：每栏独立 w-full 块（任两栏 top 必不等，块级纵排）', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    for (const g of GROUPS) {
      const col = screen.getByTestId(`nav-col-${g}`)
      expect(col.className).toContain('w-full')
    }
  })

  it('三层间距严格递增（项 gap-x-2=8px ＜ 子组 mb-6=24px ＜ 栏 pb-8=32px）且三层左边界两两不等（0/12/24）', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const col4 = screen.getByTestId('nav-col-资产与权利')
    // 栏间距 32px
    expect(col4.className).toContain('pb-8')
    // 子组间距 24px（边界线改画在项块上，包装层只留 mb-6）
    const sub = col4.querySelector('[data-subgroup="所有权"]')
    expect(sub).not.toBeNull()
    expect(sub!.className).toContain('mb-6')
    // 子组标题缩进 12px / 项块缩进 24px ＋ 可见边界 border-l-2
    expect(sub!.firstElementChild!.className).toContain('ml-3')
    const itemsBlock = sub!.querySelector('.ml-6.border-l-2')
    expect(itemsBlock).not.toBeNull()
    const itemsRow = itemsBlock!.firstElementChild
    // 项间距 8px
    expect(itemsRow!.className).toContain('gap-x-2')
  })

  it('子组均有可见边界线（border-l-2），全站统一', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const nav = screen.getByTestId('app-nav')
    const subgroups = nav.querySelectorAll('[data-subgroup]')
    expect(subgroups.length).toBeGreaterThanOrEqual(6) // 栏4×2 ＋ 栏5×2 ＋ 栏6×2
    for (const s of Array.from(subgroups)) {
      expect(s.querySelector('.border-l-2')).not.toBeNull()
    }
  })
})
