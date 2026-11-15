// =============================================================================
// TDCA 制度水印
// FC-ID: L1SI214-ACCOUNT-CONSOLE-001-A | 目标函数: 我的令牌（TokensCard）前端测试
// 约束矩阵: A 块八列清单＋三态视觉＋吊销二次确认＋就地置 revoked＋幂等＋空态（U-1/U-2/U-5）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { MePage } from '@/pages/MeConsole'
import { AuthProvider } from '@/lib/auth-context'

function envelope(payload: unknown, nature = 'real') {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-10-09T00:00:00Z', data_nature: nature }
}

const ME_PAYLOAD = {
  session: { username: 'tester', role: 'viewer', expires_at: '2026-10-09T13:30:00+00:00' },
  pending_count: 0,
  my_agents: [],
  my_pending_sign: [],
  my_decided: [],
  my_sandbox: [],
  my_governance: [],
  my_assets: [],
  my_grants: [],
  my_ownership: [],
  my_config_records: [],
  my_points: { balance: 0, data_provenance: 'simulated', note: 't' },
  my_nca: [],
  note: 'test',
}

const TOKENS_PAYLOAD = {
  tokens: [
    { id: '160b****', kind: 'session', issued_at: '2026-11-15T01:00:00+00:00',
      expires_at: '2026-11-15T03:00:00+00:00', last_used_at: null,
      status: 'active', bound_agents: [], note: null },
    { id: '9f2e****', kind: 'session', issued_at: '2026-11-10T01:00:00+00:00',
      expires_at: '2026-11-10T03:00:00+00:00', last_used_at: null,
      status: 'expired', bound_agents: [], note: null },
    { id: '77aa****', kind: 'session', issued_at: '2026-11-01T01:00:00+00:00',
      expires_at: '2026-11-01T03:00:00+00:00', last_used_at: null,
      status: 'revoked', bound_agents: ['wb-agent-02'], note: '早前吊销' },
  ],
  count: 3,
  scope: 'self',
}

function mockRoutes(routes: Record<string, unknown>) {
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    for (const [part, payload] of Object.entries(routes)) {
      if (url.includes(part)) {
        if (init?.method === 'DELETE') {
          return { ok: true, status: 200,
            json: async () => envelope({ id: '160b****', result: 'revoked', revoked_count: 1, scope: 'self' }),
          } as Response
        }
        return { ok: true, status: 200, json: async () => envelope(payload) } as Response
      }
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
  }))
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('ACCOUNT-CONSOLE A 块：我的令牌（TokensCard）', () => {
  it('U-1：令牌列表八列渲染，生效行每行有吊销按钮', async () => {
    mockRoutes({ '/api/v1/me/tokens': TOKENS_PAYLOAD, '/api/v1/me/dashboard': ME_PAYLOAD })
    render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-tokens-table')).toBeTruthy())
    const table = screen.getByTestId('me-tokens-table')
    for (const h of ['编号', '类型', '签发时间', '到期时间', '最近使用', '状态', '绑定智能体', '备注', '操作']) {
      expect(table.textContent).toContain(h)
    }
    expect(table.textContent).toContain('160b****')
    // 生效行有吊销按钮；过期/吊销行无吊销按钮
    expect(screen.getByTestId('me-token-revoke-160b****')).toBeTruthy()
    expect(table.textContent).toContain('生效中')
    expect(table.textContent).toContain('已过期')
    expect(table.textContent).toContain('已吊销')
  })

  it('U-2：吊销走二次确认，成功后该行就地变 revoked', async () => {
    mockRoutes({ '/api/v1/me/tokens': TOKENS_PAYLOAD, '/api/v1/me/dashboard': ME_PAYLOAD })
    const fetchMock = vi.mocked(fetch)
    render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-token-revoke-160b****')).toBeTruthy())
    fireEvent.click(screen.getByTestId('me-token-revoke-160b****'))
    // 二次确认文案在确认前出现
    expect(screen.getByText('吊销后立即失效，不可恢复')).toBeTruthy()
    fireEvent.click(screen.getByTestId('me-token-confirm-160b****'))
    await waitFor(() => expect(screen.getByTestId('me-tokens-hint').textContent).toContain('已吊销'))
    // DELETE 打到了 /me/tokens/{脱敏id}
    const calls = fetchMock.mock.calls
    const del = calls.find((c) => String(c[0]).includes('/api/v1/me/tokens/160b****') && (c[1]?.method === 'DELETE'))
    expect(del).toBeTruthy()
    // 该行就地变 revoked：data-status 变 revoked、出现「已吊销」、不再有吊销按钮
    const row = document.querySelector('[data-status="revoked"]')
    expect(row).toBeTruthy()
    expect(row?.textContent).toContain('已吊销')
    expect(screen.queryByTestId('me-token-revoke-160b****')).toBeNull()
  })

  it('U-5：页面不出现令牌原值形态（TDCA-SES 前缀串）', async () => {
    mockRoutes({ '/api/v1/me/tokens': TOKENS_PAYLOAD, '/api/v1/me/dashboard': ME_PAYLOAD })
    const { container } = render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-tokens-table')).toBeTruthy())
    expect(container.textContent).not.toContain('TDCA-SES-')
  })

  it('空态：无令牌写明「当前无令牌」（⛔空白）', async () => {
    mockRoutes({ '/api/v1/me/tokens': { tokens: [], count: 0, scope: 'self' },
      '/api/v1/me/dashboard': ME_PAYLOAD })
    render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-tokens-empty')).toBeTruthy())
    expect(screen.getByTestId('me-tokens-empty').textContent).toContain('当前无令牌')
  })
})
