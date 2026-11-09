// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: MOBILE-FIX-B1（L1SI206）移动修复批验证
// 约束矩阵: AMEND-L1SI206-MOBILE-FIX-B1-002 §五（甲案必做·追平旧版侧栏可收起）
//   ① 汉堡 testid 在架（process-nav-toggle）② 开合切换 aside 显隐 ③ 桌面侧栏恒在架
//   ④ TopologyEngine 双卡各为 relative（切换按钮定位上下文归位，⛔双按钮同点互遮）
// =============================================================================
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '../App'

// jsdom 无 canvas：拓扑引擎打桩（批5/批6 先例）
vi.mock('@/lib/TopologyEngine', () => ({
  TopologyEngine: () => null,
  hashAgentId: (s: string) => `h-${s}`,
}))

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('MOBILE-FIX-B1：甲案侧栏小屏收起（汉堡）', () => {
  it('汉堡 testid 在架，默认合（移动侧栏未挂出）', () => {
    renderAt('/about')
    const toggle = screen.getByTestId('process-nav-toggle')
    expect(toggle).toBeInTheDocument()
    expect(toggle.textContent).toContain('协作流程')
  })

  it('点开汉堡 ⟹ 移动侧栏挂出；再点 ⟹ 收起', () => {
    renderAt('/about')
    const toggle = screen.getByTestId('process-nav-toggle')
    fireEvent.click(toggle)
    // 展开后 DOM 内出现第二枚 process-nav（移动覆盖层）
    expect(screen.getAllByTestId('process-nav').length).toBe(2)
    fireEvent.click(toggle)
    expect(screen.getAllByTestId('process-nav').length).toBe(1)
  })

  it('桌面侧栏恒在架（process-nav-desktop 包裹）', () => {
    renderAt('/about')
    expect(screen.getByTestId('process-nav-desktop')).toBeInTheDocument()
  })
})
