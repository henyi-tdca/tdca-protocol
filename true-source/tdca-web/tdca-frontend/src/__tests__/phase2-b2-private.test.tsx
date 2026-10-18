// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块三 — 私域页面移植测试
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §二块三
// 覆盖: studio 通道六步实况段渲染 / /process 14 环可达 / /me/appeal 守卫 /
//       登记两页未登录不见操作件（两面分隔：⛔ 不删操作，只包条件渲染）
// =============================================================================
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'

// studio 渲染 TopologyEngine（Cytoscape）——jsdom 无布局环境，stub 布局计算（同 routing.test.tsx）
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

function login() {
  localStorage.setItem('tdca_auth_did', 'TDID-H-0001')
  localStorage.setItem('tdca_auth_token', 'TDCA-CRT-test')
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  localStorage.clear()
  // 登记两页 useEffect 拉取规则/记录——jsdom 无后端，fetch 兜底 fail-closed（保持 null/空表）
  vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response('{}', { status: 502 }))))
})

describe('二期改版批2块三：作业页通道六步实况段（自 tdca-site 移植）', () => {
  it('登录态渲染通道实况段：输入框/查询钮/错误位俱全', () => {
    login()
    renderAt('/studio')
    expect(screen.getByTestId('channel-gate-section')).toBeInTheDocument()
    expect(screen.getByTestId('channel-gate-input')).toBeInTheDocument()
    expect(screen.getByTestId('channel-gate-query')).toBeInTheDocument()
    // UX-PLAIN 整改层 testid 保留（⛔ 移植不覆盖）
    expect(screen.getByTestId('studio-plain-intro')).toBeInTheDocument()
    expect(screen.getByTestId('wizard-plain')).toBeInTheDocument()
  })
})

describe('二期改版批2块三：流程总览 /process（ProcessOverview 移植）', () => {
  it('14 环逐环四能渲染（ring-1 … ring-14）', () => {
    renderAt('/process')
    expect(screen.getByTestId('process-overview')).toBeInTheDocument()
    for (let i = 1; i <= 14; i++) {
      expect(screen.getByTestId(`ring-${i}`)).toBeInTheDocument()
    }
    expect(screen.getAllByText('是什么：').length).toBe(14)
    expect(screen.getAllByText('承办呈现面：').length).toBe(14)
  })
})

describe('二期改版批2块三：申诉端 /me/appeal（薄占位＋登录守卫）', () => {
  it('未登录访问重定向登录页（PROTECTED 集合）', () => {
    renderAt('/me/appeal')
    expect(screen.queryByTestId('me-appeal-placeholder')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /登录（DID）/ })).toBeInTheDocument()
  })

  it('登录态见薄占位（受理面在建，⛔ 不预置受理表单）', () => {
    login()
    renderAt('/me/appeal')
    expect(screen.getByTestId('me-appeal-placeholder')).toBeInTheDocument()
    expect(screen.getAllByText(/受理通道/).length).toBeGreaterThan(0)
  })
})

describe('二期改版批2块三：登记两页两面分隔（未登录只见查询公示面）', () => {
  it('权属登记页：未登录不见登记/变更/注销操作件，见登录门控与查询公示面', () => {
    renderAt('/ownership-registry')
    expect(screen.queryByTestId('or-register')).not.toBeInTheDocument()
    expect(screen.queryByTestId('or-amend')).not.toBeInTheDocument()
    expect(screen.queryByTestId('or-cancel')).not.toBeInTheDocument()
    expect(screen.getByTestId('or-login-gate')).toBeInTheDocument()
    expect(screen.getByTestId('or-query')).toBeInTheDocument()
  })

  it('授权登记页：未登录见公开查（免会话四字段），不见登记/操作/明细查询', () => {
    renderAt('/authorization-registry')
    expect(screen.queryByTestId('ar-register')).not.toBeInTheDocument()
    expect(screen.queryByTestId('ar-operate')).not.toBeInTheDocument()
    expect(screen.queryByTestId('ar-query')).not.toBeInTheDocument()
    expect(screen.getByTestId('ar-login-gate')).toBeInTheDocument()
    expect(screen.getByTestId('ar-public')).toBeInTheDocument()
  })
})

describe('二期改版批2块四：运维分区（ops 管理员门＋评审页）', () => {
  it('运维端：非管理员身份只见管理员门控提示（ACCESS-FIX-001-AMEND-1 交付三）', () => {
    // /ops 非 PROTECTED；jsdom 无后端，/me/dashboard 拉取失败 → 非管理员 → 见门控
    login()
    renderAt('/ops')
    expect(screen.getByTestId('ops-admin-only')).toBeInTheDocument()
    expect(screen.queryByTestId('ops-redlines')).not.toBeInTheDocument()
  })

  it('评审页：未登录重定向登录页（PROTECTED）', () => {
    renderAt('/review')
    expect(screen.queryByTestId('review-gate')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /登录（DID）/ })).toBeInTheDocument()
  })

  it('评审页：登录态见审核门（审核人标识＋写令牌，均只存本次会话）', () => {
    login()
    renderAt('/review')
    expect(screen.getByTestId('review-gate')).toBeInTheDocument()
    expect(screen.getByTestId('review-reviewer')).toBeInTheDocument()
    expect(screen.getByTestId('review-token')).toBeInTheDocument()
    expect(screen.getByTestId('review-enter')).toBeInTheDocument()
  })

  it('评审页：⛔ 不入公共导航（运维分区独立入口）', async () => {
    const { APP_NAV } = await import('@/app/app-shell')
    const all = APP_NAV.flatMap((e) => (e.kind === 'link' ? [{ to: e.to }] : e.items))
    expect(all.some((i) => i.to === '/review')).toBe(false)
  })
})
