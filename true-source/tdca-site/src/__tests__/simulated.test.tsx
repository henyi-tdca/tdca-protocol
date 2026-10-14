// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-A5 模拟态标注测试（ID92）
// 约束矩阵: ID92 + FRAMEWORK-001 §5.1
// =============================================================================
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
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

  it('应用壳顶部全站模拟态横幅', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByText(/全站模拟态 data_nature=simulated/)).toBeInTheDocument()
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