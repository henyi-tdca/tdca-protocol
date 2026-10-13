// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-M4REG-002 | 目标函数: 注册缔约门禁测试（REGISTER-002 缺口②修复，GSEQ-0671）
// 约束矩阵: 未勾选协议 → 提交按钮禁用 + 就地提示 + 零网络请求（fail-closed 前置拦截）
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

const mockFetch = vi.fn()

function jsonResponse(body: unknown, ok = true, status = 200) {
  return { ok, status, json: async () => body } as Response
}

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  mockFetch.mockReset()
  vi.stubGlobal('fetch', mockFetch)
})
afterEach(() => {
  vi.unstubAllGlobals()
})

function renderRegister() {
  return render(
    <MemoryRouter initialEntries={['/register']}>
      <App />
    </MemoryRouter>,
  )
}

describe('M4 注册缔约门禁（REGISTER-002 缺口②）', () => {
  it('未勾选协议 → 按钮禁用 + 就地提示 + 零网络请求', () => {
    renderRegister()
    const btn = screen.getByTestId('register-submit')
    expect(btn).toBeDisabled()
    expect(screen.getByTestId('register-agree-hint')).toBeInTheDocument()
    fireEvent.click(btn)
    expect(mockFetch).not.toHaveBeenCalled() // 未缔约不得发出任何注册请求
  })

  it('勾选协议后按钮启用 → 提交携带 agree_contract + contract_version', async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({
        nca_watermark: 'NCA-TEST',
        data_nature: 'real',
        data: { token: 'TDCA-SES-test', role: 'viewer', nca_id: 'NCA-WEB-test' },
      }),
    )
    renderRegister()
    fireEvent.click(screen.getByTestId('register-agree'))
    const btn = screen.getByTestId('register-submit')
    expect(btn).not.toBeDisabled()
    expect(screen.queryByTestId('register-agree-hint')).not.toBeInTheDocument()
    fireEvent.change(screen.getByTestId('register-username'), { target: { value: 'gate-t01' } })
    fireEvent.change(screen.getByTestId('register-password'), { target: { value: 'Passw0rd!2026' } })
    fireEvent.change(screen.getByTestId('register-confirm'), { target: { value: 'Passw0rd!2026' } })
    fireEvent.click(btn)
    await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/api/v1/auth/register')
    const body = JSON.parse(init.body as string)
    expect(body.agree_contract).toBe(true)
    expect(body.contract_version).toBe('V1.0')
    expect(body.username).toBe('gate-t01')
  })
})
