// 批 4 凭证自证：四令牌明型、账户四分面、授权行权两段要素
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '../App'
import {
  api, setSessionToken, tokenKindOf, TOKEN_TYPE_HEADER,
} from '@/lib/client'

const mockFetch = vi.fn()

function jsonResponse(body: unknown, ok = true, status = 200) {
  return { ok, status, json: async () => body } as Response
}

function renderAt(path: string) {
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

describe('批 4：四令牌明型（工程落法）', () => {
  it('tokenKindOf：值形前缀判型，未知/空返回 null', () => {
    expect(tokenKindOf('TDCA-SES-x')).toBe('access')
    expect(tokenKindOf('TDCA-IDT-x')).toBe('identity')
    expect(tokenKindOf('TDCA-CRT-x')).toBe('execution')
    expect(tokenKindOf('TDCA-AUC-x')).toBe('authcode')
    expect(tokenKindOf('OTHER-x')).toBeNull()
    expect(tokenKindOf(null)).toBeNull()
  })

  it('持会话：Authorization 原值不变，另附类型标记头 access（旧服务端可忽略）', async () => {
    setSessionToken('TDCA-SES-test-abc')
    mockFetch.mockResolvedValue(jsonResponse({ nca_watermark: 'w', data_nature: 'real', data: {} }))
    await api.post('/api/v1/sandbox/apply', {}, { needHuf: true })
    const headers = mockFetch.mock.calls[0][1].headers as Record<string, string>
    expect(headers.Authorization).toBe('TDCA-SES-test-abc')
    expect(headers[TOKEN_TYPE_HEADER]).toBe('access')
  })

  it('无会话 + needHuf：静态写令牌原行为不变，另附类型标记头 execution', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ nca_watermark: 'w', data: {} }))
    await api.post('/api/v1/sandbox/apply', {}, { needHuf: true })
    const headers = mockFetch.mock.calls[0][1].headers as Record<string, string>
    expect(headers.Authorization).toBe('TDCA-CRT-demo-2026')
    expect(headers[TOKEN_TYPE_HEADER]).toBe('execution')
  })

  it('未携令牌请求不附类型标记头', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ nca_watermark: 'w', data: {} }))
    await api.get('/api/v1/open')
    const headers = mockFetch.mock.calls[0][1].headers as Record<string, string>
    expect(headers[TOKEN_TYPE_HEADER]).toBeUndefined()
  })
})

describe('批 4：账户四分面与授权行权两段要素', () => {
  it('/me 追加呈现：四分面齐（账户读写/账户管理/事务执行/资产使用）', () => {
    renderAt('/me')
    expect(screen.getByTestId('cred-quadrants')).toBeInTheDocument()
    expect(screen.getByTestId('quad-access')).toBeInTheDocument()
    expect(screen.getByTestId('quad-identity')).toBeInTheDocument()
    expect(screen.getByTestId('quad-execution')).toBeInTheDocument()
    expect(screen.getByTestId('quad-authcode')).toBeInTheDocument()
  })

  it('待建者如实标：账户管理含「须强核身」「待建」；资产使用含「不等于授权本身」「待建」', () => {
    renderAt('/me')
    expect(screen.getByTestId('quad-identity-note').textContent).toContain('须强核身')
    expect(screen.getByTestId('quad-identity-note').textContent).toContain('待建')
    expect(screen.getByTestId('quad-authcode-note').textContent).toContain('不等于授权本身')
    expect(screen.getByTestId('quad-authcode-note').textContent).toContain('待建')
  })

  it('事务执行面必现「由人类签发」；授权与行权两段要素（谁＋干什么）齐', () => {
    renderAt('/me')
    expect(screen.getByTestId('quad-execution-note').textContent).toContain('由人类签发')
    const panel = screen.getByTestId('authz-action-elements').textContent ?? ''
    expect(panel).toContain('谁')
    expect(panel).toContain('干什么')
    expect(panel).toContain('人类签署')
    expect(panel).toContain('不得代签')
  })

  it('协作流程页：环 7 必现「人类签署」，环 9 必现「人类签发」', () => {
    renderAt('/process')
    expect(screen.getByTestId('ring-7').textContent).toContain('人类签署')
    expect(screen.getByTestId('ring-7').textContent).toContain('不得代签')
    expect(screen.getByTestId('ring-9').textContent).toContain('人类签发')
  })
})
