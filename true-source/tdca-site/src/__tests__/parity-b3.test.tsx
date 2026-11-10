// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 追平批B3（L1SI206-PARITY-B3）验证
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-PARITY-B3-001 §四验收——
//   ① 逐项可点（受护/私域/公开三档）② 题名净名 ③ 索引三产物机算自洽
//   ④ 三问向导悬空链接接通实测（点击可达，⛔ 404）＋必载「真实性由你本人负责」
//   ⑤ /five-orders 导轨补挂后页内可见＋过期注记已更替
//   ⑥ 授权面板受护：匿名重定向 /auth；本人登录态可达
//   ⑦ 右栏助手：testid 照旧（assistant-msgs/assistant-input/assistant-send）、
//     可收展、常驻流内⛔遮挡；「代办登记」直达项保留
//   ⑧ /ops/me 六栏只读；私域/受护面 ⛔ 入公域栏目索引
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'
import { PAGE_META, ROUTE_PATHS } from '@/pages/PagesIndex'

// 路由级实测走整 App（AuthProvider＋SiteLayout 俱在）；fetch/api 不外呼
beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals(); window.history.pushState({}, '', '/') })

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('追平批B3：/start/three-questions 三问向导（悬空链接接通实测）', () => {
  it('/start 点「先做三问」→ 落在三问向导（⛔ 404）', async () => {
    renderAt('/start')
    const link = await screen.findByTestId('start-link-threeq')
    expect(link.getAttribute('href')).toBe('/start/three-questions')
    fireEvent.click(link)
    await waitFor(() => expect(screen.getByTestId('threeq-page')).toBeTruthy())
    // 红线必载：真实性由本人负责；⛔ 代判
    expect(screen.getByTestId('threeq-duty').textContent).toContain('真实性由你本人负责')
    expect(screen.getByTestId('threeq-wizard')).toBeTruthy()
  })

  it('直达路由可渲染（匿名公开面）', async () => {
    renderAt('/start/three-questions')
    await waitFor(() => expect(screen.getByTestId('threeq-page')).toBeTruthy())
  })
})

describe('追平批B3：/five-orders 导轨补挂（主链第二环）', () => {
  it('页内 MainChainGuide 可见（补挂后实测）', async () => {
    renderAt('/five-orders')
    await waitFor(() => expect(screen.getByTestId('main-chain-guide')).toBeTruthy())
    expect(screen.getByTestId('assets-page')).toBeTruthy()
  })
})

describe('追平批B3：/authorization/panel 授权配置面板（受护页）', () => {
  it('匿名态重定向 /auth（令面「未登录重定向 /auth」）', async () => {
    renderAt('/authorization/panel')
    await waitFor(() => expect(screen.getByTestId('auth-account-form')).toBeTruthy())
    expect(screen.queryByTestId('authorization-panel')).toBeNull()
  })

  it('本人登录态可达：五操作＋四要件在架', async () => {
    localStorage.setItem('tdca_auth_did', 'did:tdca:test')
    localStorage.setItem('tdca_auth_token', 'tk')
    renderAt('/authorization/panel')
    await waitFor(() => expect(screen.getByTestId('authorization-panel')).toBeTruthy())
    for (const op of ['预收权', '实时授权', '追加授权', '许可变更', '多层级授权']) {
      expect(screen.getByText(op)).toBeTruthy()
    }
  })
})

describe('追平批B3：右栏「我的＋AI 助手」（可收展·testid 照旧）', () => {
  it('助手三件 testid 照旧＋「代办登记」直达项保留', async () => {
    renderAt('/')
    await waitFor(() => expect(screen.getByTestId('assistant-panel')).toBeTruthy())
    expect(screen.getByTestId('assistant-msgs')).toBeTruthy()
    expect(screen.getByTestId('assistant-input')).toBeTruthy()
    expect(screen.getByTestId('assistant-send')).toBeTruthy()
    // 私域导航保留「代办登记」（U-2 直达项）
    expect(screen.getByTestId('me-private-nav').textContent).toContain('代办登记')
  })

  it('收展开关：收起后助手面板退出渲染（⛔ 遮挡正文——常驻流内）', async () => {
    renderAt('/')
    await waitFor(() => expect(screen.getByTestId('assistant-panel')).toBeTruthy())
    fireEvent.click(screen.getByTestId('right-rail-toggle'))
    await waitFor(() => expect(screen.queryByTestId('assistant-panel')).toBeNull())
  })
})

describe('追平批B3：/ops/me 运维我的（六栏只读）', () => {
  it('六栏只读占位渲染（⛔ 凭据）', async () => {
    renderAt('/ops/me')
    await waitFor(() => expect(screen.getByTestId('ops-me-page')).toBeTruthy())
    const page = screen.getByTestId('ops-me-page')
    expect(page.textContent).toContain('建设中')
  })
})

describe('追平批B3：站点地图入册（34→35，私域/受护 ⛔ 入册）', () => {
  it('三问向导入册（净名）；受护/私域两面 ⛔ 入册', () => {
    expect(PAGE_META).toHaveLength(38) /* 追平批B4：+1（/verify） */ /* SMALL2-001：+2（/me/compile /me/privacy 入册） */
    expect(PAGE_META.find((m) => m.path === '/start/three-questions')?.title).toBe('三问向导 · 贡献前自述')
    expect(ROUTE_PATHS).toContain('/start/three-questions')
    expect(ROUTE_PATHS).not.toContain('/authorization/panel')
    expect(ROUTE_PATHS).not.toContain('/ops/me')
  })
})

// jsdom 无 canvas：Ω 区打桩（照旧例；全 App 渲染过首页 Ω）
vi.mock('@/lib/TopologyEngine', () => ({
  TopologyEngine: () => null,
  hashAgentId: (id: string) => 'hash-' + id,
}))
