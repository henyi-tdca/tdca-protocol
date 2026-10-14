// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: VISUAL-001 可视化增强测试（/studio 生命周期动画，拆自 visual）
// 约束矩阵: TDCA-FRONTEND-VISUAL-001
// 拆搬说明：旧 visual.test.tsx 按场景拆为 5 件，本件为 P2-1 用例，字句未改；
//   页 import 适配新树 named export。
// =============================================================================
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { StudioPage } from '@/pages/StudioPage'

// cytoscape 桩（旧 visual.test.tsx 顶层脚手架）：jsdom 无 canvas 2d，
// 新树 StudioPage 经组件链触达 TopologyEngine 真实引入 cytoscape，须桩化。
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

describe('VISUAL-001 可视化增强 · /studio', () => {
  it('P2-1 /studio：生命周期时间轴动画容器（lifecycle-anim）', () => {
    const r = render(
      <MemoryRouter initialEntries={['/studio']}>
        <StudioPage />
      </MemoryRouter>,
    )
    expect(r.container.querySelector('.lifecycle-anim')).toBeInTheDocument()
    expect(screen.getByTestId('lifecycle-anim')).toBeInTheDocument()
    expect(screen.getAllByTestId(/^node-/).length).toBeGreaterThan(0)
  })
})
