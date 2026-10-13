// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F4 通知机状态页测试（A-9 + WS + 确权推送 + 拓扑 + 熔断 HUF）
// 约束矩阵: FRAMEWORK-001 §八 + A-9 契约 + ID93 + F-4/HUF
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { NotifierPage } from '@/pages/NotifierPage'
import App from '@/App'

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

const MRCR_PAYLOAD = {
  roles: [
    { role: 'NM-Operator', tdid: 'TDID-NM-Operator', permissions: ['nm:operate'], status: 'ACTIVE', scene: 'scene-phy-notification', audit_count: 2 },
    { role: 'NM-Gov', tdid: 'TDID-NM-Gov', permissions: ['nm:govern'], status: 'ACTIVE', scene: 'scene-phy-notification', audit_count: 1 },
    { role: 'NM-Fin', tdid: 'TDID-NM-Fin', permissions: ['nm:finance'], status: 'ACTIVE', scene: 'scene-phy-notification', audit_count: 0 },
    { role: 'NM-Med', tdid: 'TDID-NM-Med', permissions: ['nm:mediate'], status: 'ACTIVE', scene: 'scene-phy-notification', audit_count: 0 },
  ],
  engine_tests: '23 + SIL 6 = 29 passed',
  note: '模拟态',
}

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-08-13T00:00:00Z', data_nature: 'simulated' }
}

class MockWS {
  static instances: MockWS[] = []
  url = ''
  onopen: (() => void) | null = null
  onmessage: ((ev: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  closed = false
  constructor(url: string) {
    this.url = url
    MockWS.instances.push(this)
  }
  close() {
    this.closed = true
    this.onclose?.()
  }
}

beforeEach(() => {
  localStorage.clear()
  // F-2 守卫预置登录态（App 级渲染跳转 /attestation/dynamic 需登录）
  localStorage.setItem('tdca_auth_did', 'TDID-H-0001')
  localStorage.setItem('tdca_auth_token', 'TDCA-CRT-test')
  MockWS.instances = []
  vi.stubGlobal('WebSocket', MockWS)
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (!String(url).includes('/api/v1/notifier/mrcr-status')) throw new Error('unexpected url')
    return { ok: true, status: 200, json: async () => envelope(MRCR_PAYLOAD) } as Response
  }))
})
afterEach(() => {
  vi.unstubAllGlobals()
})

function renderNotifier() {
  return render(
    <MemoryRouter initialEntries={['/notifier']}>
      <NotifierPage />
    </MemoryRouter>,
  )
}

describe('F4 通知机状态页 /notifier', () => {
  it('四角色实时状态渲染（A-9）+ DUAL 同构校验', async () => {
    renderNotifier()
    await waitFor(() => expect(screen.getByTestId('notifier-roles-section')).toBeInTheDocument())
    expect(screen.getByText('NM-Operator')).toBeInTheDocument()
    expect(screen.getByText('NM-Med')).toBeInTheDocument()
    expect(screen.getByTestId('dual-ok')).toHaveTextContent('DUAL 同构校验通过')
    expect(screen.getByTestId('notifier-roles')).toBeInTheDocument()
  })

  it('WS 四通道订阅 + notifier 通道消息计数（消息流速率）', async () => {
    renderNotifier()
    await waitFor(() => expect(MockWS.instances.length).toBeGreaterThanOrEqual(4))
    const notifierWs = MockWS.instances.find((w) => w.url.includes('channel=notifier'))
    expect(notifierWs).toBeDefined()
    expect(screen.getByTestId('notifier-msg-count')).toHaveTextContent('0')
    act(() => {
      notifierWs!.onmessage?.({ data: JSON.stringify({ type: 'mou_update' }) })
    })
    await waitFor(() => expect(screen.getByTestId('notifier-msg-count')).toHaveTextContent('1'))
  })

  it('坐标变换可视化拓扑挂载（物理事件 → 数字 NCA）', async () => {
    renderNotifier()
    await waitFor(() => expect(screen.getByTestId('notifier-transform')).toBeInTheDocument())
    expect(screen.getByTestId('notifier-transform')).toHaveTextContent('坐标变换可视化')
  })

  it('确权请求推送入口 → 跳转 /attestation/dynamic', async () => {
    const r = render(
      <MemoryRouter initialEntries={['/notifier']}>
        <App />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('notifier-attest')).toBeInTheDocument())
    expect(screen.getByText('DAR-001')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('notifier-go-attest'))
    await waitFor(() => expect(screen.getByText('动态确权请求队列')).toBeInTheDocument())
    r.unmount()
  })

  it('负空间熔断介入（F-4）：HUF 模态 → 确认后熔断状态', () => {
    renderNotifier()
    fireEvent.click(screen.getByTestId('notifier-fuse-open'))
    expect(screen.getByTestId('huf-modal')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('huf-confirm'))
    expect(screen.getByTestId('notifier-fused')).toHaveTextContent('熔断已触发')
  })
})
