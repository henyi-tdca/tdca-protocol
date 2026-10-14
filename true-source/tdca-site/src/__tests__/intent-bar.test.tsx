// =============================================================================
// TDCA 制度水印
// FC-ID: KIMI-WEB-DB-TASK-001-M4 | 目标函数: 全局意图导航条测试（输入 → 下拉指引 → 直达跳转）
// 约束矩阵: 创始人 2026-08-21 04:12 指令；fail-soft（后端不可用不弹窗）
// =============================================================================
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'

const mockFetch = vi.fn()

function renderApp(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  mockFetch.mockReset()
  vi.stubGlobal('fetch', mockFetch)
  localStorage.clear()
  sessionStorage.clear()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('M4 全局意图导航条', () => {
  it('顶栏在位（各页面均有入口）', () => {
    const r = renderApp('/tax')
    expect(screen.getByTestId('intent-bar')).toBeInTheDocument()
    r.unmount()
  })

  it('输入「我要签批」→ 下拉指引 → 直达跳转 /attestation/dynamic', async () => {
    // 按 URL 路由：仅意图端点返回数据，其余走 fail-closed（首页等页面的既有降级路径）
    mockFetch.mockImplementation((url: unknown) => {
      if (String(url).includes('/api/v1/intent')) {
        return Promise.resolve({
          ok: true, status: 200,
          json: async () => ({
            nca_watermark: 'w', data_nature: 'real',
            data: {
              matched: true, route: '/attestation/dynamic', title: '动态确权审批',
              action: '签批', guide: ['查看队列', 'HUF 签署'], alternatives: [],
            },
          }),
        } as Response)
      }
      return Promise.reject(new Error('offline'))
    })
    const r = renderApp('/')
    fireEvent.change(screen.getByTestId('intent-input'), { target: { value: '我要签批' } })
    fireEvent.click(screen.getByTestId('intent-go'))
    await waitFor(() => expect(screen.getByTestId('intent-result')).toBeInTheDocument())
    expect(screen.getByTestId('intent-result')).toHaveTextContent('动态确权审批')
    expect(screen.getByTestId('intent-result')).toHaveTextContent('HUF 签署')
    fireEvent.click(screen.getByTestId('intent-jump'))
    await waitFor(() =>
      expect(screen.queryByTestId('intent-result')).not.toBeInTheDocument())
    r.unmount()
  })

  it('后端不可用 → fail-soft（不弹结果、不猜测路由）', async () => {
    mockFetch.mockRejectedValue(new Error('down'))
    const r = renderApp('/')
    fireEvent.change(screen.getByTestId('intent-input'), { target: { value: '查税收' } })
    fireEvent.click(screen.getByTestId('intent-go'))
    await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    expect(screen.queryByTestId('intent-result')).not.toBeInTheDocument()
    r.unmount()
  })
})
