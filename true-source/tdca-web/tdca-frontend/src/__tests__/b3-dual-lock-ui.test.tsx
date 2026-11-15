// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-B3-001 | 目标函数: 批3 界面两处明示（L1SI214-TOKEN-B3-001 E-1/E-2）
// 约束矩阵: E-1 授权类动作前一行明示「将产生授权件（法律性文件），须本人签名」（⛔默认勾选）；
//   E-2 第 2 把拒绝（NO_CONFIG_RIGHT）时显示钥匙来源「这项配置权应由该资产的所有者授予」
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

// api 客户端打桩（同 channel-my 等既有件范式）：get 回公开视图，post 回签署拒绝
const PUB = {
  auth_id: 'AP-b3test0001', operation: 'activate', operation_label: '实时授权',
  status: 'pending_sign', subject: '配置权委托 OR-b3pub', scope: '沙盒',
  term: '至撤回为止', conditions: {}, nca_seq: 'NCA-X',
  note: '公开面仅回范围与期限与状态',
}
let signResp: { ok: boolean; data?: unknown; detail?: string } = { ok: true, data: {} }

vi.mock('@/api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/client')>()
  return {
    ...actual,
    api: {
      get: vi.fn(async (path: string) => {
        if (path.includes('/authorization/AP-b3test0001')) return { ok: true, data: PUB }
        return { ok: true, data: {} }
      }),
      post: vi.fn(async (path: string) => {
        if (path.includes('/authorization/sign')) return signResp
        return { ok: true, data: {} }
      }),
    },
  }
})

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  // 受护页须登录态：AuthProvider 以两键判 isAuthenticated
  localStorage.setItem('tdca_auth_did', 'did-b3test')
  localStorage.setItem('tdca_auth_token', 'TDCA-SES-b3test')
  // 本地种一件 pending_sign，使「本人签署」按钮出现
  localStorage.setItem('tdca_auth_panel_my_ids', JSON.stringify(['AP-b3test0001']))
  signResp = { ok: true, data: {} }
})
afterEach(() => {
  vi.clearAllMocks()
})

function renderPanel() {
  return render(
    <MemoryRouter initialEntries={['/authorization/panel']}>
      <App />
    </MemoryRouter>,
  )
}

describe('批3 界面两处明示（E-1／E-2）', () => {
  it('E-1：授权类动作前显示「将产生授权件·须本人签名」一行明示', async () => {
    renderPanel()
    const notice = await screen.findByTestId('e1-sign-notice')
    expect(notice.textContent).toContain('此操作将生成一份授权件（法律性文件），须本人签名')
    // ⛔ 默认勾选「我已阅读」：全页不得存在默认勾选项
    expect(screen.queryByText(/我已阅读/)).toBeNull()
  })

  it('E-2：签署遇 NO_CONFIG_RIGHT 时显示钥匙来源提示（该找所有者）', async () => {
    signResp = {
      ok: false,
      detail: 'NO_CONFIG_RIGHT：你对该项资产无配置权——须由该资产的所有者授予',
    }
    renderPanel()
    await screen.findByTestId('e1-sign-notice')
    const btn = (await screen.findAllByText('本人签署'))[0]
    fireEvent.click(btn)
    await waitFor(() => {
      expect(screen.getByTestId('e2-key-source').textContent)
        .toContain('这项配置权应由该资产的所有者授予')
    })
  })
})
