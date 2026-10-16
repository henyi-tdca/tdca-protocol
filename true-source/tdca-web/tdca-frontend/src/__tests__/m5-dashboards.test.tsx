// =============================================================================
// TDCA 制度水印
// FC-ID: KIMI-WEB-DB-TASK-001-M5 | 目标函数: M5 双后台前端测试（/me + /agents/:id + 路由注册）
// 约束矩阵: M5-PLAN §五 验收⑤（两页渲染 + meta 注册 + 登录引导）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { MePage } from '@/pages/me'
import { AuthProvider } from '@/app/auth-context'
import { AgentDashboardPage } from '@/pages/agent-dashboard'
import { PAGE_META, PAGE_COMPONENTS } from '@/pages/pages'

function envelope(payload: unknown, nature = 'real') {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-08-21T00:00:00Z', data_nature: nature }
}

const ME_PAYLOAD = {
  session: { username: 'founder', role: 'founder', expires_at: '2026-08-21T13:30:00+00:00' },
  pending_count: 2,
  my_agents: [
    { agent_id: 'AGENT-GENIE', name: 'Genie 效用精灵', five_role: 'mu', status: 'active', attestation_state: 'valid', audit_count: 3, data_provenance: 'simulated' },
  ],
  my_pending_sign: [
    { request_id: 'DAR-001', agent_id: 'AGENT-GENIE', request_type: 'scene_extension', urgency: 'urgent', reason: '扩展场景', ts: '2026-08-21T00:00:00Z' },
    { request_id: 'DAR-002', agent_id: 'AGENT-GENIE', request_type: 'meta', urgency: 'normal', reason: '', ts: '2026-08-21T00:00:00Z' },
  ],
  my_decided: [],
  my_sandbox: [{ apply_id: 'SBX-ab12', result: 'pending', ts: '2026-08-21T00:00:00Z' }],
  my_governance: [],
  note: 'test',
}

const AGENT_PAYLOAD = {
  profile: {
    agent_id: 'AGENT-GENIE', name: 'Genie 效用精灵', endpoint: 'tdca-utility-genie',
    capability: '正和满意解/效用计量', status: 'active', tdid: 'tdid:genie',
    five_role: 'mu', scene: 'tax', attestation_state: 'valid', audit_count: 3,
    owner_display: '创始人', created_at: '2026-08-20T00:00:00+00:00', data_provenance: 'simulated',
  },
  mou: [{ period: '2026-08', mou_inbound: 19000, mou_outbound: 1500, mou_total: 20500, note: 'n', ts: '2026-08-20T00:00:00Z' }],
  tax_events: [{ event_id: 'EVT-CASE002-01', type: 'dispatch_tax', amount: 4000, tax_rate_bp: 200, call_id: 'C1', nca_ref: 'NCA-SEED-001', ts: '2026-08-20T00:00:00Z' }],
  attestations: [{ request_id: 'DAR-001', request_type: 'scene_extension', urgency: 'urgent', status: 'pending', decided_by: null, reason: '扩展', nca_ref: null, ts: '2026-08-21T00:00:00Z' }],
  nca_chain: [{ nca_id: 'NCA-SEED-001', action: 'TaskLodge', actor: 'seed', prev_nca: 'GENESIS', ts: '2026-08-20T00:00:00Z' }],
  note: 'test',
}

function mockByUrl(routes: Record<string, unknown>) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    for (const [part, payload] of Object.entries(routes)) {
      if (url.includes(part)) return { ok: true, status: 200, json: async () => envelope(payload) } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
  }))
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('M5 双后台', () => {
  it('路由注册：/me 与 /agents/:id 均在 meta 与组件表', () => {
    const paths = PAGE_META.map((m) => m.path)
    expect(paths).toContain('/me')
    expect(paths).toContain('/agents/:id')
    expect(PAGE_COMPONENTS['/me']).toBe(MePage)
    expect(PAGE_COMPONENTS['/agents/:id']).toBe(AgentDashboardPage)
  })

  it('/me 未登录（401 fail）→ 登录引导提示', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      ({ ok: false, status: 401, json: async () => ({ detail: '未登录' }) }) as Response))
    render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-login-required')).toBeTruthy())
  })

  it('/me 登录后渲染：红签待办置顶 + 我的智能体行', async () => {
    mockByUrl({ '/api/v1/me/dashboard': ME_PAYLOAD })
    render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-pending-card').textContent).toContain('2 件'))
    expect(screen.getByTestId('me-agents').textContent).toContain('Genie 效用精灵')
    expect(screen.getByTestId('me-pending-list').textContent).toContain('DAR-001')
    expect(screen.getByTestId('me-sandbox').textContent).toContain('SBX-ab12')
  })

  it('/me 会话卡渲染最近缔约存证号（REGISTER-002 F4 前端展示，RR 复验 P3 修复）', async () => {
    mockByUrl({
      '/api/v1/me/dashboard': {
        ...ME_PAYLOAD,
        session: { ...ME_PAYLOAD.session, last_register_nca_id: 'NCA-WEB-test0123ab' },
      },
    })
    render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-register-nca').textContent).toContain('NCA-WEB-test0123ab'))
  })

  it('/me 无注册存证（如种子 founder）→ 不渲染存证行', async () => {
    mockByUrl({ '/api/v1/me/dashboard': ME_PAYLOAD })
    render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-session')).toBeTruthy())
    expect(screen.queryByTestId('me-register-nca')).toBeNull()
  })

  it('/me 运营者角色 → 渲染运营管理入口（货架/工单/公告三直达）', async () => {
    mockByUrl({
      '/api/v1/me/dashboard': {
        ...ME_PAYLOAD,
        session: { ...ME_PAYLOAD.session, role: 'operator' },
      },
    })
    render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-operator')).toBeTruthy())
    expect(screen.getByTestId('me-op-link-toolshelf')).toBeTruthy()
    expect(screen.getByTestId('me-op-link-ops')).toBeTruthy()
    expect(screen.getByTestId('me-op-link-announcements')).toBeTruthy()
  })

  it('/me 访客角色 → 不渲染运营管理入口', async () => {
    mockByUrl({
      '/api/v1/me/dashboard': {
        ...ME_PAYLOAD,
        session: { ...ME_PAYLOAD.session, role: 'viewer' },
      },
    })
    render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-session')).toBeTruthy())
    expect(screen.queryByTestId('me-operator')).toBeNull()
  })

  it('/agents/:id 渲染：画像 + MOU 合计（分→元）+ 脱敏归属', async () => {
    mockByUrl({ '/api/v1/agents/AGENT-GENIE/dashboard': AGENT_PAYLOAD })
    render(
      <MemoryRouter initialEntries={['/agents/AGENT-GENIE']}>
        <Routes><Route path="/agents/:id" element={<AgentDashboardPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('agent-dash-profile').textContent).toContain('Genie 效用精灵'))
    expect(screen.getByTestId('agent-dash-mou-total').textContent).toContain('¥205.00')
    expect(screen.getByTestId('agent-dash-profile').textContent).toContain('创始人')
    expect(screen.getByTestId('agent-dash-profile').textContent).not.toContain('owner_username')
    expect(screen.getByTestId('agent-dash-nca').textContent).toContain('NCA-SEED-001')
  })

  it('/agents/:id 不存在（404 fail）→ 兜底提示 + 返回链接', async () => {
    mockByUrl({})
    render(
      <MemoryRouter initialEntries={['/agents/AGENT-NOPE']}>
        <Routes><Route path="/agents/:id" element={<AgentDashboardPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('agent-dash-404').textContent).toContain('没有找到'))
  })
})
