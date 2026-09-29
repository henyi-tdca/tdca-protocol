// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F3 Agent Studio 测试（生命周期/向导五步/化合/HUF）
// 约束矩阵: FRAMEWORK-001 §七 + §8B.2 + ID91 + F-4/HUF
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
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

beforeEach(() => {
  localStorage.clear()
  // F-2 守卫预置登录态（/studio 为受保护路由，App 级渲染需登录）
  localStorage.setItem('tdca_auth_did', 'TDID-H-0001')
  localStorage.setItem('tdca_auth_token', 'TDCA-CRT-test')
  vi.stubGlobal('fetch', vi.fn(async () => {
    throw new Error('network down') // Studio 无后端依赖（模拟态），fail-closed 路径不阻塞页面
  }))
})
afterEach(() => {
  vi.unstubAllGlobals()
})

function renderStudio() {
  return render(
    <MemoryRouter initialEntries={['/studio']}>
      <App />
    </MemoryRouter>,
  )
}

describe('F3 Agent Studio /studio', () => {
  it('页面可达：生命周期看板 / 创建向导 / 化合衍生三区域渲染', () => {
    renderStudio()
    expect(screen.getByTestId('studio-lifecycle')).toBeInTheDocument()
    expect(screen.getByTestId('studio-wizard')).toBeInTheDocument()
    expect(screen.getByTestId('studio-compound')).toBeInTheDocument()
    expect(screen.getByText('生命周期看板 · TDID-AGENT-007')).toBeInTheDocument()
  })

  it('生命周期六阶段可导航（点击节点 → 详情更新）', () => {
    renderStudio()
    fireEvent.click(screen.getByTestId('node-MARKET'))
    expect(screen.getByTestId('detail-panel')).toHaveTextContent('市场')
    expect(screen.getByTestId('detail-panel')).toHaveTextContent('mou:')
  })

  it('创建向导五步推进 → 终点 HUF 签署（写操作模态）', () => {
    renderStudio()
    for (let i = 0; i < 4; i++) fireEvent.click(screen.getByTestId('wizard-next'))
    expect(screen.getByTestId('wizard-huf')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('wizard-huf'))
    expect(screen.getByTestId('huf-modal')).toBeInTheDocument()
  })

  it('创建向导终点确认 → 跳转 /attestation/meta（出盒终裁）', () => {
    renderStudio()
    for (let i = 0; i < 4; i++) fireEvent.click(screen.getByTestId('wizard-next'))
    fireEvent.click(screen.getByTestId('wizard-huf'))
    fireEvent.click(screen.getByTestId('huf-confirm'))
    expect(screen.getByText('元函数初始确权（出盒终裁）')).toBeInTheDocument()
  })

  it('生命周期写操作（重塑/休眠/激活/注销）全部触发 HUF 模态', () => {
    const LABELS: Record<string, string> = { remodel: '重塑', sleep: '休眠', activate: '激活', logout: '注销' }
    renderStudio()
    for (const key of ['remodel', 'sleep', 'activate', 'logout']) {
      fireEvent.click(screen.getByTestId(`life-action-${key}`))
      expect(screen.getByTestId('huf-modal')).toHaveTextContent(LABELS[key])
      fireEvent.click(screen.getByTestId('huf-cancel'))
    }
  })

  it('化合衍生拓扑挂载（ID91 NCA 链继承可视化）', () => {
    renderStudio()
    expect(screen.getByTestId('studio-compound')).toHaveTextContent('化合衍生（ID91')
  })
})
