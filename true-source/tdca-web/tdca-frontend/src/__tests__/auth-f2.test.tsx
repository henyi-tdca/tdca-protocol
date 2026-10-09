// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-F2-001 | 目标函数: F-2 鉴权测试（登录流程 + 路由守卫 + 登出）
// 约束矩阵: FRAMEWORK-001 §四（权限表）+ B-4
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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
  vi.stubGlobal('fetch', vi.fn(async () => {
    throw new Error('network down') // 公开页不依赖后端（fail-closed 路径不阻塞断言）
  }))
})
afterEach(() => {
  vi.unstubAllGlobals()
})

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('F-2 /auth 鉴权', () => {
  it('/auth 登录页可达（DID 选择 + token 输入）', () => {
    renderAt('/auth')
    expect(screen.getByTestId('auth-form')).toBeInTheDocument()
    expect(screen.getByTestId('auth-role-H')).toHaveAttribute('data-active', 'true')
    expect(screen.getByTestId('auth-token')).toHaveValue('TDCA-CRT-demo-2026')
  })

  it('忘记密码指引（件B0 零后端文案）：登录页可见「联系站点管理员人工重置」口径', () => {
    renderAt('/auth')
    const hint = screen.getByTestId('auth-forgot-hint')
    expect(hint.textContent).toContain('无自助重置通道')
    expect(hint.textContent).toContain('联系站点管理员人工重置')
  })

  it('受保护路由（/studio）未登录 → 重定向 /auth', () => {
    renderAt('/studio')
    expect(screen.getByTestId('auth-login-link')).toBeInTheDocument()
    expect(screen.getByTestId('auth-form')).toBeInTheDocument()
  })

  it('登录流程：选择身份 + token → 登录 → 回跳来源路由', async () => {
    const r = renderAt('/studio')
    expect(screen.getByTestId('auth-form')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('auth-role-M'))
    expect(screen.getByTestId('auth-did-preview')).toHaveTextContent('TDID-M-0001')
    fireEvent.change(screen.getByTestId('auth-token'), { target: { value: 'TDCA-CRT-USER-1' } })
    fireEvent.click(screen.getByTestId('auth-submit'))
    await waitFor(() => expect(screen.getByTestId('studio-lifecycle')).toBeInTheDocument())
    expect(screen.getByTestId('auth-status')).toHaveTextContent('TDID-M-0001')
    r.unmount()
  })

  it('公开路由（/tax）未登录可直接访问', () => {
    renderAt('/tax')
    expect(screen.getByText('税收仪表盘（L3 效用计量）')).toBeInTheDocument()
  })

  it('登出：清除登录态 → 受保护路由再次重定向', async () => {
    const r = renderAt('/agents')
    await waitFor(() => expect(screen.getByTestId('auth-form')).toBeInTheDocument())
    // 登录
    fireEvent.click(screen.getByTestId('auth-submit'))
    await waitFor(() => expect(screen.getByTestId('agents-cluster')).toBeInTheDocument())
    // 登出
    fireEvent.click(screen.getByTestId('auth-logout'))
    await waitFor(() => expect(screen.getByTestId('auth-login-link')).toBeInTheDocument())
    r.unmount()
    // 重新访问受保护路由 → 重定向
    const r2 = renderAt('/agents')
    await waitFor(() => expect(screen.getByTestId('auth-form')).toBeInTheDocument())
    r2.unmount()
  })
})
