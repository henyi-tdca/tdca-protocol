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

async function renderAt(path: string) {
  const __r = render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
  await waitFor(() => { expect(screen.queryByTestId('route-loading')).not.toBeInTheDocument() })
  return __r
}

describe('F-2 /auth 鉴权', () => {
  it('/auth 登录页可达（DID 选择 + token 输入）', async () => {
    await renderAt('/auth')
    expect(screen.getByTestId('auth-form')).toBeInTheDocument()
    expect(screen.getByTestId('auth-role-H')).toHaveAttribute('data-active', 'true')
    expect(screen.getByTestId('auth-token')).toHaveValue('TDCA-CRT-demo-2026')
  })

  it('忘记密码指引（件B0 零后端文案）：登录页可见「联系站点管理员人工重置」口径与管理员邮箱', async () => {
    await renderAt('/auth')
    const hint = screen.getByTestId('auth-forgot-hint')
    expect(hint.textContent).toContain('无自助重置通道')
    expect(hint.textContent).toContain('联系站点管理员人工重置')
    expect(hint.textContent).toContain('xuantan0703@agent.qq.com')
    expect(hint.querySelector('a[href="mailto:xuantan0703@agent.qq.com"]')).toBeTruthy()
  })

  it('受保护路由（/studio）匿名态 → 重定向 /auth 登录引导（LABelfIX-001 项二新口径·覆盖 L1SI188-SITE-NAV-001 旧「直渲」口径）', async () => {
    await renderAt('/studio')
    // 口径更替：TDCA-HANDOFF-EXEC-L1SI223-LABELFIX-001（创始人「三处兜底壳加门」）——/studio 匿名
    // 不再直渲兜底内容，由 RequireAuth 重定向 /auth 登录引导；旧「不重定向、直渲＋权限说明」口径（L1SI188
    // 评估件/SITE-TESTFIX-001 乙组）由本令废止，守卫 fail-closed（未登录/异常一律按匿名挡）。
    expect(screen.getByTestId('auth-form')).toBeInTheDocument()
  })

  it('登录流程：选择身份 + token → 登录 → 受护面可入', async () => {
    const r = await renderAt('/auth')
    fireEvent.click(screen.getByTestId('auth-role-M'))
    expect(screen.getByTestId('auth-did-preview')).toHaveTextContent('TDID-M-0001')
    fireEvent.change(screen.getByTestId('auth-token'), { target: { value: 'TDCA-CRT-USER-1' } })
    fireEvent.click(screen.getByTestId('auth-submit'))
    await waitFor(() => expect(screen.getByTestId('auth-status')).toHaveTextContent('TDID-M-0001'))
    r.unmount()
    const r2 = await renderAt('/studio')
    expect(screen.getByTestId('studio-lifecycle')).toBeInTheDocument()
    r2.unmount()
  })

  it('公开路由（/tax）未登录可直接访问', async () => {
    await renderAt('/tax')
    expect(screen.getByText('税收仪表盘（L3 效用计量）')).toBeInTheDocument()
  })

  it('登出：清除登录态 → 匿名态仍直渲受护面（不重定向，L1SI188-SITE-NAV-001 口径）', async () => {
    const r = await renderAt('/auth')
    fireEvent.click(screen.getByTestId('auth-submit'))
    await waitFor(() => expect(screen.getByTestId('auth-status')).toBeInTheDocument())
    r.unmount()
    // 登录态下 /agents 直渲
    const r1 = await renderAt('/agents')
    expect(screen.getByTestId('agents-cluster')).toBeInTheDocument()
    r1.unmount()
    // 登出
    const r2 = await renderAt('/auth')
    await waitFor(() => expect(screen.getByTestId('auth-logout')).toBeInTheDocument())
    fireEvent.click(screen.getByTestId('auth-logout'))
    await waitFor(() => expect(screen.getByTestId('auth-login-link')).toBeInTheDocument())
    r2.unmount()
    // 重新访问受保护路由 → 匿名态不重定向、直渲内容＋权限说明
    const r3 = await renderAt('/agents')
    expect(screen.getByTestId('agents-cluster')).toBeInTheDocument()
    expect(screen.getByText(/权限：登录 DID(?! \+ HUF)/)).toBeInTheDocument()
    r3.unmount()
  })
})
