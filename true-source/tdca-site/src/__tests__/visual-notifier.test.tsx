// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: VISUAL-001 可视化增强测试（/notifier WS 流转，拆自 visual）
// 约束矩阵: TDCA-FRONTEND-VISUAL-001
// 拆搬说明：旧 visual.test.tsx 按场景拆为 5 件，本件为 P2-2 用例（含 MockWS 脚手架），字句未改；
//   页 import 适配新树 named export。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { NotifierPage } from '@/pages/NotifierPage'

// cytoscape 桩（旧 visual.test.tsx 顶层脚手架）：jsdom 无 canvas 2d，
// 新树 NotifierPage 经组件链触达 TopologyEngine 真实引入 cytoscape，须桩化。
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

beforeEach(() => {
  localStorage.clear()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('VISUAL-001 可视化增强 · /notifier', () => {
  it('P2-2 /notifier：坐标变换实时流转（WS 消息驱动）', async () => {
    class MockWS {
      static instances: MockWS[] = []
      url = ''
      onopen: (() => void) | null = null
      onmessage: ((ev: { data: string }) => void) | null = null
      onclose: (() => void) | null = null
      onerror: (() => void) | null = null
      close() {
        this.onclose?.()
      }
      constructor(url: string) {
        this.url = url
        MockWS.instances.push(this)
      }
    }
    vi.stubGlobal('WebSocket', MockWS)
    const r = render(
      <MemoryRouter initialEntries={['/notifier']}>
        <NotifierPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('notifier-transform')).toBeInTheDocument())
    expect(screen.getByTestId('transform-flow-count')).toHaveTextContent('等待 WS 消息')
    const notifierWs = MockWS.instances.find((w) => w.url.includes('channel=notifier'))
    act(() => {
      notifierWs?.onmessage?.({ data: JSON.stringify({ type: 'event' }) })
    })
    await waitFor(() => expect(screen.getByTestId('transform-flow-count')).toHaveTextContent('实时流转 1 次'))
    r.unmount()
  })
})
