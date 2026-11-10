// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-A5 模拟态标注测试（ID92）
// 约束矩阵: ID92 + FRAMEWORK-001 §5.1
// =============================================================================
import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'
import { SimulatedBadge } from '@/lib/SimulatedBadge'
import { PageShell } from '@/components/PageShell'

describe('F0-A5 模拟态标注（ID92）', () => {
  it('SimulatedBadge：simulated → 显示角标；real → 不渲染', () => {
    const r1 = render(<SimulatedBadge nature="simulated" />)
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('SIMULATED')
    r1.unmount()
    render(<SimulatedBadge nature="real" />)
    expect(screen.queryByTestId('simulated-badge')).not.toBeInTheDocument()
  })

  it('页面占位壳默认全站模拟态标注', () => {
    render(<PageShell title="税收" dataSource="A-2" permission="公开" description="d" />)
    expect(screen.getByTestId('simulated-badge')).toBeInTheDocument()
  })

  it('模拟态标注随件呈现：模拟面经 App 渲染带 SIMULATED 角标（旧「全站顶部横幅」已随壳改撤，ID92 标注下沉为 SimulatedBadge 逐件呈现）', async () => {
    render(
      <MemoryRouter initialEntries={['/studio']}>
        <App />
      </MemoryRouter>,
    )
    // FRONTEND-PERF-001：路由级分包后页面懒加载——冲刷 Suspense 兜底再断言
    await waitFor(() => { expect(screen.queryByTestId('route-loading')).not.toBeInTheDocument() })
    // /studio 化合衍生与通道实况两节各带一枚角标——断言「至少一枚 SIMULATED」
    const badges = screen.getAllByTestId('simulated-badge')
    expect(badges.length).toBeGreaterThan(0)
    expect(badges[0]).toHaveTextContent('SIMULATED')
  })
})

// App 级渲染可能经 TopologyEngine（Cytoscape）——jsdom 无布局环境，stub 布局计算
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