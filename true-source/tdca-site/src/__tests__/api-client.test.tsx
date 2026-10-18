// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-A3 统一 API 客户端测试（NCA 水印 / fail-closed / WS / HUF token）
// 约束矩阵: FRAMEWORK-001 §5.1 + ID91（水印）/ ID85（fail-closed）/ ID92（模拟态）/ B-4（HUF token）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, BASE, wsSubscribe, type RawEnvelope } from '@/lib/client'

const mockFetch = vi.fn()

function jsonResponse(body: RawEnvelope, ok = true, status = 200) {
  return { ok, status, json: async () => body } as Response
}

beforeEach(() => {
  mockFetch.mockReset()
  vi.stubGlobal('fetch', mockFetch)
  localStorage.clear()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('F0-A3 统一 API 客户端', () => {
  it('NCA 水印在位 → 成功结果（simulated 标注，ID92）', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ nca_watermark: 'nca-abc', data_nature: 'simulated', data: { ok: 1 } }))
    const res = await api.get<{ ok: number }>('/api/v1/system/overview')
    expect(res.ok).toBe(true)
    if (res.ok) {
      expect(res.watermark).toBe('nca-abc')
      expect(res.nature).toBe('simulated')
      expect(res.data.ok).toBe(1)
    }
  })

  it('NCA 水印缺失 → 拒绝渲染（watermark_missing，ID91）', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ data: { ok: 1 } }))
    const res = await api.get('/api/v1/system/overview')
    expect(res.ok).toBe(false)
    if (!res.ok) expect(res.reason).toBe('watermark_missing')
  })

  it('后端不可用 → fail-closed 降级（不猜测数据，ID85）', async () => {
    mockFetch.mockRejectedValue(new Error('network down'))
    const res = await api.get('/api/v1/system/overview')
    expect(res.ok).toBe(false)
    if (!res.ok) expect(res.reason).toBe('fail_closed')
  })

  it('HTTP 非 2xx → http_error（fail-closed 语义）', async () => {
    mockFetch.mockResolvedValue(jsonResponse({}, false, 503))
    const res = await api.post('/api/v1/config-right/call', {})
    expect(res.ok).toBe(false)
    if (!res.ok) expect(res.reason).toBe('http_error')
  })

  it('needHuf 写操作 → 注入 Authorization: TDCA-CRT-{token}（B-4）', async () => {
    localStorage.setItem('tdca_huf_token', 'TDCA-CRT-TEST-001')
    mockFetch.mockResolvedValue(jsonResponse({ nca_watermark: 'nca-h', data_nature: 'simulated', data: null }))
    await api.post('/api/v1/governance/huf-sign', { op: 'fuse' }, { needHuf: true })
    const [url, init] = mockFetch.mock.calls[0]
    expect(String(url)).toContain(BASE)
    const headers = (init as RequestInit).headers as Record<string, string>
    expect(headers.Authorization).toBe('TDCA-CRT-TEST-001')
  })

  it('非 needHuf 请求不注入 HUF token', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ nca_watermark: 'nca-g', data_nature: 'simulated', data: null }))
    await api.get('/api/v1/tax/mou/AGENT-001')
    const [, init] = mockFetch.mock.calls[0]
    expect((init as RequestInit).headers).not.toMatchObject({ Authorization: expect.anything() })
  })

  it('wsSubscribe 订阅 notifier 通道并返回取消函数', () => {
    class MockWS {
      static instances: MockWS[] = []
      url = ''
      onopen: (() => void) | null = null
      onclose: (() => void) | null = null
      onerror: (() => void) | null = null
      onmessage: ((ev: { data: string }) => void) | null = null
      closed = false
      constructor(url: string) {
        this.url = url
        MockWS.instances.push(this)
      }
      close() {
        this.closed = true
        this.onclose?.()
      }
    }
    vi.stubGlobal('WebSocket', MockWS)
    const onMsg = vi.fn()
    const close = wsSubscribe('notifier', { onMessage: onMsg })
    const inst = MockWS.instances[0]
    expect(inst.url).toContain('/ws/events?channel=notifier')
    inst.onmessage?.({ data: JSON.stringify({ type: 'ping' }) })
    expect(onMsg).toHaveBeenCalledWith({ type: 'ping' })
    close()
    expect(inst.closed).toBe(true)
  })
})
