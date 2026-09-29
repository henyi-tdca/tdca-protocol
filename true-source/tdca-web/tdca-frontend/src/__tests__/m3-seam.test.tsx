// =============================================================================
// TDCA 制度水印
// FC-ID: KIMI-WEB-DB-TASK-001-M3 | 目标函数: M3 前端接缝测试（会话令牌/401 拦截/草稿兜底）
// 约束矩阵: 裁定②（接缝施工）+ 裁定③（被踢数据不丢、提示明确）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  api, clearDraft, loadDraft, saveDraft, sessionToken, setSessionToken,
  SESSION_EXPIRED_EVENT,
} from '@/api/client'

const mockFetch = vi.fn()

function jsonResponse(body: unknown, ok = true, status = 200) {
  return { ok, status, json: async () => body } as Response
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

describe('M3 前端接缝（F-2）', () => {
  it('持有会话 → Authorization 用 TDCA-SES 令牌（优先于 HUF 静态令牌）', async () => {
    setSessionToken('TDCA-SES-test-abc')
    mockFetch.mockResolvedValue(jsonResponse({ nca_watermark: 'w', data_nature: 'real', data: {} }))
    await api.post('/api/v1/sandbox/apply', {}, { needHuf: true })
    const headers = mockFetch.mock.calls[0][1].headers as Record<string, string>
    expect(headers.Authorization).toBe('TDCA-SES-test-abc')
  })

  it('无会话 + needHuf → 保持 B-4 静态令牌行为（向后兼容）', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ nca_watermark: 'w', data: {} }))
    await api.post('/api/v1/sandbox/apply', {}, { needHuf: true })
    const headers = mockFetch.mock.calls[0][1].headers as Record<string, string>
    expect(headers.Authorization).toBe('TDCA-CRT-demo-2026')
  })

  it('持会话被 401+session_expired → 清令牌 + 广播事件（裁定③：页面状态不动）', async () => {
    setSessionToken('TDCA-SES-old')
    const events: CustomEvent[] = []
    window.addEventListener(SESSION_EXPIRED_EVENT, (ev) => events.push(ev as CustomEvent))
    mockFetch.mockResolvedValue(
      jsonResponse({ error: 'UNAUTHORIZED', session_expired: true, detail: 'expired' }, false, 401),
    )
    const res = await api.post('/api/v1/sandbox/apply', {})
    expect(res.ok).toBe(false)
    if (!res.ok) expect(res.status).toBe(401)
    expect(sessionToken()).toBeNull()
    expect(events).toHaveLength(1)
    expect(sessionStorage.getItem('tdca:session:expired')).not.toBeNull()
  })

  it('未持会话时 401（如登录口令错误）→ 不误触会话失效事件', async () => {
    const events: CustomEvent[] = []
    window.addEventListener(SESSION_EXPIRED_EVENT, (ev) => events.push(ev as CustomEvent))
    mockFetch.mockResolvedValue(jsonResponse({ detail: '用户名或密码错误' }, false, 401))
    const res = await api.post('/api/v1/auth/login', { username: 'x', password: 'y' })
    expect(res.ok).toBe(false)
    expect(events).toHaveLength(0)
  })

  it('草稿兜底：saveDraft / loadDraft / clearDraft 往返', () => {
    saveDraft('/governance', { action: 'ota_upgrade', note: '未提交' })
    expect(loadDraft<{ action: string }>('/governance')?.action).toBe('ota_upgrade')
    clearDraft('/governance')
    expect(loadDraft('/governance')).toBeNull()
  })
})
